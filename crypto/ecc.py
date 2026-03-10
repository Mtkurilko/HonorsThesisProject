# Imports (using the library "cryptography")
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

def generate_keys():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    return public_key, private_key

def ecdh_shared_secret(private_key, peer_public_key):
    return private_key.exchange(ec.ECDH(), peer_public_key)

def sign_message(private_key, message: bytes):
    return private_key.sign(
        message,
        ec.ECDSA(hashes.SHA256())
    )

def verify_signature(public_key, signature, message: bytes):
    public_key.verify(
        signature,
        message,
        ec.ECDSA(hashes.SHA256())
    )