"""Irisan 1 — skalar Appendix A: semua baris yang
bukan wadah/tag diuji dekode == cbor2 dan (bila
kanonik) enkode == hex tabel."""
import cborku
from uji_bersama import baris_appendix_a, \
    normal_cbor2, sama, enkode_cocok
import cbor2

if __name__ == "__main__":
    cek = 0
    for diag, data in baris_appendix_a():
        if data[0] >> 5 in (4, 5, 6):
            continue
        if data[0] in (0x5F, 0x7F, 0x9F, 0xBF):
            continue  # tak-pasti: irisan 2
        if data[0] == 0xD9:  # tag 55799 dua arah di
            continue          # irisan 2
        saya = cborku.dekode(data)
        wasit = normal_cbor2(cbor2.loads(data))
        assert sama(saya, wasit), (diag, saya, wasit)
        cek += 1
        assert enkode_cocok(saya, data), \
            (diag, "enkode")
        cek += 1
    print("irisan 1: %d pemeriksaan LULUS" % cek)
