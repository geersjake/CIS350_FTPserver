from tkinter import *
from tkinter import filedialog
from encryption import Encryption
import ft_conn


class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)

        # For the text box to input IP Address
        self.entry = Entry(self)
        self.entry.pack()
        self.entry.delete(0, END)

        # Encryption Button
        self.encrypt = Button(self)
        self.encrypt["text"] = "Encrypt file to export"
        self.encrypt["command"] = self.encrypt_file
        self.encrypt.pack(side="left")

        # Decryption Button
        self.decrypt = Button(self)
        self.decrypt["text"] = "Decrypt a chosen file"
        self.decrypt["command"] = self.decrypt_file
        self.decrypt.pack(side="right")

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

        self.ft = ft_conn.FTConn()

        x=1
    def encrypt_file(self):
        file_data = filedialog.askopenfile()
        file_data = str(file_data)
        self.en = Encryption(file_data, "defaultP")
        x = self.en.encrypt()
        f = open("encrypted_data.txt", "wb")
        f.write(x)
        f.close()
        print("Your file " + file_data + " has been encrypted and can be sent")

    def decrypt_file(self):
        file_data = filedialog.askopenfile()
        file_data = str(file_data)
        self.en = Encryption(file_data, "defaultP")
        x = self.en.decrypt()
        f = open("encrypted_data.txt", "wb")
        f.write(x)
        f.close()
        print("Your file " + file_data + " has been decrypted and can be viewed")

    def connect_command(self):
        ip_and_port = self.entry.get()
        x = ip_and_port.split(",")
        ip = str(x[0])
        port = int(x[1])
        self.ft.connect(ip, port)
        return

    def requests(self):
        x, y = self.ft.check_for_request()
        if x == ft_conn.FTProto.REQ_FILE:
            #TODO y is file name, send to other computer
        if x == ft_conn.FTProto.REQ_LIST:

        #TODO last thing, call self.root.after()

root = Tk()
app = Application(master=root)
app.mainloop()
