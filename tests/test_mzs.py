import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from sgre.mzs import MAGIC, pack_mzs, unpack_mzs


def test_roundtrip():
    blob = os.urandom(300000)
    packed = pack_mzs(blob, "resg00_01.ks.scn.m")
    assert packed[:4] == MAGIC
    (n,) = struct.unpack("<i", packed[4:8])
    assert n == len(blob)
    assert unpack_mzs(packed, "resg00_01.ks.scn.m") == blob


def test_filename_keyed():
    blob = b"hello world" * 100
    assert pack_mzs(blob, "a") != pack_mzs(blob, "b")
    assert unpack_mzs(pack_mzs(blob, "a"), "a") == blob


def test_info_filename():
    blob = os.urandom(1024)
    info = pack_mzs(blob, "scenario_info.psb.m")
    assert unpack_mzs(info, "scenario_info.psb.m") == blob


def test_bad_magic():
    import pytest

    with pytest.raises(ValueError, match="bad MZS magic"):
        unpack_mzs(b"bad!" + b"\x00" * 100, "a")


def test_bad_zstd_magic():
    import pytest

    packed = bytearray(pack_mzs(b"hello world test data for corruption" * 20, "a"))
    packed[8] ^= 0xFF
    packed[9] ^= 0xFF
    with pytest.raises(ValueError):
        unpack_mzs(bytes(packed), "a")


def test_wrong_filename_fails():
    import pytest

    blob = b"secret data" * 50
    packed = pack_mzs(blob, "correct.scn.m")
    with pytest.raises(ValueError):
        unpack_mzs(packed, "wrong.scn.m")
