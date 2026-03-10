# Imports (from the library "pqcrypto")
from pqcrypto.sign.ml_dsa_44 import generate_keypair, sign, verify

def generate_keys():
    public_key, secret_key = generate_keypair()
    return public_key, secret_key

def sign_message(secret_key, message: bytes):
    return sign(secret_key, message)

def verify_signature(public_key, message: bytes, signature: bytes):
    return verify(public_key, message, signature)