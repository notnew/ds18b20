import os
import time

def pp_temperature(temp, scale='F'):
    return "{:0.2f}°{}".format(temp, scale)

class DS18B20():
    # static method and data
    base_device_path = "/sys/bus/w1/devices/"
    def list_devices():
        devices = os.listdir(DS18B20.base_device_path)
        return [d for d in devices if not d.startswith("w1_bus_master")]

    def __init__(self, id=None):
        self.id = id or DS18B20.list_devices()[0]
        self.path = os.path.join(DS18B20.base_device_path, self.id, 'w1_slave')
        self.file = open(self.path)
        self.raw_data = None

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
        if self.raw_data:
            data = "{:10f}°F {:10f}°C".format(self.fahrenheit, self.celsius)
        else:
            data = "No Data"
        return "<DS18B20 {}: {}>".format(self.id, data)

if __name__ == "__main__":
    s = DS18B20();
    print(s)
    count = 5
    fahr, celsius = (0,0)
    for i in range(count):
        s.get_temp()
        print(s)
        fahr += s.fahrenheit
        celsius += s.celsius
    (year, month, day, hour, minute, sec, wday, yday, isdst) = time.localtime()
    print("\nAverage: ({:02}:{:02}:{:02})".format(hour,minute,sec))
    print("  ", pp_temperature(fahr/count))
    print("  ", pp_temperature(celsius/count, "C"))
