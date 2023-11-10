#Rock paper scissors multiplayer game.

#Paper>Rock, Rock>Scissor, Scissor>Paper. Two equal choices results in 0 points.
#Each player has the same program - launched on separate computers.

#1. Program asks players to be Client or Server, Server must be picked first. 
#(Read from keybord  input using 'input(...)') e.g 'ans = input("Do you want... S or C: "')
#2. Server player creates a server on port 60 003 on current computer.
#3. Client player asks for the server's IP and connects to port 60 003 with the given IP.
#4. Program then prints game's state, asks player for a move. "(0,0) Your move: "".
#5. Verifies that move is valid, reenter if invalid. R/P/S is allowed.
#6. Valid move is sent to opponent computer over socket connection.
#7. The program for the opponent receives the move and inputs their own. 
#8. Move is read and printed to screen "Opponents move: "R/P/S"".
#9. Winner is determined for the round. 
#10a. If no player has 10 points we continue from 4.
#10b. If a player has 10 points both players are told their scores and who won.
#11. The game stops and socket connection is closed.
# -------- IMPORTS -------- #
import socket
import sys

# ----- GLOBAL VARIABLES -----
PORT = 60_003
ROLE = "?"
SCORE = [0,0] #[Server score, Client score]
SERVER_NAME = "Server"
CLIENT_NAME = "Client"
SINGLE_PLAYER = "single"
MAX_SCORE = 10
SOCK = None
CLIENT_CONNECTION = None
TIMEOUT = 20
MOVES = ( #Notice: n loses against n + 1. n wins against n - 1. MOVES is TIGHTLY coupled with winning logic.
    ("rock", "r"),
    ("paper", "p"),
    ("scissors", "s")
)
# ----- NETWORK FUNCTIONS ----- #
def establish_client_connection():
    global CLIENT_CONNECTION
    try:
        CLIENT_CONNECTION, address = SOCK.accept()
        CLIENT_CONNECTION.settimeout(TIMEOUT)
        print(f"Connection established with: " + str(address))
    except TimeoutError:
        print("The connection timed out")
        SOCK.close()
        sys.exit()

def user_enters_exit(exit: str):
    exit = exit.lower()
    bool = (exit == "exit")
    return bool

def get_local_IPv4():
    try:
        #Sets up a connectionless connection to Google DNS with the local IP. Does not send data since it's UDP.
        #Used to get the local IP from this UDP prepared connection.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            #Use the getsockname method in 'socket' to get a tuple of [ip, port] and pick the [ip] part ([0])
            ip = sock.getsockname()[0]
        return ip
    except Exception as e:
        print(f"Could not get the local IP: {e}")
        return None
    
def is_valid_IPv4(ip):
    if ip == "?":
        return False
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        print("ERROR: Invalid IP-address...")
        return False

def serverside_get_play_socket(single: bool):
    ip = "?"
    if (single):
        ip = "127.0.0.1"
    else:
        local_IPv4 = get_local_IPv4()
        if local_IPv4:
            while not is_valid_IPv4(ip):
                ip = input (f"Enter an IP to host server at (your current IP is \"{local_IPv4}\"): ")
                if user_enters_exit(ip):
                    return "exit"
        else:
            while not is_valid_IPv4(ip):
                ip = input ("Enter an IP to host server at: ")
    #AF_INET is IPv4, enter AF_INET6 for IPv6. SOCK_STREAM specifies socket type of TCP. Enter SOCK_DGRAM for UDP. 
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_socket.bind((ip, PORT))
    print(f"Server is running on IP {ip}...")
    server_socket.listen(1)
    server_socket.settimeout(TIMEOUT)
    return server_socket

def clientside_get_play_socket(host):
    global CLIENT_NAME
    global SERVER_NAME
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if host.lower() == "single":
        host = "127.0.0.1"
        
    client_socket.settimeout(TIMEOUT)
    client_socket.connect((host, PORT))    
    return client_socket

# ----- NETWORK PROGRAM ----- #
ans = "?"
#Ask player to be client, server or single-player
print("Welcome to the game!")
while ans not in {CLIENT_NAME, SERVER_NAME, SINGLE_PLAYER}: 
    ans = input(f"Do you want to be Server ({SERVER_NAME}), Client ({CLIENT_NAME}) or create a single-player ({SINGLE_PLAYER}) server: ")
    if user_enters_exit(ans):
        sys.exit()

if ans == SINGLE_PLAYER:
    SERVER_NAME = input("Choose your name: ")
    ROLE = SERVER_NAME
    SOCK = serverside_get_play_socket(True)
    
elif ans == SERVER_NAME:
    SERVER_NAME = input("Choose your name: ")
    ROLE = SERVER_NAME
    SOCK = serverside_get_play_socket(False)
    if  user_enters_exit(SOCK):
        sys.exit()
        
elif ans == CLIENT_NAME:
    CLIENT_NAME = input("Choose your name: ")
    ROLE = CLIENT_NAME
    HOST = "?"
    while not is_valid_IPv4(HOST):
        HOST = input("Enter the server IP or single for single player: ")
        if user_enters_exit(HOST):
            sys.exit()
        if (HOST == "single"):
            break
    
    SOCK = clientside_get_play_socket(HOST)
    
