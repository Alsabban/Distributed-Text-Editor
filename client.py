from codecs import ascii_encode
from multiprocessing import context
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

localIntakeQueue = q.Queue()
localPushQueue = q.Queue()
localStorageQueue = q.Queue()

def recvApp(network_queue, store_queue):
    context = zmq.Context()

    p2 = "tcp://"+ HOST +":"+ PORT2 # how and where to connect
    s  = context.socket(zmq.SUB)    # create reply socket

    s.connect(p2)                      # bind socket to address 
    s.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        message = s.recv_pyobj()            # wait for incoming message
        if(not store_queue.empty()):
            storeMsg = store_queue.get(False) #get the value in the queue without blocking the thread
            print("[RECEIVED MESSAGE]"+"\n" + message.toString() + "\n" + storeMsg.toString())

            if(storeMsg.cmp(message)):
                pass                    #if i am the sender the client must not write into his own text again
            else:
                network_queue.put(message, True, 120) #put the message in the intake queue  
                store_queue.queue.insert(0, storeMsg) #put the message again in the queue
        else:
            network_queue.put(message, True, 120)

def sendApp(network_queue, store_queue):
    context = zmq.Context()

    p1 = "tcp://"+ HOST +":"+ PORT1 # how and where to connect
    s  = context.socket(zmq.REQ)    # create request socket

    s.connect(p1)
    while True:
        
        dataToSend = network_queue.get(True) #get the the message in the queue and it will block if the queue is empty
        if(dataToSend):
            store_queue.put(dataToSend) #put the gotten mesasge in the store queue
            print(f"[SENDING...] on port {PORT1}")
            s.send_pyobj(dataToSend) #send it to the server 
            s.recv_string()
        else :
            print("[FAILURE]")

def textApp(input_queue, output_queue):
    #This socket is used for the "connect" method
    context = zmq.Context()
    p3 = "tcp://" + HOST + ":" + PORT3
    s = context.socket(zmq.REQ)
        
    def connect():
        """Open a file for editing."""
        txt_edit.config(state=tk.NORMAL) #Enables the textbox in the GUI
        s.connect(p3)
        s.send_string("MSG") #Sends to the server on thid socket "MSG" to request the file data on the server
        text = s.recv_string() 
        txt_edit.insert(tk.END, text) #the file writes the text received from the user on the textbox

        

    def save_file():
        """Save the current file as a new file."""
        filepath = asksaveasfilename(
            defaultextension="txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        with open(filepath, "w") as output_file:
            text = txt_edit.get(1.0, tk.END)
            output_file.write(text)
            window.update()

    def recv_input():
        
        if(input_queue.empty()): #if there is no new data received
            pass
        else: 
            data = input_queue.get(False)
            message = data.message #take the message part of the received data and store in a variable
            print(message)
            myIndex = data.index #take the index part of the received data and store in a variable
            
            if(message == 13): #if the message part was the "enter" button
                message = "\n"
                txt_edit.insert(myIndex, message)
            elif (message == 8): #if the message part was the "backspace" button
                indList = myIndex.split(".") #3.9 ["3", "9"]
                fRow = indList[0] #"3"
                nRow = fRow
                fCol = str(int(int(indList[1])-1)) 
                #86.12  #86.13 
                # a        b
                nCol = indList[1]
                fIndex = fRow + "." + fCol #index of deleted letter
                nIndex = nRow + "." + nCol #the new index
                txt_edit.delete(fIndex, nIndex)
            else: #if the message is neither of the special characters
                message = chr(message)
                txt_edit.insert(myIndex, message)
        window.after(1, recv_input)

    def keydown(e): #on key event
        cord = ord(e.char) #take the character of the key pressed
        if (cord >= 0 & cord <= 127): #if it is an accepted key
            dataToSend = TxtMsg(txt_edit.index(tk.INSERT), cord) #create an object to send with the index and the character to be sent
            print (dataToSend.toString())
            output_queue.put(dataToSend, False) #put the object into the push queue to send through the sendApp thread


    window = tk.Tk()
    window.title("Team 24 Client")
    window.rowconfigure(0, minsize=800, weight=1)
    window.columnconfigure(1, minsize=800, weight=1)

    txt_edit = tk.Text(window, bg="#242424", fg="#FFFFFF", insertbackground="#CCCCCC")
    fr_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
    btn_open = tk.Button(fr_buttons, text="Connect", command=connect)
    btn_save = tk.Button(fr_buttons, text="Save As...", command=save_file)
    



    btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    btn_save.grid(row=1, column=0, sticky="ew", padx=5)
    

    fr_buttons.grid(row=0, column=0, sticky="ns")
    txt_edit.grid(row=0, column=1, sticky="nsew")

    
    txt_edit.bind("<KeyPress>", keydown)
    
    window.after(1, recv_input)
    
    window.mainloop()

textThread = threading.Thread(target=textApp, args=(localIntakeQueue, localPushQueue,))
nSendThread = threading.Thread(target=sendApp, args=(localPushQueue, localStorageQueue,))
nRecvThread = threading.Thread(target=recvApp, args=(localIntakeQueue, localStorageQueue,))

nSendThread.start()
nRecvThread.start()
textThread.start()