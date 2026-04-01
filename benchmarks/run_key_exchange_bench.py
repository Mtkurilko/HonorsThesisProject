import sys
import os
import time

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import csv
from crypto import kex_module
from benchmarks import bandwith, latency
from workloads.tls_handshake_sim import simulate_handshake

# CONSTANTS
ITERATIONS = 1000
DEF_MESSAGE = b"message"

ALGORITHM_LABELS = {
    "RSA": "RSA",
    "ECC": "ECDH",
    "KYBER": "ML-KEM (KYBER)",
    "HYBRID": "HYBRID (ECC+KYBER)",
}

def run_key_exchange_bench(iter=ITERATIONS, message=DEF_MESSAGE, include_hybrid=False):
    algorithms = ["RSA", "ECC", "KYBER"]
    if include_hybrid:
        algorithms.append("HYBRID")

    cpu_times = {algorithm: [] for algorithm in algorithms}
    latency_data = {algorithm: {} for algorithm in algorithms}
    key_sizes = {algorithm: [] for algorithm in algorithms}

    # ----- Benchmark -----
    for module in [kex_module(algorithm) for algorithm in algorithms]:
        for _ in range(iter):
            # CPU Cycles // (WILL USE time.process_time() and report CPU time in ms)
            start_cpu = time.process_time()
            pub, ct = simulate_handshake(module)
            end_cpu = time.process_time()

            cpu_times[module.getName()].append((end_cpu - start_cpu) * 1000)

            # Key Size Transmission Cost
            key_sizes[module.getName()].append(len(pub) + len(ct))
        
        # Handshake Latency
        latency_data[module.getName()] = latency.measure_latency(lambda: simulate_handshake(module), iter)

    return {
        algorithm: {
            "cpu_ms_raw": cpu_times[algorithm],
            "latency_ms_raw": latency_data[algorithm]["times"],
            "tx_bytes_raw": key_sizes[algorithm],
            "cpu_ms": sum(cpu_times[algorithm]) / iter,
            "latency_ms": latency_data[algorithm]["mean"],
            "tx_bytes": sum(key_sizes[algorithm]) / iter,
        }
        for algorithm in algorithms
    }


def _build_csv_rows(bench_data, include_raw=False):
    rows = [["Algorithm", "CPU_ms", "Latency_ms", "Transmission_bytes"]]

    for algorithm in bench_data.keys():
        label = ALGORITHM_LABELS.get(algorithm, algorithm)
        if include_raw:
            rows.append(
                [
                    label,
                    ";".join(map(str, bench_data[algorithm]["cpu_ms_raw"])),
                    ";".join(map(str, bench_data[algorithm]["latency_ms_raw"])),
                    ";".join(map(str, bench_data[algorithm]["tx_bytes_raw"])),
                ]
            )
        else:
            rows.append(
                [
                    label,
                    bench_data[algorithm]["cpu_ms"],
                    bench_data[algorithm]["latency_ms"],
                    bench_data[algorithm]["tx_bytes"],
                ]
            )

    return rows


# Export Data
if __name__ == "__main__": # Only export raw if ran as main
    bench_data = run_key_exchange_bench(include_hybrid=True)
    csv_data = _build_csv_rows(bench_data, include_raw=False)
    csv_data_raw = _build_csv_rows(bench_data, include_raw=True)

    with open("results/raw_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data_raw)
    print("CSV exported: raw_data.csv")

    with open("results/key_exchange_benchmark.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    print("CSV exported: key_exchange_benchmark.csv")

else:
    bench_data = run_key_exchange_bench()
    csv_data = _build_csv_rows(bench_data, include_raw=False)

    with open("results/key_exchange_benchmark.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    print("CSV exported: key_exchange_benchmark.csv")
