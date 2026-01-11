from sympy import nextprime
import random

class RSA:
    
    @staticmethod    
    def encrypt(plaintext:str, public_key:tuple) -> int:
        """Encrypts plaintext using the RSA public key.

        Args:
            plaintext (str): text to encrypt
            public_key (tuple): RSA public key (N, e)

        Returns:
            int: encrypted ciphertext
        """
        N, e = public_key
        # Add random padding to plaintext to ensure uniqueness
        padding = random.randrange(10**5,10**6)
        plaintext = str(padding)+ plaintext
        
        m = int.from_bytes(plaintext.encode(), 'big')
        return pow(m, e, N)

    @staticmethod
    def decrypt(ciphertext:int, private_key:tuple) -> str:
        """Decrypts ciphertext using the RSA private key

        Args:
            ciphertext (int): text to decrypt
            private_key (tuple): RSA private key (N, d)

        Returns:
            str: decrypted plaintext
        """
        N, d = private_key
        m = pow(ciphertext, d, N)
        bytelength = (m.bit_length() + 7) // 8
        return m.to_bytes(bytelength, 'big').decode()[6:]  # remove padding




    @staticmethod
    def generate_large_prime(bits:int) -> int:
        """Generates a large prime number with the specified bit length.
         Uses sympy's nextprime function for simplicity.
         Need to double check is prime as miller-rabin can produce false positives.

        Args:
            bits (int): Number of bits for the prime

        Returns:
            int: A large prime number with the specified bit length
        """

        rand_num = random.getrandbits(bits) | (1 << (bits - 1)) | 1 
        return nextprime(rand_num) 
    
    @staticmethod
    def gcd_extended(a:int, b:int) -> tuple[int, int, int]:
        """Extended Euclidean Algorithm.
        Returns a tuple (g, x, y) such that a*x + b*y = g = gcd(a, b)

        Args:
            a (int): First integer
            b (int): Second integer

        Returns:
            tuple[int, int, int]: A tuple (g, x, y) such that a*x + b*y = g = gcd(a, b)
        """
        if b == 0:
            return (a,1,0)
        g,x1,y1 = RSA.gcd_extended(b,a%b)
        return (g, y1, x1 - (a//b)*y1)
    
    @staticmethod
    def generate_keypair(bits:int=1024) -> tuple[tuple[int, int], tuple[int, int]]:
        """Generates an RSA keypair with the specified bit length.

        Args:
            bits (int): Number of bits for the key. Defaults to 1024.

        Returns:
            tuple[tuple[int, int], tuple[int, int]]: A tuple containing the public key (N, e) and private key (N, d)
        """
        e = 65537
        while True:
            p = RSA.generate_large_prime(bits//2)
            q = RSA.generate_large_prime(bits//2)
            phi = (p-1)*(q-1)
            g,x,y = RSA.gcd_extended(e, phi)

            if g == 1:
                n = p * q
                d = x % phi
                return (n, e), (n, d)

    
