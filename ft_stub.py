"""Stub to allow UI development before FTSock et al. is completed.
:Authors:
    Colton Bates

:Date: 2018-03-26

:Version: 0.1
"""

class UnexpectedValueError(RuntimeError):
    """Raised when we receive something we did not expect according to the
    protocol specifications.
    """

    def __init__(self, state, value):
        """:param state: Identifies the state we were in (and hence what we were
        expecting).
        :param value: The data we got instead of what we were expecting.
        """
        super().__init__()
        self.state = state
        self.value = value

    def __repr__(self):
        return "UnexpectedValueError('" + self.state + "', '" + self.value + "'')"

    def __str__(self):
        return "in " + self.state + ", but got " + self.value

class BrokenSocketError(RuntimeError):
    """Raised when the socket connection is broken unexpectedly.
    """

    def __str__(self):
        return "Socket broken unexpectedly"

class FTSock:
    """Responsible for exposing socket functionality to be called by other
    parts of the project.
    """

    def __init__(self):
        pass

    def connect(self, host, port):
        """Connect to a remote host. Whichever host calls this first ends up
        technically being the server, and the other is the client, but it really
        does not matter.
        :param host: The URN/IP of the host to connect to.
        :type host: str
        :param port: The port number to use for the server of the connection. This
        means the user must have bind permissions for it, so lower numbers should
        not be used.
        :type port: number

        :return: True if connection is successful, otherwise an error is raised
        """
        return True

    def check_for_request(self):
        """Check the network buffer to see if there are any requests we need to
        respond to.
        :return: A value corresponding to the latest request received, which could
        be: No Request, File Request (in which case the filename is also returned),
        or File List Request.
        :rtype: str, str
        """
        return "None", ""

    def send_file(self, file_data):
        """Send a file in response to a File Request.
        :param file_data: The data for the file (includes file contents, file name,
        etc.).
        :return: True if the file was sent successfully, False otherwise.
        """
        return True

    def send_file_list(self, file_list):
        """Send the current local file list in response to a File List Request.
        :param file_list: The file list to send.
        :return: True if the file list was successfully sent, False otherwise.
        """
        return True

    def request_file(self, file_name):
        """Request that a file be sent to us.
        :param file_name: The file we want to request.
        :return: The file data (same type as passed to send_file()).
        """

        # pretending it will be a tuple of file name and contents
        return ("fr.txt", "Fake 'remote' file")

    def request_file_list(self):
        """Request that the remote host send its file list to us.
        :return: The file list (same type as passed to send_file_list()).
        """

        # No idea what type this is
        return None
