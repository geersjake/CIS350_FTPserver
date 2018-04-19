from tkinter import *
from encryption import Encryption
import ft_conn
import file_info
import pathlib


class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)

        # For the text box to input IP Address
        self.entry = Entry(self)
        self.entry.pack()
        self.entry.delete(0, END)

        # Quit Program
        self.quit = Button(self, text="QUIT", fg="red", command=root.destroy)
        self.quit.pack(side="bottom")

        # button to link computers
        self.connect = Button(self)
        self.connect["text"] = "Connect"
        self.connect.pack(side="top")
        self.connect["command"] = self.connect_command
        self.en = Encryption("defaultData", "defaultPassword")
        self.pack()

        self.label = Label(self)
        self.label["text"] = "File List"
        self.label.pack(side="top")

        self.ft = ft_conn.FTConn()

        self.local_files = file_info.LocalFileInfoBrowser()

        self.remote_file_list = []

        self.path = pathlib.Path(".")
        self.frame = None
        self.pack()

    def encrypt_file(self, file_data):
        # create encryption instance with data = file.read()
        return Encryption(file_data, "").encrypt()

    def decrypt_file(self, file_data):
        # create encryption instance using data = contents
        return Encryption(file_data,"").decrypt()

    def connect_command(self):
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
        try:
            self.ft.request_file_list()
        except Exception as err:
            raise err
        finally:
            root.after(10000, self.requests)

    def update_remote_file_list(self, file_list):

        self.remote_file_list = file_list
        if self.frame:
            self.frame.pack_forget()
            self.frame.destroy()
        print("updating")
        self.frame = Frame(self, height=2000, width=2000)
        for files in self.local_files.list_info(self.path):
            button = Button(self.frame)
            button["text"] = files.path.name
            button["command"] = lambda: self.ft.request_file(files.path)
            button.pack()
        self.frame.pack()
        self.pack()

    def request_handler(self):
        try:
            message_type, data = self.ft.receive_data()
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
                pathlib.Path(file_name).write_bytes(self.decrypt_file(file_data))
                print("file received")
            elif message_type is not None:
                print("unknown request")

        #except OSError as err:
            #pass

        # TODO don't raise just because no data
        except ft_conn.ft_error.BrokenSocketError as err:
            pass

        except Exception as err:
            raise err

        finally:
            root.after(10, self.request_handler)


root = Tk()
app = Application(master=root)
root.after(10, app.request_handler)
app.mainloop()
