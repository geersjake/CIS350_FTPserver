"""
:Authors:
    Chris van Zomeren

:Date: 2017-03-07
"""

from enum import Enum, unique

@unique
class SharedFileStatus(Enum):
    MISSING = 0
    REMOTE_ONLY = 1
    LOCAL_ONLY = 2
    REMOTE_NEWER = 3
    LOCAL_NEWER = 4
    IDENTICAL = 5
    
def getSharedFileStatus(*, local, remote):
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
