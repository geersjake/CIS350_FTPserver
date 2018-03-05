import socket
import struct

class FTSock:
	# Basis taken from python socket howto
	def __init__(self, sock=None):
		if sock is None:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		else:
			self.sock = sock

	def connect(self, host, port):
		self.sock.connect((host, port))

	def recvbytes(self, num):
		chunks = []
		totalrecvd = 0
		while totalrecvd < num:
			chunk = self.sock.recv(min(num-totalrecvd, 2048))
			if chunk == b'':
				raise RuntimeError("Socket connection broken")
			chunks.append(chunk)
			totalrecvd = totalrecvd + len(chunk)
		return b''.join(chunks)

	def sendbytes(self, str):
		num = len(str)
		totalsent = 0
		while totalsent < num:
			sent = self.sock.send(str[totalsent:])
			if sent == 0:
				raise RuntimeError("Socket connection broken")
			totalsent = totalsent + sent

	def sendmsg(self, msg):
		msglen = len(msg)
		if msglen > (2**16):
			raise RuntimeError("Message too long")
