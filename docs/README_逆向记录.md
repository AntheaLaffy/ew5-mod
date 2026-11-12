# 欧陆战争5：帝国 v2.6.16 逆向记录（com.easytech.ew5，CN 官方渠道）

工作目录：`/home/fuurin/reverse/ew5-mod`
产物：`欧陆战争5_2.6.16_mod_signed.apk`（160,846,245 字节，包名不变，已 v1+v2 签名）

---

## 一、样本与工具链

| 项目 | 内容 |
|---|---|
| 原始包 | `欧陆战争5：帝国_2.6.16.apk`（versionCode 53，minSdk 21，targetSdk 29） |
| 引擎 | EasyTech 自研 `libeuropean-war-5.so`（arm64-v8a / armeabi-v7a / x86 三 ABI）+ Java 壳层 |
| 反编译 | apktool 3.0.3、jadx、llvm-objdump（aarch64/i386）、rizin |
| 动态 | AOSP x86_64 API 30 模拟器 + frida-server 17.23.3 |
| 签名 | build-tools 33.0.2 `zipalign` + `apksigner`，自建 `tools/mod.keystore`（android/android） |

包内 3 个 dex：`classes.dex`、`classes2.dex`、`assets/39285EFA.dex`（后者被自定义加密，无 dex 头，未参与本次修改）。

---

## 二、关键拦截点定位

### 1. 「您的安装包不完整」签名校验

`com.easytech.lib.CheckUpdate.StartCheckUpdate()`：

```java
if (this.mEw5Activity.mApkInfo.GetKeyHash().equals("QHHyWZHOPRbQpR6Tx18ZN42XRBU=")) { ... }
else { 弹窗（Base64 内容＝“您的安装包不完整，请下载完整包”）→ System.exit(0); }
```

`GetKeyHash()` 取 APK 签名证书 SHA-1 再 Base64。原签名证书
`SHA1: 40:71:F2:59:91:CE:3D:16:D0:A5:1E:93:C7:5F:19:37:8D:97:44:15` 的 Base64 恰为
`QHHyWZHOPRbQpR6Tx18ZN42XRBU=`。

**原版改包重签必然触发该弹窗并退出**，这就是「软件损坏请到官网下载」的来源。
native 层（含 libsgcore / libmetasec）里没有该哈希常量，校验只在 Java 侧这一处。

### 2. 登录（微信 / 支付宝）

- `ew5Activity.wxSignIn()` → `WXEntryActivity`（微信 SDK）→ `WeChatLoginFinish(openid)` → `nativeGameLoginSuccess("wx"+openid, "")`
- `ew5Activity.AlipaySignIn()` → `AlipayLoginActivity` → `AlipayLoginFinish(id)` → `nativeGameLoginSuccess("al"+id, "")`
- native `Java_com_easytech_ew5_ew5Activity_nativeGameLoginSuccess`（0x166fc8）→ `CSdk::onLoginSuccess(std::string, std::string)`（0x2b45c8）
- 未登录时主菜单只弹「尚未登录，无法使用云存档」，不是硬性阻断；但登录态会影响云存档与账号相关流程。

### 3. 实名认证 / 防沉迷（真正的硬拦截）

- 拦截弹窗文案来自 `assets/stringtable_cn.ini` 的 `online_time_visitor_tip`
  （"根据国家最新法规规定，未实名认证的用户不能体验任何游戏内容…"）
- 身份接口：`https://idcert.ieasytech.cn/authentication/{identity,localcheck,check,useraction}/`
- 场景名：`SceneIdentity`、`SceneIdentityTip`、`SceneLogin`、`SceneAndroidLogin`
- **存档结构在明文中**：`assets/global_data.xml` 的 `SettingProp` 里定义了
  `IdentityStatus`、`Age`、`OnlineDay`、`OnlineTime`，全部 `save="true"`：

```xml
<data name="IdentityStatus" type="int" value="0"  save="true"/>
<data name="OnlineTime"     type="int" value="1"  save="true"/>
<data name="Age"            type="int" value="12" save="true"/>
```

