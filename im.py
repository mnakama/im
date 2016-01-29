#!/usr/bin/python3
import sys
import os
import socket
import traceback
import datetime
import time
import pickle
import platform #used for os detection

# Requires python 3 and tkinter
try:
	from tkinter import *
except ImportError:
	traceback.print_exc()
	print ('\nYou need to install tkinter (python 3)\nOn Redhat/Fedora, type: sudo yum install python3-tkinter')
	exit(1)

from tkinter.scrolledtext import ScrolledText
import _tkinter

#from tkinter import scrolledtext

if platform.system() == 'Linux':
	#this block forks to background so closing the console doesn't end the program
	#it won't work for windows, but windows python will be fine with a .pyw extention
	#update: it also seems to not work on Darwin/MacOSX
	pid = None
	try:
		pid = os.fork()
	except OSError: #this is what the example used
		pass
	except AttributeError: #this is what windows 7 actually throws
		pass
	else:
		if pid > 0: exit(0)


mainwindow = None
chunkSize = 1024
registerInterval = 60
doubleclickTime = 0.5

serverIP = '23.92.75.10'
serverHttpPort = 80
serverPort = 9050
server = (serverIP, serverPort)

users = {}
userList = []
myProxiedIP = None

class USER:
	pass

def timestamp():
	return '[' + datetime.datetime.now().strftime('%X') + ']'

def getProxiedIP():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(('23.92.75.10', 80))

	sock.send(b'GET / HTTP/1.1\n\r\n\r') #let the proxy add everything else

	ip = sock.recv(4096)

	try:
		#is this a valid ip? throws exception if not
		ip_str = socket.inet_ntoa(ip)
		#print(ip_str, ip)
	except OSError:
		ip_str = sock.getsockname()[0]
		ip = socket.inet_aton(ip_str)

	#not sure if this next line is needed, but it errors on Mac OSX
	#sock.shutdown(socket.SHUT_RDWR)
	sock.close()

	return ip

def checkSendProxyIP():
	global myProxiedIP

	print('ibm address detected. Getting proxied address.')
	try:
		myProxiedIP = getProxiedIP()
	except:
		traceback.print_exc()
		myProxiedIP = False
	else:
		print(socket.inet_ntoa(myProxiedIP))
		sock.sendto(b'PRXY' + (persist['myname'] + '\0').encode() + myProxiedIP, server)


