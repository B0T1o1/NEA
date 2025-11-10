class RSA:
    
    @staticmethod    
    def encrypt(plaintext:str, public_key:tuple) -> int:
        N, e = public_key
        m = int.from_bytes(plaintext.encode(), 'big')
        return pow(m, e, N)

    @staticmethod
    def decrypt(ciphertext:int, private_key:tuple) -> str:
        N, d = private_key
        m = pow(ciphertext, d, N)
        bytelength = (m.bit_length() + 7) // 8
        try:
            return m.to_bytes(bytelength, 'big').decode()
        except UnicodeDecodeError:
            return m.to_bytes(bytelength, 'big')

    @staticmethod
    def generate_keys(p:int, q:int, e:int):
        N = p * q
        phi = (p - 1) * (q - 1)
        d = pow(e, -1, phi)
        return (N, e), (N, d)

    @staticmethod
    def generate_large_prime(bits:int) -> int:
        from sympy import nextprime
        import random
        rand_num = random.getrandbits(bits) | (1 << (bits - 1)) | 1
        return nextprime(rand_num)
    
    @staticmethod
    def gcd_extended(a:int, b:int):
        if b == 0:
            return (a,1,0)
        g,x1,y1 = RSA.gcd_extended(b,a%b)
        return (g, y1, x1 - (a//b)*y1)
    
    @staticmethod
    def generate_keypair(bits:int=1024):
        e = 65537
        for _ in range(10):
            p = RSA.generate_large_prime(bits//2)
            q = RSA.generate_large_prime(bits//2)
            phi = (p-1)*(q-1)
            g,_,_ = RSA.gcd_extended(e, phi)
            if g == 1:
                return RSA.generate_keys(p, q, e)
        raise ValueError("Failed to generate valid keypair")


