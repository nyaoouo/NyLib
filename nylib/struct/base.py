
import ctypes
import re
import typing
import sys
from . import field
from ..utils._lazy_chunk import lazy_chunks_key

_CData = ctypes.c_int.__mro__[2]
_CStruct = typing.TypeVar('_CStruct')
bf_regex = re.compile(r'\| *(\d+|0x[\da-fA-F]+|0o[0-7]+|0b[10]+) *$')


def set_fields_from_annotations(cls: typing.Type[_CStruct]) -> typing.Type[_CStruct]:
    if not (annotations := getattr(cls, '__annotations__', None)): return cls
    global_namespace = getattr(sys.modules.get(cls.__module__, None), '__dict__', {})
    global_namespace[cls.__name__] = cls
    local_namespace = dict(vars(cls))
    fields = []
    off_fields = []

    def str_eval(v):
        if isinstance(v, str):
            return eval(v, global_namespace, local_namespace)
        return v

    if True:  # hasattr(global_namespace, lazy_chunks_key):
        def str_eval_with_lazy(v):
            if isinstance(v, str):
                for chunk in global_namespace.pop(lazy_chunks_key, ()):
                    chunk._load()
                return eval(v, global_namespace, local_namespace)
            return v
    else:
        str_eval_with_lazy = str_eval

    for name, type_hint in annotations.items():
        if isinstance(type_hint, str) and (match := bf_regex.search(type_hint)):
            bit_size = eval(match.group(1))
            type_hint = str_eval(type_hint[:match.start()])
            desc = (name, type_hint, bit_size)
            if preset := getattr(cls, name, None):
                byte_offset, bit_offset = preset
                setattr(cls, name, field.BitField(byte_offset, bit_offset, type_hint, bit_size))
                off_fields.append(desc)
            else:
                fields.append(desc)
        # field
        elif (byte_offset := getattr(cls, name, None)) is not None:
            setattr(cls, name, field.Field(type_hint, byte_offset, str_eval_with_lazy))
            off_fields.append((name, type_hint))
        else:
            fields.append((name, str_eval(type_hint)))
    if size := cls.__dict__.get('_size_'):
        try:
            p_size = ctypes.sizeof(cls.__mro__[-2])
        except TypeError:
            p_size = 0
        fields.append(('__nys_padding__', ctypes.c_uint8 * (size - p_size)))
    cls._fields_ = fields
    cls._off_fields_ = off_fields
    return cls


def struct_to_dict(data):
    d = {}
    for base in data.__class__.__mro__[-4::-1]:
        base_dict = base.__dict__
        for n, *_ in base_dict.get('_fields_', []):
            if n!='__nys_padding__':
                d[n] = serialize_data(getattr(data, n))
        for n, *_ in base_dict.get('_off_fields_', []):
            d[n] = serialize_data(getattr(data, n))
        if (pf := base_dict.get('_properties_field_')) is None:
            setattr(base, '_properties_field_', pf := [k for k, v in base_dict.items() if isinstance(v, property)])
        for n in pf:
            d[n] = serialize_data(getattr(data, n))
    return d


def array_to_list(data):
    base_type = data.__class__._type_
    if issubclass(base_type, ctypes.Array):
        return [array_to_list(v) for v in data]
    if issubclass(base_type, ctypes.Structure):
        return [struct_to_dict(v) for v in data]
    return data[:]


def serialize_data(data):
    if isinstance(data, ctypes.Array):
        return array_to_list(data)
    if isinstance(data, ctypes.Structure):
        return struct_to_dict(data)
    return data


def fmt_data(data):
    if isinstance(data, ctypes.Structure):
        return str(struct_to_dict(data))
    return str(data)


def offset(off, cls=None):
    if cls is None: return lambda _cls: offset(off, _cls)
    new_fields = []
    for base in reversed(cls.__mro__):
        if '_use_broken_old_ctypes_structure_semantics_' in cls.__dict__:
            new_fields.clear()
        new_fields.extend(getattr(base, '_fields_', []))
    # print(cls.__name__, new_fields)
    name_space = {
        '_use_broken_old_ctypes_structure_semantics_': True,
        '_fields_': [('__padding__', ctypes.c_uint8 * off), *new_fields]
    }
    new_off_fields = []
    for base in reversed(cls.__mro__):
        if '_use_broken_old_ctypes_structure_semantics_' in cls.__dict__:
            new_off_fields.clear()
        new_off_fields.extend(getattr(base, '_off_fields_', []))
    for name, *_ in new_off_fields:
        old_field: field.Field = getattr(cls, name)
        name_space[name] = field.Field(old_field._d_type, old_field.offset + off, old_field.str_eval)
    if new_off_fields:
        name_space['_off_fields_'] = new_off_fields
    return type(f'{cls.__name__}_off_{off}', (cls,), name_space)
