"""CBOR (RFC 8949) — dekoder + enkoder kanonik.

Delapan major type, panjang pasti dan tak-pasti,
float 16/32/64 (float16 didekode dari bitnya
dengan tangan), tag generik, bignum (tag 2/3)
menjadi int Python, dan penolakan tegas atas
semua kelas malformed Appendix F.
"""

import struct


class GalatCBOR(Exception):
    pass


class Tag:
    def __init__(self, nomor, nilai):
        self.nomor = nomor
        self.nilai = nilai

    def __eq__(self, lain):
        return isinstance(lain, Tag) and \
            self.nomor == lain.nomor and \
            self.nilai == lain.nilai

    def __repr__(self):
        return "Tag(%r, %r)" % (self.nomor, self.nilai)


class Simple:
    def __init__(self, nilai):
        self.nilai = nilai

    def __eq__(self, lain):
        return isinstance(lain, Simple) and \
            self.nilai == lain.nilai

    def __repr__(self):
        return "Simple(%r)" % (self.nilai,)


class _TakTerdefinisi:
    def __repr__(self):
        return "TAK_TERDEFINISI"


TAK_TERDEFINISI = _TakTerdefinisi()

_PUTUS = object()
_KEDALAMAN_MAKS = 600


class _Dekoder:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def _byte(self):
        if self.pos >= len(self.data):
            raise GalatCBOR("data habis di tengah")
        b = self.data[self.pos]
        self.pos += 1
        return b

    def _ambil(self, n):
        if self.pos + n > len(self.data):
            raise GalatCBOR("data habis di tengah")
        potong = self.data[self.pos:self.pos + n]
        self.pos += n
        return potong

    def _argumen(self, info):
        """Nilai argumen dari info tambahan; None
        berarti tak-pasti (info 31)."""
        if info < 24:
            return info
        if info == 24:
            return self._byte()
        if info == 25:
            return int.from_bytes(self._ambil(2),
                                  "big")
        if info == 26:
            return int.from_bytes(self._ambil(4),
                                  "big")
        if info == 27:
            return int.from_bytes(self._ambil(8),
                                  "big")
        if info == 31:
            return None
        raise GalatCBOR(
            "info tambahan cadangan: %d" % info)

    def item(self, dalam=0, boleh_putus=False):
        if dalam > _KEDALAMAN_MAKS:
            raise GalatCBOR("bersarang terlalu dalam")
        awal = self._byte()
        major, info = awal >> 5, awal & 31
        if major == 7 and info == 31:
            if boleh_putus:
                return _PUTUS
            raise GalatCBOR("break di luar konteks")
        if major in (0, 1):
            n = self._argumen(info)
            if n is None:
                raise GalatCBOR(
                    "major 0/1 tak boleh tak-pasti")
            return n if major == 0 else -1 - n
        if major in (2, 3):
            return self._string(major, info)
        if major == 4:
            return self._array(info, dalam)
        if major == 5:
            return self._peta(info, dalam)
        if major == 6:
            n = self._argumen(info)
            if n is None:
                raise GalatCBOR(
                    "tag tak boleh tak-pasti")
            isi = self.item(dalam + 1)
            if isi is _PUTUS:
                raise GalatCBOR("tag tanpa isi")
            if n == 2 and isinstance(isi, bytes):
                return int.from_bytes(isi, "big")
            if n == 3 and isinstance(isi, bytes):
                return -1 - int.from_bytes(isi, "big")
            return Tag(n, isi)
        return self._simple(info)

    def _string(self, major, info):
        n = self._argumen(info)
        if n is not None:
            mentah = self._ambil(n)
        else:
            gabung = bytearray()
            while True:
                if self.pos >= len(self.data):
                    raise GalatCBOR(
                        "string tak-pasti tak ditutup")
                kepala = self.data[self.pos]
                if kepala == 0xFF:
                    self.pos += 1
                    break
                self.pos += 1
                cmajor = kepala >> 5
                cinfo = kepala & 31
                if cmajor != major:
                    raise GalatCBOR(
                        "potongan string beda major")
                cn = self._argumen(cinfo)
                if cn is None:
                    raise GalatCBOR(
                        "potongan string tak-pasti")
                gabung += self._ambil(cn)
            mentah = bytes(gabung)
        if major == 2:
            return bytes(mentah)
        try:
            return mentah.decode("utf-8")
        except UnicodeDecodeError:
            raise GalatCBOR("teks bukan UTF-8 sah")

    def _array(self, info, dalam):
        n = self._argumen(info)
        hasil = []
        if n is None:
            while True:
                x = self.item(dalam + 1,
                              boleh_putus=True)
                if x is _PUTUS:
                    return hasil
                hasil.append(x)
        for _ in range(n):
            hasil.append(self.item(dalam + 1))
        return hasil

    def _peta(self, info, dalam):
        n = self._argumen(info)
        pasangan = []
        if n is None:
            while True:
                k = self.item(dalam + 1,
                              boleh_putus=True)
                if k is _PUTUS:
                    break
                v = self.item(dalam + 1)
                if v is _PUTUS:
                    raise GalatCBOR(
                        "break di posisi nilai peta")
                pasangan.append((k, v))
        else:
            for _ in range(n):
                k = self.item(dalam + 1)
                v = self.item(dalam + 1)
                if k is _PUTUS or v is _PUTUS:
                    raise GalatCBOR(
                        "break di peta pasti")
                pasangan.append((k, v))
        hasil = {}
        for k, v in pasangan:
            try:
                hash(k)
            except TypeError:
                return pasangan
            hasil[k] = v
        return hasil

    def _simple(self, info):
        if info < 20:
            return Simple(info)
        if info == 20:
            return False
        if info == 21:
            return True
        if info == 22:
            return None
        if info == 23:
            return TAK_TERDEFINISI
        if info == 24:
            b = self._byte()
            if b < 32:
                raise GalatCBOR(
                    "simple dua-byte cadangan: %d" % b)
            return Simple(b)
        if info == 25:
            return _dari_float16(self._ambil(2))
        if info == 26:
            return struct.unpack(
                ">f", self._ambil(4))[0]
        if info == 27:
            return struct.unpack(
                ">d", self._ambil(8))[0]
        raise GalatCBOR(
            "info tambahan cadangan: %d" % info)


