r"""
This module contains the data-types neccesary to describe the data being
handeled by the mbfilter client

"""
import struct

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
        variables = line.split(',')
        decoded_vars =[]
        for var in variables:
            decoded_vars.append(int(var))
        return MeasuredPeak(decoded_vars[0], decoded_vars[1], decoded_vars[2], decoded_vars[3])

    def as_line(self):
        return f"{self.timestamp},{self.peak_height},{self.cycle},{self.speed}\n"

    @staticmethod
    def decode_from_bytes(array):
        tmp = bytearray(b'\x00\x00\x00\x00')
        largetmp = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00')
        for i, b in enumerate(array[0:5]):
            largetmp[i] |= b
        timestamp = struct.unpack('<Q', largetmp)[0]
        for i, b in enumerate(array[5:7]):
            tmp[i] |= b
        tmp[2] |= array[7] & 0x03
        cycle = struct.unpack('<I', tmp)[0]
        tmp = bytearray(b'\x00\x00\x00\x00')
        tmp[0] = array[7] >> 2
        tmp[0] |= (array[8] << 6) & 0xff
        tmp[1] = (array[8] & 0x0c) >> 2
        speed = struct.unpack('<I', tmp)[0]
        tmp = bytearray(b'\x00\x00\x00\x00')
        tmp[0] = array[8] >> 4
        for i, b in enumerate(array[9:12]):
            tmp[i] |= (b << 4) & 0xff
            tmp[i+1] = b >> 4
        peak_height = struct.unpack('<I', tmp)[0]
        return MeasuredPeak(timestamp, peak_height, cycle, speed)

    def to_array(self):
        return [self.timestamp, self.peak_height, self.cycle, self.speed]
