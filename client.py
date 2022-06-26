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
nSendThread = threading.Thread(target=sendApp, args=(localPushQueue, localStorageQueue,))
nRecvThread = threading.Thread(target=recvApp, args=(localIntakeQueue, localStorageQueue,))

nSendThread.start()
nRecvThread.start()