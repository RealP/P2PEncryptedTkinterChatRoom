import socket, select, string, sys, thread
import hashlib, getpass, datetime, re
try:
    from Tkinter import *  
except:
    from tkinter import *
import bz2, base64
## Needed for the encyption
from Crypto.Cipher import AES
## somethings wrong when the KEY IS 256bytes so im hasing it into a 256 byte string
MASTER_KEY=hashlib.sha256("Some-long-base-key-to-use-as-encyrption-key").digest()
## Keep a reference of the old stdout
old_f = sys.stdout
## Monkey Patch stdout so the 
#  print statement has the timestamp appended to it
class F:
    ## Function that gets called when you call print to stdout
    # @param self A reference to a our new stdout
    # @param x The message you sent to print statement
    def write(self, x):
        old_f.write(x.replace("\n", " [%s]\n" % str(datetime.datetime.now())))
sys.stdout = F()

## Function that encrypts your string. it doesnt compress it since i had errors decompressing 
# @param clear_text The unencypted text that you want to encrypt
# @param key The key you want to encrypt the clear text with
def zip_and_encrypt_val(clear_text, key):
    # clear_text = bz2.compress(clear_text)
    enc_secret = AES.new(key[:32])
    tag_string = (str(clear_text) +
                  (AES.block_size -
                   len(str(clear_text)) % AES.block_size) * "\0")
    cipher_text = base64.b64encode(enc_secret.encrypt(tag_string))
    return cipher_text

## Function that decrypts an encypted string. it doesnt decompress it.. caused errors 
# @param clear_text The unencypted text that you want to encrypt
# @param key The key you want to encrypt the clear text with
def decrypt_val_and_unzip(cipher_text, key):
    dec_secret = AES.new(key[:32])
    cipher_text += "=" * ((4 - len(cipher_text) % 4) % 4)
    raw_decrypted = dec_secret.decrypt(base64.b64decode(cipher_text))
    clear_val = raw_decrypted.rstrip("\0")
    # clear_val = bz2.decompress(clear_val)
    return clear_val

