import hashlib
import math
import secrets
import statistics
import time


def _xor_stream(key: bytes, data: bytes, nonce: bytes, counter: int) -> bytes:
	keystream = bytearray()
	block_counter = counter

	while len(keystream) < len(data):
		block = hashlib.sha256(key + nonce + block_counter.to_bytes(8, "big")).digest()
		keystream.extend(block)
		block_counter += 1

	return bytes(d ^ k for d, k in zip(data, keystream[: len(data)]))


def simulate_file_transfer(
	session_key: bytes,
	file_size_bytes: int,
	chunk_size_bytes: int = 16 * 1024,
	renegotiate_every_chunks: int = 0,
	renegotiate_fn=None,
):
	if file_size_bytes <= 0:
		raise ValueError("file_size_bytes must be > 0")
	if chunk_size_bytes <= 0:
		raise ValueError("chunk_size_bytes must be > 0")

	chunk_count = math.ceil(file_size_bytes / chunk_size_bytes)
	nonce = secrets.token_bytes(16)

	chunk_latency_ms_raw = []
	renegotiation_latency_ms_raw = []
	renegotiation_count = 0

	bytes_transferred = 0
	counter = 0

	transfer_start = time.perf_counter()
	for idx in range(chunk_count):
		if (
			renegotiate_every_chunks > 0
			and idx > 0
			and idx % renegotiate_every_chunks == 0
			and renegotiate_fn is not None
		):
			reneg_start = time.perf_counter()
			session_key = renegotiate_fn()
			reneg_end = time.perf_counter()
			renegotiation_latency_ms_raw.append((reneg_end - reneg_start) * 1000)
			renegotiation_count += 1

		current_chunk_size = min(chunk_size_bytes, file_size_bytes - bytes_transferred)
		chunk_payload = secrets.token_bytes(current_chunk_size)

		start = time.perf_counter()
		encrypted = _xor_stream(session_key, chunk_payload, nonce, counter)
		decrypted = _xor_stream(session_key, encrypted, nonce, counter)
		end = time.perf_counter()

		if decrypted != chunk_payload:
			raise RuntimeError("File transfer integrity check failed")

		chunk_latency_ms_raw.append((end - start) * 1000)
		bytes_transferred += current_chunk_size
		counter += 1

	transfer_end = time.perf_counter()
	elapsed_s = transfer_end - transfer_start

	return {
		"file_size_bytes": file_size_bytes,
		"chunk_size_bytes": chunk_size_bytes,
		"chunk_count": chunk_count,
		"chunk_latency_ms_raw": chunk_latency_ms_raw,
		"chunk_latency_ms_mean": statistics.mean(chunk_latency_ms_raw) if chunk_latency_ms_raw else 0.0,
		"chunk_latency_ms_p95": (
			sorted(chunk_latency_ms_raw)[int(0.95 * (len(chunk_latency_ms_raw) - 1))]
			if chunk_latency_ms_raw
			else 0.0
		),
		"renegotiation_count": renegotiation_count,
		"renegotiation_latency_ms_raw": renegotiation_latency_ms_raw,
		"renegotiation_latency_ms_mean": (
			statistics.mean(renegotiation_latency_ms_raw) if renegotiation_latency_ms_raw else 0.0
		),
		"transfer_total_latency_ms": elapsed_s * 1000,
		"throughput_bytes_per_sec": (bytes_transferred / elapsed_s) if elapsed_s > 0 else 0.0,
		"throughput_mbps": ((bytes_transferred * 8) / elapsed_s / 1_000_000) if elapsed_s > 0 else 0.0,
	}