原版默认 `IdentityStatus=0`（未认证）→ 点击「战役/帝国/征服」直接被 tip 场景拦住。
这是本次最关键的发现：**不需要改 native，改默认存档字段即可**。

### 4. 内购

- `StartPurchase(String orderId, int index, int platform)` → `PurchaseConfirmDialog` → `Alipay()` / `WxPay()`
  → 支付 SDK → 结果回调 `ResPurchase(code)` → GL 线程 `PurchaseSuccess(code, SET_ORDER_ID)`（native）
- native `Java_com_easytech_ew5_ew5Activity_PurchaseSuccess`（0x16645c）把结果码经查表
  `{-2→3, -1→2, 0→0, 1→1}` 后交给游戏回调，`1` 即成功。
- 订单号由引擎在调用 `StartPurchase` 时传入（`SET_ORDER_ID`），因此跳过支付、直接回传 `1` 即可。

---

## 三、修改清单

### A. Java / smali

| 文件 | 方法 | 修改 |
|---|---|---|
| `smali/com/easytech/lib/ecApk.smali` | `GetKeyHash()` | 直接 `return "QHHyWZHOPRbQpR6Tx18ZN42XRBU="` → 通过完整性校验 |
| `smali/com/easytech/ew5/ew5Activity.smali` | `wxSignIn()` | 改为 `modx.login()`，不再依赖微信 App |
| 同上 | `AlipaySignIn()` | 改为 `modx.login()`，不再依赖支付宝 App |
| 同上 | `StartPurchase(...)` | 保留 `Purchase_Index` / `SET_ORDER_ID`，直接 `modx.buy()` |
| 同上 | `PurchaseConfirmDialog(II)` | 直接 `modx.buy()`（跳过确认框） |
| 同上 | `Alipay(I)` / `WxPay(...)` | 直接 `modx.buy()`（跳过支付 SDK） |
| 同上 | `Show_Game_View(...)` | 末尾注入 `modx.autoLogin()` |

新增类：
- `com/easytech/ew5/modx.smali`
  - `login()`：在 GL 线程复用 `ew5Activity$32` 回调 `nativeGameLoginSuccess("wxmod","")`
  - `buy()`：`ResPurchase(1)`
  - `autoLogin()`：起 `modx$auto` 线程
- `com/easytech/ew5/modx$auto.smali`：每 4 秒重试一次登录（共 10 次，幂等，同一 openid 会被引擎短路）

### B. assets

`assets/global_data.xml`：

```xml
IdentityStatus : 0  -> 18      (已实名/成年)
Age            : 12 -> 18
OnlineTime     : 1  -> 99999   (防沉迷计时)
```


### C. native 补丁（libeuropean-war-5.so，仅改 8 条指令）

原版点商店 / 账号相关入口时，会先判断账号字符串是否为空，为空则
`replaceScene("SceneNeedBound")` 弹出「尚未登录，无法使用云存档…」并把玩家挡回去。
补丁把 4 个创建点前的条件跳转改成无条件跳转，等价于「恒按已登录处理」：

| 架构 | 地址 | 原始 | 补丁 | 作用 |
|---|---|---|---|---|
| arm64 | `0x285580` | `TBZ w0,#0,+0x40` | `B +0x40` | 主菜单云存档提示 |
| arm64 | `0x2e8f0c` | `TBZ w0,#0,+0x38` | `B +0x38` | 账号相关入口 |
| arm64 | `0x309e40` | `TBZ w0,#0,+0x44` | `B +0x44` | 商店点商品 |
| arm64 | `0x339540` | `TBZ w0,#0,+0x48` | `B +0x48` | 商店/购买入口 |
| x86 | `0x231465` | `JE +0x51` | `JMP +0x51` | 同上 |
| x86 | `0x2aa759` | `JE +0x3b` | `JMP +0x3b` | 同上 |
| x86 | `0x309efc` | `JE +0x54` | `JMP +0x54` | 同上 |
| x86 | `0x2d17b6` | `JE +0x56` | `JMP +0x56` | 同上 |

