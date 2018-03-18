from tkinter import *
from tkinter import filedialog
import Encryption as en

class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.encrypt = Button(self)
        self.encrypt["text"] = "Encrypt file to export"
        self.encrypt["command"] = self.encryptfile
        self.encrypt.pack(side="left")

        self.decrypt = Button(self)
        self.decrypt ["text"] = "Decrypt a chosen file"
        self.decrypt ["command"] = self.decryptfile
        self.decrypt.pack(side="right")

        self.quit = Button(self, text="QUIT", fg="red",
                              command=root.destroy)
        self.quit.pack(side="bottom")

    def encryptfile(self):
        fileName = filedialog.askopenfilename(filetypes = (("HTML files", "*.html;*.htm"),("All files", "*.*")))
        en.encrypt(fileName)
        print("Your file " + fileName +" has been encrypted and can be sent")

    def decryptfile(self):
        fileName = filedialog.askopenfilename(filetypes=(("HTML files", "*.html;*.htm"), ("All files", "*.*")))
        en.decrypt(fileName)
        print("Your file " + fileName + " has been decrypted and can be viewed")
root = Tk()
app = Application(master=root)
app.mainloop()
