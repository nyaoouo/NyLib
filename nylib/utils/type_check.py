import inspect
import re
import types
import typing

_T = typing.TypeVar('_T')


class InvalidData(Exception):
    def __init__(self, path: typing.List[str], msg: str = ''):
        self.path = path
        _path = '/'.join(self.path)
        self.msg = f'{_path}: {msg}' if msg else _path
        super().__init__(self.msg)


class IValidator(typing.Generic[_T]):

    def validate(self, data: typing.Any, path: typing.List[str] = None) -> _T:
        if path is None: path = []
        return self.validate_(data, path)

    def validate_(self, data: typing.Any, path: typing.List[str]) -> _T:
        raise NotImplementedError()

    @classmethod
    def make(cls, t: typing.Type[_T]) -> 'IValidator[_T]':
        return cls()


class _AnyValidator(IValidator[typing.Any]):
    def validate_(self, data: typing.Any, path: typing.List[str]):
        return data


class _NoneValidator(IValidator[None]):
    def validate_(self, data: typing.Any, path: typing.List[str]):
        if data is not None:
            raise InvalidData(path, f'not None')
        return data


class _CachedInstance:
    def __new__(cls):  # should not have any arguments
        if hasattr(cls, '_instance'):
            return cls._instance
        cls._instance = super().__new__(cls)
        return cls._instance


class VString(IValidator[str], _CachedInstance):

    def validate_(self, data: typing.Any, path: typing.List[str]):
        if not isinstance(data, str):
            raise InvalidData(path, f'not a string')
        return data


class VStringEx(IValidator[str]):
    def __init__(self, min_len: int = 0, max_len: int = None, regex: str | re.Pattern = None):
        self.min_len = min_len
        self.max_len = max_len
        self.regex = regex if regex is None else re.compile(regex)

    def validate_(self, data: typing.Any, path: typing.List[str]):
        if not isinstance(data, str):
            raise InvalidData(path, f'not a string')
        if self.min_len is not None and len(data) < self.min_len:
            raise InvalidData(path, f'length too short, expect >= {self.min_len}, got {len(data)}')
        if self.max_len is not None and len(data) > self.max_len:
            raise InvalidData(path, f'length too long, expect <= {self.max_len}, got {len(data)}')
        if self.regex is not None and not re.match(self.regex, data):
            raise InvalidData(path, f'not match regex {self.regex!r}')
        return data


class VInt(IValidator[int], _CachedInstance):
    def validate_(self, data: typing.Any, path: typing.List[str]):
        if not isinstance(data, int):
            raise InvalidData(path, f'not an int')
        return data


class VIntEx(IValidator[int]):
    def __init__(self, min_val: int = None, max_val: int = None):
        self.min_val = min_val
        self.max_val = max_val

    def validate_(self, data: typing.Any, path: typing.List[str]):
        if not isinstance(data, int):
            raise InvalidData(path, f'not an int')
        if self.min_val is not None and data < self.min_val:
            raise InvalidData(path, f'value too small, expect >= {self.min_val}, got {data}')
        if self.max_val is not None and data > self.max_val:
            raise InvalidData(path, f'value too large, expect <= {self.max_val}, got {data}')
        return data


class VFloat(IValidator[float], _CachedInstance):
    def validate_(self, data: typing.Any, path: typing.List[str]):
        if not isinstance(data, (float, int)):
            raise InvalidData(path, f'not a float')
        return data


class VFloatEx(IValidator[float]):
    def __init__(self, min_val: float = None, max_val: float = None):
        self.min_val = min_val
        self.max_val = max_val

    def validate_(self, data: typing.Any, path: typing.List[str]):
        if not isinstance(data, (float, int)):
            raise InvalidData(path, f'not a float')
        if self.min_val is not None and data < self.min_val:
            raise InvalidData(path, f'value too small, expect >= {self.min_val}, got {data}')
        if self.max_val is not None and data > self.max_val:
            raise InvalidData(path, f'value too large, expect <= {self.max_val}, got {data}')
        return data


class VBool(IValidator[bool], _CachedInstance):
    def validate_(self, data: typing.Any, path: typing.List[str]):
        if isinstance(data, bool):
            return data
        if isinstance(data, (int, float)):
            return bool(data)
        raise InvalidData(path, f'not a bool')


