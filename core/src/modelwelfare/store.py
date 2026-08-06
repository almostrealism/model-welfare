"""Item-level result store: append-only streams of length-delimited protobuf.

Framing is the standard varint-delimited protobuf stream (the same wire
framing as Java's ``writeDelimitedTo``), implemented here directly so the
at-rest format has no dependency on any one language's protobuf internals.

Layout under a data root::

    <root>/<experiment_id>/<condition_id>/<kind>/<producer>.pb

``kind`` names the record family ("samples" for SampleRecord, "scores" for
JudgeScore, ...). ``producer`` must be unique per concurrently-writing
process — by convention the logical host name, qualified further if one host
runs several writers. One file per producer means multi-machine runs never
contend on a file; readers merge all producer streams.

Writers flush after every record, so a crashed producer loses at most the
record being written. Readers treat a truncated tail as an error rather than
silently dropping it — a partial file means a producer died and the caller
should know.
"""

from pathlib import Path
from typing import Iterator


def _write_varint(out, value: int) -> None:
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.write(bytes((byte | 0x80,)))
        else:
            out.write(bytes((byte,)))
            return


def _read_varint(stream):
    shift = 0
    result = 0
    while True:
        chunk = stream.read(1)
        if not chunk:
            if shift == 0:
                return None
            raise ValueError("truncated varint at end of stream")
        byte = chunk[0]
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result
        shift += 7
        if shift > 63:
            raise ValueError("varint too long; stream is corrupt")


class RecordWriter:
    """Appends messages to one delimited stream. Context manager."""

    def __init__(self, path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._out = open(self._path, "ab")

    def write(self, message) -> None:
        data = message.SerializeToString()
        _write_varint(self._out, len(data))
        self._out.write(data)
        self._out.flush()

    def close(self) -> None:
        if not self._out.closed:
            self._out.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def read_records(path, message_type) -> Iterator:
    """Yields every message in one delimited stream file.

    Raises ValueError on a truncated record or varint, naming the file.
    """
    with open(path, "rb") as stream:
        while True:
            try:
                length = _read_varint(stream)
            except ValueError as error:
                raise ValueError(f"{path}: {error}") from None
            if length is None:
                return
            data = stream.read(length)
            if len(data) < length:
                raise ValueError(
                    f"{path}: truncated record (expected {length} bytes, got {len(data)})"
                )
            message = message_type()
            message.ParseFromString(data)
            yield message


class ResultStore:
    """One data root holding every record stream for every experiment."""

    def __init__(self, root):
        self._root = Path(root)

    def path(self, experiment_id: str, condition_id: str, kind: str, producer: str) -> Path:
        return self._root / experiment_id / condition_id / kind / f"{producer}.pb"

    def writer(
        self, experiment_id: str, condition_id: str, kind: str, producer: str
    ) -> RecordWriter:
        return RecordWriter(self.path(experiment_id, condition_id, kind, producer))

    def read(self, message_type, experiment_id: str, condition_id: str, kind: str) -> Iterator:
        """Yields records merged from every producer stream, in producer-name
        then write order. Missing directories yield nothing."""
        directory = self._root / experiment_id / condition_id / kind
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*.pb")):
            yield from read_records(path, message_type)
