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

if __name__ == "__main__":
    print(Sample("test-now"))
    print(Sample("test-epoch", 0))
