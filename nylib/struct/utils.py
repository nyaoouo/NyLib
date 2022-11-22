import ctypes


class fctypes:
    c_char: bytes = getattr(ctypes, 'c_char')
    c_int: int = getattr(ctypes, 'c_int')
    c_uint: int = getattr(ctypes, 'c_uint')
    c_int8: int = getattr(ctypes, 'c_int8')
    c_int16: int = getattr(ctypes, 'c_int16')
    c_int32: int = getattr(ctypes, 'c_int32')
    c_int64: int = getattr(ctypes, 'c_int64')
    c_uint8: int = getattr(ctypes, 'c_uint8')
    c_uint16: int = getattr(ctypes, 'c_uint16')
    c_uint32: int = getattr(ctypes, 'c_uint32')
    c_uint64: int = getattr(ctypes, 'c_uint64')
    c_byte: int = getattr(ctypes, 'c_byte')
    c_ubyte: int = getattr(ctypes, 'c_ubyte')
    c_short: int = getattr(ctypes, 'c_short')
    c_ushort: int = getattr(ctypes, 'c_ushort')
    c_long: int = getattr(ctypes, 'c_long')
    c_ulong: int = getattr(ctypes, 'c_ulong')
    c_longlong: int = getattr(ctypes, 'c_longlong')
    c_ulonglong: int = getattr(ctypes, 'c_ulonglong')
    c_float: float = getattr(ctypes, 'c_float')
    c_double: float = getattr(ctypes, 'c_double')
    c_void_p = ctypes.c_void_p


def next_bit(byte_offset, bit_offset=0):
    bit_offset += 1
    return byte_offset + bit_offset // 8, bit_offset % 8
