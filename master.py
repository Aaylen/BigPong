import socket

def start_master(port=6000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen()
    
    print("Master is waiting for clients to connect")
    while True:
        client_socket, client_address = server.accept()
        print(f"Client {client_address} connected")
    

start_master()
