import tracemalloc

def measure_memory(operation):
    tracemalloc.start()

    operation()

    current, peak = tracemalloc.get_traced_memory()

    tracemalloc.stop()

    return {
        "current_bytes": current,
        "peak_bytes": peak
    }