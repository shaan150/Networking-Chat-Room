import socket
import sys
import threading
import tkinter
import tkinter.messagebox
from tkinter import *
from tkinter import simpledialog
import tkinter.scrolledtext
HOST = socket.gethostbyname(socket.gethostname()) # getting the host ip from the local computer
PORT = 50000
current_gui_state = "START_STATE"
next_gui_state = ""
current_server_state = "START_STATE"
next_server_state = ""
class Server:
    def __init__(self, host, port):
        global current_server_state, next_server_state, current_gui_state, next_gui_state
        self.host = host
        self.port = port
        self.format = "utf-8"
        self.clients = []
        self.nicknames = []
        while current_server_state != "TERMINATED":
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
                    next_gui_state = "FAILED_TO_HOST"
                    print("FAILED_TO_RUN")


            current_server_state = next_server_state
    # broadcast
    
    """
    Sends message to all clients
    
    """
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
            message = msg.encode(format)
            msg_length = len(message)
            send_length = str(msg_length).encode(format)
            send_length += b' ' * (12 - len(send_length))
            client.send(send_length) #sends message length
            client.send(message) #snds message 
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
        while current_server_state != "END_SERVER":
            conn, address = self.server.accept()
            print(f"Connected with {str(address)}")
            if current_server_state == "START_SERVER":
                next_server_state = "SERVER_RUNNING"
            elif current_server_state == "SERVER_RUNNING":
                print("[SERVER_RUNNING] Sending Nickname")
                self.send("Nickname:", conn) # Sends Request For Nickname
                nickname = self.receive(conn) # Receives Nickname
                if not nickname:
                    conn.close()
                else:
                    self.nicknames.append(nickname)
                    self.clients.append(conn)
                    welcome_msg = f"{nickname} connected to the server!\n"
                    self.broadcast(welcome_msg, conn)
                    print("[SERVER_RUNNING] Initiating New Client Thread")
                    thread = threading.Thread(target=self.handle_client, args=(conn,)) #Creates thread for each new user 
                    thread.start()

                next_server_state = "SERVER_RUNNING"
            current_server_state = next_server_state
      
    def receive(conn):
        try:
            msg_length = conn.recv(12).decode(format) # Retrieves message length
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(format) #Retrieve message based on message length

                return msg
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
        self.gui_done = False
        self.state_thread = threading.Thread(target=self.state_manager) #creates new thread to handle states for the gui
        self.state_thread.daemon = True
        self.state_thread.start()
        self.gui_loop()  # starts the gui


    def state_manager(self):
        global current_gui_state, next_gui_state
        while current_gui_state != "END_PROGRAM":
            if current_gui_state == "START_STATE":
                """
                Handles the first state, which is the main menu in the gui, it checks which button has been pressed and moves to the state based on that
                """
                if self.hosting_server:
                    print("Initalising Hosting")
                    next_gui_state = "HOST_CHAT"
                elif self.joining_server:
                    next_gui_state = "JOIN_CHAT"
                else:
                    next_gui_state = "START_STATE"
                    print(next_gui_state)
            elif current_gui_state == "HOST_CHAT":
                """
                Handles the hosting of the clients own server, it'll create a new thread for the server and move the running server state
                """
                try:
                    print("Hosting Server")
                    server_thread = threading.Thread(target=Server, args=(socket.gethostbyname(socket.gethostname()), 50001))
                    server_thread.start()
                    next_gui_state = "RUNNING_SERVER"
                except:
                    next_gui_state = "FAILED_TO_HOST" #If it fails to create server it hit thsi state
            elif current_gui_state == "RUNNING_SERVER":
                print("[RUNNING_SERVER] Client Successfully Ran Server")
                self.host = socket.gethostbyname(socket.gethostname()) # Gets details of host ip from get host name method
                self.port = 50001 
                """
                messsage box doesn't work on GUI loop, unsure why?
                """
                msg = tkinter.Tk()
                msg.withdraw()

                self.nickname = simpledialog.askstring("Nickname", "Please choose a nickname: ", parent=msg,
                                                       initialvalue="Guest")
                if not self.nickname:
                    self.stop()
                else:
                    self.gui_done = False
                    next_gui_state = "JOIN_CHAT"
            elif current_gui_state == "JOIN_CHAT":
                print("[JOIN_CHAT] User Joining Chat")
                """
                checks if GUI has been generated, then conencts locally to the server
                this never happens, i believe line 174 may be causing this?
                """
                if self.gui_done:
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.s.connect((self.host, self.host))
                    self.receive_thread = threading.Thread(target=self.handle_message)  # create a new thread to handle the GUI and the socket aspect of things seperately
                    self.receive_thread.daemon = True #when the main thread stops, so does the receive thread
                    self.receive_thread.start()
                    next_gui_state = "JOINED_CHAT"
                else:
                    next_gui_state = "JOINING_CHAT"
            elif current_gui_state == "JOINING_CHAT":
                if self.gui_done:
                    next_gui_state = "JOIN_CHAT"
                else:
                    print("attempting to join chat")
                    next_gui_state = "JOINING_CHAT"
            elif current_gui_state == "JOINED_CHAT":
                if not self.gui_done:
                    pass
            elif current_gui_state == "FAILED_TO_HOST":
                print("[FAILED_TO_HOST] Unable To Host Server, Port Isn't Available To Use")
                next_gui_state = "START_STATE"
            current_gui_state = next_gui_state

    def gui_loop(self):
        global current_gui_state, next_gui_state
        self.chat = tkinter.Tk()
        if current_gui_state == "START_STATE":
            if not self.gui_done:
                """
                Generates Main Menu
                """
                self.chat.withdraw()
                self.main_menu = Toplevel(self.chat)
                self.main_menu.title("Main Menu")
                self.main_menu.geometry("1920x1080")
                self.main_menu.configure(bg="#2b2d5d")
                self.main_menu.protocol("WM_DELETE_WINDOW", self.stop)
                Frame_Login = Frame(self.main_menu, bg="white")
                Frame_Login.place(width=600, height=500, relx=.5, rely=.5, anchor=CENTER)

                # title
                title = Label(Frame_Login, text="Main Menu", font=("Calibri", 35, "bold"), fg="#0e80fa",bg="white").place(x=180, y=30)

                self.host = Button(Frame_Login, text="Host A Chatroom", font=("Calibri", 15), fg="white", bg="red",command=lambda: self.button_change_state("HOST_CHAT"))
                self.host.place(x=180, y=170, width=260, height=60)

                self.join = Button(Frame_Login, text="Join A Chatroom", font=("Calibri", 15), fg="white", bg="red",
                                   command=lambda: self.button_change_state("JOIN_CHAT"))
                self.join.place(x=180, y=240, width=260, height=60)
                self.gui_done = True

            if self.button_clicked:
                self.button_clicked = False
                self.next_gui_state = self.button_state

        elif self.current_gui_state == "HOST_CHAT":
            print("Hosting Server")

        elif self.current_gui_state == "RUNNING_SERVER":
            print("[Client] Hosting Server]")


        elif self.current_gui_state == "JOINING_CHAT":
            """
            Never reaches this point
            """
            self.main_menu.destroy()
            self.chat_room = Toplevel(self.chat)
            self.chat_room.title("chat_room")
            self.chat_room.geometry("1920x1080")
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
        elif self.current_gui_state == "FAILED_TO_HOST":
            tkinter.messagebox.showerror("Unable To Host","Unable To Host, As Port Is Unavailable, Please Try Again Later")
            self.hosting_server = False
            self.host["state"] = "normal"


        self.chat.mainloop()

    def button_change_state(self, state):
        self.button_clicked = True
        self.button_state = state
        if state == "HOST_CHAT":
            self.hosting_server = True
            self.host["state"] = "disabled"
        elif state == "JOIN_CHAT":
            self.joining_server = True


    def write(self):
        """
        Writes message in input box, if greater than 256 bytes then error
        """
        if len(self.input_area.get('1.0', 'end')) <= 256:
            msg = f"{self.nickname}: {self.input_area.get('1.0', 'end')}"
            self.send(msg)
            self.input_area.delete('1.0', 'end')
        else:
            tkinter.messagebox.showerror("Message Too Long", "Please Enter A Smaller Message")

    def stop(self):
        global current_gui_state
        
        print("Ending Session")
        current_gui_state = "DISCONNECTED"
        try:
            self.s.close()
        except:
            print("Connection Already Closed")
        current_gui_state = "END_PROGRAM"
        self.chat.destroy()
        sys.exit(0)

    def handle_message(self):
        """
        handles the receiving and sending of messages, and displays them in scroll text area
        """
        while self.current_gui_state != "DISCONNECTED":
            print("client running")
            print("receiving message")
            msg = self.receive()
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
        try:
            msg_length = self.s.recv(12).decode(self.format)
            print(msg_length)
            if msg_length:
                msg_length = int(msg_length)
                msg = self.s.recv(msg_length).decode(self.format)

                return msg
            else:
                return "invalid_message"
        except:
            return False

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
