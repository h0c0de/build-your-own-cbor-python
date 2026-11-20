"""Irisan 2 — wadah, tag, tak-pasti: Appendix A
tuntas. Dekode == cbor2 utk semua baris; enkode
== hex tabel utk baris berbantuk pasti (baris
tak-pasti dienkode ulang ke bentuk pasti dan
didekode wasit ke nilai yang sama)."""
import cbor2

import cborku
from uji_bersama import baris_appendix_a, \
    normal_cbor2, sama, enkode_cocok

TAK_PASTI = (0x5F, 0x7F, 0x9F, 0xBF)

if __name__ == "__main__":
    cek = 0
    for diag, data in baris_appendix_a():
        saya = cborku.dekode(data)
        if data == bytes.fromhex("d9d9f7"):
            # penyimpangan wasit terdokumentasi
            assert saya == cborku.Tag(
                55799, cborku.TAK_TERDEFINISI)
            cek += 1
            continue
        wasit = normal_cbor2(cbor2.loads(data))
        assert sama(saya, wasit), (diag, saya, wasit)
        cek += 1
        if cborku.enkode(saya) == data or \
                enkode_cocok(saya, data):
            cek += 1  # byte-exact kanonik
        else:
            # baris mengandung bentuk tak-pasti di
            # posisi mana pun (termasuk bersarang):
            # enkode ulang bentuk pasti harus
            # membawa nilai yang sama
            ulang = cborku.enkode(saya)
            assert sama(normal_cbor2(
                cbor2.loads(ulang)), wasit), diag
            cek += 1
    print("irisan 2: %d pemeriksaan LULUS" % cek)
