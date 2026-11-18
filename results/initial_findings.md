# Initial Findings

## Key Exchange
- Fastest mean handshake latency: **ML-KEM (KYBER)** (0.051552 ms).
- Smallest handshake payload: **ECDH** (356.0 bytes).
- RSA latency overhead vs fastest: **1089.8x**.

## Signatures
- Fastest signing: **ECDSA** (0.019186 ms).
- Fastest verification: **ECDSA** (0.040409 ms).
- Smallest signatures: **ECDSA** (71.0 bytes).
- ML-DSA verification speedup vs ECDSA: **1.0x**.
- ML-DSA signature-size overhead vs ECDSA: **34.1x**.

## Messaging
- Best throughput: **ECC** (19962.1 msgs/s).
- Lowest handshake latency in messaging loop: **KYBER** (0.092393 ms).
- RSA handshake overhead vs best messaging handshake: **639.9x**.

## File Transfer
- Highest throughput: **RSA** (42.068 Mbps).
- Lowest setup latency: **KYBER** (0.094695 ms).
- Throughput spread across algorithms is narrow: **0.429 Mbps**.
- Hybrid KEX latency: **0.251002 ms**.
- Hybrid KEX payload: **1940.0 bytes**.
- Hybrid KEX latency vs ECDH: **1.29x**.
- Hybrid KEX payload vs ECDH: **5.45x**.

## Hybrid
- Hybrid handshake latency: **0.259276 ms**.
- Hybrid latency vs ECC: **1.25x**.
- Hybrid latency vs KYBER: **4.96x**.
- Hybrid transmission bytes: **1940.0** (sum-like overhead compared with single-scheme handshakes).

## Recommendation for Paper Figures
- `key_exchange_tradeoff.png`: strongest protocol tradeoff visualization (latency vs payload).
- `signature_comparison.png`: clear asymmetric tradeoff between signing, verification, and size.
- `messaging_system_view.png`: practical session-level behavior and handshake amortization.
- `file_transfer_comparison.png`: end-to-end throughput plus setup-cost context.
- `hybrid_overhead.png`: dedicated evidence for hybrid construction overhead.