import os
from cryptography.hazmat.primitives import serialization

from . import rsa, kyber, ecc


class kex_module:
    SUPPORTED = {"RSA", "ECC", "KYBER"}

    def __init__(self, algorithm: str):
        normalized = algorithm.strip().upper()
        if normalized not in self.SUPPORTED:
            raise ValueError(
                f"Unsupported key exchange algorithm '{algorithm}'. "
                f"Use one of: {', '.join(sorted(self.SUPPORTED))}."
            )
        self.algorithm = normalized

    def __repr__(self):
        return f"kex_module('{self.algorithm}')"

    def __eq__(self, other):
        return isinstance(other, kex_module) and self.algorithm == other.algorithm

    def __hash__(self):
        return hash(self.algorithm)
    
    def getName(self):
        return self.algorithm

    def generate_keys(self):
        if self.algorithm == "KYBER":
            return kyber.generate_keys()

        if self.algorithm == "RSA":
            public_key, private_key = rsa.generate_keys()
            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            return public_bytes, private_key

        public_key, private_key = ecc.generate_keys()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return public_bytes, private_key

    def encapsulate(self, public_key):
        if self.algorithm == "KYBER":
            return kyber.encapsulate(public_key)

        if self.algorithm == "RSA":
            receiver_public_key = serialization.load_pem_public_key(public_key)
            shared_secret = os.urandom(32)
            ciphertext = rsa.encrypt(receiver_public_key, shared_secret)
            return ciphertext, shared_secret

        receiver_public_key = serialization.load_pem_public_key(public_key)
        ephemeral_public_key, ephemeral_private_key = ecc.generate_keys()
        shared_secret = ecc.ecdh_shared_secret(ephemeral_private_key, receiver_public_key)
        ephemeral_public_bytes = ephemeral_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return ephemeral_public_bytes, shared_secret

    def decapsulate(self, private_key, ciphertext):
        if self.algorithm == "KYBER":
            return kyber.decapsulate(private_key, ciphertext)

        if self.algorithm == "RSA":
            return rsa.decrypt(private_key, ciphertext)

        sender_ephemeral_public_key = serialization.load_pem_public_key(ciphertext)
        return ecc.ecdh_shared_secret(private_key, sender_ephemeral_public_key)