## The Main class has all the methods used by the gui 
#
class ChatClientGUI(Frame):
    def __init__(self):
        ## The root instance starts the tkinter main thread?
        self.root = Tk()
        self.root.geometry("410x570")
        self.root.title("Chat Program")
        # self.root.resizable(width=False, height=False)
        self.root.configure(background='gray')
        Frame.__init__(self, self.root)
        ## Im not too sure why i do this all I know is now you use frame where people say to use root
        self.frame = Frame(self.root)
        self.frame.grid()
        self.frame.configure(background="gray")
        self.grid()
        ## The key is set to the master key... lots of redunancy here that can be sorted out
        self.key = MASTER_KEY
        self.broadcastmode=1
        self.chatRoomWindowInit()
        self.chatRoomTextBoxInit()
        self.sendButtonInit()
        self.encryptionKeyInit()
        self.iconInit()
        self.connectToServer()

    ## Creates the textbox that the messages go into
    def chatRoomWindowInit(self):
        ## textbox for incoming messages
        self.result_text = Text(self.frame, height=25, width=48, font=('Arial', 12), bg="white")
        self.result_text.configure(state=DISABLED)
        self.result_text.grid(row=0, column=0, padx=(5,5), pady=(5,5), columnspan=1)

    ## Create the entry widget that user types messages into
    def chatRoomTextBoxInit(self):
        ## some tkinter string var that hold the message the user is typing
        # access it by using .get()
        self.msg = StringVar() 
        self.entry_box = Entry(self.frame, width=48, font=('Times', 12), bg="white", textvariable=self.msg)
        self.entry_box.grid(row=1, column=0, sticky=W, padx=(5,5), pady=(0,10), columnspan=1)
        self.entry_box.bind('<Return>', self.processSendButton)
        self.entry_box.focus_set()

    ## Creates the send button that sends the message
    #  The meesage is also binded to send with the pressing of the return key
    def sendButtonInit(self):
        self.goButton = Button(self.frame, text="Send", command=self.processSendButton)
        #NOT WORKING FOR SOME REASON
        # self.goButton.configure(bg='gray', fg='blue')
        self.goButton.grid(row=2, column=0, columnspan=1, padx=(5,5), pady=(0,0), sticky=E+W)

    ## Create the entry widget that user types their encryption key into
    def encryptionKeyInit(self):
        self.keyLabel = Label(self.frame, text="Key", font=('Arial', 14),  bg='gray')
        self.keyLabel.grid(row=3, column=0, sticky=W, padx=(0,0))
        
        self.encryptionKey = StringVar()
        self.encryptionKeyBox = Entry(self.frame, width=30, bg='white', font=('Arial', 12), textvariable=self.encryptionKey)
        self.encryptionKeyBox.grid(row=3, column=0, padx=(5,5), pady=(10,10), columnspan=1)

        self.setKeyButton = Button(self.frame, text="Set", command=lambda: self.setKey(self.encryptionKey))
        self.setKeyButton.grid(row=3, column=0, sticky=E)
    def iconInit(self):
        self.unlockImage = PhotoImage(file="unlock.gif")
        self.lockImage   = PhotoImage(file="lock.gif")
        self.imageLabel  = Label(self.frame, image = self.unlockImage)
        self.imageLabel.grid(row=4, column=0, sticky=W)

    ## Searches text box for the regex provided and highlight all matches to have blue text 
    # We can end up using this for more than just highlighting the user messages. We can make
    # search box... etc 
    # @param args The regular expression you wish to search for... 
    def highlight(self, args):
        idx = '1.0'
        self.result_text.tag_remove('found', '1.0', END)
        print END
        if args=="":
            return
        while 1:
            ## find next occurrence, exit loop if no more
            idx = self.result_text.search(args, idx, nocase=1, stopindex=END, regexp=True)
            if not idx: break
            ## lastindex is the endofline after the idx occurrence
            lastidx = str(idx) + "lineend"
            ## tag the whole occurrence (start included, stop excluded)
            self.result_text.tag_add('found', idx, lastidx)
            ## prepare to search for next occurrence
            idx = lastidx
        ## use a blueforeground for all the tagged occurrences
        self.result_text.tag_config('found', foreground='blue')
    
    ## Set the users secret key, change image based on key, 
    # @param secretKey The secret key chosen by user
    def setKey(self, secretKey):
        if (secretKey.get() == "broadcast"):
            self.broadcastmode = 1
            self.imageLabel.configure(image=self.unlockImage)
        else:
            self.broadcastmode = 0
            self.imageLabel.configure(image=self.lockImage)
        self.key=hashlib.sha256(secretKey.get()).digest()
        self.encryptionKeyBox.delete(0, END)

    def connectToServer(self):
        if(len(sys.argv) < 3) :
            print 'Usage : python chat_client.py hostname port'
            sys.exit()
        host = sys.argv[1]
        port = int(sys.argv[2])

        ## client socket is an object from the socket class that can recieve data over the web
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
    
    ## This is where the magic happens a thread reads from the specified port constantly if there
    #  is data it continues by processing it, (decrypt, strip padding, catch errors
    #  The danger here is I am modifying the app from a thread that is not the main thread. This
    #  is supposed to not work since tkinter isn't thread safe but no problems yet 
    # @param clientSocket An instance on the socket (NOT USED since its global....)
    # @param host The host address (Also not used.. we can get rid of these)
    def getMessageThread(self, clientSocket, host):
        data = ""
        while 1:
            try:
              data = self.clientSocket.recv(4096)
              if not data:
                  break
              self.result_text.configure(state=NORMAL)
              if self.broadcastmode == 0:
                  print "compressed cipher text = ", data
                  data = decrypt_val_and_unzip(data, self.key)
                  print "uncompressed cipher text = ", data
              try:
                  data.decode('ascii')
              except UnicodeDecodeError:
                  print "it was not a ascii-encoded unicode string"
                  pass
              else:
                  if (data.rstrip()[-1] == "~"):
                    data = data.rstrip()[:-1] + "\r"
                  if (re.search("\[.*\].*", data) or ":(" in data):
                      self.result_text.insert("end",data)
                      self.result_text.yview(END)
                  else:
                    print "Data not in proper format data ", data               
            except KeyboardInterrupt:
                break     
            except socket.timeout:
                pass
            except TypeError: # Text is not encrypted
                print "Done: Text Not Encrypted"
                if (data.rstrip()[-1] == "~"):
                    data = data.rstrip()[:-1] + "\r"
                self.result_text.insert("end",data)
                self.result_text.yview(END)
            except ValueError: # Text is not encrypted
                print "Error on the deciphering of text"
                if (data.rstrip()[-1] == "~"):
                  data = data.rstrip()[:-1] + "\r"
                self.result_text.insert("end",data)
                self.result_text.yview(END)
            except:
                break

            # self.result_text.configure(state=DISABLED)
        print "Disconnected from server"
    
    ## Gets called on enter press or send button
    # This is where we decide to compress the cmds sent to server
    def processSendButton(self, *args):
        # encrypts all messages without colon 
        if ":" not in self.msg.get():
            message = self.msg.get()
            if (len(message) % 2 != 0):
                message += "~"
            if self.broadcastmode == 1:
                message = "["+ str(getpass.getuser()) + "] " + message + "\n"            
                print "Your in broadcast mode so not encrypting message --> ", message
            else:
                print "encrypting message -->", "["+ str(getpass.getuser()) + "] " + message
                message = zip_and_encrypt_val("["+ str(getpass.getuser()) + "] " + message + "\n", self.key)
        else:
            message = "["+ str(getpass.getuser()) + "] " + self.msg.get() + "\n"
        
        ##Provides the needed self feedback
        self.result_text.configure(state=NORMAL)
        self.result_text.insert("end", "[You] " + self.msg.get() + "\n")
        self.highlight(r"\[You\].*")
        self.result_text.yview(END)
        # self.result_text.configure(state=DISABLED)
        self.clientSocket.send(message)
        self.entry_box.delete(0, END)

    ## Just a way of starting the main loop inside the class
    #  I think this little hack allows us to modify from non-main threads 
    # @param self Instance of class
    def start(self):
        self.root.mainloop()

def main():
    ChatClientGUI().start()

if __name__ == '__main__':
    main()

