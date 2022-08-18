import io
import threading
import socket
import time as t
import os
import json
from tkinter import *
import tkinter.scrolledtext
import tkinter.messagebox
# The below rsa module i've imported is created by me, and utilises the rsa.py file
import rsa

# The below line retrieves the ip from the local machine
HOST = socket.gethostbyname(socket.gethostname())
PORT = 50000
current_server_state = "START_SERVER"
next_server_state = ""
current_client_state = "START_STATE"
next_client_state = ""

"""
The below class is a parent class of the server and client, and contains the methods needed for sending and receiving
data, i've utilised inheritance as both of the classes used the same methods, and i'd be replicating my work otherwise
"""
class Common(object):
    def __init__(self):
        self.format = "utf-8"

    # This method sends the data to a specified connection and encrypt the data, if a public key is provided
    def send(self, conn, pub, n, msg):
        try:
            # Checks if a public key has been provided, if it has it encrypts the message
            if pub:
                # Utilises my encryption method in the RSA module, and returns back a cipher
                msg = rsa.encrypt(pub, n, msg)

            # Encodes the message provided to be the format declared in the initialiser
            message = msg.encode(self.format)
            # Finds the length of the message
            msg_length = len(message)
            # Both of the lines below, encode the length of the message so that it's ready to be sent
            send_length = str(msg_length).encode(self.format)
            send_length += b' ' * (12 - len(send_length))
            """
            This is where it sends the message, on the socket provided. It firstly, sends the length of the message so
            that the retrieve methods knows how much data is expected to be received, and then sends the message
            """
            conn.send(send_length)
            conn.send(message)
            return True
        # If there's a connection reset, or connected aborted error, then it will return False, as these are expected errors
        except (ConnectionResetError, ConnectionAbortedError):
            return False

    # This method retrieves the data from a specified connection, and decrypts the message, if a private key is provided
    def receive(self, conn, pri, n):
        try:
            # This uses the io module to initialise a binary stream of data, to allow chunk of data to be added to it
            message = io.BytesIO()
            # This is where it receives the message length, decodes it and casts it to an int variable
            msg_length = int(conn.recv(12).decode(self.format))
            """
             Sets a timeout on the socket to be 1 seconds, this will allows us to check if there's any data left, else,
             it will raise a socket error
            """
            conn.settimeout(1)
            all_data = False
            timeout = 0
            user_timed_out = False
            # This while loop will catch all the chunks of data that will be sent, as the socket will stream data across
            while not all_data:
                try:
                    """
                     I am using this time out, if for some reason the socket fails, and it stays in a loop, it will only do so for 20 turns round the while loop
                    """
                    if timeout >= 20:
                        user_timed_out = True
                        break

                    # Receives the data based on the msg_length provided by the socket
                    data = conn.recv(msg_length)
                    # Writes the data to the the binary stream
                    message.write(data)
                    print("[INFO] Waiting For Message")
                    timeout += 1
                except socket.timeout:
                    all_data = True
            if not user_timed_out:
                # Resets the timeout, as to not affect other parts of the program with the timeout
                conn.settimeout(None)
                # Reads through all the data in the stream from the start
                message.seek(0)
                # if a private key is provided, then it will decrypt the message, else it will return the message as is
                if pri:
                    message = rsa.decrypt(pri, n, message.getvalue().decode(self.format))
                    return json.loads(message)
                else:
                    return json.load(message)
            else:
                return {
                     "server_state": "TIMED_OUT",
                     "client_state": "TIMED_OUT"
                     }
        # If there' an error, it'll return False
        except:
           return False
    # Defines a stop method, that will be executed when the program needs to be ended
    def stop(self, root, chatroom_socket_info):
        try:
            msg_data = json.dumps(
                {
                    "client_state": "DISCONNECTING"
                }
            )
            # This will send a disconnecting message message to the chatroom, and then close the connection
            self.send(chatroom_socket_info[0], chatroom_socket_info[1], chatroom_socket_info[2], msg_data)
            chatroom_socket_info[0].close()
        # if there's an error closing or sending the message, then the connection is already closed
        except:
            print("[CLIENT_INFO] Connection Already Closed")

        # Waits 5 Seconds, then closes it, for user convenience
        print("[CLIENT_INFO] Exiting Program...")
        t.sleep(5)
        os._exit(0)

