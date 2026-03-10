# Imports (from the library "pqcrypto")
from pqcrypto.kem.ml_kem_512 import generate_keypair, encrypt, decrypt

def generate_keys():
    public_key, secret_key = generate_keypair()
    return public_key, secret_key

def encapsulate(public_key):
    ciphertext, shared_secret = encrypt(public_key)
    return ciphertext, shared_secret

def decapsulate(secret_key, ciphertext):
    shared_secret = decrypt(secret_key, ciphertext)
    return shared_secret