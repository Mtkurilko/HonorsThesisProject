import sys
import os
import csv
import hashlib
import statistics
import tracemalloc

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from .run_key_exchange_bench import run_key_exchange_bench
    from .run_signature_bench import run_signature_bench
except ImportError:
    from run_key_exchange_bench import run_key_exchange_bench
    from run_signature_bench import run_signature_bench
from workloads.messaging_sim import run_messaging_experiment, perform_handshake
from workloads.file_transfer_sim import simulate_file_transfer


DEFAULT_RUNS = 100
DEFAULT_MESSAGE = b"message"


def _mean(values):
    return statistics.mean(values) if values else 0.0


def _serialize(values):
    return ";".join(map(str, values))


def run_messaging_suite(
    sessions=DEFAULT_RUNS,
    messages_per_session=1000,
    message_size=256,
    reuse_sessions=5,
    include_hybrid=False,
):
    results = {}

    algorithms = ["RSA", "ECC", "KYBER"]
    if include_hybrid:
        algorithms.append("HYBRID")

    for algorithm in algorithms:
        tracemalloc.start()
        metrics = run_messaging_experiment(
            algorithm=algorithm,
            sessions=sessions,
            messages_per_session=messages_per_session,
            message_size=message_size,
            reuse_sessions=reuse_sessions,
        )
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        metrics["memory_current_bytes"] = current
        metrics["memory_peak_bytes"] = peak
        results[algorithm] = metrics

    return results


def run_file_transfer_suite(
    transfers=DEFAULT_RUNS,
    file_size_bytes=5 * 1024 * 1024,
    chunk_size_bytes=16 * 1024,
    reuse_transfers=2,
    renegotiate_every_chunks=0,
    include_hybrid=False,
):
    results = {}

    algorithms = ["RSA", "ECC", "KYBER"]
    if include_hybrid:
        algorithms.append("HYBRID")

    for algorithm in algorithms:
        transfer_latency_ms_raw = []
        throughput_mbps_raw = []
        chunk_latency_ms_raw = []
        renegotiation_count_raw = []
        handshake_latency_ms_raw = []
        tx_bytes_raw = []

        session_key = None
        reuse_counter = 0

        tracemalloc.start()

        for _ in range(transfers):
            if session_key is None or reuse_counter == 0:
                shared_secret, handshake_ms, tx_bytes = perform_handshake(algorithm)
                session_key = hashlib.sha256(shared_secret).digest()
                handshake_latency_ms_raw.append(handshake_ms)
                tx_bytes_raw.append(tx_bytes)
                reuse_counter = reuse_transfers
            else:
                reuse_counter -= 1
                tx_bytes_raw.append(0)

            def renegotiate_key():
                new_secret, _, _ = perform_handshake(algorithm)
                return hashlib.sha256(new_secret).digest()

            transfer_metrics = simulate_file_transfer(
                session_key=session_key,
                file_size_bytes=file_size_bytes,
                chunk_size_bytes=chunk_size_bytes,
                renegotiate_every_chunks=renegotiate_every_chunks,
                renegotiate_fn=renegotiate_key if renegotiate_every_chunks > 0 else None,
            )

            transfer_latency_ms_raw.append(transfer_metrics["transfer_total_latency_ms"])
            throughput_mbps_raw.append(transfer_metrics["throughput_mbps"])
            chunk_latency_ms_raw.extend(transfer_metrics["chunk_latency_ms_raw"])
            renegotiation_count_raw.append(transfer_metrics["renegotiation_count"])

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        results[algorithm] = {
            "transfer_latency_ms_raw": transfer_latency_ms_raw,
            "throughput_mbps_raw": throughput_mbps_raw,
            "chunk_latency_ms_raw": chunk_latency_ms_raw,
            "renegotiation_count_raw": renegotiation_count_raw,
            "handshake_latency_ms_raw": handshake_latency_ms_raw,
            "tx_bytes_raw": tx_bytes_raw,
            "transfer_latency_ms_mean": _mean(transfer_latency_ms_raw),
            "throughput_mbps_mean": _mean(throughput_mbps_raw),
            "chunk_latency_ms_mean": _mean(chunk_latency_ms_raw),
            "handshake_latency_ms_mean": _mean(handshake_latency_ms_raw),
            "tx_bytes_mean": _mean(tx_bytes_raw),
            "memory_current_bytes": current,
            "memory_peak_bytes": peak,
        }

    return results