# This class is used to allow the user to host their own server, it takes in the common class as a parent
class Server(Common):
    def __init__(self, host, port):
        # Utilises the super method to extend the parent classes init
        super(Server, self).__init__()
        print("[SERVER_INFO] Initialising Server...")
        # This section defines the server variables needed
        self.clients = {}
        # Sets up the socket with ipv4 support, and tcp streaming
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # The lines below set up the server to run on the socket just created
        self.server.bind((host, port))
        self.server.listen()

        print(f"[SERVER_INFO] Server Running On IP: {host}")
        # Starts the start method
        self.start()

    """
    This method is used to start the server, and set up the initial requirements for each user, and create a new thread
    for each new connection    
    """
    def start(self):
        # Retrieves the global variables needed for this function
        global current_server_state, next_server_state

        # This while loop goes through each of the server states specified
        while current_server_state != "END_SERVER":
            # The first state simply prints out a message, letting the user know the server has been setup and moves
            if current_server_state == "START_SERVER":
                print("[SERVER_INFO] Server Set Up Complete")
                next_server_state = "ACCEPT_CONNECTIONS"
            # The next state accepts connections, and then passes them on to authentication
            elif current_server_state == "ACCEPT_CONNECTIONS":
                client_pub_key = ""
                client_n_key = ""
                print("[SERVER_INFO] Awaiting Connection")
                # Accepts incoming connections to the socket
                conn, address = self.server.accept()
                print(f"[SERVER_INFO] User Connected with {str(address)}")
                next_server_state = "AUTHENTICATING"
            # This next state handles the authentication of the user, and generating the new keys for them
            elif current_server_state == "AUTHENTICATING":
                print("[SERVER_INFO] Generating Authentication Data")
                # This generates a new set of keys for each new connections that passes to the authentication stage
                server_pub_key, server_pri_key, server_n_key = rsa.generateKeys(256)
                print("[SERVER_INFO] Sending Authentication Data")
                auth_data = json.dumps(
                    {
                        "server_state": current_server_state,
                        "server_pub_key": server_pub_key,
                        "server_n_key": server_n_key
                    }
                )
                # Sends public and private key of the server for this user
                auth_data_status = self.send(conn,
                                             client_pub_key,
                                             client_n_key,
                                             auth_data)
                # This checks if the message has been sent successfully, if not, then it passes to the connection error state
                if auth_data_status:
                    print("[SERVER_INFO] Awaiting Client Authentication Details")
                    # Retrieves the client authentication data, and decrypts the message using the server public keys
                    client_auth_data = self.receive(conn, server_pri_key, server_n_key)
                    # Checks if the message has been successfully retrieved, if not, then it passes to the connection error state
                    if not client_auth_data:
                        next_server_state = "CONNECTION_ERROR"
                    elif client_auth_data["client_state"] == "AUTHENTICATING":
                        client_pub_key = client_auth_data["client_pub_key"]
                        client_n_key = client_auth_data["client_n_key"]
                        # If everything is successful, and then it moves on to requesting the nickname from the user
                        next_server_state = "REQUESTING_NICKNAME"
                else:
                    next_server_state = "CONNECTION_ERROR"

            # This state is used to request and retrieve the client details and save them into the self.client variable
            elif current_server_state == "REQUESTING_NICKNAME":
                nickname_request = json.dumps(
                    {
                        "server_state": current_server_state
                    }
                )
                # sends the state over to the client, so they know that the server is requesting for the nickname
                nickname_request_status = self.send(conn, client_pub_key, client_n_key, nickname_request)
                # Checks that the send request hasn't failed, and receives the nickname data from the user
                if not nickname_request_status:
                    next_server_state = "CONNECTION_ERROR"
                else:
                    nickname = self.receive(conn, server_pri_key, server_n_key)
                    # Checks if the nickname data has been received successfully, else it will go to connection error
                    if not nickname:
                        next_server_state = "CONNECTION_ERROR"
                    else:
                        # Saves the data into the client dictionary, so it can be used in  the handle client method
                        self.clients[conn] = {
                            "nickname": nickname["nickname"],
                            "client_pub_key": client_pub_key,
                            "client_n_key": client_n_key,
                            "server_pub_key": server_pub_key,
                            "server_pri_key": server_pri_key,
                            "server_n_key": server_n_key
                        }
                        # Moves to the HANDLE_CLIENT state
                        next_server_state = "HANDLE_CLIENT"

            # This state is used to handle each client, by welcoming them to the server, and creating a new thread
            elif current_server_state == "HANDLE_CLIENT":
                print("[SERVER_INFO] Client Successfully Joined")
                welcome_msg = json.dumps(
                    {"server_state": "SENDING_MESSAGE",
                     "server_message": f"{nickname['nickname']} has connected to the server\n"
                     }
                )
                # Utilises the broadcast method to send all clients in the server the welcome message
                self.broadcast(welcome_msg)
                print("[SERVER_INFO] Initiating New Client Thread")
                # Creates new thread for client, running the handle_client method, this is to run multiple clients at once
                thread = threading.Thread(target=self.handle_client, args=(conn,))
                # This allows the thread to close when the main thread dies
                thread.daemon = True
                # Starts the thread
                thread.start()
                # Returns to the accept_connections state to allow more users to join
                next_server_state = "ACCEPT_CONNECTIONS"

            # This state handles if there's been any issues with connections
            elif current_server_state == "CONNECTION_ERROR":
                # this method utilises the remove_user method to disconnect the user, and remove their data
                self.remove_user(conn)
                # Returns to the accept_connections state to allow more users to join
                next_server_state = "ACCEPT_CONNECTIONS"

            current_server_state = next_server_state
    # This method allows messages to be sent to all users in the server
    def broadcast(self, msg):
        print("[SERVER_INFO] Broadcasting Message")
        # This loops through a copy of the dictionary, this helps to void any system errors from removing from a dict
        for client in list(self.clients):
            # Retrievies the data from the clients dictionary
            pub_key = self.clients[client]["client_pub_key"]
            n_key = self.clients[client]["client_n_key"]
            # Sends the message to each client, using their authentication details provided
            msg_status = self.send(client, int(pub_key), int(n_key), msg)
            # If there's an error, it removes the user
            if not msg_status:
                self.remove_user(client)

    # This method is used to remove the client's details from the server, and severs the connection from them
    def remove_user(self, client):
        print("[SERVER_SESSION_INFO] User No Longer Connected, Removing Session Data")
        """
        This checks if the client is not in the dictionary, if so, it simply closes the connection, else, it removes
        the clients data from the server
        """
        if client not in self.clients:
            client.close()
        else:
            disconnect_message = json.dumps(
                    {"server_state": "SENDING_MESSAGE",
                     "server_message": f"{self.clients[client]['nickname']} has disconnected\n"
                     }
                )
            # Removes the client data from the dictionary
            self.clients.pop(client)
            try:
                client.close()
            except:
                print("[SERVER_INFO] User Already Disconnected")

            self.broadcast(disconnect_message)

    def handle_client(self, client):
        # Accesses global variables
        global current_server_state
        current_server_session_state = current_server_state
        next_server_session_state = ""
        msg_data = ""
        # Create a while loop to go through this session states, and continues till either the server end or user leaves
        while current_server_session_state != "TERMINATED_USER" or current_server_state != "END_SERVER":
            # This state simply print message letting user know what's happening
            if current_server_session_state == "HANDLE_CLIENT":
                print("[SERVER_INFO] Setup Client")
                next_server_session_state = "HANDLING_USER"
            # This state handles the user, and the messages received by them
            elif current_server_session_state == "HANDLING_USER":
                # This condition checks if the user is in the list, else it terminates the while loop
                if client in self.clients:
                    # Retrieves the message data from the client using the server auth details to decrypt
                    msg_data = self.receive(client, int(self.clients[client]["server_pri_key"]),
                                            int(self.clients[client]["server_n_key"]))
                    """
                    These conditions check what the client state is from the messsage data
                    The first condition checks if there's been error receiving data from the user and terminates them
                    
                    The second condition checks if the client state is SENDING_MESSAGE, and moves to the broadcast state
                    
                    The third condition checks if the client state is disconnecting, and moves to the state of 
                    terminating the user
                    
                    The last condition checks if the client state is disconnecting, and moves to the state of 
                    terminating the user
                    """
                    if not msg_data:
                        next_server_session_state = "TERMINATING_USER"
                    elif msg_data["client_state"] == "SENDING_MESSAGE":
                        next_server_session_state = "BROADCAST_MESSAGE"
                    elif msg_data["client_state"] == "DISCONNECTING":
                        next_server_session_state = "TERMINATING_USER"
                    elif msg_data["client_state"] == "TIMED_OUT":
                        next_server_session_state = "TERMINATING_USER"
                else:
                    # This ends the while loop
                    next_server_session_state = "TERMINATED_USER"

            # This state utilises the broadcast method to send the message the client sends to all users
            elif current_server_session_state == "BROADCAST_MESSAGE":
                msg = json.dumps(
                    {"server_state": "SENDING_MESSAGE",
                     "server_message": msg_data["client_message"]
                     }
                )
                self.broadcast(msg)
                next_server_session_state = "HANDLING_USER"
            # This method utilises the remove user method to remove the clients connection
            elif current_server_session_state == "TERMINATING_USER":
                self.remove_user(client)
                next_server_session_state = "TERMINATED_USER"

            current_server_session_state = next_server_session_state


