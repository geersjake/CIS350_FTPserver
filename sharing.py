"""Query for shared file status
:Authors:
    Chris van Zomeren

:Date: 2017-03-07
"""

from enum import Enum, unique

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

