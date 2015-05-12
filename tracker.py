from ds18b20 import DS18B20
import time

class Tracker():
    """ Track the temperature over time, keeping a history of the data """

    def __init__(self):
        self.seconds = History(100, 1)
        self.minutes = History(100, 60)
        self.half_hours = History(None, 60 * 30)

        self._sensor = DS18B20()

    def get_sample(self):
        total = 0.0
        count = 3
        for i in range(count):
            self._sensor.get_temp()
            total += self._sensor.fahrenheit
        sample = Sample(total/count)
        self.seconds.add_sample(sample)
        self.minutes.add_sample(sample)
        self.half_hours.add_sample(sample)

class History():
    """ a history of temperature samples """
    def __init__(self, count, period):
        """ count is an integer for a fixed length buffer or None for unlimited
            period is the time in seconds between samples
        """
        self.init_time = time.time()
        if count is None:
            self.count = None
        else:
            value_err = ValueError(count,
                                   "Count must be a positive integer or None")
            try:
                if int(count) <= 0:
                    raise value_err
            except ValueError as err:
                raise value_err from err

        self.count = int(count) if count else None
        self.period = float(period)
        self._data = []

    def _sample_due(self, sample):
        if not self._data:
            return True
        elapsed = sample.time - self._data[-1].time
        return elapsed >= self.period


    def add_sample(self, sample):
        """ add the sample to history if enough time has elapsed
            otherwise do nothing """

        adjusted_time = sample.time - self.init_time
        adjusted_sample = Sample(value = sample.value, t = adjusted_time)

        if not self._sample_due(adjusted_sample):
            return

        if self.count is None or len(self) < self.count:
            self._data.append(adjusted_sample)
        else:
            self._data.append(adjusted_sample)
            self._data = self._data[-self.count:]


    def __str__(self):
        return "<History: {}>".format(self._data)

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, i):
        return self._data[i]

    def __len__(self):
        return len(self._data)

class Sample():
    def __init__(self, value, t=None):
        self.value = value
        self.time = time.time() if t is None else float(t)

    def __repr__(self):
        return str(self)
    def __str__(self):
        return "({:.2f}, {})".format(self.time, self.value)

if __name__ == "__main__":
    print(Sample(4))
    print(Sample("hello"))
    tracker = Tracker()
    t = tracker
    # t.seconds._data = [Sample(i, t=0.0) for i in range(200)]
    for i in range(4):
        t.get_sample()
        print(t.seconds)
        print(t.seconds[-1])
        print(t.minutes[-1])
        print(t.half_hours[-1])
