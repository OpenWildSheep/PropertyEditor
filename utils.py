import time


def timer(func):
    def internal(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"Process done in {time.perf_counter() - start} for {func.__name__}()")
        return result

    return internal
