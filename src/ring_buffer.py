
import mmap
import os
import struct
from pathlib import Path


class RingBuffer:
    """Fixed-capacity, memory-mapped ring buffer for fixed-size records."""

    def __init__(
        self,
        path: str,
        capacity: int,
        record_size: int,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if record_size <= 0:
            raise ValueError("record_size must be positive")

        self.capacity = capacity
        self.record_size = record_size
        self._header_size = 16
        self._header = struct.Struct("<QQ")
        self._size = self._header_size + capacity * record_size
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self._file = open(self.path, "w+b")
        self._file.truncate(self._size)
        self._map = mmap.mmap(self._file.fileno(), self._size)

        self._write_index = 0
        self._read_index = 0
        self._count = 0
        self._closed = False
        self._write_header()

    def _write_header(self) -> None:
        self._map[:self._header_size] = self._header.pack(
            self._write_index,
            self._read_index,
        )

    def put(self, record: bytes) -> None:
        if self._closed:
            raise ValueError("buffer is closed")
        if len(record) != self.record_size:
            raise ValueError(
                f"Expected {self.record_size} bytes, got {len(record)}"
            )
        if self._count == self.capacity:
            raise BufferError("ring buffer is full")

        offset = self._header_size + self._write_index * self.record_size
        self._map[offset:offset + self.record_size] = record

        self._write_index = (self._write_index + 1) % self.capacity
        self._count += 1
        self._write_header()

    def get(self) -> bytes:
        if self._closed:
            raise ValueError("buffer is closed")
        if self._count == 0:
            raise BufferError("ring buffer is empty")

        offset = self._header_size + self._read_index * self.record_size
        record = self._map[offset:offset + self.record_size]

        self._read_index = (self._read_index + 1) % self.capacity
        self._count -= 1
        self._write_header()
        return record

    def __len__(self) -> int:
        return self._count

    def close(self) -> None:
        if not self._closed:
            self._map.flush()
            self._map.close()
            self._file.close()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
