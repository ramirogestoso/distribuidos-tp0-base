import json
from common.utils import Bet
from typing import TypeVar, Type

T = TypeVar('T')

LENGTH_BYTES = 4

class JsonMessage:
    def __init__(self, json_content: str):
        self.json_content = json_content

    def write_to(self, stream) -> int:
        payload = self.json_content.encode("utf-8")
        length = len(payload).to_bytes(LENGTH_BYTES, byteorder='big')
        stream.sendall(length)
        stream.sendall(payload)
        return LENGTH_BYTES + len(payload)

    @classmethod
    def read_from(cls, stream):
        length_bytes = cls._recv_exact(stream, LENGTH_BYTES)
        payload_length = int.from_bytes(length_bytes, byteorder='big')
        payload = cls._recv_exact(stream, payload_length)
        return cls(payload.decode("utf-8"))

    @staticmethod
    def _recv_exact(stream, n: int) -> bytes:
        data = b""
        while len(data) < n:
            chunk = stream.recv(n - len(data))
            if not chunk:
                raise ConnectionError(f"Stream closed while expecting {n} bytes, got {len(data)}")
            data += chunk
        return data

    def to_class(self, cls: Type[T]) -> T:
        return cls(**json.loads(self.json_content))


class BetMessage(JsonMessage):
    def to_class(self) -> Bet:
        return super().to_class(Bet)
