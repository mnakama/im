#!/usr/bin/python3

import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#sock.connect(('127.0.0.1', 8081))
sock.connect(('23.92.75.10', 80))

print(sock.send(b'''GET / HTTP/1.1

'''))

#Host: 23.92.75.10
#User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0
#Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
#Accept-Language: en-US,en;q=0.5
#Accept-Encoding: gzip, deflate
#DNT: 1
#Cache-Control: max-age=0
#X-Forwarded-For: 9.58.148.241
#Connection: Keep-Alive
#X-BlueCoat-Via: e7e320db3604ed61

ip = sock.recv(4096)
print(socket.inet_ntoa(ip), ip)

#time.sleep(5)
sock.shutdown(socket.SHUT_RDWR)
sock.recv(4096)
