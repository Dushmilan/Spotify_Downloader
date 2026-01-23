import time

class Throttler:
    def __init__(self, interval):
        self.interval = interval
        self.last_call = 0

    def __call__(self, func, *args, **kwargs):
        now = time.time()
        if now - self.last_call > self.interval:
            self.last_call = now
            func(*args, **kwargs)
