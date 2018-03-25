from pathlib import PurePath
from hashlib import sha256
from os import fsencode
from file_info import FileInfo, LocalFileInfoBrowser

class MockPath:

    def __init__(self, name, *,
                 exists,
                 stat,
                 is_dir,
                 read_bytes = b"",
                 iterdir = []):

        self.name = name
        self._path = PurePath(name)
        self._exists = exists
        self._stat = stat
        self._is_dir = is_dir
        self._read_bytes = read_bytes
        self._iterdir = iterdir
    
    def exists(self): return self._exists
    def stat(self): return self._stat
    def is_dir(self): return self._is_dir
    def is_file(self): return not self.is_dir()
    def read_bytes(self): return self._read_bytes
    def iterdir(self): return self._iterdir

class MockStatResult:
    def __init__(self, *, st_mtime_ns):
        self.st_mtime_ns = st_mtime_ns


def get_mock_file_path(name="MOCK_FILE", read_bytes=b"Mock contents"):
    return MockPath(name,
                    exists=True,
                    stat=MockStatResult(st_mtime_ns=0),
                    is_dir=False,
                    read_bytes=read_bytes)

def get_mock_dir_path(name="MOCK_DIR", *, iterdir=[]):
    return MockPath(name,
                    exists=True,
                    stat=MockStatResult(st_mtime_ns=0),
                    is_dir=True,
                    iterdir=iterdir)



class TestLocalFileInfoBrowser:

    def test_get_fresh_hash__for_file(self):
        p = get_mock_file_path()
        L = LocalFileInfoBrowser()
        assert(L.get_fresh_hash(p).digest()
               == sha256(b"Mock contents").digest())

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
        assert(L.get_fresh_hash(p).digest()
               == h.digest())

    def test_is_possibly_changed__for_updated_mtime(self):
        p = get_mock_file_path()
        L = LocalFileInfoBrowser()
        assert(L.is_possibly_changed(p))
        L._cache[p] = FileInfo(path=p, is_dir=False, mtime=0, file_hash=sha256())
        assert(not L.is_possibly_changed(p))
        p._stat.st_mtime_ns += 1
        assert(L.is_possibly_changed(p))

    def test_is_possibly_changed__for_updated_dir_contents(self):
        p = get_mock_dir_path(iterdir=[
            get_mock_file_path("HAM", b"sandwich"),
            get_mock_file_path("EGGS", b"with toast")])
        L = LocalFileInfoBrowser()
        assert(L.is_possibly_changed(p))
        L._cache[p] = FileInfo(path=p, is_dir=True, mtime=0, file_hash=sha256())
        L._cache[p._iterdir[0]] = FileInfo(path="HAM", is_dir=False, mtime=0, file_hash=sha256())
        L._cache[p._iterdir[1]] = FileInfo(path="EGGS", is_dir=False, mtime=0, file_hash=sha256())
        assert(not L.is_possibly_changed(p))
        p._iterdir[1]._stat.st_mtime_ns += 1
        assert(L.is_possibly_changed(p))

    def test___shallow_refresh(self):
        p = get_mock_file_path()
        L = LocalFileInfoBrowser()
        L._shallow_refresh(p)
        assert(p in L._cache)
        old = L._cache[p]
        p._read_bytes = b"Updated"
        L._shallow_refresh(p)
        assert(L._cache[p].hash.digest() == sha256(b"Updated").digest())
        p._exists = False
        L._shallow_refresh(p)
        assert(p not in L._cache)
