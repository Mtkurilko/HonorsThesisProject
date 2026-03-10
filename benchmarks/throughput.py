import time

def measure_throughput(operation, duration=5):
    count = 0
    start = time.perf_counter()

    while time.perf_counter( - start < duration):
        operation()
        count += 1

    elapsed = time.perf_counter() - start

    return {
        "operations": count,
        "seconds": elapsed,
        "ops_per_sec": count / elapsed
    }