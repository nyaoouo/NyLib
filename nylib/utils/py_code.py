# impl of the python marshal format
# https://github.com/python/cpython/blob/main/Python/marshal.c
import ctypes
import dataclasses
import enum
import io
import marshal
import struct
import typing

FLAG_REF = 0x80
SIZEOF_LONG = ctypes.sizeof(ctypes.c_void_p)


class TYPE(enum.IntEnum):
    NULL = ord("0")
    NONE = ord("N")
    FALSE = ord("F")
    TRUE = ord("T")
    STOPITER = ord("S")
    ELLIPSIS = ord(".")
    INT = ord("i")
    INT64 = ord("I")
    FLOAT = ord("f")
    BINARY_FLOAT = ord("g")
    COMPLEX = ord("x")
    BINARY_COMPLEX = ord("y")
    LONG = ord("l")
    STRING = ord("s")
    INTERNED = ord("t")
    REF = ord("r")
    TUPLE = ord("(")
    LIST = ord("[")
    DICT = ord("{")
    CODE = ord("c")
    UNICODE = ord("u")
    UNKNOWN = ord("?")
    SET = ord("<")
    FROZENSET = ord(">")
    ASCII = ord("a")
    ASCII_INTERNED = ord("A")
    SMALL_TUPLE = ord(")")
    SHORT_ASCII = ord("z")
    SHORT_ASCII_INTERNED = ord("Z")


@dataclasses.dataclass
class PyObject:
    _type_map_ = {}
    type: TYPE = TYPE.NULL
    flag: int = 0
    value = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._type_map_[cls.type.value] = cls
        if cls.__hash__ is None:
            for c in cls.__mro__:
                if c.__hash__ is not None:
                    cls.__hash__ = c.__hash__
                    break

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag)

    def to_buf(self, buf: typing.IO[bytes]):
        write_buf(buf, 'B', self.type.value | self.flag)

    def to_py(self) -> typing.Any:
        return self.value

    def __hash__(self):
        return hash(self.to_py())

    def __eq__(self, other):
        return self.to_py() == (other.to_py() if isinstance(other, PyObject) else other)

    @classmethod
    def read(cls, buf: typing.IO[bytes]) -> 'PyObject':
        type_, = read_buf(buf, 'B')
        if not type_: raise EOFError()
        flag = type_ & FLAG_REF
        type_ &= ~FLAG_REF
        if type_ not in cls._type_map_: raise ValueError(f"unknown type '{chr(type_)}' {type_:#x} ")
        return cls._type_map_[type_].from_buf(buf, flag)


NULL = PyObject()
PyObject._type_map_[NULL.type.value] = NULL


@dataclasses.dataclass
class Py_None(PyObject):
    type: TYPE = TYPE.NONE


@dataclasses.dataclass
class Py_False(PyObject):
    type: TYPE = TYPE.FALSE

    def to_py(self):
        return False


@dataclasses.dataclass
class Py_True(PyObject):
    type: TYPE = TYPE.TRUE

    def to_py(self):
        return True


@dataclasses.dataclass
class Py_StopIter(PyObject):
    type: TYPE = TYPE.STOPITER

    def to_py(self):
        return StopIteration()


@dataclasses.dataclass
class Py_Ellipsis(PyObject):
    type: TYPE = TYPE.ELLIPSIS

    def to_py(self):
        return Ellipsis


@dataclasses.dataclass
class Py_Int(PyObject):
    type: TYPE = TYPE.INT
    value: int = 0

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, *read_buf(buf, 'i'))

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_buf(buf, 'i', self.value)


@dataclasses.dataclass
class Py_Int64(PyObject):
    type: TYPE = TYPE.INT64
    value: int = 0

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, *read_buf(buf, 'q'))

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_buf(buf, 'q', self.value)


@dataclasses.dataclass
class Py_Float(PyObject):
    type: TYPE = TYPE.FLOAT
    value: float = 0.0

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, *read_buf(buf, 'd'))

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_buf(buf, 'd', self.value)


@dataclasses.dataclass
class Py_Complex(PyObject):
    type: TYPE = TYPE.COMPLEX
    real: float = 0.
    imag: float = 0.

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, read_float_str(buf), read_float_str(buf))

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_float_str(buf, self.real)
        write_float_str(buf, self.imag)

    def to_py(self):
        return self.real + self.imag * 1j


@dataclasses.dataclass
class Py_BinaryComplex(PyObject):
    type: TYPE = TYPE.BINARY_COMPLEX
    real: float = 0.
    imag: float = 0.

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, *read_buf(buf, 'DD'))

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_buf(buf, 'DD', self.real, self.imag)

    def to_py(self):
        return self.real + self.imag * 1j


@dataclasses.dataclass
class Py_String(PyObject):
    type: TYPE = TYPE.STRING
    value: bytes = b''

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, read_bytes(buf, 'i'))

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_bytes(buf, self.value, 'i')


@dataclasses.dataclass
class Py_Short_ASCII(PyObject):
    type: TYPE = TYPE.SHORT_ASCII
    value: str = ''

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, read_str(buf, encoding='ascii'))

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_str(buf, self.value, encoding='ascii')


