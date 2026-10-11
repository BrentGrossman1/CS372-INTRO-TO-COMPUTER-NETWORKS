import socket
import sys
import os
import signal

# Python turns Ctrl-C into a KeyboardInterrupt, which can't go through while accept() is blocking.
# switching to the OS default handler lets Ctrl-C kill the server immediately.
signal.signal(signal.SIGINT, signal.SIG_DFL)

# maps a file extension to its MIME type. 
# The MIME type goes in the Content-Type header and tells the browser how to display the data.
MIME_TYPES = {
    ".txt": "text/plain",
    ".html": "text/html",
}

def read_request_header(client_socket):
    request = b""

    # a HTTP header ends with a blank line, which is "\r\n\r\n" in bytes.
    # keep receiving until that shows up in what we've collected so far.
    while b"\r\n\r\n" not in request:
        chunk = client_socket.recv(4096)

        # recv() returns empty bytes if the client closed the connection early, so break the loop.
        if len(chunk) == 0:
            break

        request += chunk
    return request

def get_file_name(request):
    # cut off everything after the blank line, then convert bytes to a string
    header = request.split(b"\r\n\r\n")[0].decode("ISO-8859-1")

    # header lines are separated by "\r\n". 
    # the first one is the request line, for example: GET /file1.txt HTTP/1.1
    first_line = header.split("\r\n")[0]

    # splitting on spaces gives ["GET", "/file1.txt", "HTTP/1.1"]
    parts = first_line.split()

    # browsers sometimes open a connection and send nothing, 
    # that gives an empty first line, so return None and send a 404.
    if len(parts) != 3:
        return None

    method, path, protocol = parts

    # keep only the part after the last "/", dropping every directory for security,
    # so the server can only open files in the folder it was started from.
    return os.path.split(path)[-1]


def send_404(client_socket):
    # the same layout as HTTP response: status line, headers, blank line, body.
    # the body "404 not found" is 13 bytes.
    response = (
        "HTTP/1.1 404 Not Found\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 13\r\n"
        "Connection: close\r\n"
        "\r\n"
        "404 not found"
    )

    # sockets send bytes, not strings, so encode before sending
    client_socket.sendall(response.encode("ISO-8859-1"))

def send_file(client_socket, file_name):
    # "rb" opens the file in binary mode, so read() returns bytes that can go straight out on the socket.
    #  If the file doesn't exist (or the name is empty because the request was just "/"), open() raises an error.
    try:
        with open(file_name, "rb") as fp:
            file_data = fp.read()
    except OSError:
        send_404(client_socket)
        return

    # splitext("file1.txt") returns ("file1", ".txt"); [1] is the extension.
    # look it up in MIME_TYPES. Anything not in the dictionary gets the generic "unknown binary data" type.
    extension = os.path.splitext(file_name)[1]
    content_type = MIME_TYPES.get(extension, "application/octet-stream")

    # content-Length is the size of the body in bytes, so the browser knows how much data to expect after the blank line.
    header = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(file_data)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )

    # The header is a string, so encode it to bytes. file_data is already bytes, so the two can be joined and sent as one response.
    client_socket.sendall(header.encode("ISO-8859-1") + file_data)


# Use the port given on the command line (python webserver.py 12345) or 28333 if none was given
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    port = 28333

# create a TCP socket for listening
s = socket.socket()

# allow reusing the port right after the server restarts, instead of getting "address already in use" for a minute or so
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# attach the socket to this port on every network address of this computer
s.bind(("", port))

# start accepting incoming connections
s.listen()
print(f"Listening on port {port}")

# handle one client at a time, loop forever
while True:
    # wait for a client to connect. accept() returns a new socket just for talking to this client, plus the client's address.
    # The listening socket s stays open for the next client.
    client_socket, client_addr = s.accept()

    # read the request, figure out which file was asked for, and respond
    request = read_request_header(client_socket)
    file_name = get_file_name(request)

    if file_name is None:
        send_404(client_socket)
    else:
        send_file(client_socket, file_name)

    # hang up on the client
    client_socket.close()