# This class handles all the client aspect of things, including the GUI, the receiving of data and the main menu
class Client(Common):
    def __init__(self, host, port):
        super(Client, self).__init__()
        self.waiting_to_join = True
        self.main_server_host = host
        self.main_server_port = port
        self.host = ""
        self.port = ""
        """
        This section initializes the "chatroom" variables, meaning these variables are used for
        the servers that the user hosts
        """
        self.server_chatroom_pub = ""
        self.server_chatroom_n = ""
        self.client_chatroom_pub = ""
        self.client_chatroom_pri = ""
        self.client_chatroom_n = ""
        self.nickname = ""

        """
        This section initializes the main method, sets up the root tkinter screen, and sets up the main loop 
        """
        # Initialises the root screen, as the gui will utilise this, to display a screen on top of
        self.root = Tk()
        # Hides the root screen, as this will never be interacted with in the foreground
        self.root.withdraw()
        self.gui_done = False
        # Initialises the main method, to begin the program
        self.main()
        # Starts the mainloop on the root screen, so that the GUI can run
        self.root.mainloop()

    # This method is the main controller of the client class, this handles the inital client states, and sets up everything
    def main(self):
        global current_client_state, next_client_state
        # This while loop runs till the state is END_PROGRAM
        while current_client_state != "END_PROGRAM":
            # This state creates the main menu for the user, as well, as getting them to write their nickname
            if current_client_state == "START_STATE":
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                welcome_msg = "Welcome To Nova Chat"
                spacing = len(welcome_msg) + 80
                self.print_format(welcome_msg,spacing)
                print("-" * spacing)
                """
                This checks if the user has got a nickname or not, and if it has then it will move on to the main menu,
                else, it will move to the RETRIEVE_NICKNAME state to get it
                """
                if not self.nickname:
                    next_client_state = "RETRIEVE_NICKNAME"
                else:
                    self.print_format("Main Menu", spacing)
                    print("-" * spacing)
                    print("(1) - Host Server\n(2) - Join Server\n(3) - Exit")
                    user_input_error = True
                    # This while loop will continue till the user enters a valid result
                    while user_input_error:
                        user_choice = input("What Would You Like To Do: \n")
                        # This checks if the choice is numeric else it will error out
                        if user_choice.isnumeric():
                            user_choice = int(user_choice)
                            # This checks what the user enters, and move them to the relavent state
                            if user_choice == 1:
                                next_client_state = "HOST_CHAT"
                                user_input_error = False
                            elif user_choice == 2:
                                next_client_state = "CHOOSE_SERVER"
                                user_input_error = False
                            elif user_choice == 3:
                                next_client_state = "END_PROGRAM"
                                user_input_error = False
                            else:
                                print("Invalid Entry, Please Try Again")
                        else:
                            print("Invalid Entry, Please Try Again")
                            next_client_state = "START_STATE"

            # This state gets the nickname from the user, if the user doesn't input anything, then it will cause it to repeat
            elif current_client_state == "RETRIEVE_NICKNAME":
                self.nickname = input("Please Enter A Nickname:\n")
                if self.nickname:
                    next_client_state = "START_STATE"
                else:
                    print("Please Enter A Valid Nickname")
                    next_client_state = "RETRIEVE_NICKNAME"
            # This state allows the user to host a server locally, and create the server on a new thread
            elif current_client_state == "HOST_CHAT":
                    print("[CLIENT_INFO] Checking If Port Is Open, Please Wait")
                    # Retrieves the ip from the local machine
                    self.host = socket.gethostbyname(socket.gethostname())
                    self.port = 50001
                    # Create a new socket, to test if the port is available
                    check_port_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    """
                     If the port is available, it will allow the user to create the server, and will move them to the 
                     "JOINING_CHAT" state, else, it will send the user to the FAILED_TO_HOST state
                     """
                    try:
                        check_port = check_port_socket.connect((self.host, self.port))
                        check_port_socket.close()
                        next_client_state = "FAILED_TO_HOST"
                    except ConnectionRefusedError:
                        # It create a thread for the server, and uses the server class in it
                        server_thread = threading.Thread(target=Server, args=(socket.gethostbyname(socket.gethostname())
                                                                              , 50001))
                        server_thread.daemon = True
                        server_thread.start()
                        next_client_state = "JOINING_CHAT"

            # This states allows the user to join a custom server or the main server e.g. server.py
            elif current_client_state == "CHOOSE_SERVER":
                join_server_choice = input("Would You Like To Join The Main Chatroom: (Y) Or (N)")
                if join_server_choice.upper() == "N" or join_server_choice.upper() == "Y":
                    next_client_state = "CHOOSE_SERVER"
                    if join_server_choice.upper() == "Y":
                        # Sets the host and port variables to be equal to the main server details
                        self.host = self.main_server_host
                        self.port = self.main_server_port
                    elif join_server_choice.upper() == "N":
                        self.host = input("Please Enter The IP You Wish To Connect To: ")
                        self.port = 50001

                    # This try and exception section tests if the IP given is a real ip, else it will error, and restart
                    try:
                        socket.inet_aton(self.host)
                        # If the ip is correct, it will move to the JOINING_CHAT state
                        next_client_state = "JOINING_CHAT"
                    except:
                        print("Invalid IP Address")
                        next_client_state = "CHOOSE_SERVER"
                else:
                    print("[CLIENT_INFO] Invalid Data, Please Re-Enter")
                    next_client_state = "CHOOSE_SERVER"

            # This state attempts to join the server, and sets up the receive thread to handle incoming data
            elif current_client_state == "JOINING_CHAT":
                try:
                    # This will connected to the server on the data provided
                    self.s.connect((self.host, self.port))
                    # This create a new thread to retrieve the data, as this allows data to run parallel to my GUI
                    self.receive_thread = threading.Thread(
                        target=self.handle_message)
                    self.receive_thread.daemon = True
                    self.receive_thread.start()
                    self.attempt = 0
                    # Moves to the state WAITING_TO_JOIN to prepare the GUI
                    next_client_state = "WAITING_TO_JOIN"
                except ConnectionRefusedError:
                    # If it fails to join the server, it'll send the user back to the start of the states
                    print("[CLIENT_INFO] Failed To Join, Please Validate And Try Again")
                    next_client_state = "START_STATE"

                except TimeoutError:
                    print("[CLIENT_INFO] Invalid Connection, Please Try Again")
                    next_client_state = "CHOOSE_SERVER"

            # This state allows the GUI to be created after all the server setup has happened
            elif current_client_state == "WAITING_TO_JOIN":
                # if the socket exists, it will then check if the data has loaded in yet, for the GUI
                if self.s:
                    if not self.waiting_to_join:
                        # If the data has loaded in, it will load up the GUI, and move to the JOIN_CHAT state
                        self.gui_loop()
                        next_client_state = "JOIN_CHAT"
                    else:
                        # This will print out to the user that the client is joining the server, and then wait 5 seconds
                        print("[CLIENT_INFO] Joining Server, Please Wait")
                        t.sleep(5)
                        # This will check how many attempts have been made to join the server, if it's 10 or more then it will stop
                        if self.attempt >= 5:
                            print("[CLIENT_INFO] Failed To Join Server")
                            self.s.close()
                            next_client_state = "START_STATE"
                        else:
                            next_client_state = "WAITING_TO_JOIN"
                        self.attempt += 1
                else:
                    next_client_state = "START_STATE"

            # This state is for checking if gui has loaded in, else it will go back to the main menu
            elif current_client_state == "JOIN_CHAT":
                print("[JOIN_CHAT] User Joining Chat")
                if self.gui_done:
                    next_client_state = "JOINED_CHAT"
                else:
                    print("Failed To Join")
                    next_client_state = "START_STATE"
            elif current_client_state == "JOINED_CHAT":
                    next_client_state = "JOINED_CHAT"

            # This state will restart the program back to the main menu, if the user fails to host
            elif current_client_state == "FAILED_TO_HOST":
                print("[SERVER_INFO] Unable To Host Server, Port Isn't Available To Use")
                next_client_state = "START_STATE"
            current_client_state = next_client_state

        # If the while loop is exited, then it will use the stop method
        self.stop(self.root, (self.s, self.client_chatroom_pri, self.server_chatroom_n))

    # This method allows for text to be printed formatted with spacing
    def print_format(self, msg, spacing):
        print("{:^{SPACING}s}".format(msg, SPACING=spacing))

    # This method sets up the GUI of the chatroom
    def gui_loop(self):
        # This makes a new screen appear with the parent of the root screen
        self.chat_room = Toplevel(self.root)
        # This changes what happens when the user closes the window, it will use the stop method
        self.chat_room.protocol('WM_DELETE_WINDOW', lambda: self.stop(self.root,
                                                                      (self.s,
                                                                       self.client_chatroom_pri,
                                                                       self.client_chatroom_n)))
        # This makes the chatroom appear on top
        self.chat_room.attributes('-topmost', 1)
        self.chat_room.title("chat_room")
        self.chat_room.configure(bg="lightgray")
        # This section is the header of my chatroom GUI, it has a label with Chat in it
        self.chat_label = tkinter.Label(self.chat_room, text=f"Chat:{self.host}", bg="lightgray")
        self.chat_label.config(font=("Arial", 12))
        self.chat_label.pack(padx=20, pady=5)

        # This section is the chat area, it feature a scrollable section of text, that all the messages will go
        self.chat_area = tkinter.scrolledtext.ScrolledText(self.chat_room)
        self.chat_area.pack(padx=20, pady=5)
        self.chat_area.config(state='disabled')

        # This section is the input area, allowing users to send messages
        self.msg_label = tkinter.Label(self.chat_room, text="Message:", bg="lightgray")
        self.msg_label.config(font=("Arial", 12))
        self.msg_label.pack(padx=20, pady=5)

        self.input_area = tkinter.Text(self.chat_room, height=3)
        self.input_area.pack(padx=20, pady=5)
        # This is the button that will send messages, it utilises the write method
        self.send_btn = tkinter.Button(self.chat_room, text="Send", command=self.write)
        self.send_btn.config(font=("Arial", 12))
        self.send_btn.pack(padx=20, pady=5)
        # Sets the GUI to be recognised as done
        self.gui_done = True
        self.chat_room.mainloop()

    # This method allows the messages users have inputted to be sent to the server
    def write(self):
        # This checks that the length of the message is less than or equal to 1024, if it isn't it will show an error
        if len(self.input_area.get('1.0', 'end')) <= 1024:
            # Retrieves the input that the user just sent, and then deletes it from the message box
            msg = f"{self.nickname}: {self.input_area.get('1.0', 'end')}"
            self.input_area.delete('1.0', 'end')
            msg_data = json.dumps(
                {
                    "client_state": "SENDING_MESSAGE",
                    "client_message": msg
                }
            )
            # This sends the message to the server, if it's not received, it'll present a messsage box with an error
            nickname_status = self.send(self.s, self.server_chatroom_pub, self.server_chatroom_n, msg_data)
            if not nickname_status:
                tkinter.messagebox.showerror("Message Unable To Send", "Message Is Unable To Be Sent", parent=self.chat_room)
                self.stop(self.root, (self.s, "",""))

        else:
            tkinter.messagebox.showerror("Message Too Long", "Please Enter A Smaller Message", parent=self.chat_room)

    # This method handles all the session states with the server, and all the receiving messages
    def handle_message(self):
        # This section defines the variables that will be needed, just before the while loop starts
        self.server_chatroom_pub = ""
        self.server_chatroom_n = ""
        authenticated = False
        print("[CLIENT_INFO] Generating Auth Keys")
        # Generates the client authentication keys
        client_chatroom_pub, client_chatroom_pri, client_chatroom_n = rsa.generateKeys(256)
        print("[CLIENT_INFO] Generated Auth Keys")

        current_client_session_state = "RETRIEVING_MESSAGE"
        next_client_session_state = ""
        # This while loop iterates through the states to process the information from the server
        while current_client_session_state != "TERMINATED":
            # This state is responsible for receiving and handling all messages from the server
            if current_client_session_state == "RETRIEVING_MESSAGE":
                print("[CLIENT_INFO] Retrieving Server Message")
                # This checks to see if the data has been authenticated, if not, it won't supply the chatroom auth keys
                if authenticated:
                    server_data = self.receive(self.s, client_chatroom_pri, client_chatroom_n)
                else:
                    server_data = self.receive(self.s, "", "")
                print("[CLIENT_INFO] Received Message: " + json.dumps(server_data))
                """
                This condition checks whether the server data has received anything, if not, then the server is
                offline, and it'll move to the SERVER_OFFLINE state.
                """
                if not server_data:
                    next_client_session_state = "SERVER_OFFLINE"

                # Checks whether the server data state is AUTHENTICATING and gets the auth data, and passes to the client state authenticating
                elif server_data["server_state"] == "AUTHENTICATING":
                    print("[CLIENT_INFO] Retrieved CHATROOM Authentication Data")
                    self.server_chatroom_pub = server_data["server_pub_key"]
                    self.server_chatroom_n = server_data["server_n_key"]
                    next_client_session_state = "AUTHENTICATING"

                # Checks whether the server data state is REQUESTING_NICKNAME, if so it'll send nickname data to the server
                elif server_data["server_state"] == "REQUESTING_NICKNAME":
                    print("[CLIENT_INFO] Sending User Details")
                    user_details = json.dumps(
                    {
                        "client_state": "SENDING_NICKNAME",
                        "nickname": self.nickname
                    }
                    )
                    # Sends the nickname data to server
                    user_details_status = self.send(self.s,
                                                    self.server_chatroom_pub,
                                                    self.server_chatroom_n,
                                                    user_details)

                    # If the nickname data is unable to be sent it'll go to the SERVER_OFFLINE state, else it will return to the retrieving message state
                    if not user_details_status:

                        next_client_session_state = "SERVER_OFFLINE"

                    else:
                        next_client_session_state = "RETRIEVING_MESSAGE"
                # If the server state is timed_out it will be sent to the SERVER_OFFLINE state
                elif server_data["server_state"] == "TIMED_OUT":
                    next_client_session_state = "SERVER_OFFLINE"
                # As the only other state it can be, which is SENDING_MESSAGE, then it goes to the state DISPLAY_MESSAGE
                else:
                    next_client_session_state = "DISPLAY_MESSAGE"

            # This state is used to authenticate the user with the server
            elif current_client_session_state == "AUTHENTICATING":
                print("[CLIENT_INFO] Sending Client Authentication Details")
                auth_data = json.dumps(
                    {
                        "client_state": current_client_session_state,
                        "client_pub_key": client_chatroom_pub,
                        "client_n_key": client_chatroom_n
                    }
                )
                # This sends the auth data to the server, it returns with information, then it will be passed back
                auth_data_status = self.send(self.s, self.server_chatroom_pub, self.server_chatroom_n, auth_data)
                if not auth_data_status:
                    next_client_session_state = "SERVER_OFFLINE"
                else:
                    authenticated = True
                    next_client_session_state = "RETRIEVING_MESSAGE"

            # This state displays the messages into the chat area in the GUI
            elif current_client_session_state == "DISPLAY_MESSAGE":
                if self.waiting_to_join:
                    self.waiting_to_join = False
                # This checks to ensure the GUI has been set up, else it'll loop back round
                if self.gui_done:
                    # Sets the chat area to allow the ability to write data into it
                    self.chat_area.config(state='normal')
                    # Inserts the data at the end of the chat area
                    self.chat_area.insert('end', server_data['server_message'])
                    # Sets the user view, to most recent message
                    self.chat_area.yview('end')
                    # Disables the chat area to stop user entering message into it
                    self.chat_area.config(state='disabled')
                    next_client_session_state = "RETRIEVING_MESSAGE"
                else:
                    next_client_session_state = "DISPLAY_MESSAGE"

            # This state stops the client as this will get triggered when the server is offline
            elif current_client_session_state == "SERVER_OFFLINE":
                print("[CLIENT_INFO] Server Offline")
                # It first checks if the GUI is done, then displays that the server is offline
                if self.gui_done:
                    self.chat_area.config(state='normal')
                    self.chat_area.insert('end', "Server Offline. Exiting")
                    self.chat_area.yview('end')
                    self.chat_area.config(state='disabled')
                next_client_session_state = "TERMINATED"
                # It runs the stop method to shutdown everything
                self.stop(self.root, (self.s, self.client_chatroom_pri, self.client_chatroom_n))

            current_client_session_state = next_client_session_state

if __name__ == "__main__":
    # This sets up the program
    Client(HOST, PORT)