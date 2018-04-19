"""Common data structures and constants for file information.
:Authors:
    Chris van Zomeren

:Date: 2018-03-07
"""

from base64 import b64encode



class FileInfo:
    """Contains information about a file
    which should be sufficient to determine:
    a) Whether a given file on a given system has changed.
    b) Whether a given file on one host is identical to
        a given file on another host.
    c) Which file is more recent, given one file each from
        the two hosts.
    d) Whether a file is a regular file, a directory, or
        something unusual like a pipe or link, since these
        are all handled differently in various parts of the
        application.
    """

    def __init__(self, *, path, file_hash, is_dir, mtime):
        """Initialize a FileInfo
        :param path: The path of the file associated with this FileInfo,
            as a pathlib.Path instance.
        :type path: pathlib.Path

        :param file_hash: A SHA256 digest of the file's contents.
        :type file_hash: bytes

        :param is_dir: Whether the file is a directory.
        :type is_dir: boolean

        :param mtime: The last modification time of the file, using the
            same convention as st_mtime_ns.
        :type mtime: integer
        """
        self.path = path
        self.hash = file_hash
        self.is_dir = is_dir
        self.mtime = mtime

    def __repr__(self):
        """__repr__ for FileInfo
        :returns: a readable representation containing all important fields
        :rtype: string
        """
        return '<FileInfo: path=\'{}\' hash={} is_dir={} mtime={}>'\
            .format(
                self.path,
                b64encode(self.hash),
                self.is_dir,
                self.mtime)