import sys
import socket
import signal
# makes it so ctrl-c works when trying to shut down the server
signal.signal(signal.SIGINT, signal.SIG_DFL)

# if a port number is used on the command line, use it,
# ex: $ python webserver.py 12399
# otherwise default to 28333
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    port = 28333

# make a socket
s = socket.socket()
# lets the port be reused if the server crashes or restarts,
# prevents the "Address already in use" error
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# bind the socket to the port, "" means any address on this computer
s.bind(("", port))

# start listening for incoming connections
s.listen()

# loop forever, handling one connection at a time
while True:
    # wait for a client to connect, accept() returns a new socket for this connection
    client_socket, client_addr = s.accept()
    # prints out the clients (IP address, port)
    print(client_addr)

    # read the request until the blank line that ends the header
    request = b""
    while b"\r\n\r\n" not in request:
        chunk = client_socket.recv(4096)
        # if the length of the chunk is 0 bytes/empty, the client closed the connection
        if len(chunk) == 0:
            break
        request += chunk

    # build the HTTP response
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 6\r\n"
        "Connection: close\r\n"
        "\r\n"
        "Hello!"
    )
    # .encode() turns the string into bytes to be sent
    client_socket.sendall(response.encode("ISO-8859-1"))
    # close the connection, then loop back to accept() a new client
    client_socket.close()
