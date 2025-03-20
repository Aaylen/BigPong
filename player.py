import socket
import os

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("10.16.8.220", 6000))
client.send("Hello from the client".encode())
print("Connected to the server")