def _dari_float16(dua):
    h = int.from_bytes(dua, "big")
    tanda = -1.0 if h & 0x8000 else 1.0
    eksp = (h >> 10) & 0x1F
    frac = h & 0x3FF
    if eksp == 0:
        return tanda * (frac / 1024) * 2 ** -14
    if eksp == 31:
        if frac == 0:
            return tanda * float("inf")
        return float("nan")
    return tanda * (1 + frac / 1024) * 2 ** (eksp - 15)


def dekode(data):
    """bytes CBOR -> nilai Python. Seluruh byte
    harus terpakai (sisa = GalatCBOR)."""
    d = _Dekoder(bytes(data))
    nilai = d.item()
    if nilai is _PUTUS:
        raise GalatCBOR("break di luar konteks")
    if d.pos != len(d.data):
        raise GalatCBOR("byte sisa tak terpakai")
    return nilai


# ---------------- enkoder (kanonik) --------------

def _kepala(major, n):
    if n < 24:
        return bytes([(major << 5) | n])
    if n < 256:
        return bytes([(major << 5) | 24, n])
    if n < 65536:
        return bytes([(major << 5) | 25]) + \
            n.to_bytes(2, "big")
    if n < 2 ** 32:
        return bytes([(major << 5) | 26]) + \
            n.to_bytes(4, "big")
    return bytes([(major << 5) | 27]) + \
        n.to_bytes(8, "big")


def _enkode_float(v):
    if v != v:  # NaN -> bentuk kanonik RFC
        return bytes.fromhex("f97e00")
    if v == float("inf"):
        return bytes.fromhex("f97c00")
    if v == float("-inf"):
        return bytes.fromhex("f9fc00")
    for fmt, info in (("e", 25), ("f", 26)):
        try:
            kemas = struct.pack(">" + fmt, v)
        except OverflowError:
            continue
        if struct.unpack(">" + fmt, kemas)[0] == v:
            return bytes([(7 << 5) | info]) + kemas
    return bytes([(7 << 5) | 27]) + \
        struct.pack(">d", v)


def enkode(nilai):
    """Nilai Python -> bytes CBOR kanonik
    (bentuk terpendek, panjang pasti)."""
    if nilai is True:
        return b"\xf5"
    if nilai is False:
        return b"\xf4"
    if nilai is None:
        return b"\xf6"
    if nilai is TAK_TERDEFINISI:
        return b"\xf7"
    if isinstance(nilai, Simple):
        n = nilai.nilai
        if n < 24:
            return bytes([(7 << 5) | n])
        if n < 32:
            # f8 18..f8 1f adalah bentuk cadangan
            # (Appendix F subkind 2) — tak bisa
            # dienkode secara sah
            raise GalatCBOR(
                "simple 24..31 tak terenkode sah")
        return bytes([0xF8, n])
    if isinstance(nilai, Tag):
        return _kepala(6, nilai.nomor) + \
            enkode(nilai.nilai)
    if isinstance(nilai, int):
        if 0 <= nilai < 2 ** 64:
            return _kepala(0, nilai)
        if -2 ** 64 <= nilai < 0:
            return _kepala(1, -1 - nilai)
        if nilai >= 2 ** 64:
            mentah = nilai.to_bytes(
                (nilai.bit_length() + 7) // 8, "big")
            return _kepala(6, 2) + \
                _kepala(2, len(mentah)) + mentah
        m = -1 - nilai
        mentah = m.to_bytes(
            (m.bit_length() + 7) // 8, "big")
        return _kepala(6, 3) + \
            _kepala(2, len(mentah)) + mentah
    if isinstance(nilai, float):
        return _enkode_float(nilai)
    if isinstance(nilai, (bytes, bytearray)):
        return _kepala(2, len(nilai)) + bytes(nilai)
    if isinstance(nilai, str):
        mentah = nilai.encode("utf-8")
        return _kepala(3, len(mentah)) + mentah
    if isinstance(nilai, (list, tuple)):
        return _kepala(4, len(nilai)) + b"".join(
            enkode(x) for x in nilai)
    if isinstance(nilai, dict):
        pasangan = [(enkode(k), enkode(v))
                    for k, v in nilai.items()]
        # Deterministik inti RFC 8949 4.2.1: kunci
        # diurutkan menurut byte enkodenya
        pasangan.sort(key=lambda p: p[0])
        return _kepala(5, len(pasangan)) + b"".join(
            k + v for k, v in pasangan)
    raise GalatCBOR("tipe tak didukung: %r"
                    % type(nilai))