class MainWindow(Tk):
	def __init__(self):
		Tk.__init__(self)
		self.title('im.py')
		self.lastClick = None

		self.main = Frame(self)
		self.main.pack(expand=True, fill=BOTH)

		self.name_Frame = Frame(self.main)
		self.name_Frame.pack(side=TOP)
		self.name_Label = Label(self.name_Frame, text='Your name:')
		self.name_Label.pack(side=LEFT)
		self.name_Entry = Entry(self.name_Frame)
		self.name_Entry.pack(side=LEFT)
		self.name_Entry.bind('<Return>', self.changeName_Action)
		self.name_Entry.bind('<FocusOut>', self.changeName_Action)
		self.name_Entry.insert(0, persist['myname'])

		self.host_Frame = Frame(self.main)
		self.host_Frame.pack(side=TOP)
		self.host_Label = Label(self.host_Frame, text='Message to "IP:Port":')
		self.host_Label.pack(side=LEFT)
		self.host_Entry = Entry(self.host_Frame)
		self.host_Entry.pack(side=LEFT)
		self.host_Entry.bind('<Return>', self.connect_Action)
		self.host_Entry.focus()

		self.roster_Listbox = Listbox(self.main)
		self.roster_Listbox.pack(side=BOTTOM, expand=True, fill=BOTH)
		self.roster_Listbox.bind('<ButtonRelease>', self.rosterClick_Action)

		#debug
		self.host_Entry.insert(0, 'localhost:9001')

		self.checker = None

		try: #this only works in linux for some reason
			self.tk.createfilehandler(sock, _tkinter.READABLE, self.eventChecker)

		except: #rescue windows
			traceback.print_exc()
			print ('Windows mode!')
			sock.setblocking(False)
			self.checker = self.main.after(100, self.eventChecker)

		self.registrator = None #self.main.after(registerInterval * 1000, self.register)
		self.register() #registers every registerInterval seconds

	def destroy(self):
		if self.checker != None: self.main.after_cancel(self.checker)
		Tk.destroy(self)
	
	def receive(self, message):
		global users
		global userList
		global myProxiedIP
		msgType = message[:4]
		msg = message[4:]

		if msgType == b'ROST': #roster
			users = pickle.loads(msg)
			userList = sorted(users.values(), key=lambda u: u.name)

			self.roster_Listbox.delete(0, END)
			for user in userList:
				try:
					proxiedIP = user.proxiedIP
					proxy_str = ' internal: {:s}'.format(proxiedIP)
				except AttributeError:
					proxy_str = ''
				self.roster_Listbox.insert(END, '{:s} ({:s}:{:d}{:s})'.format(user.name, user.peer[0], user.peer[1], proxy_str))
		elif msgType == b'REGA': #registration ack
			if not users:
				sock.sendto(b'ROS?', server) #hey, send us the roster!

			if msg[0] == 129: #possibly in IBM intranet
				if myProxiedIP is None:
					print('ibm address detected. Getting proxied address.')
					checkSendProxyIP()

		elif msgType == b'PCH ': #punch a udp hole to a peer
			ip = msg[0:4]
			ip_str = socket.inet_ntoa(ip)
			port = int.from_bytes(msg[4:6], byteorder='big')

			print('Received hole punch request. Punching UDP to peer', ip_str + ':' + str(port))

			sock.sendto(b'PCHA', (ip_str, port)) #hole punch acknowledgement
		else:
			print('Message type: {:s}\nMessage: {:s}'.format(str(msgType), str(msg)))

	def eventChecker(self, *args): #could be (self, socket_fd, mask)
		try:
			try:
				message, peer = sock.recvfrom(4096)
			except socket.error as e:
				if e.errno != 11 and e.errno != 10035: raise
			else:
				if peer == (serverIP, 9050):
					self.receive(message)
				else:
					cw = ChatWindow.get(peer)
					cw.receive(message)
		except Exception as e:
			traceback.print_exc()
		finally:
			#try:
			#	if time.time() - sock.lastActive > registerInterval:
			#		#sock.sendto(b'NOP ', server)
			#		self.register()
			#		sock.lastActive = time.time()
			#except:
			#	traceback.print_exc()
			if self.checker != None: self.checker = self.main.after(100, self.eventChecker)

	def connect_Action(self, *args):
		peer = self.host_Entry.get()

		try:
			peer, port = peer.split(':', 1)
		except ValueError:
			peer = socket.gethostbyname(peer)
			peer = (peer, 9000)
		else:
			peer = socket.gethostbyname(peer)
			peer = (peer, int(port))

		ChatWindow.get(peer)

	def changeName_Action(self, event):
		newname = self.name_Entry.get()
		if persist['myname'] != newname:
			self.reregister(persist['myname'], newname)
			persist['myname'] = newname
	
	def rosterClick_Action(self, event):
		if event.num == 1:
			try:
				sel = int(self.roster_Listbox.curselection()[0]) #int is required for python 3.2, but not 3.4+
			except IndexError:
				pass #list box is empty; nothing was clicked
			else:
				user = userList[sel]
				peer = getProperPeer(user)
				self.host_Entry.delete(0, END)
				self.host_Entry.insert(END, '{:s}:{:d}'.format(peer[0], peer[1]))
				if self.lastClick and self.lastClick > time.time() - doubleclickTime:
					#ChatWindow.get(userList[sel].peer)
					ChatWindow.get(peer)
				self.lastClick = time.time()
	
	def reregister(self, oldname, newname):
		try:
			sock.sendto(b'REG2' + (oldname + '\0' + newname).encode(), server)
		except:
			traceback.print_exc()
		finally:
			pass #if self.registrator is not False: self.registrator = self.main.after(registerInterval * 1000, self.register)

	def register(self, *args):
		try:
			sock.sendto(b'REG1' + persist['myname'].encode(), server)
		except:
			traceback.print_exc()
		finally:
			if self.registrator is not False: self.registrator = self.main.after(registerInterval * 1000, self.register)

	def deregister(self, *args):
		try:
			sock.sendto(b'REG0' + persist['myname'].encode(), server)
		except:
			traceback.print_exc()
		finally:
			self.registrator = False


