from ds18b20 import DS18B20
from http.server import HTTPServer, BaseHTTPRequestHandler
import pickle
import socket
import threading
import time

class TemperatureRH (BaseHTTPRequestHandler):
    def do_GET(self):
        request = self.path.split("/")[1]

        if request in ["temp", "", "temp_str"]:
            self.temp_str()
        elif request == "latest":
            latest = self.server.latest
            self.send_pickled(latest)
        elif request in self.server.histories.keys():
            history = self.server.histories[request]
            self.send_pickled(history)
        else:
            self.bad_request()

    def temp_str(self):
        latest = self.server.latest
        temperature = "{}\n".format(latest.value).encode("utf-8")
        length = len(temperature)

        self.send_response(200, "ok")
        self.send_header("Content-Length", length)
        self.end_headers()
        self.wfile.write(temperature)

    def send_pickled(self, value):
        data = pickle.dumps(value)
        length = len(data)

        self.send_response(200, "ok")
        self.send_header("Content-Length", length)
        self.send_header("Content-Type", "application/python-pickle")
        self.end_headers()
        self.wfile.write(data)

    def bad_request(self):
        self.send_response(400, "Bad Request")
        self.end_headers()


class Tracker(HTTPServer):
    """ Track the temperature over time, keeping a history of the data """

    def __init__(self, port=9901, server_address=('', 9901), histories={},
                 minimum_period = 60):
        super().__init__(server_address, TemperatureRH)

        self.minimum_period = minimum_period

        self.latest = Sample("No data")
        self.histories = histories

        self._sensor = DS18B20()
        self.stopping_ev = threading.Event()

    def _sampler(self):
        print("_sampler started")
        self._get_sample()
        while not self.stopping_ev.wait(self.minimum_period):
            self._get_sample()
        print("_sampler ended")

    def _get_sample(self):
        total = 0.0
        count = 3

        for i in range(count):
            self._sensor.get_temp()
            total += self._sensor.fahrenheit
        sample = Sample(total/count)

        self.latest = sample
        for history in self.histories.values():
            history.add_sample(sample)

    def start_sampler(self):
        self.stopping_ev.clear()
        threading.Thread(target=self._sampler).start()

    def stop_sampler(self):
        self.stopping_ev.set()

class History():
    """ a history of temperature samples """
    def __init__(self, count, period):
        """ count is an integer for a fixed length buffer or None for unlimited
            period is the time in seconds between samples
        """
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
        if not self._sample_due(sample):
            return

        if self.count is None or len(self) < self.count:
            self._data.append(sample)
        else:
            self._data.append(sample)
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
    histories = {"seconds": History(100, 1),
                 "minutes": History(100, 60),
                 "five_minutes": History(12*24*5, 60*5),
                 "half_hours": History(None, 60*30) }

    httpd = Tracker(histories=histories, minimum_period=1)
    httpd.start_sampler()
    try:
        print("starting server...")
        httpd.serve_forever()
    finally:
        httpd.stop_sampler()
