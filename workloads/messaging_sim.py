import hashlib
import secrets
import statistics
import time

from crypto import kex_module


def _kdf(*parts: bytes) -> bytes:
	return hashlib.sha256(b"".join(parts)).digest()


def _xor_stream(key: bytes, data: bytes, nonce: bytes, counter: int) -> bytes:
	keystream = bytearray()
	block_counter = counter

	while len(keystream) < len(data):
		block = hashlib.sha256(key + nonce + block_counter.to_bytes(8, "big")).digest()
		keystream.extend(block)
		block_counter += 1

	return bytes(d ^ k for d, k in zip(data, keystream[: len(data)]))


def _perform_shared_secret_exchange(algorithm: str):
	start = time.perf_counter()
	module = kex_module(algorithm)
	pub, priv = module.generate_keys()
	ct, client_secret = module.encapsulate(pub)
	server_secret = module.decapsulate(priv, ct)
	shared_secret = client_secret
	tx_bytes = len(pub) + len(ct)

	handshake_ms = (time.perf_counter() - start) * 1000

	if shared_secret != server_secret:
		raise RuntimeError(f"Shared secret mismatch for {algorithm} handshake")

	return shared_secret, handshake_ms, tx_bytes


def perform_handshake(algorithm: str):
	return _perform_shared_secret_exchange(algorithm)


def run_secure_messaging_session(session_key: bytes, message_count: int = 1000, message_size: int = 256):
	payload = secrets.token_bytes(message_size)
	nonce = secrets.token_bytes(16)

	per_message_latency_ms = []
	total_bytes = 0

	start = time.perf_counter()
	for i in range(message_count):
		msg_start = time.perf_counter()

		ciphertext = _xor_stream(session_key, payload, nonce, i)
		plaintext = _xor_stream(session_key, ciphertext, nonce, i)

		if plaintext != payload:
			raise RuntimeError("Messaging payload integrity check failed")

		msg_end = time.perf_counter()
		per_message_latency_ms.append((msg_end - msg_start) * 1000)
		total_bytes += len(payload)

	elapsed = time.perf_counter() - start

	return {
		"per_message_latency_ms": per_message_latency_ms,
		"session_total_latency_ms": elapsed * 1000,
		"messages_per_sec": message_count / elapsed if elapsed > 0 else 0.0,
		"bytes_per_sec": total_bytes / elapsed if elapsed > 0 else 0.0,
		"bytes_total": total_bytes,
	}


def run_messaging_experiment(
	algorithm: str,
	sessions: int = 100,
	messages_per_session: int = 1000,
	message_size: int = 256,
	reuse_sessions: int = 0,
):
	handshake_latency_ms_raw = []
	session_latency_ms_raw = []
	per_message_latency_ms_raw = []
	tx_bytes_raw = []

	current_session_key = None
	reuse_counter = 0
	handshake_count = 0
	reused_sessions = 0

	start = time.perf_counter()
	for _ in range(sessions):
		needs_handshake = current_session_key is None or reuse_counter == 0

		if needs_handshake:
			shared_secret, handshake_ms, tx_bytes = _perform_shared_secret_exchange(algorithm)
			current_session_key = _kdf(shared_secret)
			handshake_latency_ms_raw.append(handshake_ms)
			tx_bytes_raw.append(tx_bytes)
			handshake_count += 1
			reuse_counter = reuse_sessions
		else:
			reused_sessions += 1
			tx_bytes_raw.append(0)
			reuse_counter -= 1

		session_metrics = run_secure_messaging_session(
			session_key=current_session_key,
			message_count=messages_per_session,
			message_size=message_size,
		)

		session_latency_ms_raw.append(session_metrics["session_total_latency_ms"])
		per_message_latency_ms_raw.extend(session_metrics["per_message_latency_ms"])

	elapsed_total = time.perf_counter() - start
	total_messages = sessions * messages_per_session

	return {
		"algorithm": algorithm,
		"sessions": sessions,
		"messages": total_messages,
		"handshakes": handshake_count,
		"reused_sessions": reused_sessions,
		"reuse_ratio": (reused_sessions / sessions) if sessions else 0.0,
		"total_runtime_ms": elapsed_total * 1000,
		"session_latency_ms_raw": session_latency_ms_raw,
		"per_message_latency_ms_raw": per_message_latency_ms_raw,
		"handshake_latency_ms_raw": handshake_latency_ms_raw,
		"tx_bytes_raw": tx_bytes_raw,
		"session_latency_ms_mean": statistics.mean(session_latency_ms_raw) if session_latency_ms_raw else 0.0,
		"message_latency_ms_mean": statistics.mean(per_message_latency_ms_raw) if per_message_latency_ms_raw else 0.0,
		"handshake_latency_ms_mean": statistics.mean(handshake_latency_ms_raw) if handshake_latency_ms_raw else 0.0,
		"tx_bytes_mean": statistics.mean(tx_bytes_raw) if tx_bytes_raw else 0.0,
		"messages_per_sec": (total_messages / elapsed_total) if elapsed_total > 0 else 0.0,
	}
