import zlib
from deca.file import ArchiveFile


class AafHeader:
    def __init__(self):
        self.magic = None
        self.version = None
        self.aic = None
        self.size_u = None
        self.section_max_size_u = None
        self.section_count = None


def load_aaf_header(fin):
    with ArchiveFile(fin) as f:
        aafh = AafHeader()
        aafh.magic = f.read(4)
        aafh.version = f.read_u32()
        aafh.aic = f.read(8+16+4)
        aafh.size_u = f.read_u32()  # uncompressed length, whole file
        aafh.section_size = f.read_u32()  # uncompress length, max any section?
        aafh.section_count = f.read_u32()  # section count? Normally 1 (2-5 found), number of 32MiB blocks?
    return aafh


def extract_aaf(src, dst):
    f = src
    magic = f.read(4)
    version = f.read_u32()
    aic = f.read(8+16+4)
    uncompressed_length = f.read_u32()  # uncompressed length, whole file
    section_size = f.read_u32()  # uncompress length, max any section?
    section_count = f.read_u32()  # section count? Normally 1 (2-5 found), number of 32MiB blocks?

    with open(dst, 'wb') as fo:
        for i in range(section_count):
            section_start = f.tell()
            section_compressed_length = f.read_u32()  # compressed length no including padding
            section_uncompressed_length = f.read_u32()  # full length?
            section_length_with_header = f.read_u32()  # padded length + 16
            magic_ewam = f.read(4)                         # 'EWAM'
            buf = f.read(section_compressed_length)
            obuf = zlib.decompress(buf,-15)
            fo.write(obuf)
            f.seek(section_length_with_header + section_start)
            # print(section_compressed_length, section_uncompressed_length, section_length_with_header, magic_ewam)
            if len(obuf) != section_uncompressed_length:
                raise Exception('Uncompress Failed {} -> {}'.format(src, dst))
