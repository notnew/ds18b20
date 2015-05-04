import os

class Sensor():
    # static method and data
    base_device_path = "/sys/bus/w1/devices/"
    def list_devices():
        devices = os.listdir(Sensor.base_device_path)
        return [d for d in devices if not d.startswith("w1_bus_master")]

    def __init__(self, id=None):
        self.id = id or Sensor.list_devices()[0]
        self.path = os.path.join(Sensor.base_device_path, self.id, 'w1_slave')
        self.file = open(self.path)

        self.celsius = "unset"
        self.fahrenheit = "unset"

    def get_temp(self):
        self.file.seek(0)
        self.raw_data = self.file.read()

        # get last column of second line (format is t=000000)
        raw = self.raw_data.splitlines()[1]
        raw = raw.split(" ")[-1]
        assert(raw.startswith("t="))
        raw = raw[2:]
        raw = int(raw)

        celsius = raw / 1000.0
        fahrenheit = celsius * 9/5. + 32

        self.raw = raw
        self.celsius = celsius
        self.fahrenheit = fahrenheit

    def __str__(self):
        return "Fahrenheit: {}, Celsius: {}".format(self.fahrenheit, self.celsius)

if __name__ == "__main__":
    s = Sensor();
    print(s)
    count = 5
    fahr, celsius = (0,0)
    for i in range(count):
        s.get_temp()
        print(s)
        fahr += s.fahrenheit
        celsius += s.celsius
    print("Average:")
    print("  Fahrenheit:", fahr/count)
    print("  Celsius:", celsius/count)
