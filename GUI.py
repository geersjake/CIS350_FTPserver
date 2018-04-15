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
    def encrypt_file(self):
        file_data = filedialog.askopenfile()
        enc_data = open("encrypted_data.txt", "wb")  # open file, wb = write bytes

        en = Encryption(file_data.read(), "password")  # create encryption instance with data = file.read()
        temp = en.encrypt()  # encrypt
        enc_data.write(temp)  # write the encrypted data to file

        file_data.close()  # close files
        enc_data.close()

        print("Your file " + file_data.name + " has been encrypted and can be sent")

    def decrypt_file(self):
        file_data = filedialog.askopenfile()
        with open("encrypted_data.txt",'rb') as file:  # open the file containing crazy egyptian bytes and read it into content
            contents = file.read()
        dec_data = open("decrypted_data.txt", "w")  # open decrypted data file for writing

        en2 = Encryption(contents, "password")  # create encryption instance using data = contents

        dec_data.write(en2.decrypt())  # write to the file

        dec_data.close()
        print("Your file " + file_data.name + " has been decrypted and can be viewed")

    def connect_command(self):
        ip_and_port = self.entry.get()
        x = ip_and_port.split(",")
        ip = str(x[0])
        port = int(x[1])
        self.ft.connect(ip, port)
        return

    #def requests(self):
     #   x, y = self.ft.check_for_request()
      #  if x == ft_conn.FTProto.REQ_FILE:
            #TODO y is file name, send to other computer
       # if x == ft_conn.FTProto.REQ_LIST:

        #TODO last thing, call self.root.after()

root = Tk()
app = Application(master=root)
app.mainloop()
