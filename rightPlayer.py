import socket
import os

masterIP = os.environ.get('masterIP')

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("10.16.9.13", 6000))
client.send("Hello from the client".encode())
print("Connected to the server")