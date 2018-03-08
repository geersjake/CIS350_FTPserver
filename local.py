"""
:Authors:
    Chris van Zomeren
    
:Date: 2018-03-07
"""
from pathlib import Path
from hashlib import sha256
from collections import defaultdict
from os import fsencode

from FileInfo import FileInfo



class LocalFileInfoBrowser:
    """
    This class handles requests for information about local files.
    """
    # Note that there is a cycle between
    #   getFreshHash, listInfo, getInfo, and forceRefresh
    # when getting the hash of a directory.
    # This is because we determine the hash of a directory
    # from the hashes of its contents, and we want to get
    # those hashes from the cache if possible.

    # Files which are deleted on disk may have their information
    # still left in the cache until one of the refresh methods
    # is called with that specific path, or until refreshAll() is called.
    # This should not be a problem, since
    # a) isPossiblyChanged() will be true for a deleted file,
    #     so deleted files _will_ be refreshed when needed.
    # b) listings of directory contents are not cached,
    #     so deleted files will _not_ be included by mistake.

    def __init__(self):
        self.__cache = dict()


    def getFreshHash(self, path):
        """
        Get the hash of the file located at path.
        For regular files, this hash is generated from the file contents.
        For directories, this hash is generated from the names and
        (possibly cached) hashes of the directory contents.

        :param path: The path of the file to hash.
        """
        hash = sha256()
        if path.is_file():
            hash.update(path.read_bytes())
        elif path.is_dir():
            for info in sorted(self.listInfo(path), key=lambda _:_.path.name):
                hash.update(fsencode(info.path.name))
                hash.update(info.hash.digest())
        else:
            raise NotImplemented()
        
        return hash


    def isPossiblyChanged(self, path):
        """
        Determine whether the file located at path is different
        from the last cached version, allowing some false positives.
        For directories, a directory is changed if any of its contents
        have changed.

        :param path: The path of the file to check for changes.
        """
        return (
            path not in self.__cache
            or not path.exists()
            or path.is_dir and any(
                (self.isPossiblyChanged(f_path) for f_path in path.iterdir()))
            or path.stat().st_mtime_ns > self.__cache[path].mtime)


    def __shallowRefresh(self, path):
        """
        Replace the cached information for the file located at path
        with fresh information from the filesystem.
        If the file is a directory, this is not guaranteed to refresh
        all the information for its contents; to force an entire
        directory tree to be refreshed, use forceRefresh().

        :param path: The path of the file to refresh information for.
        """
        if path.exists():
            self.__cache[path] = FileInfo(
                path = path,
                is_dir = path.is_dir(),
                mtime = path.stat().st_mtime_ns,
                hash = self.getFreshHash(path))
        else:
            del self.__cache[path]


    def forceRefresh(self, path):
        """
        Replace the cached information for the file located at path
        with fresh information from the filesystem.
        If the file is a directory, this includes recursively refreshing
        the information for all its contents.

        :param path: The path of the file to refresh information for.
        """
        if path.is_dir():
            for f_path in path.iterdir():
                self.forceRefresh(f_path)
        self.__shallowRefresh(path)


    def getInfo(self, path):
        """
        Get a FileInfo instance representing the file at path.

        :param path: The path of the file.
        """
        if self.isPossiblyChanged(path):
            self.__shallowRefresh(path)
        return self.__cache.get(path)


    def listInfo(self, path):
        """
        Get a list of FileInfo instances representing all the files
        in the directory at path.

        :param path: The path of the directory to list files of.
        """
        return [self.getInfo(f_path) for f_path in path.iterdir()]
