import socket
import sys
import threading
import tkinter.messagebox
from tkinter import *
from tkinter import simpledialog
import tkinter.scrolledtext
HOST = socket.gethostbyname(socket.gethostname()) # getting the host ip from the local computer
PORT = 50000
current_server_state = "START_STATE"
next_server_state = ""
current_client_state = "START_STATE"
next_client_state = ""
class Server:
    def __init__(self, host, port):
        global current_server_state, next_server_state, current_client_state, next_client_state
        self.host = host
        self.port = port
        self.format = "utf-8"
        self.clients = []
        self.nicknames = []
        while current_server_state != "END_PROGRAM":
            if current_server_state == "START_STATE":
                next_server_state = "START_SERVER"
            elif current_server_state == "START_SERVER":
                print("STARTing Server")
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    self.server.bind((self.host, self.port))
                    self.server.listen()
                    print("[SERVER STATUS] Server Running...")
                    self.start()
                except:
                    print("FAILED_TO_RUN")
                    next_client_state = "FAILED_TO_RUN"
                    next_server_state = "END_PROGRAM"
                    

            print("Testing")
            current_server_state = next_server_state
    # broadcast
    def broadcast(self, msg, client):
        for c in self.clients:
            self.send(msg, c)

    def handle_client(self, client):
        global current_server_state, next_server_state
        current_server_session_state = current_server_state
        next_server_session_state = ""
        while current_server_session_state != "TERMINATED_USER":
            if current_server_session_state == "SERVER_RUNNING":
                next_server_session_state = "HANDLING_USER"
            elif current_server_session_state == "HANDLING_USER":
                try:
                    msg = self.receive(client)
                    print(f"{self.nicknames[self.clients.index(client)]}")
                    self.broadcast(msg, client)
                except:
                    next_server_session_state = "TERMINATING_USER"
            elif current_server_session_state == "TERMINATING_USER":
                print("Removing User")
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                self.nicknames.remove(nickname)
                next_server_session_state = "TERMINATED_USER"

            current_server_session_state = next_server_session_state

    def send(self, msg, client):
        try:
            message = msg.encode(self.format)
            msg_length = len(message)
            send_length = str(msg_length).encode(self.format)
            send_length += b' ' * (12 - len(send_length))
            client.send(send_length)
            client.send(message)
            return True
        except ConnectionResetError:
            if not self.clients[client]:
                client.close()
            else:
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                self.nicknames.remove(nickname)

            return False

    # receive
    def start(self):
        global current_server_state, next_server_state
        print("[STARTING_SERVER] Listening For Connections")
        while current_server_state != "END_PROGRAM":
            conn, address = self.server.accept()
            print(conn)
            print("[LISTENING] Accepting Connection")
            print(f"Connected with {str(address)}")
            if current_server_state == "START_SERVER":
                print("[RUNNING_SERVER] Client Successfully Ran Server")
                next_server_state = "SERVER_RUNNING"
            elif current_server_state == "SERVER_RUNNING":
                print("test")
                print("[SERVER_RUNNING] Sending Nickname")
                self.send("Nickname:", conn)
                nickname = self.receive(conn)
                if not nickname:
                    conn.close()
                else:
                    self.nicknames.append(nickname)
                    self.clients.append(conn)
                    welcome_msg = f"{nickname} connected to the server!\n"
                    self.broadcast(welcome_msg, conn)
                    print("[SERVER_RUNNING] Initiating New Client Thread")
                    thread = threading.Thread(target=self.handle_client, args=(conn,))
                    thread.start()

                next_server_state = "SERVER_RUNNING"
            current_server_state = next_server_state

    def receive(self,conn):
        try:
            msg_length = conn.recv(12).decode(self.format)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(self.format)

                return msg
                print(msg)
            else:
                return False
        except ConnectionResetError:
            print("User Offline")
            return False
    # handle


