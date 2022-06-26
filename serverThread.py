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

nRecvThread = threading.Thread(target=recvApp, args=(localRecvQueue,))
nSendThread = threading.Thread(target=sendApp, args=(localPubQueue,))

nRecvThread.start()
nSendThread.start()