class ChatWindow(Toplevel):
	chats = {}

	@staticmethod
	def get(peer):
		try:
			return ChatWindow.chats[peer]
		except KeyError:
			ChatWindow.chats[peer] = ChatWindow(peer)
			return ChatWindow.chats[peer]
		
	def __init__(self, peer):
		Toplevel.__init__(self, mainwindow)
		self.peer = peer
		self.recvFile = None

		self.title(peer[0] + ':' + str(peer[1]))

		#self.root = Tk()
		#self.main = Frame(self.root)
		self.main = Frame(self)
		self.main.pack(expand=True, fill=BOTH)

		self.chat_Text = ScrolledText(self.main)
		self.chat_Text.pack(expand=True, fill=BOTH)
		self.chat_Text['height'] = 10
		#print self.keys()
		#print self.chat_Text.keys()

		self.send_Frame = Frame(self.main)
		self.send_Frame.pack(fill=X)

		self.send_Text = Entry(self.send_Frame)
		self.send_Text.pack(side=LEFT, expand=True, fill=X)
		self.send_Text.bind('<Return>', self.send_Action)
		self.send_Button = Button(self.send_Frame, text='Send', command=self.send_Action)
		self.send_Button.pack(side=LEFT)
		self.holePunch_Button = Button(self.send_Frame, text='UDP punch', command=self.holePunch_Action)
		self.holePunch_Button.pack(side=LEFT)
		self.sendFile_Button = Button(self.send_Frame, text='File', command=self.sendFile_Action)
		self.sendFile_Button.pack(side=LEFT)

		self.status_Label = Label(self.main, text='Peer: ' + self.peer[0] + ':' + str(self.peer[1]))
		self.status_Label.pack()

		self.send_Text.focus()

		#self.protocol("WM_DELETE_WINDOW", self._destroy)
	
	def destroy(self):
		#print 'destroy'
		del ChatWindow.chats[self.peer]
		Toplevel.destroy(self)

	def send_Action(self, *args):
		text = self.send_Text.get()
		message = persist['myname'] + ': ' + text
		if (text.strip()):
			self.chat_Text.insert(END, timestamp() + ' ' + message)
			self.chat_Text.see(END)
			self.send_Text.delete(0, len(text))

			sock.sendto(b'TEXT' + message.encode(), self.peer)
			#sock.lastActive = time.time()
		else:
			self.send_Text.delete(0,END)
	
	def holePunch_Action(self, *args):
		#request server to forward our hole punch request to peer
		print('Sending hole punch request')
		sock.sendto(b'PCH?' + socket.inet_aton(self.peer[0]) + self.peer[1].to_bytes(2, 'big'), server)
	
	def sendFile_Action(self, *args):
		filename = '/tmp/test'
		size = os.path.getsize(filename)
		net_size = socket.htonl(size)
		
