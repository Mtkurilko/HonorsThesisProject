import sys
import os

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import csv
from crypto import ecc, dilithium
from benchmarks import latency, bandwith

# Message
message = b"message"

# ECDSA keys
ecdsa_pub, ecdsa_priv = ecc.generate_keys()
# ML-DSA (Dilithium) keys
mldsa_pub, mldsa_priv = dilithium.generate_keys()

# ----- Benchmark -----

# Sign Time
ecdsa_sign_data = latency.measure_latency(lambda: ecc.sign_message(ecdsa_priv, message))
mldsa_sign_data = latency.measure_latency(lambda: dilithium.sign_message(mldsa_priv, message))

# Verify Time
ecdsa_signature = ecc.sign_message(ecdsa_priv, message)
ecdsa_verify_data = latency.measure_latency(lambda: ecc.verify_signature(ecdsa_pub, ecdsa_signature, message))

mldsa_signature = dilithium.sign_message(mldsa_priv, message)
mldsa_verify_data = latency.measure_latency(lambda: dilithium.verify_signature(mldsa_pub, mldsa_signature, message))

# Signature Size
ecdsa_size_data = bandwith.measure_size(ecdsa_signature)
mldsa_size_data = bandwith.measure_size(mldsa_signature)


# Data Export
csv_data = [
    ["Algorithm", "SignTime_mean_s", "VerifyTime_mean_s", "SignatureSize_bytes"],
    ["ECDSA", ecdsa_sign_data["mean"], ecdsa_verify_data["mean"], ecdsa_size_data],
    ["ML-DSA (Dilithium)", mldsa_sign_data["mean"], mldsa_verify_data["mean"], mldsa_size_data],
]

csv_rawdata = [
    ["Algorithm", "SignTime_s", "VerifyTime_s", "SignatureSize_bytes"],
    ["ECDSA", ";".join(map(str, ecdsa_sign_data["times"])), ";".join(map(str, ecdsa_verify_data["times"])), ecdsa_size_data],
    ["ML-DSA (Dilithium)", mldsa_sign_data["times"], mldsa_verify_data["times"], mldsa_size_data],
]

csv_rawdata[2][1] = ";".join(map(str, mldsa_sign_data["times"]))
csv_rawdata[2][2] = ";".join(map(str, mldsa_verify_data["times"]))

def run_signature_bench():
    return {
        "MEAN DATA": csv_data,
        "RAW DATA": csv_rawdata
    }

if __name__ == "__main__":

    with open("results/signature_benchmark.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    print("CSV exported: signature_benchmark.csv")

    with open("results/raw_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_rawdata)
    print("CSV exported: raw_data.csv")