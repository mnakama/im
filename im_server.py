#!/usr/bin/python3
import sys
import os
import socket
import traceback
import datetime
import time
import pickle

chunkSize = 1024
maxIdleTime = 60 * 5 #5 minutes

serverIP = '23.92.75.10'

users = {}

class USER:
	def isActive(self):
		if self.lastActive + maxIdleTime < time.time():
			return False
		else:
			return True

	def keepalive(self):
		self.lastActive = time.time()

class UDPsock(socket.socket):
	def __init__(self, *args):
		socket.socket.__init__(self, *args)
		self.lastActive = time.time()
	
	def send(self, *args):
		socket.socket.send(self, *args)
		self.lastActive = time.time()

def markRosterStale():
	for user in users:
		user.needsRoster = True

def sendRosterToPeer(peer):
	sock.sendto(b'ROST' + pickle.dumps(users), peer)

def sendRosterToAll():
	for user in users.values():
		sendRosterToPeer(user.peer)

def processMsg(message, peer):
	print('From: {:s}\nMessage: {:s}'.format(str(peer), str(message)))

	msgType = message[:4]
	msg = message[4:]

	rosterChanged = False

	#remove inactive users
	for username in list(users.keys()):
		user = users[username]
		if not user.isActive():
			del users[username]
			rosterChanged = True


	if msgType == b'REG1': #signing on/keepalive
		username = str(msg, encoding='utf-8')

		if username in users:
			rosterChanged = False
			user = users[username]
		else:
			rosterChanged = True
			user = USER()

		user.name = username
		user.peer = peer

		users[username] = user

		user.keepalive()

		printUsers()

		if rosterChanged:
			#send roster list
			sendRosterToAll()

		sock.sendto(b'REGA' + socket.inet_aton(peer[0]) + peer[1].to_bytes(2, 'big'), peer)

	elif msgType == b'REG2': #changing name
		olduser, newuser = str(msg, encoding='utf-8').split('\0')
		try:
			user = users[olduser]
			del users[olduser]
		except KeyError:
			traceback.print_exc()
			user = USER()

		user.name = newuser
		user.peer = peer

		users[newuser] = user

		user.keepalive()

		printUsers()

		#send roster list
		sendRosterToAll()

	elif msgType == b'REG0': #signing off
		username = str(msg, encoding='utf-8')
		try:
			del users[username]
		except:
			traceback.print_exc()
		printUsers()
		sendRosterToAll()

	elif msgType == b'ROS?': #user is requesting the roster
		user.keepalive()
		sendRosterToPeer(peer)

	elif msgType == b'PCH?': #send hole punch request to peer
		dest_ip = socket.inet_ntoa(msg[0:4])
		dest_port = int.from_bytes(msg[4:6], byteorder='big')
		src_ip = socket.inet_aton(peer[0])
		src_port = peer[1]
		sock.sendto(b'PCH ' + src_ip + src_port.to_bytes(2, 'big'), (dest_ip, dest_port))
	
	elif msgType == b'PRXY': #proxied IP provided
		username, ip = msg.split(b'\0')
		username = str(username, encoding='utf-8')
		ip = socket.inet_ntoa(ip)
		print(username, ip)

		user = users[username]
		user.proxiedIP = ip
		user.keepalive()
		sendRosterToAll()


def printUsers():
	for username, user in users.items():
		print(username, user.__dict__)


try:
	myport = int(sys.argv[1])
except IndexError:
	myport = 9050 #server port

sock = UDPsock(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', myport))

while True:
	try:
		message, peer = sock.recvfrom(4096)
	except socket.error as e:
		if e.errno != 11 and e.errno != 10035: raise
	else:
		try:
			processMsg(message, peer)
		except KeyboardInterrupt:
			raise
		except:
			traceback.print_exc()


sock.close()
