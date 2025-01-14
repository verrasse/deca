import numpy as np
import struct
from deca.file import ArchiveFile
from deca.ff_aaf import load_aaf_header
from deca.ff_avtx import DdImageHeader
from deca.ff_types import *

# guess type
raw_image_size = {
    0x1000000: '',
    0x800000: '',
    0x400000: '',
    0x280000: '',
    0x200000: '',
    0x140000: '',
    0x100000: '',
    0xa0000: '',
    0x80000: '',
    0x40000: '',
    0x20000: '',
}


def file_stats(f, file_size):
    # TODO huge files will take a WHILE
    counts = np.zeros((256,), dtype=np.uint32)
    while True:
        buf = f.read(1024 * 1024)
        if len(buf) == 0:
            break
        buf = bytearray(buf)
        cnt = np.bincount(buf, minlength=256)
        counts = counts + cnt
    return counts


def determine_file_type_and_size(f, file_size0):
    file_type = None
    file_sub_type = None
    file_size = file_size0

    start_pos = f.tell()
    magic: bytes = f.read(256)
    magic_int = None
    if len(magic) >= 20:
        magic_int = struct.unpack('I', magic[0:4])[0]

        if magic.startswith(b' FDA'):
            file_type = FTYPE_ADF
        elif magic.startswith(b'\x00FDA'):
            file_type = FTYPE_ADF0
        elif magic.startswith(b'\x01\x01\x00\x00\x00 FDA'):
            file_type = FTYPE_ADF5
        elif magic.startswith(b'AVTX'):
            file_type = FTYPE_AVTX
            header = DdImageHeader()
            header.deserialize_ddsc(magic)
            file_sub_type = header.dds_header_dxt10.dxgiFormat
        elif magic.startswith(b'DDS '):
            file_type = FTYPE_DDS
            header = DdImageHeader()
            header.deserialize_dds(magic)
            file_sub_type = header.dds_header_dxt10.dxgiFormat
        elif magic.upper().startswith(b'AAF'):
            file_type = FTYPE_AAF
            f.seek(start_pos)
            aafh = load_aaf_header(f)
            file_size = aafh.size_u
        elif magic.startswith(b'RTPC'):
            file_type = FTYPE_RTPC
        elif magic.startswith(b'CFX'):
            file_type = FTYPE_GFX
        elif magic.startswith(b'GFX'):
            file_type = FTYPE_GFX
        elif magic.startswith(b'RIFF'):
            file_type = FTYPE_RIFF
        elif magic.startswith(b'OggS'):
            file_type = FTYPE_OGG
        elif magic.startswith(b'BM6'):
            file_type = FTYPE_BMP
        elif magic.startswith(b'BM8'):
            file_type = FTYPE_BMP
        elif magic.startswith(b'MDI\x00'):
            file_type = FTYPE_MDI
        elif magic.startswith(b'PFX\x00'):
            file_type = FTYPE_PFX
        elif b'SARC' == magic[4:8]:
            file_type = FTYPE_SARC
        elif b'TAG0' == magic[4:8]:
            file_type = FTYPE_TAG0
        elif b'FSB5' == magic[16:20]:
            file_type = FTYPE_FSB5C
        elif magic.startswith(b'\x57\xE0\xE0\x57\x10\xC0\xC0\x10'):
            file_type = FTYPE_H2014
        elif magic.startswith(b'\x05\x00\x00\x00RBMDL'):
            file_type = FTYPE_RBMDL
        elif magic.startswith(b'KB2'):
            file_type = FTYPE_BINK_KB2
        elif magic.startswith(b'BIK'):
            file_type = FTYPE_BINK_BIK
        elif magic.startswith(b'GT0C'):
            file_type = FTYPE_GT0C

    # need to inspect file structure

    fm = ArchiveFile(f)

    if file_type is None:
        # OBC files with (u32)4, (u32)count , 80 * count bytes, something to do with areas on the map? object placement?
        fm.seek(start_pos)
        ver = fm.read_u32()
        cnt = fm.read_u32()
        if ver == 4 and cnt * 80 + 8 == file_size0:
            file_type = FTYPE_OBC

    if file_type is None:  # text file only contains text bytes, json, xml, ...
        fm.seek(start_pos)
        counts = file_stats(fm, file_size0)
        all_sum = np.sum(counts)
        pri_sum = np.sum(counts[[9, 10, 13] + list(range(20, 128))])
        if all_sum == pri_sum:
            file_type = FTYPE_TXT

    return file_type, file_size, magic_int, file_sub_type
