# RENCANA — Build 29: CBOR

Sumber: **RFC 8949** (Concise Binary Object
Representation) — saudaranya JSON (build 16)
dalam bentuk biner. Jangkar: **Appendix A**
(81 contoh resmi: diagnostik <-> hex) dan
**Appendix F** (contoh malformed yang wajib
ditolak). Wasit diferensial: pustaka **cbor2**.

## Lingkup

MASUK:
- Dekoder: 8 major type, panjang pasti &
  tak-pasti (indefinite), float 16/32/64
  (float16 didekode dari bit dengan tangan),
  tag generik + bignum (tag 2/3) menjadi int,
  nilai simple (false/true/null/undefined +
  simple tak-terpakai), string UTF-8 divalidasi,
  penolakan semua malformed Appendix F +
  terpotong/cadangan/break liar.
- Enkoder kanonik: bentuk terpendek untuk int
  dan panjang, float terpendek yang eksak
  (16 -> 32 -> 64), panjang pasti, kunci peta
  diurutkan menurut byte enkodenya
  (deterministik inti RFC 8949 4.2.1 — dipindah
  MASUK lingkup saat diferensial irisan 3
  membuktikan cbor2 kanonik mengurutkannya).

DILUAR (tercatat):
- Tag tanggal/waktu tidak
  dikonversi otomatis (tetap objek Tag),
  streaming API.

## Irisan

- [x] Irisan 1 — Dekoder inti + Appendix A
  bagian skalar: int semua lebar, float16,
  simple, string pendek.
- [x] Irisan 2 — Wadah + tag + tak-pasti:
  array/peta/tag/bignum/indefinite; Appendix A
  tuntas dua arah (dekode == cbor2, enkode ==
  hex tabel utk baris kanonik).
- [x] Irisan 3 — Penolakan + diferensial acak:
  Appendix F semua ditolak; ratusan nilai acak
  bolak-balik kita <-> cbor2.

## Pagar selesai

- [x] `uji_irisan1.py` … `uji_irisan3.py` hijau.
- [x] `CATATAN.md` satu halaman per irisan.
- [ ] Repo GitHub publik
  `build-your-own-cbor-python` terbit dan
  terverifikasi (SHA blob lokal == remote, halaman
  publik terbaca).
