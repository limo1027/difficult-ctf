"""
Shamir 秘密共享工具
支持：
- GF(256) 逐字节拆分
- ssss 兼容格式（十六进制文本）
- 二进制格式（bytes）
- 文件保存与加载
"""

import secrets
import binascii
import os

# ==================== GF(256) 有限域运算 ====================


def gf256_mul(a: int, b: int) -> int:
    """GF(256) 乘法（不可约多项式 x^8 + x^4 + x^3 + x + 1）"""
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi_bit = a & 0x80
        a = (a << 1) & 0xFF
        if hi_bit:
            a ^= 0x1B
        b >>= 1
    return p


def gf256_inv(a: int) -> int:
    """GF(256) 乘法逆元"""
    if a == 0:
        return 0
    # 扩展欧几里得算法
    t, new_t = 0, 1
    r, new_r = 0x11B, a
    while new_r != 0:
        temp_r, temp_new_r = r, new_r
        quotient = 0
        while temp_r and temp_new_r:
            deg_diff = temp_r.bit_length() - temp_new_r.bit_length()
            if deg_diff < 0:
                break
            temp_r ^= temp_new_r << deg_diff
            quotient ^= 1 << deg_diff
        r, new_r = new_r, temp_r
        t, new_t = new_t, t ^ (quotient * new_t)
    return t & 0xFF


def gf256_poly_eval(coeffs: list, x: int) -> int:
    """在 GF(256) 上计算多项式值"""
    result = 0
    for coeff in reversed(coeffs):
        result = gf256_mul(result, x) ^ coeff
    return result


def gf256_poly_interpolate(points: list) -> int:
    """
    拉格朗日插值，返回 f(0)
    points: [(x1, y1), (x2, y2), ...]
    """
    result = 0
    for i, (xi, yi) in enumerate(points):
        li = 1
        for j, (xj, _) in enumerate(points):
            if i != j:
                denom = xi ^ xj
                inv_denom = gf256_inv(denom)
                li = gf256_mul(li, gf256_mul(0 ^ xj, inv_denom))
        result ^= gf256_mul(yi, li)
    return result & 0xFF


# ==================== 核心 Shamir 函数 ====================

def split_bytes(data: bytes, n: int = 2, k: int = 2) -> list:
    """
    在 GF(256) 上逐字节进行 Shamir 秘密共享

    Args:
        data: 要拆分的字节数据
        n: 分片总数
        k: 还原所需的最少分片数（阈值）

    Returns:
        list of bytes: n 个分片
    """
    if k > n:
        raise ValueError(f"阈值 k({k}) 不能大于分片数 n({n})")
    if k < 2:
        raise ValueError("阈值 k 必须 >= 2")
    if not data:
        return [b''] * n

    xs = list(range(1, n + 1))
    shares = [[] for _ in range(n)]

    for byte_val in data:
        coeffs = [secrets.randbelow(256) for _ in range(k - 1)]
        coeffs.insert(0, byte_val)

        for idx, x in enumerate(xs):
            y = gf256_poly_eval(coeffs, x)
            shares[idx].append(y)

    return [bytes(s) for s in shares]


def combine_bytes(shares: list) -> bytes:
    """
    从分片还原原始数据

    Args:
        shares: 至少 k 个分片（bytes 列表）

    Returns:
        bytes: 原始数据
    """
    if len(shares) < 2:
        raise ValueError("需要至少2个分片才能还原")

    data_len = len(shares[0])
    for i, s in enumerate(shares):
        if len(s) != data_len:
            raise ValueError(f"分片 {i} 长度不一致: {len(s)} vs {data_len}")

    if data_len == 0:
        return b''

    points = [(i + 1, shares[i]) for i in range(len(shares))]

    recovered = bytearray()
    for byte_idx in range(data_len):
        byte_points = [(xi, yi[byte_idx]) for xi, yi in points]
        recovered.append(gf256_poly_interpolate(byte_points))

    return bytes(recovered)


def get_key(code):
    shares = split_bytes(code.encode(), n=2, k=2)
    hex1 = binascii.hexlify(shares[0]).decode().upper()
    hex2 = binascii.hexlify(shares[1]).decode().upper()
    return hex1, hex2
