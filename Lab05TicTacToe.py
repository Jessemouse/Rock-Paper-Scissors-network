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
SERVER_SCORE = 0 
CLIENT_SCORE = 0
SERVER = "server"
CLIENT = "client"
SINGLE_PLAYER = "single"
MAX_SCORE = 0
SOCK = None
CLIENT_CONNECTION = None
TIMEOUT = 60
MOVES = ( #Notice: n loses against n + 1. MOVES is TIGHTLY coupled with winning logic.
    ("rock", "r"),
    ("paper", "p"),
    ("scissors", "s")
)
# ----- NETWORK FUNCTIONS ----- #

#Exchange name of the player. Check they're not the same as opponents. Return opponent's name
def exch_name(name):
    send_data(name)
    opponent = recv_data()
    return opponent
        
#Asks for IP to connect to
def ask_for_host():
    host = "?"
    while not is_valid_IPv4(host):
        host = input(f"Enter the server IP or connect to your own server using '{SINGLE_PLAYER}': ")
        check_if_quit(host)
        if (host == SINGLE_PLAYER):
            break
    return host

#If player enters exit, closes connection and program.
def check_if_quit(exit: str):
    try:
        exit = exit.lower()
    except AttributeError or WindowsError:
        exit = "exit"

    if exit == "exit":
        print("The connection has been terminated.")
        if SOCK:
            if exit:
                send_data(exit)
            close_connection()
            sys.exit()
        else:
            sys.exit()
            
#Establish the game connection with appropriate roles and sockets
def establish_connection(ans):
    global ROLE, SOCK
    if ans == SINGLE_PLAYER:
        ROLE = SERVER
        try:
            SOCK = serverside_get_play_socket(True)
        except OSError:
            ROLE = CLIENT
            host = "127.0.0.1"
            SOCK = clientside_get_play_socket(host)
    
    elif ans == SERVER:
        ROLE = SERVER
        SOCK = serverside_get_play_socket(False)

    elif ans == CLIENT:
        ROLE = CLIENT
        host = ask_for_host()
        SOCK = clientside_get_play_socket(host)
        
#Lets server pick the score
def pick_score():
    global MAX_SCORE
    if ROLE == SERVER:
        while MAX_SCORE <= 0 or MAX_SCORE >= 11:
            try:
                MAX_SCORE = input("Pick the max score for this game (1-10): ")
                check_if_quit(MAX_SCORE)
                MAX_SCORE = int(MAX_SCORE)
            except ValueError or TypeError: 
                print("Please enter an integer between 1 and 10")
        send_data(MAX_SCORE)
    else:
        print("Waiting for server...")
        try:
            MAX_SCORE = recv_data()
        except OSError:
            print("Did not receive MAX_SCORE")
            check_if_quit("exit")
        if(MAX_SCORE == "exit"):
            print("Opponent exited the game.")
            check_if_quit(MAX_SCORE)
        else: 
            MAX_SCORE = int(MAX_SCORE)

#Get data from the buffer. Notice that it's always received as string
def recv_data():
    try:
        if ROLE == CLIENT:
            if SOCK:
                return SOCK.recv(1024).decode()
        elif ROLE == SERVER:
            if CLIENT_CONNECTION:
                return CLIENT_CONNECTION.recv(1024).decode()
    except socket.timeout:
        print("Connection timed out.")
        return None
    except Exception as e:
        print (f"An error occured {e}")
        return None

#Use to send data to the other computer's buffer. Notice it's always sent as a string.
def send_data(data):
    data = str(data)
    try:
        if ROLE == CLIENT:
            if SOCK:
                SOCK.send(data.encode()) 
        elif ROLE == SERVER:
            if CLIENT_CONNECTION:
                CLIENT_CONNECTION.send(data.encode())
    except socket.timeout:
        print("Connection timed out.")
        return None
    except Exception as e:
        print (f"An error occured {e}")
        return None
    
#Shuts down SOCK and CLIENT_CONNECTION
def close_connection():
    global SOCK, CLIENT_CONNECTION
    
    if ROLE == CLIENT:
        if SOCK:
            SOCK.close()
            SOCK = None
    elif ROLE == SERVER:
        if SOCK:
            SOCK.close()
            SOCK = None
        if CLIENT_CONNECTION:
            CLIENT_CONNECTION.close()
            CLIENT_CONNECTION = None

#Used by server to open the connection.
def establish_client_connection():
    global CLIENT_CONNECTION
    try:
        CLIENT_CONNECTION, address = SOCK.accept()
        CLIENT_CONNECTION.settimeout(TIMEOUT)
        print(f"Connection established with: " + str(address))
    except TimeoutError:
        print("The connection timed out. Exiting program.")
        close_connection()
        sys.exit()

#Fetch the computer's IPv4
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

#Check if input IPv4 is valid
def is_valid_IPv4(ip):
    if ip == "?":
        return False
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        print("ERROR: Invalid IP-address...")
        return False

