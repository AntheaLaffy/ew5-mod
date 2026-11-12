#!/usr/bin/env bash
# 安装修改版到已连接的设备/模拟器
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
ADB="$SDK/platform-tools/adb"
APK="$ROOT/build/欧陆战争5_2.6.16_mod_signed.apk"

[ -x "$ADB" ] || ADB="$(command -v adb)"
[ -f "$APK" ] || { echo "找不到 APK: $APK" >&2; exit 1; }

echo "==> 卸载旧包（避免旧存档的 IdentityStatus=0 覆盖新默认值）"
"$ADB" uninstall com.easytech.ew5 >/dev/null 2>&1 || true

echo "==> 安装 $APK"
"$ADB" install -r "$APK"

echo "==> 启动"
"$ADB" shell am start -n com.easytech.ew5/com.easytech.ew5.LauncherActivity >/dev/null
echo "已启动。首次进入需同意隐私协议，然后在主菜单点「战役」确认实名拦截已消失。"
