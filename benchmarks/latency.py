import time
import statistics

def measure_latency(operation, iterations=1000):
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        operation()
        end = time.perf_counter()

        times.append(end - start)

    return {
        "times": times,
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "std": statistics.stdev(times),
        "min": min(times),
        "max": max(times)
    }