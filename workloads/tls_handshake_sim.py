from crypto import ecc, kyber, dilithium

def simulate_handshake(kex_module):
    # Server generates keypair
    pub, priv = kex_module.generate_keys()

    # Client encapsulates secret
    ciphertext, client_secret = kex_module.encapsulate(pub)

    # Server decapsulates
    server_secret = kex_module.decapsulate(priv, ciphertext)

    return pub, ciphertext