from socket import *
import sys 
import threading
import json

SUPPORTED_METHODS = ['GET', 'POST', 'HEAD']

def get_configs():
    file_name = open('config.json')
    configs = json.load(file_name)
    return configs['supported_methods'], configs['cache_time'], configs['whtelisting_enabled'], configs['']

def send_error(conn):
    with open("error403.html", 'r') as f:
        resdata = f.read()
    conn.send(b'HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n' + resdata.encode('ISO-8859-1'))

def respond_client(response):
    try:
        print(response.decode())
    except:
        print("Cannot decode")
        print(response)

def extract_msg(msg):
    #Trích method
    method = msg.split()[0]

    #Trích url
    url = msg.split()[1] 

    #Từ url trích ra domain + filepath
    if (url.find("://") != -1):
        url = url.partition("://")[2]
    domain, punk, file_path = url.partition("/")
    file_path = "/" + file_path
    return method, domain, file_path

#Tạo request để gửi cho Web Server
def handle_requests(msg):
    method, domain, file_path = extract_msg(msg)
    request = f"{method} {file_path} HTTP/1.1\r\n"

    #Thêm Connection: close để tự ngắt kết nối khi đã nhận đủ dữ liệu 
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

    #message nhận được từ Client
    msg = tcpClient.recv(4096)
    
    if not msg:
        return
    try: 
        print(f"<><><><><><><><><><><><><><><><><><><><><><>")
        print(f"Receive connection from: {addr}\r\n")
    except:
        tcpClient.close()
        return
    
    
    if msg.find(b'Accept-Encoding:') != -1:
        msg = msg.replace(msg[msg.find(b'Accept-Encoding:'):].split(b'\r\n')[0] + b'\r\n', b'')
    #Decode
    msg = msg.decode('ISO-8859-1')
    #Trích xuất method, domain và file_path từ msg 
    method, domain, file_path = extract_msg(msg)

    #Nếu method nằm trong SUPPORTED_METHODS thì tạo request
    if method in SUPPORTED_METHODS:
        request = handle_requests(msg) 
    else:
        #Gửi lỗi 403 
        send_error(tcpClient)
        tcpClient.close()
        return
    
    #Tạo socket cho Webserver, kết nối với port 80
    server = socket(AF_INET, SOCK_STREAM)
    server.connect((domain, 80))

    #In request và gửi request đã encode
    
    print(f"Request from client to server: \r\n{request}")
    server.send(request.encode())

    #Bắt đầu nhận response
    response = b""
    while True:
        chunk = server.recv(4096) #config later
        if len(chunk) == 0:
            break
        response += chunk

    #In ra response, sẽ làm thành một hàm sau 
    
    respond_client(response)

    #Gửi response về cho Client
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