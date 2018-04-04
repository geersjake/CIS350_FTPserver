"""Contains errors that the network operations can throw.
:Authors:
    Colton Bates

:Version 0.6:
"""

class UnexpectedValueError(RuntimeError):
    """Raised when we receive something we did not expect according to the
    protocol specifications.
    """

    def __init__(self, state, value):
        """:param state: Identifies the state we were in (and hence what we were
        expecting).
        :type state: string
        :param value: The data we got instead of what we were expecting.
        :type value: string
        """
        super().__init__()
        self.state = state
        self.value = value

    def __repr__(self):
        """:return: The human-readable construction of the error.
        :rtype: string
        """
        return "UnexpectedValueError('" + self.state + "', '" + self.value + "'')"

    def __str__(self):
        """:return: The string representation of the error (as would be printed,
        etc.).
        :rtype: string
        """
        return "in " + self.state + ", but got " + self.value

class BrokenSocketError(RuntimeError):
    """Raised when the socket connection is broken unexpectedly.
    """

    def __str__(self):
        """:return: The string representation of the error (as would be printed,
        etc.).
        :rtype: string
        """
        return "Socket broken unexpectedly"
