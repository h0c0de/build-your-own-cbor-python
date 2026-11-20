"""Irisan 3 — penolakan Appendix F + diferensial
acak dua arah melawan cbor2."""
import random

import cbor2

import cborku
from uji_bersama import normal_cbor2, sama

# Contoh malformed Appendix F.1 (ditranskrip dari
# teks RFC 8949 di ../cbor-ref, dikelompokkan apa
# adanya per subjenis di sana).
F_MALFORMED = """
18, 19, 1a, 1b, 19 01, 1a 01 02,
1b 01 02 03 04 05 06 07, 38, 58, 78, 98,
9a 01 ff 00, b8, d8, f8, f9 00, fa 00 00,
fb 00 00 00,
41, 61, 5a ff ff ff ff 00,
5b ff ff ff ff ff ff ff ff 01 02 03,
7a ff ff ff ff 00,
7b 7f ff ff ff ff ff ff ff 01 02 03,
81, 81 81 81 81 81 81 81 81, 82 00, a1,
a2 01 02, a1 00, a2 00 00 00,
c0,
5f 41 00, 7f 61 00,
9f, 9f 01 02, bf, bf 01 02 01 02, 81 9f,
9f 80 00, 9f 9f 9f 9f 9f ff ff ff ff,
9f 81 9f 81 9f 9f ff ff ff,
1c, 1d, 1e, 3c, 3d, 3e, 5c, 5d, 5e, 7c, 7d,
7e, 9c, 9d, 9e, bc, bd, be, dc, dd, de, fc,
fd, fe,
f8 00, f8 01, f8 18, f8 1f,
5f 00 ff, 5f 21 ff, 5f 61 00 ff, 5f 80 ff,
5f a0 ff, 5f c0 00 ff, 5f e0 ff, 7f 41 00 ff,
5f 5f 41 00 ff ff, 7f 7f 61 00 ff ff,
ff, 81 ff, 82 00 ff, a1 ff, a1 ff 00,
a1 00 ff, a2 00 00 ff, 9f 81 ff,
9f 82 9f 81 9f 9f ff ff ff ff,
bf 00 ff, bf 00 00 00 ff,
1f, 3f, df
"""


def daftar_f():
    keluar = []
    for potong in F_MALFORMED.replace("\n", " ") \
            .split(","):
        potong = potong.strip()
        if potong:
            keluar.append(bytes.fromhex(potong))
    return keluar


def nilai_acak(acak, dalam=0):
    pilihan = ["int", "float", "bytes", "str",
               "bool", "none"]
    if dalam < 3:
        pilihan += ["list", "dict", "tag", "bigint"]
    jenis = acak.choice(pilihan)
    if jenis == "int":
        return acak.choice([
            0, 1, 23, 24, 255, 256, 65535, 65536,
            2 ** 32, 2 ** 64 - 1, -1, -24, -256,
            -65536, -2 ** 64,
            acak.randrange(-10 ** 6, 10 ** 6)])
    if jenis == "bigint":
        return acak.choice([
            2 ** 64, 2 ** 64 + 12345, -2 ** 64 - 1,
            10 ** 30, -10 ** 30])
    if jenis == "float":
        return acak.choice([
            0.0, -0.0, 1.5, -2.25, 0.1, 3.14159,
            1e10, 1e-10, 65504.0,
            float("inf"), float("-inf")])
    if jenis == "bytes":
        return bytes(acak.randrange(256)
                     for _ in range(
                         acak.randrange(0, 12)))
    if jenis == "str":
        return acak.choice([
            "", "a", "IETF", "ü", "水", "𐅑",
            "teks panjang " * 5])
    if jenis == "bool":
        return acak.choice([True, False])
    if jenis == "none":
        return None
    if jenis == "tag":
        return cborku.Tag(
            acak.choice([61, 466, 1000, 55799]),
            nilai_acak(acak, dalam + 1))
    if jenis == "list":
        return [nilai_acak(acak, dalam + 1)
                for _ in range(acak.randrange(0, 5))]
    return {acak.choice(["a", "b", 1, 2, "kunci"]):
            nilai_acak(acak, dalam + 1)
            for _ in range(acak.randrange(0, 4))}


if __name__ == "__main__":
    cek = 0
    for data in daftar_f():
        try:
            cborku.dekode(data)
        except cborku.GalatCBOR:
            cek += 1
            continue
        raise AssertionError(
            "malformed diterima: " + data.hex())
    # setiap awalan murni dari item sah = terpotong
    for hx in ("8301820203820405", "a201020304",
               "1bffffffffffffffff",
               "9f018202039f0405ffff"):
        penuh = bytes.fromhex(hx)
        for i in range(len(penuh)):
            try:
                cborku.dekode(penuh[:i])
            except cborku.GalatCBOR:
                cek += 1
                continue
            raise AssertionError(
                "awalan diterima: %s[:%d]" % (hx, i))
    # byte sisa sesudah item sah -> ditolak
    try:
        cborku.dekode(bytes.fromhex("0001"))
        raise AssertionError("sisa diterima")
    except cborku.GalatCBOR:
        cek += 1
    acak = random.Random(29)
    for _ in range(300):
        v = nilai_acak(acak)
        data = cborku.enkode(v)
        assert sama(cborku.dekode(data), v)
        wasit = normal_cbor2(cbor2.loads(data))
        assert sama(wasit, v), (v, wasit)
        def ada_tag(x):
            if isinstance(x, (cborku.Tag,
                              cborku.Simple)) or \
                    x is cborku.TAK_TERDEFINISI:
                return True
            if isinstance(x, list):
                return any(ada_tag(i) for i in x)
            if isinstance(x, dict):
                return any(ada_tag(k) or ada_tag(i)
                           for k, i in x.items())
            return False

        data2 = None if ada_tag(v) else \
            cbor2.dumps(v, canonical=True)
        if data2 is not None:
            assert cborku.dekode(data2) == v or \
                sama(cborku.dekode(data2), v)
            assert data2 == data, (v, data2, data)
        cek += 1
    print("irisan 3: %d pemeriksaan LULUS" % cek)