#Open server socket
def serverside_get_play_socket(single: bool):
    ip = "?"
    if (single):
        ip = "127.0.0.1"
    else:
        local_IPv4 = get_local_IPv4()
        if local_IPv4:
            while not is_valid_IPv4(ip):
                ip = input (f"Enter an IP to host server at (your current IP is \"{local_IPv4}\"): ")
                check_if_quit(ip)
        else:
            while not is_valid_IPv4(ip):
                ip = input ("Enter an IP to host server at: ")
    #AF_INET is IPv4, enter AF_INET6 for IPv6. SOCK_STREAM specifies socket type of TCP. Enter SOCK_DGRAM for UDP. 
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_socket.bind((ip, PORT))
    print(f"Connection established with IP {ip}. Waiting for opponent. Terminating connection in {TIMEOUT} seconds")
    server_socket.settimeout(TIMEOUT)
    server_socket.listen(1)
    return server_socket

#Open client socket
def clientside_get_play_socket(host):
    global CLIENT, SERVER
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if host.lower() == "single":
        host = "127.0.0.1"
    client_socket.settimeout(TIMEOUT)
    client_socket.connect((host, PORT))    
    return client_socket

#User picks own name, role is assigned based on this. 
def pick_name():
    name = ""
    print("Please pick a name with a minimum length of 2")
    while len(name) <= 1:
        name = input("Pick your name: ")   
        check_if_quit(name)
    return name

#Initialize the game
def init_game():
    ans = "?"
    print("Welcome to the game! You can enter 'exit' at any time to quit.")
    while ans not in("play", "start"): 
        ans = input("Enter 'play' to start the game: ")
        check_if_quit(ans)
    while ans not in {CLIENT, SERVER, SINGLE_PLAYER}: 
        ans = input(f"Do you want to create a '{SERVER}' to play at, connect to a server as '{CLIENT}' or create a '{SINGLE_PLAYER}' instance? ")
        check_if_quit(ans)
    establish_connection(ans)

# ----- GAME LOGIC -----#
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

def check_winner(opponents_move, move, opponent, name):
    opponents_move_index = get_move_index(opponents_move)
    move_index = get_move_index(move)
    
    if move is None or opponents_move is None:
        return ("Invalid move was made")
    
    winning_move = (opponents_move_index + 1) % (len(MOVES))
    losing_move = (move_index + 1) % (len(MOVES))
    #print(f"You picked number {move_index}, opponent picked number {opponents_move_index}, the winning number is {winning_move},")
          
    if move_index == winning_move:
        print(f"{move} wins over {opponents_move}")
        return name
    elif opponents_move_index == losing_move:
        print(f"{opponents_move} wins over {move}")
        return opponent
    else: 
        print("DRAW!")
        return "DRAW"

def get_move_index(move):
    move = move.lower()
    
    for n, (fullname, charname) in enumerate(MOVES):
        if move == fullname or move == charname:
            return n
    return None

def make_move():
    move = "?"
    while not is_valid_move(move):
        move = input("Pick your move: ")
        check_if_quit(move)
    return move
    
#Score added locally for security. 
def add_score(winner, opponent, name):
    global CLIENT_SCORE, SERVER_SCORE
    
    if winner == name:
        if ROLE == CLIENT:
            CLIENT_SCORE += 1
        elif ROLE == SERVER:
            SERVER_SCORE += 1
    elif winner == opponent:
        if ROLE == SERVER:
            CLIENT_SCORE += 1
        elif ROLE == CLIENT:
            SERVER_SCORE += 1
    else: return None
    
def play_a_round(opponent, name):
    move = make_move()
    try: 
        send_data(move)
        opponents_move = recv_data()
    except OSError:
        check_if_quit("exit")

    check_if_quit(opponents_move)
    
    print(f"{opponent} picks {opponents_move}!")
    
    winner = check_winner(opponents_move, move, opponent, name)
    
    add_score(winner, opponent, name)

def check_game_winner(opponent, name):
    if SERVER_SCORE >= MAX_SCORE:
        if ROLE == SERVER:
            return name
        else:
            return opponent
    elif CLIENT_SCORE >= MAX_SCORE:
        if ROLE == CLIENT:
            return name
        else:
            return opponent
    return "None"
    
# ---- CALLER FUNCTIONS ---- #
def play(opponent, name):
    global CLIENT_SCORE, SERVER_SCORE
    winner = "None"
    
    print(f"\n{name} vs {opponent}! Max score is {MAX_SCORE}. Good luck!")
    while winner == "None":
        result = play_a_round(opponent, name)
        if ROLE == CLIENT:
            print(f"{name}: {CLIENT_SCORE}, {opponent}: {SERVER_SCORE}\n")
            winner = check_game_winner(opponent, name)
            continue
        elif ROLE == SERVER:
            print(f"{name}: {SERVER_SCORE}, {opponent}: {CLIENT_SCORE}\n")
            winner = check_game_winner(opponent, name)
            continue
        check_game_winner(opponent, name)

    print(f"The winner is {winner}! Congratulations!")

#Start game for server
def server_start():
    establish_client_connection()
    name = pick_name()
    opponent = exch_name(name)
    while(opponent == name):
        name = pick_name()
        send_data(name)
        opponent = recv_data()
    pick_score()
    play(opponent, name)

#Start game for client
def client_start():
    name = pick_name()
    opponent = exch_name(name)
    while(opponent == name):
        name = pick_name()
        send_data(name)
        opponent = recv_data()
    pick_score()
    play(opponent, name)
    
# ----- PROGRAM ----- #
#Ask player to be client, server or single-player
init_game()
if ROLE == CLIENT:
    client_start()
elif ROLE == SERVER:
    server_start()
else: 
    print("ROLE error")
    close_connection()
    sys.exit()
print("Connection shutting down.") 
close_connection()