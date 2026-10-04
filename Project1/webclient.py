import sys
import socket

# the host name entered on the command line when ran,
# ex: $ python webclient.py example.com
host = sys.argv[1]

# if a second argument is included after the web host name,
# it is the port number
if len(sys.argv) > 2:
    port = int(sys.argv[2])
else: 
    port = 80

# make a socket and connect
s = socket.socket()
s.connect((host, port))

# build the request and send it with s.sendall()
request = (
    "GET / HTTP/1.1\r\n"
    f"Host: {host}\r\n"
    "Connection: close\r\n"
    "\r\n"
)
# .encode() turns the string into bytes to be sent
s.sendall(request.encode("ISO-8859-1")) 

# response holds the response, and b"" is an empty bytes object
response = b""
# walrus loop to receive chunks until recv() returns 0/empty bytes
while chunk := s.recv(4096):
    response += chunk


print(response.decode("ISO-8859-1"))
s.close()
