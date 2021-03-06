# pylint: disable = missing-docstring, missing-return-doc, missing-return-type-doc
# pylint: disable = invalid-name
# pylint: disable = no-self-use
# pylint: disable = protected-access

import pytest

from base64 import b64decode
from pathlib import PurePath
from hashlib import sha256
from os import fsencode
from file_info import FileInfo, LocalFileInfoBrowser, UnrecognizedSpecialFile

class MockPath:

    def __init__(self, name, *,
                 exists,
                 stat,
                 is_dir,
                 is_file,
                 read_bytes = b"",
                 iterdir = []):

        self.name = name
        self._path = PurePath(name)
        self._exists = exists
        self._stat = stat
        self._is_dir = is_dir
        self._is_file = is_file
        self._read_bytes = read_bytes
        self._iterdir = iterdir

    def exists(self):
        return self._exists
    def stat(self):
        return self._stat
    def is_dir(self):
        return self._is_dir
    def is_file(self):
        return self._is_file
    def read_bytes(self):
        return self._read_bytes
    def iterdir(self):
        return self._iterdir

class MockStatResult:
    def __init__(self, *, st_mtime_ns):
        self.st_mtime_ns = st_mtime_ns


def get_mock_file_path(name="MOCK_FILE", read_bytes=b"Mock contents"):
    return MockPath(name,
                    exists=True,
                    stat=MockStatResult(st_mtime_ns=0),
                    is_dir=False,
                    is_file=True,
                    read_bytes=read_bytes)

def get_mock_dir_path(name="MOCK_DIR", *, iterdir=[]):
    return MockPath(name,
                    exists=True,
                    stat=MockStatResult(st_mtime_ns=0),
                    is_dir=True,
                    is_file=False,
                    iterdir=iterdir)

def get_mock_special_file_path(name="MOCK_SPECIAL_FILE"):
    return MockPath(name,
                    exists=True,
                    stat=MockStatResult(st_mtime_ns=0),
                    is_dir=False,
                    is_file=False)

def get_mock_hash():
    return b"NOT A REAL HASH! THIS IS A TEST!" # must be 32 bytes
    #        00000000011111111112222222222333
    #        12345678901234567890123456789012



class TestFileInfo:

    def test_repr(self):
        fi = FileInfo(path='a', file_hash=b64decode('b000'), is_dir='c', mtime='d')
        assert repr(fi) == '<FileInfo: path=\'a\' hash=b\'b000\' is_dir=c mtime=d>'



class TestLocalFileInfoBrowser:

    def test_get_fresh_hash__for_file(self):
        p = get_mock_file_path()
        L = LocalFileInfoBrowser()
        assert L.get_fresh_hash(p) == sha256(b"Mock contents").digest()

    def test_get_fresh_hash__for_dir(self):
        p = get_mock_dir_path(iterdir=[
            get_mock_file_path("HAM", b"sandwich"),
            get_mock_file_path("EGGS", b"with toast")])
        L = LocalFileInfoBrowser()
        h = sha256()
        h.update(fsencode("EGGS"))
        h.update(sha256(b"with toast").digest())
        h.update(fsencode("HAM"))
        h.update(sha256(b"sandwich").digest())
        assert L.get_fresh_hash(p) == h.digest()

    def test__get_fresh_hash__for_special_file(self):
        p = get_mock_special_file_path()
        L = LocalFileInfoBrowser()
        with pytest.raises(UnrecognizedSpecialFile) as e:
            L.get_fresh_hash(p)

    def test_is_possibly_changed__for_updated_mtime(self):
        p = get_mock_file_path()
        L = LocalFileInfoBrowser()
        assert L.is_possibly_changed(p)
        L._cache[p]\
            = FileInfo(path=p, is_dir=False, mtime=0, file_hash=get_mock_hash())
        assert not L.is_possibly_changed(p)
        p._stat.st_mtime_ns += 1
        assert L.is_possibly_changed(p)

    def test_is_possibly_changed__for_updated_dir_contents(self):
        p = get_mock_dir_path(iterdir=[
            get_mock_file_path("HAM", b"sandwich"),
            get_mock_file_path("EGGS", b"with toast")])
        L = LocalFileInfoBrowser()
        assert L.is_possibly_changed(p)
        L._cache[p]\
            = FileInfo(path=p, is_dir=True, mtime=0, file_hash=get_mock_hash())
        L._cache[p._iterdir[0]]\
            = FileInfo(path="HAM", is_dir=False, mtime=0, file_hash=get_mock_hash())
        L._cache[p._iterdir[1]]\
            = FileInfo(path="EGGS", is_dir=False, mtime=0, file_hash=get_mock_hash())
        assert not L.is_possibly_changed(p)
        p._iterdir[1]._stat.st_mtime_ns += 1
        assert L.is_possibly_changed(p)

    def test___shallow_refresh(self):
        p = get_mock_file_path()
        L = LocalFileInfoBrowser()
        L._shallow_refresh(p)
        assert p in L._cache
        p._read_bytes = b"Updated"
        L._shallow_refresh(p)
        assert L._cache[p].hash == sha256(b"Updated").digest()
        p._exists = False
        L._shallow_refresh(p)
        assert p not in L._cache

    def test__force_refresh(self):
        p = get_mock_dir_path(iterdir=[
            get_mock_file_path("HAM", b"sandwich"),
            get_mock_dir_path("EGGS")])
        L = LocalFileInfoBrowser()
        L.force_refresh(p)
        assert p in L._cache
        assert p._iterdir[1] in L._cache