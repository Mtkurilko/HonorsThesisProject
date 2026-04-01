import hashlib

from cryptography.hazmat.primitives import serialization

from . import ecc, kyber


def _pack_blob(left: bytes, right: bytes) -> bytes:
    return len(left).to_bytes(4, "big") + left + len(right).to_bytes(4, "big") + right


def _unpack_blob(blob: bytes):
    if len(blob) < 8:
        raise ValueError("Invalid hybrid blob: too short")

    left_len = int.from_bytes(blob[:4], "big")
    left_start = 4
    left_end = left_start + left_len

    if len(blob) < left_end + 4:
        raise ValueError("Invalid hybrid blob: missing right length")

    right_len = int.from_bytes(blob[left_end:left_end + 4], "big")
    right_start = left_end + 4
    right_end = right_start + right_len

    if len(blob) != right_end:
        raise ValueError("Invalid hybrid blob: trailing or missing bytes")

    return blob[left_start:left_end], blob[right_start:right_end]


def _kdf(ecc_secret: bytes, kyber_secret: bytes) -> bytes:
    return hashlib.sha256(ecc_secret + kyber_secret).digest()


def generate_keys():
    ecc_public_key, ecc_private_key = ecc.generate_keys()
    ecc_public_bytes = ecc_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    kyber_public_key, kyber_secret_key = kyber.generate_keys()

    public_blob = _pack_blob(ecc_public_bytes, kyber_public_key)
    private_bundle = (ecc_private_key, kyber_secret_key)

    return public_blob, private_bundle


def encapsulate(public_blob: bytes):
    ecc_public_bytes, kyber_public_key = _unpack_blob(public_blob)

    receiver_ecc_public = serialization.load_pem_public_key(ecc_public_bytes)
    ephemeral_public_key, ephemeral_private_key = ecc.generate_keys()
    ecc_secret = ecc.ecdh_shared_secret(ephemeral_private_key, receiver_ecc_public)
    ecc_ciphertext = ephemeral_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    kyber_ciphertext, kyber_secret = kyber.encapsulate(kyber_public_key)

    shared_secret = _kdf(ecc_secret, kyber_secret)
    ciphertext_blob = _pack_blob(ecc_ciphertext, kyber_ciphertext)

    return ciphertext_blob, shared_secret


def decapsulate(private_bundle, ciphertext_blob: bytes):
    ecc_private_key, kyber_secret_key = private_bundle
    ecc_ciphertext, kyber_ciphertext = _unpack_blob(ciphertext_blob)

    sender_ecc_ephemeral = serialization.load_pem_public_key(ecc_ciphertext)
    ecc_secret = ecc.ecdh_shared_secret(ecc_private_key, sender_ecc_ephemeral)
    kyber_secret = kyber.decapsulate(kyber_secret_key, kyber_ciphertext)

    return _kdf(ecc_secret, kyber_secret)
