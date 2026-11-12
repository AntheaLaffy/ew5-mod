# ew5-mod —— 欧陆战争5：帝国 2.6.16 逆向改造

```
ew5-mod/
├── build/                     成品 APK（唯一交付物）
├── src/                       补丁源文件（smali + 打补丁脚本）
├── analysis/                  反编译产物与原始样本
│   ├── original/              原始 APK
│   ├── apktool_out/           已打补丁的反编译树（可直接 apktool b）
│   ├── apktool_out_orig/      未打补丁的反编译树（对照）
│   ├── jadx_out/              jadx 反编译的 Java 源码
│   ├── libs/                  从 APK 抽出的 native 库（arm64 / armeabi-v7a / x86）
│   ├── dexsrc/                拆出来的 dex 与修复过校验和的 assets dex
│   └── logs/                  apktool / jadx / rizin 运行日志
├── tools/                     签名密钥、Frida 验证脚本
├── evidence/                  模拟器实测截图
├── docs/                      完整逆向记录
└── scripts/                   build.sh / install.sh
```

## 成品

`build/欧陆战争5_2.6.16_mod_signed.apk`
包名 `com.easytech.ew5` 不变，v1+v2 重签
SHA-256 `dd77cc76c78de7f414c4fb0e74a6783fa9c5d514ea2a14a24077e85a25737ee4`

## 改动摘要

| 目标 | 位置 | 做法 |
|---|---|---|
| 去掉「安装包不完整」校验 | `ecApk.GetKeyHash()` | 恒返回原厂证书哈希 `QHHyWZHOPRbQpR6Tx18ZN42XRBU=` |
| 去掉实名/防沉迷硬拦截 | `assets/global_data.xml` | `IdentityStatus 0→18`、`Age 12→18`、`OnlineTime 1→99999` |
| 登录不再依赖微信/支付宝 | `wxSignIn()` / `AlipaySignIn()` | 直接 `nativeGameLoginSuccess("wxmod","")`；启动后自动重试 |
| 商店购买免支付 | `StartPurchase` / `PurchaseConfirmDialog` / `Alipay` / `WxPay` | 直接 `ResPurchase(1)`，把成功码回传 native |

native 库一个字节都没改。

## 使用

```bash
# 安装（务必先卸载：旧存档里的 IdentityStatus=0 会盖掉新默认值）
bash scripts/install.sh

# 或者手动
adb uninstall com.easytech.ew5
adb install -r build/欧陆战争5_2.6.16_mod_signed.apk
```

## 重建

```bash
bash scripts/build.sh
```

脚本会：反编译原始 APK → 打 smali 补丁 → 改 global_data.xml → 重打包 → zipalign → 签名。
需要 `apktool`、`zipalign`、`apksigner`（脚本里 `$ANDROID_HOME/build-tools/33.0.2`）。

## 验证

真机/模拟器接上 frida-server 后：

```bash
frida -U -p $(adb shell pidof com.easytech.ew5 | tr -d '\r') \
      -l tools/verify_purchase.js --runtime=qjs -q
```

输出 `ResPurchase(1)` → `PurchaseSuccess(1, MODTEST_ORDER_1)` 即购买链路已绕过支付。

## 已知限制

1. 云存档需要真账号：伪造 openid 只让客户端进「已登录」分支，服务端不认。
2. 实名状态是存档默认值，只对全新安装生效；旧存档在 `/data/data/com.easytech.ew5/files/na.czl`。
3. 内购若运营侧做订单二次校验，物品可能不落库；纯本地发放的道具不受影响。

详见 [docs/README_逆向记录.md](docs/README_逆向记录.md)。