class vList(IValidator[list]):
    def __init__(self, item_validator: IValidator = None):
        self.item_validator = item_validator

    def validate_(self, data: typing.Any, path: typing.List[str]):
        if not isinstance(data, list):
            raise InvalidData(path, f'not a list')
        if self.item_validator is None or not data:
            return data
        res = []
        for i, item in enumerate(data):
            try:
                res.append(self.item_validator.validate_(item, path + [str(i)]))
            except InvalidData as e:
                raise InvalidData(path, f'item {i} invalid: {e.msg}') from e
        return res

    @classmethod
    def make(cls, t: typing.Type[list | typing.List]) -> 'vList':
        if not (args := typing.get_args(t)):  return cls()
        if len(args) != 1: raise TypeError('invalid list type')
        return cls(make_validator(args[0]))


class vDict(IValidator[dict]):
    def __init__(self, key_validator: IValidator = None, value_validator: IValidator = None):
        self.key_validator = key_validator
        self.value_validator = value_validator

    def validate_(self, data: typing.Any, path: typing.List[str]):
        if not isinstance(data, dict):
            raise InvalidData(path, f'not a dict')
        if (self.key_validator is None and self.value_validator is None) or not data:
            return data
        res = {}
        for k, v in data.items():
            new_path = path + [str(k)]
            if self.key_validator is not None:
                k = self.key_validator.validate_(k, new_path)
            if self.value_validator is not None:
                v = self.value_validator.validate_(v, new_path)
            res[k] = v
        return res

    @classmethod
    def make(cls, t: typing.Type[dict | typing.Dict]) -> 'vDict':
        if not (args := typing.get_args(t)):  return cls()
        if len(args) > 2: raise TypeError('invalid dict type')
        if len(args) == 1: return cls(value_validator=make_validator(args[0]))
        return cls(make_validator(args[0]), make_validator(args[1]))


class vTypedDict(IValidator[dict]):
    def __init__(self, validators: list[tuple[str, IValidator]]):
        self.validators = validators

    def validate_(self, data: typing.Any, path: typing.List[str]):
        if not isinstance(data, dict):
            raise InvalidData(path, f'not a dict')
        res = {}
        _data = data.copy()
        for k, v in self.validators:
            new_path = path + [k]
            if k not in _data:
                raise InvalidData(new_path, f'key not found')
            res[k] = v.validate_(_data.pop(k), new_path)
        return res | _data

    @classmethod
    def make(cls, t: typing.Type[dict | typing.Dict]) -> 'vTypedDict':
        return cls([(k, make_validator(v)) for k, v in t.__annotations__.items()])


class vUnion(IValidator[_T]):
    def __init__(self, validators: list[IValidator]):
        self.validators = validators

    def validate_(self, data: typing.Any, path: typing.List[str]):
        for v in self.validators:
            try:
                return v.validate_(data, path)
            except InvalidData:
                pass
        raise InvalidData(path, f'not match any validator')

    @classmethod
    def make(cls, t: typing.Type[_T]) -> 'vUnion[_T]':
        return cls([make_validator(v) for v in typing.get_args(t)])


def make_validator(t: typing.Type[_T]) -> IValidator[_T]:
    if t is None: return _NoneValidator()
    if inspect.isclass(t) or type(t) is types.GenericAlias:
        base_t = t.__mro__[0]
        if base_t is str:
            return VString()
        elif base_t is int:
            return VInt()
        elif base_t is float:
            return VFloat()
        elif base_t is bool:
            return VBool()
        elif base_t is list:
            return vList.make(t)
        elif base_t is dict:
            return vDict.make(t)
        elif base_t is typing.Union:
            return vUnion.make(t)
        elif base_t is typing.Any:
            return _AnyValidator()
        elif type(t) is typing._TypedDictMeta:
            return vTypedDict.make(t)
        else:
            raise TypeError(f'invalid type {t!r}')
    else:
        match type(t):
            case typing._SpecialGenericAlias | typing._GenericAlias:
                if t.__origin__ is list:
                    return vList.make(t)
                elif t.__origin__ is dict:
                    return vDict.make(t)
                else:
                    raise TypeError(f'invalid type {t!r}')
            case typing._UnionGenericAlias | types.UnionType:
                return vUnion.make(t)
            case _:
                raise TypeError(f'invalid type {t!r}')
