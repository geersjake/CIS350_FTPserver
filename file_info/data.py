"""Common data structures and constants for file information.
:Authors:
    Chris van Zomeren

:Date: 2018-03-07
"""

from base64 import b64encode
from enum import Enum, unique



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

        :param file_hash: A hash of the file's contents.
        :type file_hash: hashlib.sha256

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
                b64encode(self.hash.digest()),
                self.is_dir,
                self.mtime)



@unique
class SharedFileStatus(Enum):
    """Represents the status of a (local, remote) pair of files.
    """

    MISSING = 0
    REMOTE_ONLY = 1
    LOCAL_ONLY = 2
    REMOTE_NEWER = 3
    LOCAL_NEWER = 4
    IDENTICAL = 5



def determine_shared_file_status(*, local, remote):
    """Determine the "sharing" status of a file based on a local and a remote
    FileInfo.

    :param local: Information for a local file.
    :type local: FileInfo

    :param remote: Information for a remote file.
    :type remote: FileInfo

    :returns: The sharing status of the pair of files.
    :rtype: SharedFileStatus
    """

    if local is None and remote is None:
        return SharedFileStatus.MISSING
    elif local is None:
        return SharedFileStatus.REMOTE_ONLY
    elif remote is None:
        return SharedFileStatus.LOCAL_ONLY
    elif local.hash == remote.hash:
        return SharedFileStatus.IDENTICAL
    elif local.mtime < remote.mtime:
        return SharedFileStatus.REMOTE_NEWER
    else:
        return SharedFileStatus.LOCAL_NEWER

