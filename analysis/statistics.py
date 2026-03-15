import numpy as np

def stats(data):
    arr = np.array(data)

    return {
        "mean": arr.mean(),
        "median": np.median(arr),
        "std": arr.std(),
        "p95": np.percentile(arr, 95),
        "p99": np.percentile(arr, 99),
    }