# Initial Findings

## Key Exchange
- Fastest mean handshake latency: **ML-KEM (KYBER)** (0.046813 ms).
- Smallest handshake payload: **ECDH** (356.0 bytes).
- RSA latency overhead vs fastest: **1039.4x**.

## Signatures
- Fastest signing: **ECDSA** (0.031333 ms).
- Fastest verification: **ML-DSA (Dilithium)** (0.001333 ms).
- Smallest signatures: **ECDSA** (71.0 bytes).
- ML-DSA verification speedup vs ECDSA: **46.9x**.
- ML-DSA signature-size overhead vs ECDSA: **34.1x**.

## Messaging
- Best throughput: **KYBER** (21137.0 msgs/s).
- Lowest handshake latency in messaging loop: **KYBER** (0.089166 ms).
- RSA handshake overhead vs best messaging handshake: **210.7x**.

## File Transfer
- Highest throughput: **ECC** (44.066 Mbps).
- Lowest setup latency: **KYBER** (0.093250 ms).
- Throughput spread across algorithms is narrow: **0.606 Mbps**.
- Hybrid KEX latency: **0.243000 ms**.
- Hybrid KEX payload: **1940.0 bytes**.
- Hybrid KEX latency vs ECDH: **1.27x**.
- Hybrid KEX payload vs ECDH: **5.45x**.

## Hybrid
- Hybrid handshake latency: **0.253125 ms**.
- Hybrid latency vs ECC: **0.93x**.
- Hybrid latency vs KYBER: **4.66x**.
- Hybrid transmission bytes: **1940.0** (sum-like overhead compared with single-scheme handshakes).

## Recommendation for Paper Figures
- `key_exchange_tradeoff.png`: strongest protocol tradeoff visualization (latency vs payload).
- `signature_comparison.png`: clear asymmetric tradeoff between signing, verification, and size.
- `messaging_system_view.png`: practical session-level behavior and handshake amortization.
- `file_transfer_comparison.png`: end-to-end throughput plus setup-cost context.
- `hybrid_overhead.png`: dedicated evidence for hybrid construction overhead.