@dataclasses.dataclass
class Py_Short_ASCII_Interned(Py_Short_ASCII):
    type: TYPE = TYPE.SHORT_ASCII_INTERNED


@dataclasses.dataclass
class Py_Ascii(PyObject):
    type: TYPE = TYPE.ASCII
    value: str = ''

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, read_str(buf, 'i', encoding='ascii'))

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_str(buf, self.value, 'i', encoding='ascii')


@dataclasses.dataclass
class Py_Ascii_Interned(Py_Ascii):
    type: TYPE = TYPE.ASCII_INTERNED


@dataclasses.dataclass
class Py_Unicode(PyObject):
    type: TYPE = TYPE.UNICODE
    value: str = ''

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, read_str(buf, 'i', errors="surrogatepass"))

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_str(buf, self.value, 'i', errors="surrogatepass")


@dataclasses.dataclass
class Py_Interned(Py_Unicode):
    type: TYPE = TYPE.INTERNED


@dataclasses.dataclass
class Py_Tuple(PyObject):
    type: TYPE = TYPE.TUPLE
    value: typing.List[PyObject] = dataclasses.field(default_factory=list)

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, [PyObject.read(buf) for _ in range(*read_buf(buf, 'i'))])

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_buf(buf, 'i', len(self.value))
        for obj in self.value:
            obj.to_buf(buf)

    def to_py(self):
        return tuple(obj.to_py() for obj in self.value)


@dataclasses.dataclass
class Py_SmallTuple(PyObject):
    type: TYPE = TYPE.SMALL_TUPLE
    value: typing.List[PyObject] = dataclasses.field(default_factory=list)

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, [PyObject.read(buf) for _ in range(*read_buf(buf, 'B'))])

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_buf(buf, 'B', len(self.value))
        for obj in self.value:
            obj.to_buf(buf)

    def to_py(self):
        return tuple(obj.to_py() for obj in self.value)


@dataclasses.dataclass
class Py_List(Py_Tuple):
    type: TYPE = TYPE.LIST

    def to_py(self):
        return list(obj.to_py() for obj in self.value)


@dataclasses.dataclass
class Py_Dict(PyObject):
    type: TYPE = TYPE.DICT
    value: typing.Dict[PyObject, PyObject] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        d = {}
        while True:
            key = PyObject.read(buf)
            if key.type == TYPE.NULL: break
            d[key] = PyObject.read(buf)
        return cls(cls.type, flag, d)

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        for key, value in self.value.items():
            key.to_buf(buf)
            value.to_buf(buf)
        NULL.to_buf(buf)

    def to_py(self):
        return {key.to_py(): value.to_py() for key, value in self.value.items()}


@dataclasses.dataclass
class Py_Set(PyObject):
    type: TYPE = TYPE.SET
    value: typing.Set[PyObject] = dataclasses.field(default_factory=set)

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, {PyObject.read(buf) for _ in range(*read_buf(buf, 'i'))})

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_buf(buf, 'i', len(self.value))
        for obj in self.value:
            obj.to_buf(buf)

    def to_py(self):
        return {obj.to_py() for obj in self.value}


@dataclasses.dataclass
class Py_FrozenSet(Py_Set):
    type: TYPE = TYPE.FROZENSET

    def to_py(self):
        return frozenset(obj.to_py() for obj in self.value)


@dataclasses.dataclass
class Py_Code(PyObject):
    type: TYPE = TYPE.CODE
    argcount: int = 0
    posonlyargcount: int = 0
    kwonlyargcount: int = 0
    stacksize: int = 0
    flags: int = 0
    code: PyObject = NULL
    consts: PyObject = NULL
    names: PyObject = NULL
    localsplusnames: PyObject = NULL
    localspluskinds: PyObject = NULL
    filename: PyObject = NULL
    name: PyObject = NULL
    qualname: PyObject = NULL
    firstlineno: int = 0
    linetable: PyObject = NULL
    exceptiontable: PyObject = NULL

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(
            cls.type, flag,
            *read_buf(buf, 'iiiii'),  # argcount, posonlyargcount, kwonlyargcount, stacksize, flags
            PyObject.read(buf),  # code
            PyObject.read(buf),  # consts
            PyObject.read(buf),  # names
            PyObject.read(buf),  # localsplusnames
            PyObject.read(buf),  # localspluskinds
            PyObject.read(buf),  # filename
            PyObject.read(buf),  # name
            PyObject.read(buf),  # qualname
            *read_buf(buf, 'i'),  # firstlineno
            PyObject.read(buf),  # linetable
            PyObject.read(buf),  # exceptiontable
        )

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_buf(buf, 'iiiii', self.argcount, self.posonlyargcount, self.kwonlyargcount, self.stacksize, self.flags)
        self.code.to_buf(buf)
        self.consts.to_buf(buf)
        self.names.to_buf(buf)
        self.localsplusnames.to_buf(buf)
        self.localspluskinds.to_buf(buf)
        self.filename.to_buf(buf)
        self.name.to_buf(buf)
        self.qualname.to_buf(buf)
        write_buf(buf, 'i', self.firstlineno)
        self.linetable.to_buf(buf)
        self.exceptiontable.to_buf(buf)

    def to_py(self):
        return Code(
            self.argcount,
            self.posonlyargcount,
            self.kwonlyargcount,
            self.stacksize,
            CodeFlags(self.flags),
            self.code.to_py(),
            self.consts.to_py(),
            self.names.to_py(),
            self.localsplusnames.to_py(),
            self.localspluskinds.to_py(),
            self.filename.to_py(),
            self.name.to_py(),
            self.qualname.to_py(),
            self.firstlineno,
            self.linetable.to_py(),
            self.exceptiontable.to_py(),
        )


