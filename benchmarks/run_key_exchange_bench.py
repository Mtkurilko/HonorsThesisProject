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

def run_key_exchange_bench(iter=ITERATIONS, message=DEF_MESSAGE):
    cpu_times = {
        "RSA": [],
        "ECC": [],
        "KYBER": [],
    }
    latency_data = {
        "RSA": {},
        "ECC": {},
        "KYBER": {},
    }
    key_sizes = {
        "RSA": [],
        "ECC": [],
        "KYBER": [],
    }

    # ----- Benchmark -----
    for module in [kex_module("RSA"), kex_module("ECC"), kex_module("KYBER")]:
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
        "RSA": {
            "cpu_ms_raw": cpu_times["RSA"],
            "latency_ms_raw": latency_data["RSA"]["times"],
            "tx_bytes_raw": key_sizes["RSA"],
            "cpu_ms": sum(cpu_times["RSA"]) / iter,
            "latency_ms": latency_data["RSA"]["mean"],
            "tx_bytes": sum(key_sizes["RSA"]) / iter,
        },
        "ECC": {
            "cpu_ms_raw": cpu_times["ECC"],
            "latency_ms_raw": latency_data["ECC"]["times"],
            "tx_bytes_raw": key_sizes["ECC"],
            "cpu_ms": sum(cpu_times["ECC"]) / iter,
            "latency_ms": latency_data["ECC"]["mean"],
            "tx_bytes": sum(key_sizes["ECC"]) / iter,
        },
        "KYBER": {
            "cpu_ms_raw": cpu_times["KYBER"],
            "latency_ms_raw": latency_data["KYBER"]["times"],
            "tx_bytes_raw": key_sizes["KYBER"],
            "cpu_ms": sum(cpu_times["KYBER"]) / iter,
            "latency_ms": latency_data["KYBER"]["mean"],
            "tx_bytes": sum(key_sizes["KYBER"]) / iter,
        },
    }


# Export Data
if __name__ == "__main__": # Only export raw if ran as main
    bench_data = run_key_exchange_bench()
    
    csv_data = [
        ["Algorithm", "CPU_ms", "Latency_ms", "Transmission_bytes"],
        ["RSA", bench_data["RSA"]["cpu_ms"], bench_data["RSA"]["latency_ms"], bench_data["RSA"]["tx_bytes"]],
        ["ECDH", bench_data["ECC"]["cpu_ms"], bench_data["ECC"]["latency_ms"], bench_data["ECC"]["tx_bytes"]],
        ["ML-KEM (KYBER)", bench_data["KYBER"]["cpu_ms"], bench_data["KYBER"]["latency_ms"], bench_data["KYBER"]["tx_bytes"]],
    ]

    csv_data_raw = [
        ["Algorithm", "CPU_ms", "Latency_ms", "Transmission_bytes"],
        ["RSA", ";".join(map(str, bench_data["RSA"]["cpu_ms_raw"])), ";".join(map(str, bench_data["RSA"]["latency_ms_raw"])), ";".join(map(str, bench_data["RSA"]["tx_bytes_raw"]))],
        ["ECDH", ";".join(map(str, bench_data["ECC"]["cpu_ms_raw"])), ";".join(map(str, bench_data["ECC"]["latency_ms_raw"])), ";".join(map(str, bench_data["ECC"]["tx_bytes_raw"]))],
        ["ML-KEM (KYBER)", ";".join(map(str, bench_data["KYBER"]["cpu_ms_raw"])), ";".join(map(str, bench_data["KYBER"]["latency_ms_raw"])), ";".join(map(str, bench_data["KYBER"]["tx_bytes_raw"]))],
    ]

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
    
    csv_data = [
        ["Algorithm", "CPU_ms", "Latency_ms", "Transmission_bytes"],
        ["RSA", bench_data["RSA"]["cpu_ms"], bench_data["RSA"]["latency_ms"], bench_data["RSA"]["tx_bytes"]],
        ["ECDH", bench_data["ECC"]["cpu_ms"], bench_data["ECC"]["latency_ms"], bench_data["ECC"]["tx_bytes"]],
        ["ML-KEM (KYBER)", bench_data["KYBER"]["cpu_ms"], bench_data["KYBER"]["latency_ms"], bench_data["KYBER"]["tx_bytes"]],
    ]

    with open("results/key_exchange_benchmark.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    print("CSV exported: key_exchange_benchmark.csv")
