# Build Your Own — CBOR

Enkoder + dekoder **CBOR** (RFC 8949) dalam
Python murni — saudara biner JSON (build 16).
Dibuktikan dengan **81 contoh resmi Appendix A**
dua arah (dekode cocok dengan wasit `cbor2`,
enkode byte-exact dengan hex tabel untuk semua
baris kanonik), **semua contoh malformed
Appendix F ditolak**, dan 300 nilai acak
bolak-balik identik dengan cbor2 — termasuk
byte enkode kanoniknya.

## Isi

| Berkas | Isi |
| --- | --- |
| `cborku.py` | Dekoder (8 major type, pasti + tak-pasti, float16 dari bit, tag, bignum) + enkoder kanonik deterministik |
| `uji_bersama.py` | Ekstraktor tabel Appendix A dari teks RFC + normalisasi wasit |
| `uji_irisan1.py` … `uji_irisan3.py` | Uji per irisan (perlu cbor2) |

## Memakai

```python
from cborku import enkode, dekode, Tag

data = enkode({"a": 1, "b": [True, None, 2.5]})
assert dekode(data) == {"a": 1, "b": [True, None, 2.5]}
assert dekode(bytes.fromhex("c249010000000000000000")) \
    == 2 ** 64          # bignum tag 2 -> int
```

## Tiga hal yang menentukan

1. **Satu byte kepala membawa tiga hal**: 3 bit
   major type, 5 bit info tambahan — nilai kecil
   langsung, 24/25/26/27 berarti argumen 1/2/4/8
   byte menyusul, 31 berarti "tak-pasti, baca
   sampai break". Info 28–30 adalah cadangan dan
   wajib ditolak, bukan ditebak.

2. **Float16 tidak punya pustaka di sini** —
   didekode dari bitnya: subnormal, normal, dan
   inf/NaN disusun manual dari tanda/eksponen/
   fraksi. Enkoder memilih lebar float *terpendek
   yang eksak* (16 → 32 → 64), jadi 1.0 menjadi
   `f93c00`, bukan 8 byte.

3. **Kanonik berarti juga mengurutkan kunci**:
   enkoder mengurutkan kunci peta menurut byte
   enkodenya (deterministik inti RFC §4.2.1).
   Tanpa itu, dua enkode dari peta yang sama bisa
   berbeda byte — dan diferensial melawan cbor2
   membuktikannya pada percobaan pertama.

## Kejujuran wasit

cbor2 menyimpang dari representasi build ini di
tiga tempat yang terdokumentasi di harness: tag
0/1 selalu diubahnya menjadi `datetime`, tag
55799 (self-describe) diloloskannya transparan,
dan `d9d9f7` gagal didekode olehnya sama sekali.
Ketiganya dinormalisasi/dicatat, bukan disembunyikan.

## Lisensi

Kode: MIT. RFC 8949 © IETF Trust. cbor2 hanya
wasit uji, tidak disertakan.
