from socket import *
import sys 
import threading

SUPPORTED_METHODS = ['GET', 'POST', 'HEAD']



def send_error(conn):
    with open("error403.html", 'r') as f:
        resdata = f.read()
    conn.send(b'HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n' + resdata.encode('ISO-8859-1'))

def extract_msg(msg):
    method = msg.split()[0] #extract the method from the message
    url = msg.split()[1] #extract the url from the message
    if (url.find("://") != -1):
        url = url.partition("://")[2]
    domain, punk, file_path = url.partition("/")
    file_path = "/" + file_path
    return method, domain, file_path

def handle_requests(msg):
    method, domain, file_path = extract_msg(msg)
    request = f"{method} {file_path} HTTP/1.1"
    if method == "POST":
        if msg.find("Connection: ") != -1:
            request += msg.partition("\r\n")[2].partition("Connection: ")[0] + "Connection: close\r\n" + msg.partition("Connection: ")[2].partition("\r\n")[2]
        else:
            request += msg.partition("\r\n\r\n")[0] + "\r\nConnection: close\r\n\r\n" + msg.partition("\r\n\r\n")[2]
    else:
        request += f"Host: {domain}\r\n\r\n"
        request += f"Connection: close\r\n\r\n"
    return request
def handle_Client(tcpClient, addr):
    #msg receiving from client
    msg = tcpClient.recv(4096).decode("ISO-8859-1")
    if not msg:
        return
    try: 
        print(f"Request: {addr}\n{msg}\r\n")
    except:
        tcpClient.close()
        return
    #extract the info we need from the given message
    method, domain, file_path = extract_msg(msg)
    print(domain + "fuck")
    if method in SUPPORTED_METHODS:
        request = handle_requests(msg) 
    else:
        send_error()
    host = socket(AF_INET, SOCK_STREAM)
    host.connect((domain, 80))
    host.send(request)
    response = b""
    while True:
        chunk = host.recv(4096) #config later
        if len(chunk) == 0:
            break
        response += chunk
    filetouse = "/" + file_path
    #print(filetouse)
    print(response.decode())
    tcpClient.sendall(response)
if len(sys.argv) <= 1:
    print('Usage: "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server]')
    sys.exit(2)

# Create a server socket, bind it to a port and start listening

#AF_INET constant for the socket family, stand for Internet Protocol with IPv4 addresses
#SOCK_STREAM for the socket type, needed for TCP
server = socket(AF_INET, SOCK_STREAM)

# Re-use the socket   
server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

HOST = sys.argv[1].split(':')[0]
PORT = int(sys.argv[1].split(':')[1])

server.bind((HOST, PORT))
# become a server socket
server.listen(10)
print(f'Proxy server is listening on {HOST}:{PORT}')
print('Ready to serve...')

while True: 
    #Start receiving data from the client
    print('Ready to serve...')
    tcpClient, addr = server.accept()
    print('Received a connection from:', addr)
    thread = threading.Thread(target=handle_Client, args=(tcpClient, addr))
    #thread.setDaemon(True)
    #Daemon threads are threads that run in the background and are terminated when the main program exits. 
    thread.start()