class Client:
    def __init__(self, host, port):
        self.format = "utf-8"
        self.button_clicked = False
        self.hosting_server = False
        self.joining_server = False
        self.main_server_ip = host
        self.main_server_port = port
        self.nickname = "Guest"
        self.gui_done = False
        self.root = Tk()
        self.state_manager()
        self.root.mainloop()


    def print_format(self, msg, spacing):
        print("{:^{SPACING}s}".format(msg, SPACING=spacing))

    def state_manager(self):
        global current_client_state, next_client_state
        self.root.withdraw()
        user_input_error = True
        while current_client_state != "END_PROGRAM":
            if current_client_state == "START_STATE":
                welcome_msg = "Welcome To Nova Chat"
                spacing = len(welcome_msg) + 80
                self.print_format(welcome_msg,spacing)
                print("-" * spacing)
                self.print_format("Main Menu", spacing)
                print("-" * spacing)
                print("(1) - Host Server\n(2) - Join Server\n(3) - Exit")
                while user_input_error:
                    user_choice = input("What Would You Like To Do: \n")
                    if user_choice.isnumeric():
                        user_choice = int(user_choice)
                        if user_choice == 1:
                            next_client_state = "HOST_CHAT"
                            user_input_error = False
                        elif user_choice == 2:
                            next_client_state = "CHOOSE_SERVER"
                            user_input_error = False
                        elif user_choice == 3:
                            next_client_state = "ENDING_PROGRAM"
                            user_input_error = False
                        else:
                            print("Invalid Entry, Please Try Again")
                    else:
                        print("Invalid Entry, Please Try Again")

            elif current_client_state == "HOST_CHAT":
                try:
                    print("Hosting Server")
                    server_thread = threading.Thread(target=Server, args=(socket.gethostbyname(socket.gethostname()), 50001))
                    server_thread.daemon = False
                    server_thread.start()
                    next_client_state = "RUNNING_SERVER"
                except:
                    next_client_state = "FAILED_TO_HOST"
            elif current_client_state == "RUNNING_SERVER":
                self.host = socket.gethostbyname(socket.gethostname())
                self.port = 50001
                next_client_state = "JOINING_CHAT"

            elif current_client_state == "CHOOSE_SERVER":
                self.host = input("Please Enter The IP You Wish To Connect To: ")
                self.port = 50000
                try:
                    socket.inet_aton(self.host)
                    next_client_state = "JOINING_CHAT"
                except:
                    print("Invalid IP Address")
                    next_client_state = "CHOOSE_SERVER"
            elif current_client_state == "JOINING_CHAT":
                #try:
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    print(self.host)
                    self.s.settimeout(10)
                    self.s.connect((self.host, self.port))
                    self.s.settimeout(None)

                    self.receive_thread = threading.Thread(
                        target=self.handle_message)  # create a new thread to handle the GUI and the socket aspect of things seperately
                    self.receive_thread.daemon = True  # when the main thread stops, so does the receive thread
                    self.receive_thread.start()
                    self.gui_loop()
                    next_client_state = "JOINED_CHAT"
                #except:
                    #print("failed to join")
            elif current_client_state == "JOIN_CHAT":
                print("[JOIN_CHAT] User Joining Chat")
                if self.gui_done:

                    next_client_state = "JOINED_CHAT"
                else:
                    print("Failed To Join")
                    next_client_state = "START_STATE"

            elif current_client_state == "JOINED_CHAT":
                if not self.gui_done:
                    pass
            elif current_client_state == "FAILED_TO_HOST":
                print("[FAILED_TO_HOST] Unable To Host Server, Port Isn't Available To Use")
                next_client_state = "START_STATE"""
            current_client_state = next_client_state
            

    def gui_loop(self):
        self.chat_room = Toplevel(self.root)
        self.chat_room.title("chat_room")
        self.chat_room.configure(bg="lightgray")
        self.chat_room.protocol("WM_DELETE_WINDOW", self.stop)
        self.chat_label = tkinter.Label(self.chat_room, text="Chat:", bg="lightgray")
        self.chat_label.config(font=("Arial", 12))
        self.chat_label.pack(padx=20, pady=5)

        # chat history body

        self.chat_area = tkinter.scrolledtext.ScrolledText(self.chat_room)
        self.chat_area.pack(padx=20, pady=5)
        self.chat_area.config(state='disabled')

        # input box
        self.msg_label = tkinter.Label(self.chat_room, text="Message:", bg="lightgray")
        self.msg_label.config(font=("Arial", 12))
        self.msg_label.pack(padx=20, pady=5)

        self.input_area = tkinter.Text(self.chat_room, height=3)
        self.input_area.pack(padx=20, pady=5)

        self.send_btn = tkinter.Button(self.chat_room, text="Send", command=self.write)
        self.send_btn.config(font=("Arial", 12))
        self.send_btn.pack(padx=20, pady=5)
        self.gui_done = True

        self.chat_room.mainloop()

    def write(self):
        if len(self.input_area.get('1.0', 'end')) <= 256:
            msg = f"{self.nickname}: {self.input_area.get('1.0', 'end')}"
            print(msg)
            self.input_area.delete('1.0', 'end')
            nickname_status = self.send(msg)
            if not nickname_status:
                tkinter.messagebox.showerror("Message Unable To Send")
        else:
            tkinter.messagebox.showerror("Message Too Long", "Please Enter A Smaller Message")

    def stop(self):
        global current_server_state, current_client_state

        print("Ending Session")
        self.gui_done = False
        try:
            self.s.close()
        except:
            print("Connection Already Closed")
        current_server_state = "END_SERVER"
        current_client_state = "TERMINATED"
        self.root.destroy()
        sys.exit(0)

    def handle_message(self):
        global current_client_state
        while current_client_state != "DISCONNECTED":
            print("client running")
            print("receiving message")
            msg = self.receive()
            print(msg)
            if msg == "invalid_message":
                print("invalid msg")
            elif msg == "Nickname:":
                nickname_msg_status = self.send(self.nickname)
                if not nickname_msg_status:
                    print("invalid msg")
                    self.stop()
                else:
                    pass
            else:
                if self.gui_done:
                    print("Ready To Display")
                    self.chat_area.config(state='normal')
                    self.chat_area.insert('end', msg)
                    self.chat_area.yview('end')
                    self.chat_area.config(state='disabled')

    def receive(self):
        #try:
            msg_length = self.s.recv(12).decode(self.format)
            print(msg_length)
            if msg_length:
                msg_length = int(msg_length)
                msg = self.s.recv(msg_length).decode(self.format)

                return msg
            else:
                return "invalid_message"
        #except:
            #return False

    def send(self, msg):
        try:
            message = msg.encode(self.format)
            msg_length = len(message)
            send_length = str(msg_length).encode(self.format)
            send_length += b' ' * (12 - len(send_length))
            self.s.send(send_length)
            self.s.send(message)
            return True
        except:
            return False
if __name__ == "__main__":
    Client(HOST,PORT)
