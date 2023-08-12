from socket import *
import sys
import threading

SUPPORTED_METHODS = ['GET', 'POST', 'HEAD']

#define GET 
def handle_GET(url = ""):
    request = f'GET / HTTP/1.1\r\nHost:{url}\r\n\r\n'
    host = socket(AF_INET, SOCK_STREAM)
    host.connect((url, 80))
    host.send(request.encode())
    src = host.recv(4096)
    #print(f"Source: {src.decode()}")

#define POST
def handle_POST(url = ""):
    return

#define HEAD 
def handle_HEAD(url = ""):
    request = f'HEAD / HTTP/1.1\r\nHost:{url}\r\n\r\n'
    host = socket(AF_INET, SOCK_STREAM)
    host.connect((url, 80))
    host.send(request.encode())
    headers = b''
    while True:
        chunk = host.recv(4096)
        if not chunk:
            break
        headers += chunk
        if b'\r\n\r\n' in headers:
            break
    host.close()
    return headers
def send_error(conn):
    with open("error403.html", 'r') as f:
        resdata = f.read()
    conn.send(b'HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n' + resdata.encode('ISO-8859-1'))

def extract_msg(msg):
    method = msg.split()[0] #extract the method from the message
    url = msg.decode().split()[1] #extract the url from the message
    url = url.strip("/") #remove '/' from url

    return method, url 
def handle_Client(tcpClient, addr):

    msg = tcpClient.recv(4096).decode()
    if not msg:
        return
    method, url = extract_msg(msg)
    if method in SUPPORTED_METHODS
        if method == "GET":
            response = handle_GET(msg)
        elif method == "POST":
            response = handle_POST(msg)
        elif method == "HEAD":
            response = handle_HEAD(url)
    filetouse = "/" + url
    print(filetouse)
    print(msg.decode())
    tcpClient.send(response)
 
if len(sys.argv) <= 1:
    print('Usage: "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server]')
    sys.exit(2)

# Create a server socket, bind it to a port and start listening
#AF_INET constant for the socket family, stand for Internet Protocol with IPv4 addresses
#SOCK_STREAM for the socket type, needed for TCP
server = socket(AF_INET, SOCK_STREAM)   
server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

HOST = sys.argv[1].split(':')[0]
PORT = int(sys.argv[1].split(':')[1])

server.bind((HOST, PORT))
server.listen(3)
print(f'Proxy server is listening on {HOST}:{PORT}')

while 1: 
    #Start receiving data from the client
    print('Ready to serve...')
    tcpClient, addr = server.accept()
    print('Received a connection from:', addr)
    
    break