#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  serpy.py
#  
#  Copyright 2018 Arthur Luciani <arthur@arthur-X550JD>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import socket
import threading
import queue
import select
#from weakref import finalize
from base64 import b85encode, b85decode
from time import sleep

STIMEOUT = 0.050

class Connection:
    """
    pass
    """
    def __init__(self, sock=None, encoding='ascii', auto_restart=False):
        self.conn = sock
        self.encoding = encoding
        self.auto_restart = auto_restart
        self.connected = sock != None
        self.in_q = queue.Queue(10)
        self.out_q = queue.Queue(10)
        self.block_q = queue.Queue(64)
        self.out_block_q = queue.Queue(64)
        self.stop_sig = False
        self.in_mode = 0
        self.out_mode = 0
        self.ackEvent = threading.Event()
        self.modeChangeEvent = threading.Event()
        self.adr = 0

    def connect(self, adr, port):
        self.adr = (adr, port)
        if self.connected:
            Warning("Already connected !! -> Closing connection")
            self.conn.close()
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(self.adr)
        self.connected = True
        self.start()
        return self

    def start(self):
        self.stop_sig = False
        threadSet = set()
        threadSet.add(threading.Thread(target=self.inThread))
        threadSet.add(threading.Thread(target=self.outThread))
        threadSet.add(threading.Thread(target=self.listeningCenterThread))
        threadSet.add(threading.Thread(target=self.speechCenterThread))
        for t in threadSet:
            t.start()
        self.threadSet = threadSet

    def close(self):
        self.stop_sig = True
        for t in self.threadSet:
            t.join()
        self.conn.close()
        self.connected = False

    def _brokenConnection(self):
        if self.adr:
            Warning("Connection to {} broken !".format(self.adr))
        self.connected = False
        self.stop_sig = True
        threading.Thread(target=self._brokenConnHandler).start()

    def _brokenConnHandler(self):
        if self.auto_restart :
            print("Attempting connection restart")
            self.close()
            self.connect(*self.adr)
            print("finished")
        else :
            Warning("Closing connection")
            self.close()
        exit()
            
        
    def outThread(self):
        while not self.stop_sig:
            readable, writable, errored = select.select([], (self.conn,), [], STIMEOUT)
            for s in writable:
                if not self.out_block_q.empty():
                    s.sendall(self.out_block_q.get()+b'\x1F')
                else :
                    sleep(STIMEOUT)
        #print("closing : outThread")
        exit()
                
    def inThread(self):
        data = bytes()
        while not self.stop_sig:
            readable, writable, errored = select.select((self.conn,), [], (self.conn,), STIMEOUT)
            if errored :
                self._brokenConnection()
                continue
            
            for s in readable:
                if not self.block_q.full():
                    chunk = self.conn.recv(4096)
                    if chunk:
                        data += chunk
                    else :
                        self._brokenConnection()

            if b'\x1F' in data:
                *blocks, data = data.split(b'\x1F')
                for block in blocks:
                    if block :
                        self.block_q.put(block)
        #print("closing : inThread")
        exit()
        
    def listeningCenterThread(self):
        """
        This thread controls the Input of this connection. It interprets 
        the data received (eg: commands)
        """
        data = bytes()
        while not self.stop_sig:
            if not self.block_q.empty():
                block = self.block_q.get()
                if block.startswith(b'\x01'): # indicates internal communication
                    block = block.decode(self.encoding)[1:]
                    if block.startswith("SETMODE") :
                        self.in_mode = int(block[-1])
                        self.out_block_q.put(b"\x01ACKMODCG")
                        continue

                    elif block == "ACKEOT!!":
                        self.ackEvent.set()
                        continue
                    
                    elif block == "ACKMODCG":
                        self.modeChangeEvent.set()
                        continue
                
                if self.in_mode == 0:
                    self.in_q.put(block)
                
                elif self.in_mode == 1:
                    data += block
                    if b'\x04' in data:
                        message, data = data.split(b'\x04')
                        self.out_block_q.put(b"\x01ACKEOT!!")
                        self.in_q.put(message)
                    
                elif self.in_mode == 2: # for b85-encoded bytes
                    self.in_q.put(b85decode(block))
            else :
                sleep(STIMEOUT)
        #print("closing : listeningCenterThread")
        exit()
                    
            
    def speechCenterThread(self):
        """
        This thread controls the Output of this connection.
        """
        while not self.stop_sig:
            if not self.out_q.empty():
                block, mode = self.out_q.get()
                if mode != self.out_mode :
                    self.modeChangeEvent.clear()
                    self.out_block_q.put(b"\x01SETMODE" +
                                        str(mode).encode(self.encoding))
                    self.modeChangeEvent.wait()
                    self.out_mode = mode
                
                if mode == 0 or mode == 2:
                    self.out_block_q.put(block)
                
                elif mode == 1:
                    self.out_block_q.put(block+b'\x04')
            else :
                sleep(STIMEOUT)
        #print("closing : speechCenterThread")
        exit()
                
    
    def getData(self, timeout=None):
        return self.in_q.get(timeout=timeout)
    
    def sendData(self, data, mode=0, timeout=None):
        if type(data) == float or type(data) == int:
            data = str(data)
        elif type(data) == bytes:
            data = b85encode(data)
            mode = 2
        
        if type(data) == str:
            data = data.encode(self.encoding)
        
        if mode == 0 or mode == 2:
            self.out_q.put((data, mode), timeout=timeout)
            return
        
        elif mode == 1:
            self.ackEvent.clear()
            self.out_q.put((data, mode), timeout=timeout)
            return self.ackEvent.wait(timeout=timeout) #returns True if no timeout, else False
        
        return

    def enableRestart(self):
        self.auto_restart = True
    
    def disableRestart(self):
        self.auto_restart = False




class Server:
    """
    33
    """
    def __init__(self, adr, port, nb_conn=5, encoding='ascii'):
        self.adr = adr
        self.port = port
        self.nb_conn = nb_conn
        self.encoding = encoding
        self.lock = threading.Lock()
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serv.bind((adr,port))
        self.serv.listen(nb_conn)
        self.connections = []
        self.newConn = queue.Queue(nb_conn)
        self.stop_sig = False

    def serverThread(self):
        while not self.stop_sig:
            readable, writable, errored = select.select((self.serv,), [], [], STIMEOUT)
            for s in readable :
                conn, adr = s.accept()
                print("Connection to ", adr, " accepted")
                c = Connection(sock=conn, encoding=self.encoding)
                c.start()
                self.connections.append(c)
                self.newConn.put(c)
        exit()
    
    def start(self):
        self.tSer = threading.Thread(target=self.serverThread)
        self.tSer.start()
        return self
    
    def close(self):
        self.stop_sig = True
        self.tSer.join()
        for c in self.connections :
            c.close()
        self.serv.close()
        
    def getConnection(self):
        return self.newConn.get()

    def getConnectionsList(self):
        return self.connections[:]
        
    def closeServer(self):
        for c in self.connections:
            c.close()
        self.close()

def main(args):
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
