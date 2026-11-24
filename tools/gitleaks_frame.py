"""Bounded, path-free TSG1 protocol, for trusted host/worker code only."""
import hashlib
import struct

HEADER = struct.Struct("!4sIQ")
RECORD = struct.Struct("!BI")
MAX_COUNT = 2048
MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024


def profile(mode):
    if mode == "content":
        return b"TSG1", 2, MAX_COUNT, MAX_TOTAL, 1
    if mode == "paths":
        return b"TSP1", 10, 256, 16 * 1024 * 1024, 0
    raise ValueError("FRAME_MODE_INVALID")


def valid(category, data, categories=2):
    if type(category) is not int or not 0 <= category < categories or not isinstance(data, bytes):
        raise ValueError("FRAME_RECORD_INVALID")
    if len(data) > MAX_FILE or b"\0" in data:
        raise ValueError("FRAME_DATA_INVALID")
    data.decode("utf-8", "strict")


def encode(records, stream, *, mode="content"):
    magic, categories, max_count, max_total, min_count = profile(mode)
    if not min_count <= len(records) <= max_count:
        raise ValueError("FRAME_COUNT_INVALID")
    total = 0
    for category, data in records:
        valid(category, data, categories)
        total += len(data)
        if total > max_total:
            raise ValueError("FRAME_TOTAL_LIMIT")
    digest = hashlib.sha256()
    def write(data):
        if stream.write(data) != len(data):
            raise ValueError("FRAME_SHORT_WRITE")
        digest.update(data)
    write(HEADER.pack(magic, len(records), total))
    for category, data in records:
        write(RECORD.pack(category, len(data)))
        write(data)
    return digest.hexdigest()


def decode(stream, *, mode="content"):
    expected_magic, categories, max_count, max_total, min_count = profile(mode)
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
    if magic != expected_magic or not min_count <= count <= max_count or expected > max_total:
        raise ValueError("FRAME_HEADER_INVALID")
    records = []
    total = 0
    for _ in range(count):
        category, size = RECORD.unpack(read(RECORD.size))
        if not 0 <= category < categories or size > MAX_FILE or total + size > expected:
            raise ValueError("FRAME_RECORD_INVALID")
        data = read(size)
        valid(category, data, categories)
        records.append((category, data))
        total += size
    if total != expected or stream.read(1):
        raise ValueError("FRAME_TOTAL_OR_TRAILING")
    return records, digest.hexdigest()
