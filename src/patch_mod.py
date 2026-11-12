#!/usr/bin/env python3
"""Apply smali patches to the decoded EW5 tree (apktool_out)."""
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT = os.path.join(os.path.dirname(_HERE), "analysis", "apktool_out")
ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT

LOGIN_BODY = """    .locals 0

    invoke-static {}, Lcom/easytech/ew5/modx;->login()V

    return-void"""

BUY_BODY = """    .locals 0

    invoke-static {}, Lcom/easytech/ew5/modx;->buy()V

    return-void"""

START_PURCHASE_BODY = """    .locals 0

    sput p2, Lcom/easytech/ew5/ew5Activity;->Purchase_Index:I

    sput-object p1, Lcom/easytech/ew5/ew5Activity;->SET_ORDER_ID:Ljava/lang/String;

    invoke-static {}, Lcom/easytech/ew5/modx;->buy()V

    return-void"""

GET_KEY_HASH_BODY = """    .locals 1

    const-string v0, "QHHyWZHOPRbQpR6Tx18ZN42XRBU="

    return-object v0"""


def replace_method(path, signature, new_body, locals_hint=None):
    """Replace the body of a method, keeping its .method line."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    out = []
    i = 0
    patched = False
    while i < len(lines):
        line = lines[i]
        if line.startswith(".method") and signature in line:
            out.append(line)
            # skip original body
            j = i + 1
            while j < len(lines) and not lines[j].startswith(".end method"):
                j += 1
            out.append(new_body)
            out.append(".end method")
            i = j + 1
            patched = True
            continue
        out.append(line)
        i += 1
    if not patched:
        raise SystemExit("method not found: %s in %s" % (signature, path))
    new_text = "\n".join(out)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("patched %-40s in %s" % (signature, os.path.relpath(path, ROOT)))


def append_before_return(path, anchor_signature, snippet):
    """Insert snippet right before the `return-void` of a method."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")
    inside = False
    for idx, line in enumerate(lines):
        if line.startswith(".method") and anchor_signature in line:
            inside = True
            start = idx
            continue
        if inside and line.startswith(".end method"):
            # walk back to the last return-void
            back = idx - 1
            while back > start and lines[back].strip() != "return-void":
                back -= 1
            if lines[back].strip() != "return-void":
                raise SystemExit("no return-void in %s" % anchor_signature)
            lines[back:back] = snippet.split("\n") + [""]
            # bump .locals
            for k in range(start, start + 6):
                m = re.match(r"^(\s*\.locals )(\d+)$", lines[k])
                if m:
                    lines[k] = "%s%d" % (m.group(1), max(int(m.group(2)), 3))
                    break
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print("injected autoLogin into %s" % anchor_signature)
            return
    raise SystemExit("method not found: %s" % anchor_signature)


def main():
    act = os.path.join(ROOT, "smali", "com", "easytech", "ew5", "ew5Activity.smali")
    apk = os.path.join(ROOT, "smali", "com", "easytech", "lib", "ecApk.smali")

    replace_method(apk, "GetKeyHash()Ljava/lang/String;", GET_KEY_HASH_BODY)
    replace_method(act, "wxSignIn()V", LOGIN_BODY)
    replace_method(act, "AlipaySignIn()V", LOGIN_BODY)
    replace_method(act, "StartPurchase(Ljava/lang/String;II)V", START_PURCHASE_BODY)
    replace_method(act, "PurchaseConfirmDialog(II)V", BUY_BODY)
    replace_method(act, "Alipay(I)V", BUY_BODY)
    replace_method(act, "WxPay(ILjava/lang/String;)V", BUY_BODY)

    auto = """
    invoke-static {}, Lcom/easytech/ew5/modx;->autoLogin()V
"""
    append_before_return(act, "Show_Game_View(II)V", auto)


if __name__ == "__main__":
    main()
