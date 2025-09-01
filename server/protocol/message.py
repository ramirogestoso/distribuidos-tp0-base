from abc import ABC, abstractmethod
from common.utils import Bet

# agency, first_name, last_name, documento, date, number
BET_LENGTH_BYTES = 4 + 30 + 20 + 8 + 10 + 4

class Message(ABC):
    def __init__(self, message: bytes):
        self.message = message

    def write_to(self, stream):
        stream.sendall(self.message)

    @abstractmethod
    def read_from(cls, stream):
        raise NotImplementedError()


class BetMessage(Message):
    @classmethod
    def read_from(cls, stream):
        message = _recv_exact(stream, BET_LENGTH_BYTES)
        return cls(message)
    
    def to_bet(self):
        msg = self.message
        agency = _decode(msg[0:4])
        first_name = _decode(msg[4:34])
        last_name = _decode(msg[34:54])
        documento = _decode(msg[54:62])
        date = _decode(msg[62:72])
        number = _decode(msg[72:76])
        return Bet(agency, first_name, last_name, documento, date, number)


def _recv_exact(stream, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = stream.recv(n - len(data))
        if not chunk:
            raise ConnectionError(f"Stream closed while expecting {n} bytes, got {len(data)}")
        data += chunk
    return data

def _decode(bytes: bytes) -> str:
    return bytes.decode('utf-8').rstrip('\x00')