def run_hybrid_overhead_experiment(iterations=DEFAULT_RUNS, include_hybrid=False):
    if not include_hybrid:
        return {}

    results = {}

    for algorithm in ["ECC", "KYBER", "HYBRID"]:
        handshake_latency_ms_raw = []
        tx_bytes_raw = []

        for _ in range(iterations):
            _, handshake_ms, tx_bytes = perform_handshake(algorithm)
            handshake_latency_ms_raw.append(handshake_ms)
            tx_bytes_raw.append(tx_bytes)

        results[algorithm] = {
            "handshake_latency_ms_raw": handshake_latency_ms_raw,
            "tx_bytes_raw": tx_bytes_raw,
            "handshake_latency_ms_mean": _mean(handshake_latency_ms_raw),
            "tx_bytes_mean": _mean(tx_bytes_raw),
        }

    return results


def export_refined_results(
    kex_data,
    sig_data,
    messaging_data,
    file_transfer_data,
    hybrid_data,
):
    summary_rows = [["Experiment", "Algorithm", "Metric", "Value"]]
    raw_rows = [["Experiment", "Algorithm", "Metric", "RawValues"]]

    kex_label_map = {
        "RSA": "RSA",
        "ECC": "ECDH",
        "KYBER": "ML-KEM (KYBER)",
        "HYBRID": "HYBRID (ECC+KYBER)",
    }

    # Key exchange
    for alg_key, values in kex_data.items():
        label = kex_label_map.get(alg_key, alg_key)
        summary_rows.extend(
            [
                ["key_exchange", label, "cpu_ms_mean", values["cpu_ms"]],
                ["key_exchange", label, "latency_ms_mean", values["latency_ms"]],
                ["key_exchange", label, "tx_bytes_mean", values["tx_bytes"]],
            ]
        )
        raw_rows.extend(
            [
                ["key_exchange", label, "cpu_ms_raw", _serialize(values["cpu_ms_raw"])],
                ["key_exchange", label, "latency_ms_raw", _serialize(values["latency_ms_raw"])],
                ["key_exchange", label, "tx_bytes_raw", _serialize(values["tx_bytes_raw"])],
            ]
        )

    # Signatures
    signature_map = [
        ("ECDSA", "RAW ECDSA SIGN", "RAW ECDSA VERIFY", "RAW ECDSA SIZE"),
        ("ML-DSA (Dilithium)", "RAW ML-DSA SIGN", "RAW ML-DSA VERIFY", "RAW ML-DSA SIZE"),
    ]
    for label, sign_key, verify_key, size_key in signature_map:
        summary_rows.extend(
            [
                ["signatures", label, "sign_ms_mean", sig_data[sign_key]["mean"]],
                ["signatures", label, "verify_ms_mean", sig_data[verify_key]["mean"]],
                ["signatures", label, "signature_size_bytes_mean", _mean(sig_data[size_key])],
            ]
        )
        raw_rows.extend(
            [
                ["signatures", label, "sign_ms_raw", _serialize(sig_data[sign_key]["times"])],
                ["signatures", label, "verify_ms_raw", _serialize(sig_data[verify_key]["times"])],
                ["signatures", label, "signature_size_bytes_raw", _serialize(sig_data[size_key])],
            ]
        )

    # Messaging
    for algorithm, metrics in messaging_data.items():
        summary_rows.extend(
            [
                ["messaging", algorithm, "session_latency_ms_mean", metrics["session_latency_ms_mean"]],
                ["messaging", algorithm, "message_latency_ms_mean", metrics["message_latency_ms_mean"]],
                ["messaging", algorithm, "handshake_latency_ms_mean", metrics["handshake_latency_ms_mean"]],
                ["messaging", algorithm, "messages_per_sec", metrics["messages_per_sec"]],
                ["messaging", algorithm, "reuse_ratio", metrics["reuse_ratio"]],
                ["messaging", algorithm, "memory_peak_bytes", metrics["memory_peak_bytes"]],
            ]
        )
        raw_rows.extend(
            [
                ["messaging", algorithm, "session_latency_ms_raw", _serialize(metrics["session_latency_ms_raw"])],
                ["messaging", algorithm, "message_latency_ms_raw", _serialize(metrics["per_message_latency_ms_raw"])],
                ["messaging", algorithm, "handshake_latency_ms_raw", _serialize(metrics["handshake_latency_ms_raw"])],
                ["messaging", algorithm, "tx_bytes_raw", _serialize(metrics["tx_bytes_raw"])],
            ]
        )

    # File transfer
    for algorithm, metrics in file_transfer_data.items():
        summary_rows.extend(
            [
                ["file_transfer", algorithm, "transfer_latency_ms_mean", metrics["transfer_latency_ms_mean"]],
                ["file_transfer", algorithm, "throughput_mbps_mean", metrics["throughput_mbps_mean"]],
                ["file_transfer", algorithm, "chunk_latency_ms_mean", metrics["chunk_latency_ms_mean"]],
                ["file_transfer", algorithm, "handshake_latency_ms_mean", metrics["handshake_latency_ms_mean"]],
                ["file_transfer", algorithm, "tx_bytes_mean", metrics["tx_bytes_mean"]],
                ["file_transfer", algorithm, "memory_peak_bytes", metrics["memory_peak_bytes"]],
            ]
        )
        raw_rows.extend(
            [
                ["file_transfer", algorithm, "transfer_latency_ms_raw", _serialize(metrics["transfer_latency_ms_raw"])],
                ["file_transfer", algorithm, "throughput_mbps_raw", _serialize(metrics["throughput_mbps_raw"])],
                ["file_transfer", algorithm, "chunk_latency_ms_raw", _serialize(metrics["chunk_latency_ms_raw"])],
                ["file_transfer", algorithm, "handshake_latency_ms_raw", _serialize(metrics["handshake_latency_ms_raw"])],
                ["file_transfer", algorithm, "tx_bytes_raw", _serialize(metrics["tx_bytes_raw"])],
                ["file_transfer", algorithm, "renegotiation_count_raw", _serialize(metrics["renegotiation_count_raw"])],
            ]
        )

    # Hybrid overhead
    for algorithm, metrics in hybrid_data.items():
        summary_rows.extend(
            [
                ["hybrid_overhead", algorithm, "handshake_latency_ms_mean", metrics["handshake_latency_ms_mean"]],
                ["hybrid_overhead", algorithm, "tx_bytes_mean", metrics["tx_bytes_mean"]],
            ]
        )
        raw_rows.extend(
            [
                ["hybrid_overhead", algorithm, "handshake_latency_ms_raw", _serialize(metrics["handshake_latency_ms_raw"])],
                ["hybrid_overhead", algorithm, "tx_bytes_raw", _serialize(metrics["tx_bytes_raw"])],
            ]
        )

    with open("results/refined_experiment_summary.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(summary_rows)

    with open("results/refined_experiment_raw.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(raw_rows)


def run_refined_experiments(runs=DEFAULT_RUNS, message=DEFAULT_MESSAGE, include_hybrid=False):
    kex_data = run_key_exchange_bench(runs, message, include_hybrid=include_hybrid)
    sig_data = run_signature_bench(runs, message)
    messaging_data = run_messaging_suite(sessions=runs, include_hybrid=include_hybrid)
    file_transfer_data = run_file_transfer_suite(transfers=runs, include_hybrid=include_hybrid)
    hybrid_data = run_hybrid_overhead_experiment(iterations=runs, include_hybrid=include_hybrid)

    export_refined_results(
        kex_data=kex_data,
        sig_data=sig_data,
        messaging_data=messaging_data,
        file_transfer_data=file_transfer_data,
        hybrid_data=hybrid_data,
    )

    return {
        "key_exchange": kex_data,
        "signatures": sig_data,
        "messaging": messaging_data,
        "file_transfer": file_transfer_data,
        "hybrid": hybrid_data,
    }


if __name__ == "__main__":
    runs = int(input("How many runs do you want for each experiment?: "))
    run_refined_experiments(runs=runs, message=DEFAULT_MESSAGE, include_hybrid=False)
    print("CSV exported: refined_experiment_summary.csv")
    print("CSV exported: refined_experiment_raw.csv")
