import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mzs import MAGIC, pack_mzs, unpack_mzs

blob = os.urandom(300000)
packed = pack_mzs(blob, "resg00_01.ks.scn.m")
assert packed[:4] == MAGIC
(n,) = struct.unpack("<i", packed[4:8])
assert n == len(blob)
assert unpack_mzs(packed, "resg00_01.ks.scn.m") == blob
info = pack_mzs(blob, "scenario_info.psb.m")
assert unpack_mzs(info, "scenario_info.psb.m") == blob
assert pack_mzs(blob, "a") != pack_mzs(blob, "b")
print("selftest ok")
