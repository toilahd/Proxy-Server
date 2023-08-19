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

def send403(conn):
    with open("403.html", 'r') as f:
        resdata = f.read()
    conn.send(b'HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n' + resdata.encode('ISO-8859-1'))
    print("Send HTTP Error 403 Forbidden")

def respond_client(response):
    data = response.decode().split('\r\n')[0]
    try:
        print("Response received: ")
        print(data + '\r\n')
    except:
        print("Cannot decode")


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

def check_time(img, img_header):
    # Tìm thời gian hiện tại
    current_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    # Lấy nguồn chứa thời gian ảnh từ header
    img_time_src = img_header.decode(decode_format).partition("Date: ")[2].partition(" GMT")[0].partition(", ")[2]
    # Lấy thời gian ảnh
    img_time = datetime.datetime.strptime(img_time_src, "%d %b %Y %H:%M:%S")

    # Kiểm tra nếu ảnh đã lưu quá <cache_time> (thời gian tối đa cho phép lưu giữ ảnh trong cache)
    if (current_time >= img_time + datetime.timedelta(seconds = int(cache_time))):
        return False, ""
    return True, img_header + b"\r\n\r\n" + img

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

def ImgFromCache(msg):
    method, domain, file_path = extract_msg(msg)
    # If does not request image or image type not supported
    fileEx = file_path.split("/").pop().partition(".")[2]
    if fileEx not in supported_img_formats:
        return False, ""
    # Get the image and image header path
    img_path = f"{os.getcwd()}/cache/{domain}{file_path}"
    img_header_path = img_path[:img_path.rfind(".")] + ".bin"
    # If the image is cached
    try:
        with open(img_path, "rb") as file:
            img = file.read()
        with open(img_header_path, "rb") as file:
            img_header = file.read()
    except:
        return False, ""
    
    # Kiểm tra điều kiện thời gian
    return check_time(img, img_header)

def saveImg(img, img_path, img_header, img_header_path):
    # Save image and header to cache
    with open(img_path, "wb") as file:
        file.write(img.encode(decode_format))
    with open(img_header_path, "wb") as file:
        file.write(img_header.encode(decode_format))
    return

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

def ImgToCache(msg, response):

    method, domain, file_path = extract_msg(msg)

    # If does not request image or image type not supported
    fileEx = file_path.split("/").pop().partition(".")[2]
    if fileEx not in supported_img_formats:
        return
    
    # Get the path of the image, header and the folder containing them
    img_path = f"{os.getcwd()}/cache/{domain}{file_path}"
    img_header_path = img_path[:img_path.rfind(".")] + ".bin"
    folder_path = img_path[:img_path.rfind("/")]

    # If the folder does not exist, create that folder
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    img_header, trash, img = response.decode(decode_format).partition("\r\n\r\n")
    saveImg(img, img_path, img_header, img_header_path)
    return


#Tạo request để gửi cho Web Server
def handle_requests(msg):
    #Nếu đã cached
    status, cachedReply = ImgFromCache(msg)
    if status == True:
        print("\r\nGET FROM CACHE SUCCESSFULLY\r\n")
        return cachedReply
    
    #Nếu chưa cached
    method, web_server, file_path = extract_msg(msg)

    #Tạo socket cho web server
    host = socket(AF_INET, SOCK_STREAM)
    #Ket noi toi web server voi port 80
    host.connect((web_server, 80))

    request = f"{method} {file_path} HTTP/1.1\r\n"
    #Thêm Connection: close để tự ngắt kết nối khi đã nhận đủ dữ liệu 
    if method == "POST":
        if msg.find("Connection: ") != -1:
            request += msg.partition("\r\n")[2].partition("Connection: ")[0] + "Connection: close\r\n" + msg.partition("Connection: ")[2].partition("\r\n")[2]
        else:
            request += msg.partition("\r\n\r\n")[0] + "\r\nConnection: close\r\n\r\n" + msg.partition("\r\n\r\n")[2]
    else:
        request += f"Host: {web_server}\r\n"
        request += f"Connection: close\r\n\r\n"
        
    #In request và gửi request đã encode
    print(f"Sending request: \r\n{request}")
    host.send(request.encode())

    #Bắt đầu nhận response
    response = b""
    while True:
        chunk = host.recv(4096)
        if len(chunk) == 0:
            break
        response += chunk

    # Nhét img vào cache
    ImgToCache(msg, response)
    host.close()

    return response

def handle_Client(tcpClient, addr):
    
    print(f"<><><><><><><><><><><><><><><><><><><><><><>\r\n") 
     
    try:
        msg = tcpClient.recv(4096)
    except:
        msg = ""
  
    if not msg:
        print("No message from client\r\n")
        tcpClient.close()
        return

    try: 
        print(f"Receive connection from: {addr}\r\n")
    except:
        tcpClient.close()
        return
    
    if msg.find(b'Accept-Encoding:') != -1:
        msg = msg.replace(msg[msg.find(b'Accept-Encoding:'):].split(b'\r\n')[0] + b'\r\n', b'')

    #Nếu bật time-restriction và đang nằm trong khoảng thời gian không cho phép thì gửi mã 403
    start_time, end_time = map(int, time_allow.split('-'))    
    if time_restriction and (time(start_time,0,0) < datetime.now().time() < time(end_time,0,0)):
        print("Not in available time!")
        send403(tcpClient)
        tcpClient.close()
        return 
    
    #nếu bật whitelist và domain không nằm trong whitelist thì gửi mã 403
    if whitelist_enabled and domain not in white_list: 
        print("This domain is not allowed to access!")
        send403(tcpClient)
        tcpClient.close()
        return  

    #Decode message 
    msg = msg.decode(decode_format)
    #Trích xuất method, domain và file_path từ msg 
    method, domain, file_path = extract_msg(msg)
    

    #Nếu method nằm trong SUPPORTED_METHODS thì bắt đầu tạo resquest và gửi
    if method in supported_methods:
        response = handle_requests(msg) 
    else:
    #Nếu không thì trả về mã 403 
        print("Unsupported method:" + method)
        send403(tcpClient)
        tcpClient.close()
        return
    
    #In ra response
    respond_client(response)

    #Gửi response về cho Client
    tcpClient.sendall(response)
    tcpClient.close()



def main():
    if len(sys.argv) <= 1:
        print('Usage: "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server]')
        sys.exit(2)
    
    print(f"cache_time: {cache_time}")
    print(f"whitelist: {white_list}")
    print(f"time_forbid: {time_allow}")

    # Create a server socket, bind it to a port and start listening
    # Re-use the socket   
    server = socket(AF_INET, SOCK_STREAM)
    server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    HOST = sys.argv[1].split(':')[0]
    PORT = int(sys.argv[1].split(':')[1])

    # become a server socket
    server.bind((HOST, PORT))
    server.listen(3)
    print(f'Proxy server is listening on {HOST}:{PORT}')

    while True:
        try:
            #Start receiving data from the client
            print('Ready to serve...')
            tcpClient, addr = server.accept()

            thread = threading.Thread(target=handle_Client, args=(tcpClient, addr))
            #thread.setDaemon(True)
            thread.start()
        except KeyboardInterrupt:
            print("Closing program")
            tcpClient.close()
if __name__ == "__main__":
	main()