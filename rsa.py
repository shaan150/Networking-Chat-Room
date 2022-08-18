import random
import math
# sympy used for prime number checker
import sympy


def generateKeys(keysize=1024):
    e = d = N = 0

    # get prime nums, p & q
    p = generateLargePrime(keysize)
    q = generateLargePrime(keysize)

    print(f"p: {p}")
    print(f"q: {q}")
    # Gets the rsa modulus
    N = p * q
    # Works out the totient
    phiN = (p - 1) * (q - 1)


    while True:
        # Calculates the number by doing 2^keysize-1 + 1, 2^keysize-1
        e = random.randrange(2 ** (keysize - 1), 2 ** keysize - 1)
        # Checks if the gcd is a co prime by using the maths modules gcd method
        if (math.gcd(e, phiN) == 1):
            break

    # d is the modulo inverse of e and phiN
    d = pow(e, -1, phiN)


    return e, d, N


# This method generates a large prime number based on the key size provided
def generateLargePrime(keysize):
    while True:
        # Calculates the number by doing 2^keysize-1 + 1, 2^keysize-1
        num = random.randrange(2 ** (keysize - 1), 2 ** keysize - 1)
        # Uses sympy to check if number is prime
        if (sympy.isprime(num)):
            return num

# This method utilises Extended Euclidean Algorithm to find the greatest divisors between a & b
def egcd(a, b):
    s = 0
    old_s = 1
    t = 1
    old_t = 0
    r = b
    old_r = a

    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t

    # return gcd, x, y
    return old_r, old_s, old_t


def encrypt(e, N, msg):
    cipher = ""
    # Convert each letter in the plaintext to numbers based on the character using a^b mod m
    cipher = [pow(ord(char), e, N) for char in msg]
    # Return the array of bytes
    return ','.join([str(x) for x in cipher])


def decrypt(d, N, cipher):
    msg = ""
    cipher_split = cipher.split(',')
    # Generate the plaintext based on the ciphertext and key using a^b mod m
    aux = [str(pow(int(char), d, N)) for char in cipher_split]
    # Return the array of bytes as a string
    plain = [chr(int(char2)) for char2 in aux]

    return ''.join(plain)
