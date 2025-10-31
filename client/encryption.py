

class RSA():

    @staticmethod    
    def encrypt(plaintext:str, public_key:tuple) -> str:
        # Computes ciphertext = plaintext^e mod N
        N, e = public_key
        ciphertext = pow(int.from_bytes(plaintext.encode(), 'big'), e, N)
        return ciphertext

    @staticmethod
    def decrypt(ciphertext:str, private_key:tuple) -> str:
        # Computes plaintext = ciphertext^d mod N
        N, d = private_key
        plaintext = pow(ciphertext, d, N)
        bytelength = (plaintext.bit_length() + 7) // 8
        return plaintext.to_bytes((bytelength), 'big').decode()
    
    @staticmethod
    def generate_keys(p:int,q:int,e:int) -> tuple:
        N = p * q
        phi = (p - 1) * (q - 1)
        # Compute d, the modular multiplicative inverse of e mod phi
        d = pow(e, -1, phi)
        return (N, e), (N, d)
    
    @staticmethod
    def generate_large_prime(bits:int) -> int:
        from sympy import nextprime
        import random
        rand_num = random.getrandbits(bits)
        prime = nextprime(rand_num)
        return prime
    
    @staticmethod
    def generate_keypair(bits:int = 1024) -> tuple:
        p = RSA.generate_large_prime(bits // 2)
        q = RSA.generate_large_prime(bits // 2)
        #TODO ensure e is coprime to (p-1)(q-1)
        e = 65537  # Common choice for e
        phi = (p-1)*(q-1)
        if RSA.gcd_extended(phi,e) == 1:
            return RSA.generate_keys(p, q, e)
        else:
            return RSA.generate_keypair(bits)
        

    @staticmethod
    def modular_exponentiation(base:int, exponent:int, modulus:int) -> int:
        result = 1
        base = base % modulus
        while exponent > 0:
            if (exponent % 2) == 1:
                result = (result * base) % modulus
            exponent = exponent >> 1
            base = (base * base) % modulus
        return result
    
    @staticmethod
    def compute_d (e:int,phi:int) -> int:
        # e*d mod phi = 1
        # e*d + k*phi = 1  for some integer k
        # since e and phi are comprime we know gcd(e,phi) = 1 so can use Extended Euclidean Algorithm
        # e*d + k*phi = gcd(e,phi)
        gcd, x, y = RSA.gcd_extended(e, phi)
        if gcd == 1:
            d = x % phi
            return d    
        
    @staticmethod     
    def gcd_extended(a:int, b):
        #recusive function to find Bézout's identity
        #base case
        if b == 0: 
            return (a,1,0) # gcd,x,y
        else:
            g,x1,y1 = RSA.gcd_extended(b,a%b) # standard gcd
            # back substitute to find x and y
            x = y1
            y = x1 - (a//b) *y1
            return (g,x,y) #gcd,x,y
        


