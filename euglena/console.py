"""
Console functionality
"""


class RedisStream(object):
    """
    File I/O object that streams data to/from redis keys (strings)

    """
    _read_position = 0
    _connection = None
    _buffer = bytes()

    def __init__(self, buffer_size=80, ttl=30):
        self._buffer_size = buffer_size
        self.ttl = ttl
        self.clear()

    def read(self, size=None):
        """
        Read from the input key stored in the redis server

        Parameters
        ----------
        size: int, optional
            How many bytes to read, if not specified reads everyting

        Returns
        -------
        bytes:
            Data read
        """
        if size:
            end = self._read_position + size
        else:
            end = -1
        data = self._buffer[self._read_position,end]
        self._read_position += len(data)
        return data

    def write(self, data):
        """
        Write data bytestring to a string in the output redis key

        Parameters
        ----------
        data : bytes
            The bytestring to write

        Returns
        -------
        The number of bytes written
        """
        if not self._buffer_size:
            self._buffer += data 
            return len(data)
			
        return len(data)

    def flush(self):
        """
        Write buffered data to the output key on the redis server and reset the buffer.
        """
        if not self._buffer:
            return
        self._buffer = bytes()

    def clear(self):
        """
        Clear all data from the redis output key on the redis server
        """
        self._buffer = bytes()

    def init(self):
        pass

    def deinit(self):
        pass

    def any(self):
        strlen = int(self._connection.execute_command('STRLEN', self.redis_stdin_key))
        return strlen - self._read_position

    def sendbreak(self):
        pass

    def readall(self):
        return self.read()

    def readinto(buf, nbytes=0):
        pass

    def readline(self):
        pass


class NullIO(object):
    def read(self):
        return b''

    def write(self, data):
        return len(data)

    def clear(self):
        pass

    def flush(self):
        pass

    def sendbreak(self):
        pass

    def readall(self):
        return b''