# 0x12345678
# 78 56 34 12
# 12 34 56 78

		self.sendFile = BLANK()
		self.sendFile.handle = open(filename, 'br')

		data = size.to_bytes(4, 'big') + self.sendFile.handle.read(chunkSize)
		sock.sendto(b'FILE' + data, self.peer)
		section = 0

		while True:
			data = self.sendFile.handle.read(chunkSize)
			if data == b'': break
			section += 1
			sock.sendto(b'FILE' + section.to_bytes(4, 'big') + data, self.peer)



	def receive(self, message):
		msgType = message[:4]
		msg = message[4:]
		if msgType == b'TEXT':
			self.chat_Text.insert(END, timestamp() + ' ' + str(msg, encoding='utf-8') + '\n')
			self.chat_Text.see(END)
			self.bell()

			#ip = self.peer[0].split('.')
			#ip = bytes((int(ip[0]), int(ip[1]), int(ip[2]), int(ip[3])))
			ip = self.peer[0]
			ip = socket.inet_aton(ip)

			port = self.peer[1]
			port = bytes((port // 0x100, port & 0xFF))

			sock.sendto(b'CFRM' + ip + port, self.peer)
			#sock.lastActive = time.time()

		elif msgType == b'CFRM':
			#ip = '{}.{}.{}.{}'.format(msg[0], msg[1], msg[2], msg[3])
			ip = socket.inet_ntoa(msg[0:4])
			port = msg[4] * 0x100 + msg[5]
			self.chat_Text.insert(END, ' [R]\n')
		
		elif msgType == b'PCHA':
			print('Received hole punch from:', self.peer)
			self.chat_Text.insert(END, timestamp() + ' ' + '[UDP hole punch success]\n')
			self.chat_Text.see(END)

		elif msgType == b'FILE':
			if self.recvFile == None:
				self.recvFile = BLANK()
				self.recvFile.size = int.from_bytes(msg[:4], 'big')
				self.recvFile.part = 0

				self.recvFile.handle = open('/tmp/test2', 'wb')
				self.recvFile.handle.write(msg[4:])
			else:
				self.recvFile.part = int.from_bytes(msg[:4], 'big')
				self.recvFile.handle.seek(self.recvFile.part * chunkSize)
				self.recvFile.handle.write(msg[4:])

			sock.sendto(b'FCNF' + self.recvFile.part.to_bytes(4, 'big'), self.peer)

			if self.recvFile.handle.tell() == self.recvFile.size:
				self.recvFile.handle.close()
				self.recvFile = None

class BLANK:
	pass

def getMyExtAddr():
	return users[persist['myname']].peer
	
	
def getProperPeer(user):
	#if external IP is the same, we need to use internal IP
	if getMyExtAddr()[0] == user.peer[0]:
		try:
			return (user.proxiedIP, 9000)
		except AttributeError:
			return user.peer
	else:
		return user.peer

def printUsers():
	for username, user in users.items():
		print('Users:')
		print(username, user.__dict__)

class UDPsock(socket.socket):
	def __init__(self, *args):
		socket.socket.__init__(self, *args)
		self.lastActive = time.time()
	
	def send(self, *args):
		socket.socket.send(self, *args)
		self.lastActive = time.time()




home = os.getenv('HOME')
if home is None:
	home = os.getenv('APPDATA')

if home is not None:
	config = os.path.join(home, '.im')
else:
	config = '.im'

print ('Config file:',config)

try:
	persist = pickle.load(open(config, 'rb'))
except FileNotFoundError:
	persist = {}
	try:
		myname = os.getlogin()
	except OSError: #windows doesn't have a concept of getlogin()
		myname = os.getenv('USER', default='user')
	except AttributeError:
		myname = 'user'
	persist['myname'] = myname


try:
	if sys.argv[1] == '-h':
		print ('Usage: ', sys.argv[0], '[listenport]')
		exit(0)
except IndexError:
	pass


try:
	myport = int(sys.argv[1])
except IndexError:
	myport = 9000

#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock = UDPsock(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', myport))

mainwindow = MainWindow()




try:
	mainwindow.main.mainloop()
finally:
	pickle.dump(persist, open(config, 'wb'))
	mainwindow.deregister()

#sock.shutdown(socket.SHUT_RDWR) #not in UDP
sock.close()
