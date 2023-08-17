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
    request = f"{method} {file_path} HTTP/1.1\r\n"
    if method == "POST":
        if msg.find("Connection: ") != -1:
            request += msg.partition("\r\n")[2].partition("Connection: ")[0] + "Connection: close\r\n" + msg.partition("Connection: ")[2].partition("\r\n")[2]
        else:
            request += msg.partition("\r\n\r\n")[0] + "\r\nConnection: close\r\n\r\n" + msg.partition("\r\n\r\n")[2]
    else:
        request += f"Host: {domain}\r\n"
        request += f"Connection: close\r\n\r\n"
    return request
def handle_Client(tcpClient, addr):
    #msg receiving from client
    msg = tcpClient.recv(4096).decode("ISO-8859-1")
    #extract the info we need from the given message
    
    if not msg:
        return
    try: 
        #print(f"Request: {addr}\n{msg}\r\n")
        print(f"Receive connection from: {addr}\r\n")
    except:
        tcpClient.close()
        return
    
    method, domain, file_path = extract_msg(msg)
    if method in SUPPORTED_METHODS:
        request = handle_requests(msg) 
    else:
        send_error()
        return
    
    server = socket(AF_INET, SOCK_STREAM)
    server.connect((domain, 80))
    print(request)
    server.send(request.encode())
    response = b""
    while True:
        chunk = server.recv(4096) #config later
        if len(chunk) == 0:
            break
        response += chunk
    try:
        print(response.decode())
    except:
        print("Cannot decode")

    tcpClient.sendall(response)

if len(sys.argv) <= 1:
    print('Usage: "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server]')
    sys.exit(2)


# Create a server socket, bind it to a port and start listening
server = socket(AF_INET, SOCK_STREAM)
# Re-use the socket   
server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

HOST = sys.argv[1].split(':')[0]
PORT = int(sys.argv[1].split(':')[1])

# become a server socket
server.bind((HOST, PORT))
server.listen(10)

print(f'Proxy server is listening on {HOST}:{PORT}')

while True: 
    #Start receiving data from the client
    print('Ready to serve...')
    tcpClient, addr = server.accept()
    thread = threading.Thread(target=handle_Client, args=(tcpClient, addr))
    #thread.setDaemon(True)
    #Daemon threads are threads that run in the background and are terminated when the main program exits. 
    thread.start()