#!/usr/bin/python3

import socket
import traceback

port = 80

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind(('0.0.0.0', port))
lsock.listen(5)

try:
	while True:
		sock, addr = lsock.accept()
		try:
			print (addr)
			headers = str(sock.recv(4096), encoding='utf-8')
			print (headers)
			lines = headers.splitlines()
			reply_lines = []
			ip = None
			for header in lines:
				#if 'X-' == header[:2]:
				#	reply_lines.append(header)
				if 'X-Forwarded-For:' in header:
					ip_str = header[17:]
					ip = socket.inet_aton(ip_str)

			#reply = '\n'.join(reply_lines).encode()
			reply = ip
			if ip is not None:
				sock.send(reply)
			else:
				seck.send(b'\0\0\0\0')
			#sock.send(b'\x04')
		except KeyboardInterrupt:
			raise
		except:
			traceback.print_exc()
		finally:
			sock.shutdown(socket.SHUT_RDWR)
			sock.recv(4096)
			sock = None
finally:
	lsock.shutdown(socket.SHUT_RDWR)

#Host: 23.92.75.10
#User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0
#Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
#Accept-Language: en-US,en;q=0.5
#Accept-Encoding: gzip, deflate
#DNT: 1

#BlueCoat adds this:
#Cache-Control: max-age=0
#X-Forwarded-For: 9.58.148.241
#Connection: Keep-Alive
#X-BlueCoat-Via: e7e320db3604ed61
