"""Handle queries and updates of local files.
:Authors:
    Chris van Zomeren

:Date: 2018-03-07
"""
from hashlib import sha256
from os import fsencode

from file_info import FileInfo



class UnrecognizedSpecialFile(Exception):
    """An exception raised when the file browser encounters a special file
    (e.g. symbolic link, socket, device, etc.) that it does not know how to
    handle.
    """
    def __init__(self, offending_path):
        """:param offending_path: The path which caused this exception.
        :type offending_path: pathlib.Path
        """
        self.offending_path = offending_path
        super().__init__(
            "Unrecognized special file '{}'".format(str(offending_path)))



class LocalFileInfoBrowser:
    """Handles requests for information about local files.
    """
    # Note that there is a cycle between
    #   get_fresh_hash, list_info, get_info, and force_refresh
    # when getting the hash of a directory.
    # This is because we determine the hash of a directory
    # from the hashes of its contents, and we want to get
    # those hashes from the cache if possible.

    # Files which are deleted on disk may have their information
    # still left in the cache until one of the refresh methods
    # is called with that specific path, or until refreshAll() is called.
    # This should not be a problem, since
    # a) is_possibly_changed() will be true for a deleted file,
    #     so deleted files _will_ be refreshed when needed.
    # b) listings of directory contents are not cached,
    #     so deleted files will _not_ be included by mistake.

    def __init__(self):
        self._cache = dict()


    def get_fresh_hash(self, path):
        """Get the hash of the file located at path.
        For regular files, this hash is generated from the file contents.
        For directories, this hash is generated from the names and
        (possibly cached) hashes of the directory contents.

        :param path: The path of the file to hash.
        :type path: pathlib.Path

        :raises UnrecognizedSpecialFile: given a path that is not a regular file or directory.

        :returns: A SHA256 digest of the file contents.
        :rtype: bytes
        """
        file_hash = sha256()
        if path.is_file():
            file_hash.update(path.read_bytes())
        elif path.is_dir():
            for info in sorted(self.list_info(path), key=lambda _: _.path.name):
                file_hash.update(fsencode(info.path.name))
                file_hash.update(info.hash)
        else:
            raise UnrecognizedSpecialFile(path)

        return file_hash.digest()


    def is_possibly_changed(self, path):
        """Determine whether the file located at path is different
        from the last cached version, allowing some false positives.
        For directories, a directory is changed if any of its contents
        have changed.

        :param path: The path of the file to check for changes.
        :type path: pathlib.Path

        :returns: Whether the file at path has possibly changed.
        :rtype: boolean
        """
        return (
            path not in self._cache
            or not path.exists()
            or path.is_dir and any(
                (self.is_possibly_changed(f_path) for f_path in path.iterdir()))
            or path.stat().st_mtime_ns > self._cache[path].mtime)


    def _shallow_refresh(self, path):
        """Replace the cached information for the file located at path
        with fresh information from the filesystem.
        If the file is a directory, this is not guaranteed to refresh
        all the information for its contents; to force an entire
        directory tree to be refreshed, use force_refresh().

        :param path: The path of the file to refresh information for.
        :type path: pathlib.Path
        """
        if path.exists():
            self._cache[path] = FileInfo(
                path = path,
                is_dir = path.is_dir(),
                mtime = path.stat().st_mtime_ns,
                file_hash = self.get_fresh_hash(path))
        else:
            del self._cache[path]


    def force_refresh(self, path):
        """Replace the cached information for the file located at path
        with fresh information from the filesystem.
        If the file is a directory, this includes recursively refreshing
        the information for all its contents.

        :param path: The path of the file to refresh information for.
        :type path: pathlib.Path
        """
        if path.is_dir():
            for f_path in path.iterdir():
                self.force_refresh(f_path)
        self._shallow_refresh(path)


    def get_info(self, path):
        """Get a FileInfo instance representing the file at path.

        :param path: The path of the file.
        :type path: pathlib.Path

        :returns: A summary of the file at path.
        :rtype: FileInfo
        """
        if self.is_possibly_changed(path):
            self._shallow_refresh(path)
        return self._cache.get(path)


    def list_info(self, path):
        """Get a list of FileInfo instances representing all the files
        in the directory at path.

        :param path: The path of the directory to list files of.
        :type path: pathlib.Path

        :returns: A summary of all files in the directory at path.
        :rtype: list of FileInfo
        """
        return [self.get_info(f_path) for f_path in path.iterdir()]