补丁脚本：`src/patch_lib.py`，已并入 `scripts/build.sh` 第 5 步。

### D. 跳过新手教程

`assets/global_data.xml` 的 `Tutorial` 默认值 `0 → 99`，新号直接进关卡选择，
避免卡在教程第一步（方便调试，正常游玩可改回）。

### E. 未改动

- `libeuropean-war-5.so` 等 native 库完全未改（签名校验与实名判断均在 Java/资源层，改 native 无必要）
- 任何联网协议、服务器交互逻辑均未改

---

## 四、验证记录（模拟器实测）

| 验证项 | 结果 | 证据 |
|---|---|---|
| 改包重签后可启动，无「安装包不完整」 | ✅ | `../evidence/evidence_4_mod_mainmenu.png` |
| 原版点「战役」被实名提示拦截 | ✅（复现） | `../evidence/evidence_1_original_identity_block.png` |
| 修改版点「战役」进入战役场景 | ✅ | `../evidence/evidence_2_mod_campaign_unlocked.png` |
| 进入关卡简报（B.C.480 出征） | ✅ | `../evidence/evidence_3_mod_briefing.png` |
| 购买链路绕过支付 | ✅ | Frida 直调 `StartPurchase("MODTEST_ORDER_1",3,2)` 输出：`ResPurchase(1)` → `PurchaseSuccess(1, MODTEST_ORDER_1)` |
| 登录链路 | ✅（代码路径） | `wxSignIn()`/`AlipaySignIn()` 直接走 `nativeGameLoginSuccess`，无需微信/支付宝 |

购买验证脚本：`tools/verify_purchase.js`
登录验证脚本：`tools/verify_login.js`

模拟器日志（Frida 17，Java 桥）：

```
hooks ok
activity=com.easytech.ew5.ew5Activity@3e9b59a
[JAVA] ResPurchase(1)
StartPurchase invoked
[JAVA] PurchaseSuccess(1, MODTEST_ORDER_1)
```

---

## 五、重建步骤

```bash
cd /home/fuurin/reverse/ew5-mod
bash scripts/build.sh      # 反编译 → 打 smali 补丁 → 改 global_data → 重打包 → zipalign → 签名
bash scripts/install.sh    # 卸载旧包 + 安装 + 启动
```

`scripts/build.sh` 内部等价于：

1. `apktool d -f analysis/original/欧陆战争5：帝国_2.6.16.apk -o analysis/apktool_out`
2. 复制 `src/modx.smali`、`src/modx$auto.smali` 到 `analysis/apktool_out/smali/com/easytech/ew5/`
3. `python3 src/patch_mod.py analysis/apktool_out`
4. 改 `analysis/apktool_out/assets/global_data.xml`（IdentityStatus=18 / Age=18 / OnlineTime=99999）
5. `apktool b` → `zipalign -f -p 4` → `apksigner sign --ks tools/mod.keystore`（口令 android/android）

产物固定输出到 `build/欧陆战争5_2.6.16_mod_signed.apk`。

安装注意：**首次必须卸载旧包**（`adb uninstall com.easytech.ew5`），否则旧存档里的
`IdentityStatus=0` 会覆盖新的默认值，实名弹窗仍会出现。

## 六、已知限制

1. **云存档 / 微信支付宝真正登录**仍要走服务器：伪造 openid 只让客户端进入「已登录」分支，
   服务端不认这个账号，所以云存档不会真的可用。需要真账号时把 `wxSignIn()` 还原即可。
2. **实名状态是本地默认值**：只在全新安装（无旧存档）时生效。旧存档路径
   `/data/data/com.easytech.ew5/files/na.czl`，未 root 无法直接改；卸载重装即可。
3. **内购**：客户端已回传成功码，但若运营侧对订单做服务端二次校验，物品可能不落库；
   纯本地发放的道具（金币/勋章礼包）不受影响。
4. 模拟器为软件渲染，进入战役场景后 GL 线程负载很高，触摸响应会明显变慢，属模拟器性能问题，
   真机不受影响。
