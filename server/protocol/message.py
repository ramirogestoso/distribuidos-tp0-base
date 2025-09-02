from abc import ABC
import io
from common.utils import Bet

# first_name, last_name, documento, date, number
BET_LENGTH_BYTES = 30 + 20 + 8 + 10 + 4
BATCH_LENGTH_BYTES = 4
BET_AGENCY_BYTES = 4

class Message(ABC):
    def __init__(self, message: bytes):
        self.message = message

    def write_to(self, stream):
        stream.sendall(self.message)


class BetMessage(Message):
    @classmethod
    def read_from(cls, stream):
        message = _recv_exact(stream, BET_LENGTH_BYTES)
        return cls(message)

    def to_bet(self, agency: str):
        msg = io.BytesIO(self.message)
        first_name = _decode(msg.read(30))
        last_name = _decode(msg.read(20))
        documento = _decode(msg.read(8))
        date = _decode(msg.read(10))
        number = _decode(msg.read(4))
        return Bet(agency, first_name, last_name, documento, date, number)
    
class BatchMessage(Message):
    @classmethod
    def read_bets(cls, stream) -> tuple[list[Bet], str]:
        agency = _decode(_recv_exact(stream, BET_AGENCY_BYTES))
        bets_amount = _recv_exact(stream, BATCH_LENGTH_BYTES)
        length = int.from_bytes(bets_amount, byteorder='big')
        return [BetMessage.read_from(stream).to_bet(agency) for _ in range(length)], agency

class CodeMessage(Message):
    def __init__(self, code: int):
        super().__init__(code.to_bytes(4, byteorder='big'))


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