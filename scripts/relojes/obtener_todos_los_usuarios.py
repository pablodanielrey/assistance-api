import logging
logging.getLogger().setLevel(logging.INFO)
import struct
import socket

if __name__ == '__main__':
    
    d = 0x70,0x14,0x00000000,0x00000000,0x00,0x84,0x0A
    v = struct.pack('<bbiibBb', *d)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('163.10.56.25',4370))
        s.sendall(v)
        data = s.recv(1024)
        print(data)

    finally:
        s.close()
