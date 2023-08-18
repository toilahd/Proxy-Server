import socket
from socket import *
import sys
import threading
import time as pytime
from datetime import date, datetime, time
import os
import json

def get_configs():
    file_name = open('config.json')
    configs = json.load(file_name)
    return configs['supported_methods'], configs['cache_time'], configs['whitelist_enabled'], configs['white_list'], configs['time_restriction'], configs['time_allow'], configs['decode_format'], configs['supported_img_formats']
supported_methods, cache_time, whitelist_enabled, white_list, time_restriction, time_allow, decode_format, supported_img_formats = get_configs()
start_time, end_time = map(int, time_allow.split('-'))

def send_error(conn):
    with open("403.html", 'r') as f:
        resdata = f.read()
    conn.send(b'HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n' + resdata.encode('ISO-8859-1'))

def respond_client(response):
    data = response.split("\r\n\r\n")[0]
    try:
        print(data.decode())
    except:
        print("Cannot decode")
        print("Its an image!")

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

def respond_client(response):
    response
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


def getCachedImage(message):
    method, webServer, file = extract_msg(message)
    # If does not request image or image type not supported
    filenameExtension = file.split("/").pop().partition(".")[2]
    if filenameExtension not in supported_img_formats:
        return False, ""
    # Get the image and image header path
    imgPath = f"{os.getcwd()}/cache/{webServer}{file}"
    imgHeaderPath = imgPath[:imgPath.rfind(".")] + ".bin"
    # If the image is cached
    try:
        with open(imgPath, "rb") as fb:
            img = fb.read()
        with open(imgHeaderPath, "rb") as fb:
            imgHeader = fb.read()
    except:
        return False, ""

    # Get current time and compare with img time + cache time
    currentUTCtime = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    imgTimeStr = imgHeader.decode(decode_format).partition("Date: ")[2].partition(" GMT")[0].partition(", ")[2]
    imgTime = datetime.datetime.strptime(imgTimeStr, "%d %b %Y %H:%M:%S")

    if (imgTime + datetime.timedelta(seconds = int(cache_time)) <= currentUTCtime):
        return False, ""
    return True, imgHeader + b"\r\n\r\n" + img


def saveImageToCache(message, webReply):
    method, webServer, file = extract_msg(message)

    # If does not request image or image type not supported
    filenameExtension = file.split("/").pop().partition(".")[2]
    if filenameExtension not in supported_img_formats:
        return
    
    # Get the path of the image, header and the folder containing them
    imgPath = f"{os.getcwd()}/cache/{webServer}{file}"
    imgHeaderPath = imgPath[:imgPath.rfind(".")] + ".bin"
    folderPath = imgPath[:imgPath.rfind("/")]

    # If the folder does not exist, create that folder
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    # Save image and header to cache
    imgHeader, trash, img = webReply.decode(decode_format).partition("\r\n\r\n")
    with open(imgPath, "wb") as fb:
        fb.write(img.encode(decode_format))
    with open(imgHeaderPath, "wb") as fb:
        fb.write(imgHeader.encode(decode_format))
        
    return


#Tạo request để gửi cho Web Server
def handle_requests(msg):
    # If is cached
    status, cachedReply = getCachedImage(msg)
    if status == True:
        print("\r\nGET FROM CACHE SUCCESSFULLY\r\n")
        return cachedReply
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
    saveImageToCache(msg, response)
    server.close()
    return response


def handle_Client(tcpClient, addr):
    #message nhận được từ Client
    msg = tcpClient.recv(4096)   
    #Nếu bật time restriction và đang trong khoảng thời gian không cho phép
    if time_restriction:
        if (time(start_time,0,0) < datetime.now().time() < time(end_time,0,0)):
            print("Not in available time")
            send_error(tcpClient)
            tcpClient.close()
            return 

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
    if whitelist_enabled:
        if domain not in white_list:
            print("Not in whitelist!")
            send_error(tcpClient)
            tcpClient.close()
            return 

    #Nếu method nằm trong SUPPORTED_METHODS thì tạo request
    if method in supported_methods:
        response = handle_requests(msg) 
    else:
        #Gửi lỗi 403 
        send_error(tcpClient)
        tcpClient.close()
        return
    
    #In ra response, sẽ làm thành một hàm sau 
    
    #respond_client(response)

    #Gửi response về cho Client
    tcpClient.sendall(response)
    tcpClient.close()

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