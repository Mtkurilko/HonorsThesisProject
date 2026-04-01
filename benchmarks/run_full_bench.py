from run_key_exchange_bench import run_key_exchange_bench
from run_signature_bench import run_signature_bench

import csv

# Prompt for values
runs : int = int(input("How many runs do you want to do?: "))
message = b"message"

# Run the benches
kex_bench_data = run_key_exchange_bench(runs, message)
sig_bench_data = run_signature_bench(runs, message)

# Export the raw data
csv_data_raw = [
    ["Algorithm", "CPU_ms", "Latency_ms", "Transmission_bytes", "SignTime_ms", "VerifyTime_ms", "SignatureSize_bytes"],
    ["RSA", ";".join(map(str, kex_bench_data["RSA"]["cpu_ms_raw"])), ";".join(map(str, kex_bench_data["RSA"]["latency_ms_raw"])), ";".join(map(str, kex_bench_data["RSA"]["tx_bytes_raw"])), "N/A", "N/A", "N/A"],
    ["ECDH", ";".join(map(str, kex_bench_data["ECC"]["cpu_ms_raw"])), ";".join(map(str, kex_bench_data["ECC"]["latency_ms_raw"])), ";".join(map(str, kex_bench_data["ECC"]["tx_bytes_raw"])), "N/A", "N/A", "N/A"],
    ["ML-KEM (KYBER)", ";".join(map(str, kex_bench_data["KYBER"]["cpu_ms_raw"])), ";".join(map(str, kex_bench_data["KYBER"]["latency_ms_raw"])), ";".join(map(str, kex_bench_data["KYBER"]["tx_bytes_raw"])), "N/A", "N/A", "N/A"],
    ["ECDSA", "N/A", "N/A", "N/A", ";".join(map(str, sig_bench_data["RAW ECDSA SIGN"]["times"])), ";".join(map(str, sig_bench_data["RAW ECDSA VERIFY"]["times"])), ";".join(map(str, sig_bench_data["RAW ECDSA SIZE"]))],
    ["ML-DSA (Dilithium)", "N/A", "N/A", "N/A", ";".join(map(str, sig_bench_data["RAW ML-DSA SIGN"]["times"])), ";".join(map(str, sig_bench_data["RAW ML-DSA VERIFY"]["times"])), ";".join(map(str, sig_bench_data["RAW ML-DSA SIZE"]))],
]

with open("results/raw_data.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(csv_data_raw)
print("CSV exported: raw_data.csv")