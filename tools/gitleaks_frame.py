"""Bounded, path-free TSG1 protocol, for trusted host/worker code only."""
import hashlib
import struct

HEADER = struct.Struct("!4sIQ")
RECORD = struct.Struct("!BI")
MAX_COUNT = 2048
MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024


def valid(category, data):
    if type(category) is not int or category not in (0, 1) or not isinstance(data, bytes):
        raise ValueError("FRAME_RECORD_INVALID")
    if len(data) > MAX_FILE or b"\0" in data:
        raise ValueError("FRAME_DATA_INVALID")
    data.decode("utf-8", "strict")


def encode(records, stream):
    if not 1 <= len(records) <= MAX_COUNT:
        raise ValueError("FRAME_COUNT_INVALID")
    total = 0
    for category, data in records:
        valid(category, data)
        total += len(data)
        if total > MAX_TOTAL:
            raise ValueError("FRAME_TOTAL_LIMIT")
    digest = hashlib.sha256()
    def write(data):
        stream.write(data)
        digest.update(data)
    write(HEADER.pack(b"TSG1", len(records), total))
    for category, data in records:
        write(RECORD.pack(category, len(data)))
        write(data)
    return digest.hexdigest()


def decode(stream):
    digest = hashlib.sha256()
    def read(size):
        chunks = bytearray()
        while len(chunks) < size:
            chunk = stream.read(size - len(chunks))
            if not chunk:
                raise ValueError("FRAME_TRUNCATED")
            chunks.extend(chunk)
        digest.update(chunks)
        return bytes(chunks)
    magic, count, expected = HEADER.unpack(read(HEADER.size))
    if magic != b"TSG1" or not 1 <= count <= MAX_COUNT or expected > MAX_TOTAL:
        raise ValueError("FRAME_HEADER_INVALID")
    records = []
    total = 0
    for _ in range(count):
        category, size = RECORD.unpack(read(RECORD.size))
        if category not in (0, 1) or size > MAX_FILE or total + size > expected:
            raise ValueError("FRAME_RECORD_INVALID")
        data = read(size)
        valid(category, data)
        records.append((category, data))
        total += size
    if total != expected or stream.read(1):
        raise ValueError("FRAME_TOTAL_OR_TRAILING")
    return records, digest.hexdigest()
