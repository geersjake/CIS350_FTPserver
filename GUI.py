from tkinter import *
from encryption import Encryption
import ft_conn
import file_info
import pathlib


class Application(Frame):
    def __init__(self, master=None):
        """Initialize an instance of the Application and creates widgets"""
        super().__init__(master)

        # For the text box to input IP Address
        self.entry = Entry(self)
        self.entry.pack(side="top")
        self.entry.delete(0, END)

        # Entry box for the password in Encryption
        self.password_entry = Entry(self)
        self.password_entry.pack(side="top")

        # button to link computers
        self.connect = Button(self)
        self.connect["text"] = "Connect"
        self.connect.pack(side="top")
        self.connect["command"] = self.connect_command
        self.pack()

        # Quit Program
        self.quit = Button(self, text="QUIT", fg="red", command=root.destroy)
        self.quit.pack(side="bottom")

        # Label above the buttons of files to request
        self.label = Label(self)
        self.label["text"] = "File List"
        self.label.pack(side="top")

        # initializes the global variables used throughout the project
        self.ft = ft_conn.FTConn()
        self.local_files = file_info.LocalFileInfoBrowser()
        self.remote_file_list = []
        self.path = pathlib.Path(".")
        self.frame = None
        self.pack()

    def encrypt_file(self, file_data):
        """File given to the method becomes encrypted before it is sent across the network
            :param file_data is the bytes that are being encrypted"""
        # create encryption instance then encrypts
        return Encryption(file_data, self.password_entry.get()).encrypt()

    def decrypt_file(self, file_data):
        """File given to the method becomes encrypted before it is sent across the network
            :param file_data is the bytes that are being decrypted"""
        # create encryption instance then decrypts
        return Encryption(file_data, self.password_entry.get()).decrypt()

    def connect_command(self):
        """File given to the method becomes encrypted before it is sent across the network"""
        # retrieves ip address and port number
        ip_and_port = self.entry.get()
        # breaks those two into a list
        x = ip_and_port.split(":")

        # uses list to set each value independently
        ip = str(x[0])
        port = int(x[1])

        # attempts to connect
        message = self.ft.connect(ip, port)
        print(message)
        root.after(100, app.requests)
        return

    def requests(self):
        """File given to the method becomes encrypted before it is sent across the network"""
        try:
            # asks other user for a their file list
            self.ft.request_file_list()
        except Exception as err:
            raise err
        finally:
            root.after(10000, self.requests)

    def update_remote_file_list(self, file_list):
        """creates a new list of buttons that are on the other user's code
            :param file_list is the list of files that are on the other user's computer"""
        # sets a global variable that keeps track of the other user's file list
        self.remote_file_list = file_list

        # checks if the frame still exists, if it is, destroys it
        if self.frame:
            self.frame.pack_forget()
            self.frame.destroy()

        # creates new frame after it was destroyed
        self.frame = Frame(self, height=2000, width=2000)

        # sets up new buttons that are for file requests
        for files in file_list:
            button = Button(self.frame)
            button["text"] = files.path.name
            # requests a file with the file name, file_name
            button["command"] = lambda file_name = files.path.name.encode(): self.ft.request_file(file_name)
            button.pack()
        self.frame.pack()
        self.pack()

    def request_handler(self):
        """Handles all the requests that are given to each computer"""
        try:
            # message_type is a code that determines what type of request is being asked
            # data is what is in the file or file list
            message_type, data = self.ft.receive_data()
            # the types of message types and how to handle each one
            if message_type == ft_conn.FTProto.REQ_LIST:
                self.ft.send_file_list(self.local_files.list_info(self.path))
                print("file list sent")
            elif message_type == ft_conn.FTProto.REQ_FILE:
                self.ft.send_file(data, self.encrypt_file(pathlib.Path(data).read_bytes()))
                print("file sent")
            elif message_type == ft_conn.FTProto.RES_LIST:
                self.update_remote_file_list(data)
                print("file list received")
            elif message_type == ft_conn.FTProto.RES_FILE:
                file_name, file_data = data
                pathlib.Path(file_name.decode()).write_bytes(self.decrypt_file(file_data))
                print("file received")
            elif message_type is not None:
                print("unknown request")
        # if an error is given allows our loop to continue but shows the user still
        except Exception as err:
            raise err
        # refreshes the requests ever 10 milliseconds
        finally:
            root.after(10, self.request_handler)


root = Tk()
app = Application(master=root)
root.after(10, app.request_handler)
app.mainloop()