else: 
    breakpoint
    # ----- GAME FUNCTIONS -----#
#Strings should be transfered as byte-arrays using 'barr = bytearray(str, "ASCII")'
#Received byte-arrays are reconverted into strings using 'str = barr.decode("ASCII")'
def is_valid_move(move):
    move = move.lower()
    
    if (move == "?"):
        return False
    for fullname, charname in MOVES:
        if move == fullname or move == charname:
            return True
    else: 
        print("Invalid move.") 
        return False

def add_score(winner):
    global SCORE
    
    if winner == CLIENT_NAME:
        SCORE[1] += 1
    elif winner == SERVER_NAME:
        SCORE[0] += 1
    else: 
        return None

def get_move_index(move):
    move.lower()
    
    for n, (fullname, charname) in enumerate(MOVES):
        if move == fullname or move == charname:
            return n
    return None

def check_who_wins_round(move_server, move_client):
    print(f"{SERVER_NAME} throws {move_server} and {CLIENT_NAME} throws {move_client}")
    
    move_server = move_server.lower()
    move_client = move_client.lower()
    
    server_index = get_move_index(move_server)
    client_index = get_move_index(move_client)
    
    if server_index is None:
        return (f"{SERVER_NAME} made invalid move.")
    elif client_index is None:
        return (f"{CLIENT_NAME} made invalid move")
    
    client_win_index = (server_index + 1) % len(MOVES)
    server_win_index = (client_index + 1) % len(MOVES)
    
    if server_win_index == client_index:
        add_score(SERVER_NAME)
        return (f"{SERVER_NAME} wins the round!")
    elif client_win_index == server_index:
        add_score(CLIENT_NAME)
        return (f"{CLIENT_NAME} wins the round!")
    else:
        return "DRAW!"

def end_game(max_score):
    global SOCK
    for n in range(len(SCORE)):
        if SCORE[n] >= max_score:
            print(f"Game over! Final scores are: {SCORE}")
            return True
    else: 
        return False
    
def recv_data():
    global SOCK
    global CLIENT_CONNECTION
    try:
        if ROLE == CLIENT_NAME:
            if SOCK:
                return SOCK.recv(1024).decode()
        elif ROLE == SERVER_NAME:
            if CLIENT_CONNECTION:
                return CLIENT_CONNECTION.recv(1024).decode()
    except socket.timeout:
        print("Connection timed out.")
        return None
    except Exception as e:
        print (f"An error occured {e}")
        return None
        
    
def send_data(data):
    global SOCK
    global CLIENT_CONNECTION
    try:
        if ROLE == CLIENT_NAME:
            if SOCK:
                SOCK.send(data.encode()) 
        elif ROLE == SERVER_NAME:
            if CLIENT_CONNECTION:
                CLIENT_CONNECTION.send(data.encode())
    except socket.timeout:
        print("Connection timed out.")
        return None
    except Exception as e:
        print (f"An error occured {e}")
        return None

def close_socket():
    global SOCK
    global CLIENT_CONNECTION
    
    if ROLE == CLIENT_NAME:
        if SOCK:
            SOCK.close()
            SOCK = None
    elif ROLE == SERVER_NAME:
        if SOCK:
            SOCK.close()
            SOCK = None
            CLIENT_CONNECTION.close()
            CLIENT_CONNECTION = None
        

# ---- CLIENT FUNCTION ---- #
def client_program(max_score: int):
    while True:
        if end_game(max_score):
            break
        print("Waiting for opponents move...")
        server_move = recv_data()
        if server_move == None:
            print("No move received from opponent. Ending game")
            break
        if server_move == "exit":
            print ("The opponent quit the game. Game over.")
            break
        
        move = "?"
        while not is_valid_move(move):
            move = input("Pick your move: ")
            if user_enters_exit(move):
                send_data(move)
                break

        send_data(move)

        print (f"Move from {SERVER_NAME}: " + server_move)
        result = check_who_wins_round(server_move, move)
        print(result)
    print("Connection is taken down.") 
    close_socket()

# ---- SERVER FUNCTION ---- #
def server_program(max_score: int):
    establish_client_connection()

    while True:
        if end_game(max_score):
            break
        
        move = "?"
        while not is_valid_move(move):
            move = input ("Pick your move: ")
            if user_enters_exit(move):
                send_data(move)
                close_socket()
                sys.exit()
                
        send_data(move)
        
        print("Awaiting opponents move...")
        client_move = recv_data()
        if client_move == None:
            print("No move received from opponent. Ending game.")
            break
        if client_move == "exit":
            print("The opponent quit the game. Game over.")
            break
        else:
            print ("Move by client: " + client_move)
            result = check_who_wins_round(move, client_move)
            print(result)
    
    close_socket()
    sys.exit()

# ----- GAME PROGRAM ----- #
if ROLE == CLIENT_NAME:
    client_program(MAX_SCORE)
elif ROLE == SERVER_NAME:
    server_program(MAX_SCORE)
else: 
    print("ROLE error: " + ROLE + "Client name: " + CLIENT_NAME + "Server name: " + SERVER_NAME)
    SOCK.close()
    sys.exit()