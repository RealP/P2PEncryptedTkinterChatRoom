import socket, select, string, sys, thread
import hashlib, getpass, datetime
try:
    from Tkinter import *  
except:
    from tkinter import *
import bz2, base64
from Crypto.Cipher import AES
########## somethings wrong when the message number of characters!!!
MASTER_KEY=hashlib.sha256("Some-long-base-key-to-use-as-encyrption-key").digest()
#Monkey Patch Print Statement
old_f = sys.stdout
class F:
    def write(self, x):
        old_f.write(x.replace("\n", " [%s]\n" % str(datetime.datetime.now())))
sys.stdout = F()

def zip_and_encrypt_val(clear_text, key):
    # clear_text = bz2.compress(clear_text)
    enc_secret = AES.new(key[:32])
    tag_string = (str(clear_text) +
                  (AES.block_size -
                   len(str(clear_text)) % AES.block_size) * "\0")
    cipher_text = base64.b64encode(enc_secret.encrypt(tag_string))
    return cipher_text
def decrypt_val_and_unzip(cipher_text, key):
    print "Staring decryption"
    dec_secret = AES.new(key[:32])
    # cipher_text += "=" * ((4 - len(cipher_text) % 4) % 4)
    raw_decrypted = dec_secret.decrypt(base64.b64decode(cipher_text))
    clear_val = raw_decrypted.rstrip("\0")
    # clear_val = bz2.decompress(clear_val)
    print "Done decryption"
    return clear_val

class ChatClientGUI(Frame):
    def __init__(self):
        self.root = Tk()
        self.root.geometry("310x470")
        self.root.title("Chat Program")
        self.root.resizable(width=False, height=False)
        self.root.configure(background='gray')
        Frame.__init__(self, self.root)
        self.frame = Frame(self.root)
        self.frame.grid()
        self.frame.configure(background="gray")
        self.grid()
        self.key = MASTER_KEY
        self.chatRoomWindowInit()
        self.chatRoomTextBoxInit()
        self.sendButtonInit()
        self.encryptionKeyInit()
        self.connectToServer()

    def chatRoomWindowInit(self):
        self.result_text = Text(self.frame, height=25, width=48, font=('Arial', 12), bg="white")
        self.result_text.configure(state=DISABLED)
        self.result_text.grid(row=0, column=0, padx=(5,5), pady=(5,5), columnspan=1)

    def chatRoomTextBoxInit(self):
        self.msg = StringVar() 
        self.entry_box = Entry(self.frame, width=48, font=('Times', 12), bg="white", textvariable=self.msg)
        self.entry_box.grid(row=1, column=0, sticky=W, padx=(5,5), pady=(0,10), columnspan=1)
        self.entry_box.bind('<Return>', self.processSendButton)
        self.entry_box.focus_set()

    def sendButtonInit(self):
        self.goButton = Button(self.frame, text="Send", command=self.processSendButton)
        #NOT WORKING FOR SOME REASON
        # self.goButton.configure(bg='gray', fg='blue')
        self.goButton.grid(row=2, column=0, columnspan=1, padx=(5,5), pady=(0,0), sticky=E+W)

    def encryptionKeyInit(self):
        self.keyLabel = Label(self.frame, text="Key", font=('Arial', 14),  bg='gray')
        self.keyLabel.grid(row=3, column=0, sticky=W, padx=(0,0))
        
        self.encryptionKey = StringVar()
        self.encryptionKeyBox = Entry(self.frame, width=30, bg='white', font=('Arial', 12), textvariable=self.encryptionKey)
        self.encryptionKeyBox.grid(row=3, column=0, padx=(5,5), pady=(10,10), columnspan=1)

        self.setKeyButton = Button(self.frame, text="Set", command=lambda: self.setKey(self.encryptionKey))
        self.setKeyButton.grid(row=3, column=0, sticky=E)

    def setKey(self, secretKey):
        self.key=hashlib.sha256(secretKey.get()).digest()
        self.encryptionKeyBox.delete(0, END)
        print self.key

    def connectToServer(self):
        if(len(sys.argv) < 3) :
            print 'Usage : python chat_client.py hostname port'
            sys.exit()
        host = sys.argv[1]
        port = int(sys.argv[2])

        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSocket.settimeout(2)
        # connect to remote host
        try :
            self.clientSocket.connect((host, port))
        except :
            print 'Unable to connect'
            sys.exit()
        print 'Connected to remote host. You can start sending messages'
        thread.start_new_thread(self.getMessageThread, (self.clientSocket, host))

    def getMessageThread(self, clientSocket, host):
        data = ""
        while 1:
            try:
              data = self.clientSocket.recv(4096)
              if not data:
                  break
              self.result_text.configure(state=NORMAL)
              print "compressed cipher text = ", data
              data = decrypt_val_and_unzip(data, self.key)
              print "uncompressed cipher text = ", data
              try:
                  data.decode('ascii')
              except UnicodeDecodeError:
                  print "it was not a ascii-encoded unicode string"
                  pass
              else:
                  print "It may have been an ascii-encoded unicode string"
                  if (data.rstrip()[-1] == "~"):
                    print "Got padding msg"
                    data = data.rstrip()[:-1] + "\r"
                  self.result_text.insert("end",data)
            except KeyboardInterrupt:
                break     
            except socket.timeout:
                pass
            except TypeError: # Text is not encrypted
                print "Done: Text Not Encrypted"
                self.result_text.insert("end",data)
            # except ValueError: # Text is not encrypted
            #     print "Error on the decompression of cipher text"
            self.result_text.configure(state=DISABLED)
        print "Disconnected from server"

    def processSendButton(self, *args):
        ## Dont compress cmds sent to server
        ## encrypt all messages without colon
        if ":" not in self.msg.get():
            message = self.msg.get()
            if (len(message) % 2 != 0):
                message += "~" 
            message = zip_and_encrypt_val("["+ str(getpass.getuser()) + "] " + message + "\n", self.key)
        else:
            message = self.msg.get() + "\n"
        self.clientSocket.send(message)
        self.entry_box.delete(0, END)

    def start(self):
        self.root.mainloop()

def main():
    ChatClientGUI().start()

if __name__ == '__main__':
    main()

