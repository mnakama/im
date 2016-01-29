#!/usr/bin/python2
import sys
import os
import socket
import traceback
import datetime
import time

try:
	from Tkinter import *
except ImportError:
	print 'You need to install tkinter (python 2.7/2.6)\nOn Redhat 6, type: sudo yum install tkinter'

from ScrolledText import ScrolledText

mainwindow = None

def timestamp():
	return '[' + datetime.datetime.now().strftime('%X') + ']'

class MainWindow(Tk):
	def __init__(self):
		Tk.__init__(self)
		self.title('im.py')

		self.main = Frame(self)
		self.main.pack()

		self.host_Label = Label(self.main, text='Host:')
		self.host_Label.pack(side=LEFT)
		self.host_Entry = Entry(self.main)
		self.host_Entry.pack(side=LEFT)
		self.host_Entry.bind('<Return>', self.connect_Action)
		self.host_Entry.focus()

		#debug
		self.host_Entry.insert(0, 'localhost:9001')

                self.checker = None

                try: #this only works in linux for some reason
                    mainwindow.tk.createfilehandler(sock, tkinter.READABLE, mainwindow.eventChecker)
                except: #rescue windows
                    print 'Windows mode!'
                    sock.setblocking(False)
                    self.checker = self.main.after(100, self.eventChecker)
	def destroy(self):
                if self.checker != None: self.main.after_cancel(self.checker)
		Tk.destroy(self)

	def eventChecker(self, *args): #could be (self, socket_fd, mask)
		try:
			try:
				message, peer = sock.recvfrom(4096)
			except socket.error as e:
				if e.errno != 11 and e.errno != 10035: raise
			else:
				msgType = message[:4]
				msg = message[4:]
				if mt == 'TEXT':
					cw = ChatWindow.get(peer)
					cw.chat_Text.insert(END, timestamp() + ' ' + msg + '\n')
					cw.chat_Text.see(END)
					cw.bell()

					ip = peer[0].split('.')
					ip = chr(int(ip[0])) + chr(int(ip[1])) + chr(int(ip[2])) + chr(int(ip[3]))
					port = peer[1]
					port = chr(port / 0x100) + chr(port & 0xFF)
					sock.sendto('CFRM' + ip + port, peer)
					sock.lastActive = time.time()

				elif msgType == 'CFRM':
					ip = '{a:}.{b:}.{c:}.{d:}'.format(a=ord(msg[0]), b=ord(msg[1]), c=ord(msg[2]), d=ord(msg[3]))
					port = ord(msg[4]) * 0x100 + ord(msg[5])
					ChatWindow.get(peer).chat_Text.insert(END, ' [R]\n')
		except Exception as e:
			traceback.print_exc()
		finally:
			try:
				if time.time() - sock.lastActive > 60:
					sock.sendto('NOP ', ChatWindow.chats.keys()[0])
					sock.lastActive = time.time()
			except:
				traceback.print_exc()
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
		message = myname + ': ' + text
		if (text.strip()):
			self.chat_Text.insert(END, timestamp() + ' ' + message)
			self.chat_Text.see(END)
			self.send_Text.delete(0, len(text))

			sock.sendto('TEXT' + message, self.peer)
			sock.lastActive = time.time()
		else:
			self.send_Text.delete(0,END)

class UDPsock(socket.socket):
	def __init__(self, *args):
		socket.socket.__init__(self, *args)
		self.lastActive = time.time()


def callback(s, m):
    print "got some data"


try:
	myname = os.getlogin()
except OSError:
	myname = os.getenv('USER', default='user')
except AttributeError: #windows doesn't have a concept of getlogin()
	myname = 'user'


try:
	if sys.argv[1] == '-h':
		print 'Usage: ', sys.argv[0], '[listenport]'
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




mainwindow.main.mainloop()

#sock.shutdown(socket.SHUT_RDWR) #not in UDP
sock.close()
