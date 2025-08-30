import json
from common.utils import Bet
from typing import TypeVar, Type

T = TypeVar('T')

LENGTH_BYTES = 4

class JsonMessage:
    def __init__(self, json_content: str):
        self.json_content = json_content

    def write(self, stream) -> int:
        payload = self.json_content.encode("utf-8")
        length = len(payload).to_bytes(LENGTH_BYTES, byteorder='big')
        stream.sendall(length)
        stream.sendall(payload)
        return LENGTH_BYTES + len(payload)

    @classmethod
    def read(cls, stream):
        length_bytes = cls._recv_exact(stream, LENGTH_BYTES)
        if not length_bytes:
            raise ConnectionError("Stream closed before receiving length")
        length = int.from_bytes(length_bytes, byteorder='big')
        payload = cls._recv_exact(stream, length)
        if not payload:
            raise ConnectionError("Stream closed before receiving payload")
        return cls(payload.decode("utf-8"))

    @staticmethod
    def _recv_exact(stream, n: int) -> bytes:
        data = b""
        while len(data) < n:
            chunk = stream.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def to_class(self, cls: Type[T]) -> T:
        return cls(**json.loads(self.json_content))


class BetMessage(JsonMessage):
    def __init__(self, bet: Bet):
        content = {
            "agency": str(bet.agency),
            "first_name": bet.first_name,
            "last_name": bet.last_name,
            "document": bet.document,
            "birthdate": bet.birthdate.isoformat(),
            "number": str(bet.number)
        }
        super().__init__(json.dumps(content))

    def to_class(self) -> Bet:
        return super().to_class(Bet)
