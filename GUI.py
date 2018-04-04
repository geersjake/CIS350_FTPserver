from tkinter import *
from tkinter import filedialog
import encryption


class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        # For the text box to input IP Address
        e = Entry(self)
        e.pack()
        e.delete(0, END)

        # Encryption Button
        self.encrypt = Button(self)
        self.encrypt["text"] = "Encrypt file to export"
        self.encrypt["command"] = self.encryptfile
        self.encrypt.pack(side="left")

        # Decryption Button
        self.decrypt = Button(self)
        self.decrypt["text"] = "Decrypt a chosen file"
        self.decrypt["command"] = self.decryptfile
        self.decrypt.pack(side="right")

        # Quit Program
        self.quit = Button(self, text="QUIT", fg="red",command=root.destroy)
        self.quit.pack(side="bottom")

    def encryptfile(self):
        filename = filedialog.askopenfilename(filetypes=(("HTML files", "*.html;*.htm"), ("All files", "*.*")))
        encryption.Encryption.encrypt(filename)
        print("Your file " + filename + " has been encrypted and can be sent")

    def decryptfile(self):
        filename = filedialog.askopenfilename(filetypes=(("HTML files", "*.html;*.htm"), ("All files", "*.*")))
        encryption.Encryption.decrypt(filename)
        print("Your file " + filename + " has been decrypted and can be viewed")


root = Tk()
app = Application(master=root)
app.mainloop()
