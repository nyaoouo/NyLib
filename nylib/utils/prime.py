from random import randint


def miller_rabin(p):
    if p == 1: return False
    if p == 2: return True
    if p % 2 == 0: return False
    m, k, = p - 1, 0
    while m % 2 == 0:
        m, k = m // 2, k + 1
    a = randint(2, p - 1)
    x = pow(a, m, p)
    if x == 1 or x == p - 1: return True
    while k > 1:
        x = pow(x, 2, p)
        if x == 1: return False
        if x == p - 1: return True
        k = k - 1
    return False


def is_prime(p, r=40):
    for i in range(r):
        if not miller_rabin(p):
            return False
    return True


def get_prime_by_max(_max):
    s_num = num = randint(_max // 2, _max)
    while True:
        if is_prime(num):
            return num
        elif num + 1 >= _max:
            break
        else:
            num += 1
    while True:
        if is_prime(s_num): return s_num
        s_num -= 1


class SimpRsa:
    def __init__(self, n=0, e=0, d=0):
        self.n, self.e, self.d = n, e, d
        self.default_size = (n.bit_length() + 7) // 8

    def encrypt(self, v: int | bytes):
        assert v < self.n, f'v={v:#x}, n={self.n:#x}'
        return pow(v, self.e, self.n)

    def decrypt(self, v: int | bytes):
        assert v < self.n, f'v={v:#x}, n={self.n:#x}'
        return pow(v, self.d, self.n)

    def encrypt_bytes(self, v: bytes, to_size=0):
        return self.encrypt(int.from_bytes(v, 'little')).to_bytes(to_size or self.default_size, 'little')

    def decrypt_bytes(self, v: bytes, to_size=0):
        return self.decrypt(int.from_bytes(v, 'little')).to_bytes(to_size or self.default_size, 'little')


def get_prime(bit_size):
    return get_prime_by_max(1 << bit_size)


def _rsa_test():
    p1, p2 = get_prime(64), get_prime(64)
    n = p1 * p2
    o = (p1 - 1) * (p2 - 1)
    e = get_prime_by_max(o)
    d = pow(e, -1, o)
    test_rsa = SimpRsa(n, e, d)
    print(f'n={n:#x}')
    print(f'e={e:#x}')
    print(f'd={d:#x}')
    print(hex(encr := test_rsa.encrypt(9)))
    print(hex(test_rsa.decrypt(encr)))
    print((encr := test_rsa.encrypt_bytes(b'test')).hex(' '))
    print(test_rsa.decrypt_bytes(encr))

if __name__ == '__main__':
    _rsa_test()
