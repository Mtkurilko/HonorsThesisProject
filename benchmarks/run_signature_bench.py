import sys
import os

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import csv
from crypto import ecc, dilithium
from benchmarks import latency, bandwith
import statistics

# CONSTANTS
ITERATIONS = 1000
DEF_MESSAGE = b"message"

def run_signature_bench(iter=ITERATIONS, message=DEF_MESSAGE): # Call function from out of file to retrieve data

    # ECDSA keys
    ecdsa_pub, ecdsa_priv = ecc.generate_keys()
    # ML-DSA (Dilithium) keys
    mldsa_pub, mldsa_priv = dilithium.generate_keys()

    # ----- Benchmark -----

    # Sign Time
    ecdsa_sign_data = latency.measure_latency(lambda: ecc.sign_message(ecdsa_priv, message), iter)
    mldsa_sign_data = latency.measure_latency(lambda: dilithium.sign_message(mldsa_priv, message), iter)

    # Signature Size
    ecdsa_size_data_raw = []
    mldsa_size_data_raw = []

    for i in range(ITERATIONS): # Iterate to find mean size
        ecdsa_signature = ecc.sign_message(ecdsa_priv, message)
        ecdsa_size_data_raw.append(bandwith.measure_size(ecdsa_signature))

        mldsa_signature = dilithium.sign_message(mldsa_priv, message)
        mldsa_size_data_raw.append(bandwith.measure_size(mldsa_signature))

    ecdsa_size_data = statistics.mean(ecdsa_size_data_raw)
    mldsa_size_data = statistics.mean(mldsa_size_data_raw)

    # Verify Time
    ecdsa_verify_data = latency.measure_latency(lambda: ecc.verify_signature(ecdsa_pub, ecdsa_signature, message), iter)
    mldsa_verify_data = latency.measure_latency(lambda: dilithium.verify_signature(mldsa_pub, mldsa_signature, message), iter)

    # Signature Size
    ecdsa_size_data = bandwith.measure_size(ecdsa_signature)
    mldsa_size_data = bandwith.measure_size(mldsa_signature)


    # Data Export
    csv_data = [
        ["Algorithm", "SignTime_mean_ms", "VerifyTime_mean_ms", "SignatureSize_bytes"],
        ["ECDSA", ecdsa_sign_data["mean"], ecdsa_verify_data["mean"], ecdsa_size_data],
        ["ML-DSA (Dilithium)", mldsa_sign_data["mean"], mldsa_verify_data["mean"], mldsa_size_data],
    ]

    csv_rawdata = [
        ["Algorithm", "SignTime_ms", "VerifyTime_ms", "SignatureSize_bytes"],
        ["ECDSA", ";".join(map(str, ecdsa_sign_data["times"])), ";".join(map(str, ecdsa_verify_data["times"])), ecdsa_size_data_raw],
        ["ML-DSA (Dilithium)", mldsa_sign_data["times"], mldsa_verify_data["times"], mldsa_size_data_raw],
    ]

    csv_rawdata[2][1] = ";".join(map(str, mldsa_sign_data["times"]))
    csv_rawdata[2][2] = ";".join(map(str, mldsa_verify_data["times"]))

    return {
        "MEAN DATA": csv_data,
        "RAW DATA": csv_rawdata,
        "RAW ECDSA SIGN": ecdsa_sign_data,
        "RAW ML-DSA SIGN": mldsa_sign_data,
        "RAW ECDSA VERIFY": ecdsa_verify_data,
        "RAW ML-DSA VERIFY": mldsa_verify_data,
        "RAW ECDSA SIZE": ecdsa_size_data_raw,
        "RAW ML-DSA SIZE": mldsa_size_data_raw,
    }


if __name__ == "__main__": # Only export raw if ran as main
    bench_data = run_signature_bench()

    with open("results/raw_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(bench_data["RAW DATA"])
    print("CSV exported: raw_data.csv")

    with open("results/signature_benchmark.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(bench_data["MEAN DATA"])
    print("CSV exported: signature_benchmark.csv")
else:
    bench_data = run_signature_bench()

    with open("results/signature_benchmark.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(bench_data["MEAN DATA"])
    print("CSV exported: signature_benchmark.csv")