from cgitb import text
from codecs import ascii_encode
from concurrent.futures import thread
import zmq
from constCS import * #-
import tkinter as tk
import threading
import queue as q
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tokenize import String
from xml.etree.ElementTree import tostring

class TxtMsg:
    def __init__(self, index, message):
        self.index = index
        self.message = message
    def toString(self):
        return "Index: " + self.index + "\nMessage: " + chr(self.message) + "\n"
    def cmp(self, otherTxt):
        return ((self.index == otherTxt.index) & (self.message == otherTxt.message))

localPubQueue = q.Queue() 
localRecvQueue = q.Queue()
counter = 0

def recvApp(network_queue):
    context = zmq.Context()

    p1 = "tcp://"+ HOST +":"+ PORT1 # how and where to connect
    s  = context.socket(zmq.REP)    # create reply socket using zmq
    s.bind(p1)                      # bind socket to address
    while True:
        message = s.recv_pyobj()                     # wait for incoming message
        network_queue.put(message, True, 120)       # append message to the network_queue (queue) 
        s.send_string(f"[RECEIVED]{HOST} {PORT1}") 

def sendApp(network_queue):
    context = zmq.Context()

    p2 = "tcp://"+ HOST +":"+ PORT2 # how and where to connect
    s = context.socket(zmq.PUB)     

    s.bind(p2)

    while True:
        #read from queue, block until eternity, if queue has item, send item.
        message = network_queue.get(True)           #dequeue message from the queue if the queue is empty thread will block
        s.send_pyobj(message)                       #send the message got from the queue
        print(f"[SENDING message from queue (Publisher)...]")

def textApp(input_queue, output_queue):
    

    def open_file():
        """Open a file for editing."""
        
        txt_edit.delete(1.0, tk.END)
        file = open ("test.txt", "r")
        text = file.read()
        txt_edit.insert(tk.END, text)
        window.title(f"Team 24 Server- test.txt")

    def save_file():
        """Save the current file as a new file."""

        file = open ("test.txt", "w")
        text = txt_edit.get(1.0, tk.END)
        file.write(text)
        window.update()
        window.title(f"Team 24 Server- text.txt")

    def recv_input():
        
        if(input_queue.empty()):
            pass
        else:
            data = input_queue.get(False)
            output_queue.put(data)
            message = data.message
            print(message)
            myIndex = data.index
            save_file()
            
            if(message == 13):
                message = "\n"
                txt_edit.insert(myIndex, message)
                save_file()
            elif (message == 8):
                indList = myIndex.split(".") #3.9 ["3", "9"]
                fRow = indList[0] #"3"
                nRow = fRow
                fCol = str(int(int(indList[1])-1)) 
                #86.12  #86.13 
                # a        b
                nCol = indList[1]
                fIndex = fRow + "." + fCol
                nIndex = nRow + "." + nCol
                txt_edit.delete(fIndex, nIndex)
                save_file()
            else:
                message = chr(message)
                txt_edit.insert(myIndex, message)
                save_file()
            print(txt_edit.index(tk.INSERT))
        window.after(1, recv_input)
    

    window = tk.Tk()
    window.title("Team 24 Server")
    window.rowconfigure(0, minsize=800, weight=1)
    window.columnconfigure(1, minsize=800, weight=1)

    txt_edit = tk.Text(window, bg="#242424", fg="#FFFFFF", insertbackground="#CCCCCC")
    fr_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)

    btn_conn = tk.Button(fr_buttons, text="Start Server", command=open_file)

    btn_conn.grid(row=0, column=0, sticky="ew", padx=5)
    

    fr_buttons.grid(row=0, column=0, sticky="ns")
    txt_edit.grid(row=0, column=1, sticky="nsew")

    window.after(1, recv_input)

    window.mainloop()

textThread = threading.Thread(target=textApp, args=(localRecvQueue, localPubQueue,))
nRecvThread = threading.Thread(target=recvApp, args=(localRecvQueue,))
nSendThread = threading.Thread(target=sendApp, args=(localPubQueue,))

nRecvThread.start()
nSendThread.start()
textThread.start()