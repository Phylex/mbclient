r"""
This module contains the data-types neccesary to describe the data being
handeled by the mbfilter client

"""

class MeasuredPeak:
    """a class that represents an event measured by the MBFilter"""
    def __init__(self, timestamp, peak_height, cycle, speed):
        self.timestamp = timestamp
        self.peak_height = peak_height
        self.cycle = cycle
        self.speed = speed

    def __str__(self):
        return f"ts: {self.timestamp}, ph: {self.peak_height},\
cycle: {self.cycle}, speed: {self.speed}"

    @staticmethod
    def decode_from_line(line):
        r"""
        decode a line received directly from the server into the MeasuredPeak object

        The line contains the values timestamp, peak height, cycle and speed in that
        order from left to right seperated by spaces. Each value is the a hex encoded
        big-endian string representation of the respektive value.

        Parameters
        ----------
        line: sting
        This is the line that comes from the websocket directly from the server
        """
        variables = line.split()
        decoded_vars =[]
        for var in variables:
            # the values are big-endian encoded and have to be reversed and then converted
            decoded_vars.append(int(''.join([var[j:j+2] for j in range(0, len(var), 2)][::-1]), 16))
        return MeasuredPeak(decoded_vars[0], decoded_vars[1], decoded_vars[2], decoded_vars[3])

    def as_line(self):
        return f"{self.timestamp},{self.peak_height},{self.cycle},{self.speed}\n"
