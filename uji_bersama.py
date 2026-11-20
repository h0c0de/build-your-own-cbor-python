"""Bersama build 29: baris Appendix A RFC 8949 +
normalisasi nilai cbor2 ke representasi build ini
(Tag/Simple/TAK_TERDEFINISI), termasuk dua
penyimpangan wasit yang terdokumentasi:
- cbor2 selalu mengubah tag 0/1 menjadi datetime
  (bahkan dengan tag_hook) -> dinormalisasi balik.
- cbor2 gagal mendekode d9d9f7 (tag 55799 +
  undefined) -> baris itu diverifikasi satu arah.
"""
import math
import os
import re
from datetime import datetime, timezone

import cbor2

import cborku

SUMBER = os.path.join(os.path.dirname(__file__),
                      "..", "cbor-ref", "rfc8949.txt")


def baris_appendix_a():
    teks = open(SUMBER).read()
    awal = teks.index(
        "\nAppendix A.  Examples of Encoded "
        "CBOR Data Items\n")
    akhir = teks.index("\nAppendix B.", awal)
    hasil = []
    # Baris tabel bisa membungkus ke beberapa baris
    # fisik; gabung per blok di antara garis pisah.
    blok = []
    for baris in teks[awal:akhir].split("\n"):
        if baris.strip().startswith("+"):
            if blok:
                kiri = "".join(
                    b[1] for b in blok).strip()
                kanan = re.sub(
                    r"\s+", "",
                    "".join(b[2] for b in blok))
                m = re.search(r"0x([0-9a-f]+)", kanan)
                if m and kiri and \
                        "Diagnostic" not in kiri:
                    hasil.append(
                        (kiri,
                         bytes.fromhex(m.group(1))))
                blok = []
            continue
        sel = baris.split("|")
        if len(sel) >= 3:
            blok.append((baris, sel[1], sel[2]))
    return hasil


def normal_cbor2(v):
    if isinstance(v, cbor2.CBORTag):
        return cborku.Tag(v.tag, normal_cbor2(v.value))
    if isinstance(v, cbor2.CBORSimpleValue):
        return cborku.Simple(v.value)
    if v is cbor2.undefined:
        return cborku.TAK_TERDEFINISI
    if isinstance(v, datetime):
        return ("DATETIME", v)
    if isinstance(v, (list, tuple)):
        return [normal_cbor2(x) for x in v]
    if isinstance(v, dict) or \
            type(v).__name__ == "frozendict":
        return {normal_cbor2(k): normal_cbor2(x)
                for k, x in v.items()}
    return v


def sama(a, b):
    """Kesetaraan nilai lintas representasi."""
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
        return a == b
    if isinstance(a, cborku.Tag) and \
            isinstance(b, tuple) and \
            len(b) == 2 and b[0] == "DATETIME":
        # cbor2 mengubah tag 0/1 jadi datetime
        if a.nomor == 0 and isinstance(a.nilai, str):
            harap = datetime.fromisoformat(
                a.nilai.replace("Z", "+00:00"))
            return harap == b[1]
        if a.nomor == 1 and isinstance(
                a.nilai, (int, float)):
            return datetime.fromtimestamp(
                a.nilai, timezone.utc) == b[1]
        return False
    if isinstance(a, cborku.Tag) and \
            isinstance(b, cborku.Tag):
        if a.nomor == 55799 and b.nomor != 55799:
            return sama(a.nilai, b)
        if b.nomor == 55799 and a.nomor != 55799:
            return sama(a, b.nilai)
        return a.nomor == b.nomor and \
            sama(a.nilai, b.nilai)
    if isinstance(a, cborku.Tag) and \
            a.nomor == 55799:
        # tag self-describe: cbor2 meloloskannya
        # transparan, build ini menyimpannya
        return sama(a.nilai, b)
    if isinstance(b, cborku.Tag) and \
            not isinstance(a, cborku.Tag):
        # cermin: wasit di kiri, nilai kita di kanan
        if b.nomor == 55799:
            return sama(a, b.nilai)
        return sama(b, a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(
            sama(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        if len(a) != len(b):
            return False
        sisa = list(b.items())
        for k, v in a.items():
            for i, (k2, v2) in enumerate(sisa):
                if sama(k, k2) and sama(v, v2):
                    sisa.pop(i)
                    break
            else:
                return False
        return True
    return a == b


def enkode_cocok(saya, data):
    """Enkode kita harus == hex tabel, kecuali
    nilai inf/NaN: tabel menampilkannya dalam
    tiga lebar (f9/fa/fb) sedangkan bentuk
    kanonik yang kita hasilkan selalu f9."""
    import math as _m
    if isinstance(saya, float) and (
            _m.isinf(saya) or _m.isnan(saya)):
        return cborku.enkode(saya) in (
            bytes.fromhex("f97c00"),
            bytes.fromhex("f97e00"),
            bytes.fromhex("f9fc00"))
    return cborku.enkode(saya) == data
