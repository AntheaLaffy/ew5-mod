#!/usr/bin/env bash
# 从原始样本重建修改版 APK
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
BT="$SDK/build-tools/33.0.2"
SRC_APK="$ROOT/analysis/original/欧陆战争5：帝国_2.6.16.apk"
WORK="$ROOT/analysis/apktool_out"
KEYSTORE="$ROOT/tools/mod.keystore"
OUT="$ROOT/build/欧陆战争5_2.6.16_mod_signed.apk"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

[ -f "$SRC_APK" ] || { echo "缺少原始样本: $SRC_APK" >&2; exit 1; }
[ -f "$KEYSTORE" ] || { echo "缺少签名密钥: $KEYSTORE" >&2; exit 1; }
[ -x "$BT/zipalign" ] || { echo "缺少 build-tools: $BT" >&2; exit 1; }

echo "==> 1/6 反编译"
rm -rf "$WORK"
apktool d -f "$SRC_APK" -o "$WORK" >"$ROOT/analysis/logs/apktool.log" 2>&1

echo "==> 2/6 注入 modx 辅助类"
cp "$ROOT/src/modx.smali" "$ROOT/src/modx\$auto.smali" "$WORK/smali/com/easytech/ew5/"

echo "==> 3/6 打 smali 补丁"
python3 "$ROOT/src/patch_mod.py" "$WORK"

echo "==> 4/6 改实名/防沉迷默认值"
python3 - "$WORK/assets/global_data.xml" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
for old, new in [
    ('<data name="IdentityStatus" type="int" value="0" save="true"/>',
     '<data name="IdentityStatus" type="int" value="18" save="true"/>'),
    ('<data name="Age" type="int" value="12" save="true"/>',
     '<data name="Age" type="int" value="18" save="true"/>'),
    ('<data name="OnlineTime" type="int" value="1" save="true"/>',
     '<data name="OnlineTime" type="int" value="99999" save="true"/>'),
]:
    if old not in s:
        sys.exit("global_data.xml 未找到预期字段: " + old)
    s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print("global_data.xml 已改")
PY

echo "==> 5/6 重打包"
apktool b "$WORK" -o "$TMP/unsigned.apk" >"$ROOT/analysis/logs/build.log" 2>&1

echo "==> 6/6 对齐与签名"
"$BT/zipalign" -f -p 4 "$TMP/unsigned.apk" "$TMP/aligned.apk"
mkdir -p "$(dirname "$OUT")"
"$BT/apksigner" sign \
    --ks "$KEYSTORE" --ks-pass pass:android --key-pass pass:android \
    --v1-signing-enabled true --v2-signing-enabled true \
    --out "$OUT" "$TMP/aligned.apk"
"$BT/apksigner" verify --print-certs "$OUT" | head -3

echo
echo "完成: $OUT"
ls -la "$OUT"
