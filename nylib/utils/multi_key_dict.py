class Any(object): pass


class _NULL(object): pass


def _select(d, key=_NULL, *keys):
    if key is _NULL:
        yield d
    elif key is Any:
        for v in d.values():
            yield from _select(v, *keys)
    elif key in d:
        yield from _select(d[key], *keys)


def _update(v, d, key, *keys):
    if keys:
        _update(v, d.setdefault(key, {}), *keys)
    else:
        d[key] = v


def _drop(d, key, *keys):
    if key is Any:
        if keys:
            for v in d.values():
                _drop(v, *keys)
        else:
            d.clear()
    elif key in d:
        if keys:
            _drop(d[key], *keys)
        else:
            del d[key]


def _size(d, depth):
    return sum(_size(v, depth - 1) for v in d.values()) if depth > 0 else 1


def _keys(d: dict, depth):
    if depth <= 1:
        for k in d.keys():
            yield (k,)
    else:
        for k, v in d.items():
            for _k in _keys(v, depth - 1):
                yield (k,) + _k


def _values(d: dict, depth):
    if depth <= 1:
        yield from d.values()
    else:
        for v in d.values():
            yield from _values(v, depth - 1)


def _items(d: dict, depth):
    if depth <= 1:
        for k, v in d.items():
            yield (k,), v
    else:
        for k, v in d.items():
            for _k, _v in _items(v, depth - 1):
                yield (k,) + _k, _v


class MultiKeyDict:
    def __init__(self, key_size):
        self.key_size = key_size
        self.data = {}

    def select(self, *keys):
        if len(keys) != self.key_size: raise KeyError(f'invalid key size, expect {self.key_size}, got {len(keys)}')
        return _select(self.data, *keys)

    def update(self, v, *keys):
        if len(keys) != self.key_size: raise KeyError(f'invalid key size, expect {self.key_size}, got {len(keys)}')
        _update(v, self.data, *keys)

    def drop(self, *keys):
        if len(keys) != self.key_size: raise KeyError(f'invalid key size, expect {self.key_size}, got {len(keys)}')
        _drop(self.data, *keys)

    def __getitem__(self, keys):
        try:
            return next(self.select(*keys))
        except StopIteration:
            raise KeyError(keys)

    def __setitem__(self, keys, v):
        self.update(v, *keys)

    def __delitem__(self, keys):
        self.drop(*keys)

    def clear(self):
        self.data.clear()

    def __len__(self):
        return _size(self.data, self.key_size)

    def keys(self):
        return _keys(self.data, self.key_size)

    def __iter__(self):
        return self.keys()

    def values(self):
        return _values(self.data, self.key_size)

    def items(self):
        return _items(self.data, self.key_size)

    def __contains__(self, keys):
        try:
            next(self.select(*keys))
            return True
        except StopIteration:
            return False

    def __repr__(self):
        return f'<MultiKeyDict size={self.key_size}>'


def test():
    # Writing test cases for the MultiKeyDict class

    def test_initialization():
        # Test initialization with a specific key size
        key_size = 2
        mkd = MultiKeyDict(key_size)
        assert mkd.key_size == key_size, f"Expected key size {key_size}, got {mkd.key_size}"

    def test_update():
        # Test updating with various key sizes and values
        mkd = MultiKeyDict(2)
        mkd.update(10, 'a', 'b')
        assert list(mkd.select('a', 'b')) == [10], "Update with correct keys failed"

        try:
            mkd.update(20, 'a')  # Incorrect key size
        except KeyError:
            pass  # Expected behavior
        else:
            assert False, "Update did not raise KeyError for incorrect key size"

    def test_select():
        # Test selecting with specific keys
        mkd = MultiKeyDict(2)
        mkd.update(30, 'x', 'y')
        assert list(mkd.select('x', 'y')) == [30], "Select did not return correct value"

        assert list(mkd.select('x', 'z')) == [], "Select with non-existent key did not return empty list"

    def test_drop():
        # Test drop functionality
        mkd = MultiKeyDict(2)
        mkd.update(40, 'p', 'q')
        mkd.drop('p', 'q')
        assert list(mkd.select('p', 'q')) == [], "Drop did not remove the entry"

    # Running the tests
    test_initialization()
    test_update()
    test_select()
    test_drop()

    def test_any_key_select():
        # Test selecting with 'Any' key
        mkd = MultiKeyDict(2)
        mkd.update(50, 'a', 'b')
        mkd.update(60, 'a', 'c')

        # Using 'Any' in different positions
        assert set(mkd.select('a', Any)) == {50, 60}, "Select with Any key failed"
        assert set(mkd.select(Any, 'b')) == {50}, "Select with Any key in second position failed"

    def test_any_key_drop():
        # Test dropping with 'Any' key
        mkd = MultiKeyDict(2)
        mkd.update(70, 'x', 'y')
        mkd.update(80, 'x', 'z')
        mkd.drop('x', Any)

        # After dropping, no entry with 'x' as the first key should exist
        assert list(mkd.select('x', 'y')) == [], "Drop with Any key did not remove the entry"
        assert list(mkd.select('x', 'z')) == [], "Drop with Any key did not remove the entry"

    # Running the tests for Any key
    test_any_key_select()
    test_any_key_drop()

    print("All tests passed!")


if __name__ == '__main__':
    test()
