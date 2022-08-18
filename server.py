import threading
import socket
import rsa
import json
import io
HOST = socket.gethostbyname(socket.gethostname()) # getting the host ip from the local computer
PORT = 50000
current_server_state = "START_SERVER"
next_server_state = ""


class Server:
    def __init__(self, host, port):
        self.format = "utf-8"
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


#handle

if __name__ == "__main__":
    Server(HOST, PORT)