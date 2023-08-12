from socket import *

def getPageSrc(url = "", msg = ""):
    \
    host = socket(AF_INET, SOCK_STREAM)
    host.connect((url, 80))
    host.send(msg.encode())

    src = host.recv(4096)
    print(f"Source: {src.decode()}")

getPageSrc("info.cern.ch", "")