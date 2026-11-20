# CATATAN — Build 29: CBOR

Satu halaman per irisan: konsep inti + temuan.
Panduan: RFC 8949. Jangkar: Appendix A (81
contoh) + Appendix F (malformed). Wasit: cbor2.

## Irisan 1 — Skalar (106)

**Konsep.** Hampir semua CBOR adalah satu pola:
kepala (major, info) lalu argumen atau muatan.
Bilangan negatif dienkode sebagai −1−n supaya
rentangnya simetris; float16 adalah satu-satunya
skalar yang perlu dirakit dari bit.

**Temuan.** Tabel Appendix A sendiri mengajari
satu hal: Infinity dan NaN tampil di sana dalam
*tiga* lebar (f9/fa/fb) — tabel itu contoh
enkode yang sah, bukan tabel kanonik. Aturan
ujinya menyesuaikan: dekode harus cocok semua,
enkode hanya diikat pada bentuk kanonik f9
untuk nilai-nilai khusus itu.

## Irisan 2 — Wadah, tag, tak-pasti (162)

**Konsep.** Bentuk tak-pasti (info 31) mengubah
array/peta/string menjadi aliran yang ditutup
byte break 0xff; potongan string di dalamnya
wajib ber-major sama dan berbentuk pasti. Tag
adalah pembungkus bernomor: 2/3 = bignum,
sisanya disimpan generik sebagai Tag(n, isi).

**Temuan.** Dua pelajaran dokumen lagi: sel hex
tabel RFC membungkus ke baris fisik berikutnya
*tanpa* awalan 0x (baris URL tag 32 terpotong
sampai ekstraktornya menggabung per blok dan
membuang semua spasi), dan satu contoh
(`[1, [2, 3], [_ 4, 5]]`) menyembunyikan array
tak-pasti di *dalam* array pasti — jadi aturan
"byte-exact atau nilai-sama" tidak boleh hanya
melihat byte pertama berkas.

## Irisan 3 — Penolakan + diferensial (427)

**Konsep.** Appendix F membagi malformed jadi
tiga keluarga: data berlebih, data kurang
(termasuk kepala yang menggantung dan wadah tak
ditutup), dan galat sintaks lima subjenis —
cadangan info 28–30, simple dua-byte f8 <32,
potongan string salah major/berbentuk tak-pasti,
break di posisi liar, dan info 31 pada major
0/1/6. Dekoder yang menolak kelimanya dengan
tepat adalah dekoder yang strukturnya benar.

**Temuan.** Temuan terbesar seri build ini
justru dari diferensial acak: cbor2 kanonik
*mengurutkan kunci peta* menurut byte enkodenya
(RFC §4.2.1), enkoderku awalnya tidak. Lingkup
yang kutulis "di luar" ternyata bagian dari
definisi kanonik — RENCANA diperbaiki terbuka,
enkoder mengurutkan, dan sesudah itu byte
enkode 300 nilai acak identik dengan wasit,
bukan hanya nilainya.
