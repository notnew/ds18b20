if __name__ == "__main__":
    from ds18b20 import DS18B20
else:
    from .ds18b20 import DS18B20

import queue
import threading
import time

class Sample():
    def __init__(self, value, t=None):
        self.value = value
        self.time = time.time() if t is None else float(t)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "({:.2f}, {})".format(self.time, self.value)

    def __iter__(self):
        return iter((self.time, self.value))

class Sampler():
    """ periodically sample the temperature """
    def __init__(self, period, sample_q=None):
        self.period = period
        self.sample_q = sample_q or queue.Queue()

        self._sensor = DS18B20()
        self._thread = None
        self._stop_event = threading.Event()
        self._sampling_time = 0           # how long it takes to read sensor
        self._timeout = self.period  - self._sampling_time

    def run(self):
        def _read_sample():
            start_time = time.time()
            self._sensor.get_temp()
            end_time = time.time()

            self._sampling_time = end_time - start_time
            self._timeout = self.period - self._sampling_time

            return self._sensor.fahrenheit

        def _run():
            self._timeout = self.period - self._sampling_time
            while not self._stop_event.wait(self._timeout):
                samp = Sample(_read_sample())
                self.sample_q.put(samp)

        if not self.is_running():
            self._stop_event.clear()
            self._thread = threading.Thread(target = _run)
            self._thread.start()

    def stop(self):
        if self.is_running():
            self._stop_event.set()
            self._thread.join()

    def is_running(self):
        return self._thread and self._thread.is_alive()

class SmoothSampler():
    """ average sevaral readings to get sample """
    def __init__(self, count, period, sample_q=None):
        self.count = count
        self.period = period
        self.sample_q = sample_q or queue.Queue()

        self._raw_sampler = Sampler(period=self.period/self.count)
        self._thread = None

    def run(self):
        def _run():
            self._raw_sampler.run()

            total = 0
            sample_count = 0
            raw_q = self._raw_sampler.sample_q

            try:
                for sample in  (iter(raw_q.get, None)):
                    total += sample.value
                    sample_count += 1
                    if (sample_count >= self.count):
                        averaged_sample = Sample(total/sample_count, sample.time)
                        self.sample_q.put(averaged_sample)
                        total = 0
                        sample_count = 0

            finally:
                self._raw_sampler.stop()

        if not self.is_running():
            self._thread = threading.Thread(target=_run)
            self._thread.start()

    def stop(self):
        if self.is_running():
            raw_q = self._raw_sampler.sample_q
            raw_q.put(None)
            self._thread.join()

    def is_running(self):
        return self._thread and self._thread.is_alive()

if __name__ == "__main__":
    print(Sample("test-now"))
    print(Sample("test-epoch", 0))
    q = queue.Queue()
    sampler = SmoothSampler(3, 10, q)
    sampler.run()
    for x in range(5):
        (t, v) = q.get()
        print((t,v))
    sampler.stop()
    print("run2")
    sampler.run()
    for x in range(5):
        (t, v) = q.get()
        print((t,v))
    sampler.stop()
