#!/usr/bin/env python3
"""给 libeuropean-war-5.so 打「未登录不再弹云存档提示（SceneNeedBound）」补丁。

背景
----
点商店/商品时，引擎先判断账号字符串是否为空；为空且命中某个标志位就
replaceScene("SceneNeedBound")，弹出「尚未登录，无法使用云存档…」并把玩家挡回去。

arm64 原始逻辑（0x309e3c 附近）：
    BL  0x261920                    ; 判断是否需要登录
    TBZ w0, #0, 0x309e84            ; w0==0 -> 走正常流程
    ... replaceScene("SceneNeedBound")
    0x309e84: <正常打开购买界面>

x86 原始逻辑（0x309ef0 附近）：
    CALL 0x204830
    TEST al, al
    JE   0x309f52                   ; al==0 -> 走正常流程
    ... replaceScene("SceneNeedBound")
    0x309f52: <正常打开购买界面>

补丁把条件跳转改成无条件跳转，等价于「恒按已登录处理」，商店不再被拦截。

用法：python3 patch_lib.py <apktool_out 目录>
"""
import os
import struct
import sys

# (相对路径, VMA, 原始字节, 补丁后字节)
PATCHES = [
    # ---- arm64-v8a ----
    # 0x285580: TBZ w0,#0,0x2855c0  -> B 0x2855c0   (主菜单云存档提示)
    ("lib/arm64-v8a/libeuropean-war-5.so", 0x285580,
     bytes.fromhex("00020036"), bytes.fromhex("10000014")),
    # 0x2e8f0c: TBZ w0,#0,0x2e8f44  -> B 0x2e8f44
    ("lib/arm64-v8a/libeuropean-war-5.so", 0x2E8F0C,
     bytes.fromhex("c0010036"), bytes.fromhex("0e000014")),
    # 0x309e40: TBZ w0,#0,0x309e84  -> B 0x309e84   (点商店商品)
    ("lib/arm64-v8a/libeuropean-war-5.so", 0x309E40,
     bytes.fromhex("20020036"), bytes.fromhex("11000014")),
    # 0x339540: TBZ w0,#0,0x339588  -> B 0x339588
    ("lib/arm64-v8a/libeuropean-war-5.so", 0x339540,
     bytes.fromhex("40020036"), bytes.fromhex("12000014")),

    # ---- x86 ----
    # 0x231465: JE 0x2314b8 -> JMP
    ("lib/x86/libeuropean-war-5.so", 0x231465,
     bytes.fromhex("7451"), bytes.fromhex("eb51")),
    # 0x2aa759: JE 0x2aa796 -> JMP
    ("lib/x86/libeuropean-war-5.so", 0x2AA759,
     bytes.fromhex("743b"), bytes.fromhex("eb3b")),
    # 0x309efc: JE 0x309f52 -> JMP
    ("lib/x86/libeuropean-war-5.so", 0x309EFC,
     bytes.fromhex("7454"), bytes.fromhex("eb54")),
    # 0x2d17b6: JE 0x2d180e -> JMP
    ("lib/x86/libeuropean-war-5.so", 0x2D17B6,
     bytes.fromhex("7456"), bytes.fromhex("eb56")),
]


def parse_phdrs(data):
    """返回 [(p_offset, p_vaddr, p_filesz, p_flags)]，兼容 ELF32/ELF64。"""
    is64 = data[4] == 2
    if is64:
        e_phoff = struct.unpack_from("<Q", data, 0x20)[0]
        e_phentsize = struct.unpack_from("<H", data, 0x36)[0]
        e_phnum = struct.unpack_from("<H", data, 0x38)[0]
    else:
        e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
        e_phentsize = struct.unpack_from("<H", data, 0x2A)[0]
        e_phnum = struct.unpack_from("<H", data, 0x2C)[0]
    out = []
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        if is64:
            p_type, p_flags = struct.unpack_from("<II", data, off)
            p_offset, p_vaddr, _, p_filesz, _ = struct.unpack_from("<QQQQQ", data, off + 8)
        else:
            p_type, p_offset, p_vaddr, _, p_filesz, _, p_flags, _ = struct.unpack_from("<IIIIIIII", data, off)
        if p_type == 1:
            out.append((p_offset, p_vaddr, p_filesz, p_flags))
    return out


def vma_to_off(data, vma):
    for p_offset, p_vaddr, p_filesz, _ in parse_phdrs(data):
        if p_vaddr <= vma < p_vaddr + p_filesz:
            return p_offset + (vma - p_vaddr)
    return None


def patch_file(path, vma, old, new):
    data = bytearray(open(path, "rb").read())
    if data[:4] != b"\x7fELF":
        raise SystemExit("不是 ELF: " + path)
    off = vma_to_off(data, vma)
    if off is None:
        raise SystemExit("VMA 未映射到文件: %#x" % vma)
    cur = bytes(data[off:off + len(old)])
    if cur == new:
        print("  已打过，跳过  %#x" % vma)
        return False
    if cur != old:
        raise SystemExit("原始字节不匹配 @ %#x: 期望 %s 实际 %s" % (vma, old.hex(), cur.hex()))
    data[off:off + len(new)] = new
    open(path, "wb").write(bytes(data))
    print("  patch %-34s %#x  %s -> %s" % (os.path.basename(os.path.dirname(os.path.dirname(path))), vma,
                                           old.hex(), new.hex()))
    return True


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis", "apktool_out")
    print("==> 打 native 补丁（跳过未登录拦截）")
    n = 0
    for rel, vma, old, new in PATCHES:
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            print("  跳过（不存在）: " + rel)
            continue
        if patch_file(p, vma, old, new):
            n += 1
    print("完成，改动 %d 处" % n)


if __name__ == "__main__":
    main()
