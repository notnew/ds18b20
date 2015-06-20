# hack to import DS18B20 whether module is executed as script or not
if __name__ == "__main__":
    from ds18b20 import DS18B20
else:
    from .ds18b20 import DS18B20

from sample import Sample

from http.server import HTTPServer, BaseHTTPRequestHandler
import pickle
import queue
import socket
import threading
import time

class TemperatureRH (BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.replace("http://", "")
        request = path.split("/")[1]

        tracker = self.server.tracker
        if request in ["temp", "", "temp_str"]:
            self.temp_str()
        elif request == "latest":
            latest = tracker.latest
            self.send_pickled(latest)
        elif request in tracker.histories.keys():
            history = tracker.histories[request]
            self.send_pickled(history)
        else:
            self.bad_request()

    def temp_str(self):
        latest = tracker.latest
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

class Server(HTTPServer):
    def __init__(self, port=9901, server_address=('', 9901), tracker=None):
        self.tracker = tracker
        super().__init__(server_address, TemperatureRH)

class Tracker():
    """ Track the temperature over time, keeping a history of the data """

    def __init__(self,  histories={}, minimum_period = 60, sample_q=None):
        self.minimum_period = minimum_period

        self.latest = Sample("No data")
        self.histories = histories

        self._sensor = DS18B20()
        self.stopping_ev = threading.Event()
        self._sampling_time = 0
        self.sample_q = sample_q or queue.Queue()

    def _sampler(self):
        print("_sampler started")
        self._get_sample()
        while not self.stopping_ev.wait(self.minimum_period-self._sampling_time):
            self._get_sample()
        print("_sampler ended")

    def _get_sample(self):
        total = 0.0
        count = 3

        start_time = time.time()
        for i in range(count):
            self._sensor.get_temp()
            total += self._sensor.fahrenheit
        end_time = time.time()
        self._sampling_time = end_time - start_time
        sample = Sample(total/count)

        self.latest = sample
        was_updated = False
        for history in self.histories.values():
            if history.add_sample(sample):
                was_updated = True
        if was_updated:
            self.sample_q.put(sample)

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
        """ if enough time has elapsed, add the sample to history, return True
            otherwise do nothing and return False
        """
        if not self._sample_due(sample):
            return False

        if self.count is None or len(self) < self.count:
            self._data.append(sample)
        else:
            self._data.append(sample)
            self._data = self._data[-self.count:]
        return True

    def __str__(self):
        return "<History: {}>".format(self._data)

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, i):
        return self._data[i]

    def __len__(self):
        return len(self._data)

if __name__ == "__main__":
    histories = {"seconds": History(100, 1),
                 "minutes": History(100, 60),
                 "five_minutes": History(12*24*5, 60*5),
                 "half_hours": History(None, 60*30) }

    tracker = Tracker(histories=histories, minimum_period=10)
    tracker.start_sampler()
    httpd = Server(tracker=tracker)
    try:
        print("starting server...")
        httpd.serve_forever()
    finally:
        tracker.stop_sampler()
