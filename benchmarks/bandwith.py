def measure_size(data):
    if isinstance(data, bytes):
        return len(data)
    
    if isinstance(data, tuple):
        return sum(len(x) for x in data)
    
    return len(data)