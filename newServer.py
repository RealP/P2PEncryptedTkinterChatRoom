 
import sys
import socket
import select
import thread, re

POSSIBLE_COMMANDS = ["join","bye","crea","subs","unsu","defa","lscr","lssu","read","writ","chmod"]
#at home
HOST = '0.0.0.0'
#ON CWolf
# HOST = '29' 
SOCKET_LIST = []
RECV_BUFFER = 4096 
PORT = 8022

class Client:
    name = ''
    socket = None
    addr = None

def processClientCommands(cmd, clientSocket):
    if "crea:" in cmd:
        print "Client want a new room"
    else:
        sendResponseFromServer("Command not implemented :(\n", clientSocket)

def sendResponseFromServer(response, userSocket):
    userSocket.send(response)

def clientMessage(clientSoc, clientAddr, serverSocket):
    while 1:
        try:
            data = clientSoc.recv(4096)
            if not data:
                break
            broadcast(serverSocket, clientSoc, data)  
        except socket.timeout:
            break
    SOCKET_LIST.remove(clientSoc)
    broadcast(serverSocket, clientSoc, "Client (%s, %s) is offline\n" % clientAddr)
    
# broadcast chat messages to all connected clients
def broadcast (server_socket, sock, message):
    ### SEARCH FOR ONE OF THE POSSIBLE COMMANDS FROM THE USER. 
    ### AND PROCESS IT AS APPROPRIATE
    for cmd in POSSIBLE_COMMANDS:
        m = re.search(cmd+":.*", message)
        if m:
            processClientCommands(message, sock)
            return
    for socket in SOCKET_LIST:
        # send the message only to peers not server or self
        if socket != server_socket and socket != sock :
            try :
                socket.send(message)
            except :
                # broken socket connection
                socket.close()
                # broken socket, remove it
                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)
 
def chat_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(10)
    # add server socket object to the list of readable connections
    SOCKET_LIST.append(server_socket)
    print "Main chat server started on port " + str(PORT)
    while 1:
        sockfd, addr = server_socket.accept()
        SOCKET_LIST.append(sockfd)
        print "Client (%s, %s) connected to main chat room" % addr
        broadcast(server_socket, sockfd, "[%s:%s] entered main chat room\n" % addr)
        thread.start_new_thread(clientMessage, (sockfd, addr, server_socket))
    server_socket.close()

if __name__ == "__main__":
    sys.exit(chat_server(HOST, PORT))         