@dataclasses.dataclass
class Py_Ref(PyObject):
    type: TYPE = TYPE.REF
    value: int = 0

    @classmethod
    def from_buf(cls, buf: typing.IO[bytes], flag: int):
        return cls(cls.type, flag, *read_buf(buf, 'i'))

    def to_buf(self, buf: typing.IO[bytes]):
        super().to_buf(buf)
        write_buf(buf, 'i', self.value)

    def to_py(self):
        return Ref(self.value)


@dataclasses.dataclass
class Ref:
    id: int

    def to_py_obj(self):
        return Py_Ref(value=self.id)


class CodeFlag(enum.IntEnum):
    CO_OPTIMIZED = 0x0001
    CO_NEWLOCALS = 0x0002
    CO_VARARGS = 0x0004
    CO_VARKEYWORDS = 0x0008
    CO_NESTED = 0x0010
    CO_GENERATOR = 0x0020
    CO_COROUTINE = 0x0080
    CO_ITERABLE_COROUTINE = 0x0100
    CO_ASYNC_GENERATOR = 0x0200
    CO_FUTURE_DIVISION = 0x20000
    CO_FUTURE_ABSOLUTE_IMPORT = 0x40000
    CO_FUTURE_WITH_STATEMENT = 0x80000
    CO_FUTURE_PRINT_FUNCTION = 0x100000
    CO_FUTURE_UNICODE_LITERALS = 0x200000
    CO_FUTURE_BARRY_AS_BDFL = 0x400000
    CO_FUTURE_GENERATOR_STOP = 0x800000
    CO_FUTURE_ANNOTATIONS = 0x1000000


class CodeFlags(set):
    def __init__(self, value: int):
        super().__init__(flag for flag in CodeFlag if bool(value & flag.value))

    @property
    def value(self):
        return sum(flag.value for flag in self)

    def __repr__(self):
        return self.__class__.__name__ + '(' + '|'.join(flag.name for flag in self) + ')'


@dataclasses.dataclass
class Code:
    argcount: int
    posonlyargcount: int
    kwonlyargcount: int
    stacksize: int
    flags: CodeFlags
    code: typing.Any
    consts: typing.Any
    names: typing.Any
    localsplusnames: typing.Any
    localspluskinds: typing.Any
    filename: typing.Any
    name: typing.Any
    qualname: typing.Any
    firstlineno: int
    linetable: typing.Any
    exceptiontable: typing.Any

    def to_py_obj(self):
        return


def read_bytes(buf: typing.IO[bytes], size_def='B'):
    return buf.read(*read_buf(buf, size_def))


def write_bytes(buf: typing.IO[bytes], value: bytes, size_def='B'):
    write_buf(buf, size_def, len(value))
    buf.write(value)


def read_str(buf: typing.IO[bytes], size_def='B', encoding='utf-8', errors='strict'):
    return read_bytes(buf, size_def).decode(encoding, errors)


def write_str(buf: typing.IO[bytes], value: str, size_def='B', encoding='utf-8', errors='strict'):
    write_bytes(buf, value.encode(encoding, errors), size_def)


def read_float_str(buf: typing.IO[bytes]):
    return float(read_bytes(buf))


def write_float_str(buf: typing.IO[bytes], value: float):
    write_bytes(buf, str(value).encode())


def read_buf(buf: typing.IO[bytes], struct_def):
    read_size = struct.calcsize(struct_def)
    data = buf.read(read_size)
    if len(data) != read_size: raise EOFError()
    return struct.unpack(struct_def, data)


def write_buf(buf: typing.IO[bytes], struct_def, *args):
    buf.write(struct.pack(struct_def, *args))


def test():
    code = '''
a = 'world'
b = 123
def print_hello(c):
    if c:
        print('hello', a, c)
    else:
        print('hello', a)
if __name__ == '__main__':
    print_hello(b)
'''
    code_bytes = marshal.dumps(compile(code, 'test.py', 'exec'))
    obj: Py_Code = PyObject.read(io.BytesIO(code_bytes))
    # print(obj)
    # print(obj.to_py())
    import dis,opcode
    for i, op, arg in dis._unpack_opargs(obj.to_py().consts[2].code):
        print(i, opcode.opname[op], arg)


if __name__ == '__main__':
    test()
