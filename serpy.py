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
import warnings
#from weakref import finalize
from base64 import b85encode, b85decode
from time import sleep

STIMEOUT = 0.050

class Connection:
    """
    Handles the connection over a TCP/IP socket and grants some tools.
    
    This object can either 'inherit' an existing connected socket or 
    create its own via the connect method.
    
    ------
    Usage:
     - To create a Connection with socket inheritance :
        >>> c = Connection(sock=socket, encoding=encoding)
        >>> c.start()
    
     - To create a Connection and connect it:
        >>> c = Connection(encoding, auto_restart).connect(adr, port)
    """
    def __init__(self, sock=None, encoding='ascii', auto_restart=False):
        self.conn = sock
        self.encoding = encoding
        self.auto_restart = auto_restart
        self.connected = sock != None
        self.in_q = queue.Queue(10)
        self.out_q = queue.Queue(10)
        self.block_q = queue.Queue(10)
        self.out_block_q = queue.Queue(10)
        self.stop_sig = False
        self.in_mode = 0
        self.out_mode = 0
        self.ackEvent = threading.Event()
        self.modeChangeEvent = threading.Event()
        self.adr = 0

    def connect(self, adr, port):
        """
        Connects this Connection to a remote socket at adr (adress) and
        port then start the connection by calling self.start().
        If the Connection was already connected, this method will first
        close this connection (socket)
        

        """
        self.adr = (adr, port)
        if self.connected:
            #warnings.warn("Already connected !! -> Closing connection")
            self.conn.close()
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(self.adr)
        self.connected = True
        self.start()
        return self

    def start(self):
        """Start the connection (start the threads)"""
        self.stop_sig = False
        threadSet = set()
        threadSet.add(threading.Thread(target=self._inThread))
        threadSet.add(threading.Thread(target=self._outThread))
        threadSet.add(threading.Thread(target=self._listeningCenterThread))
        threadSet.add(threading.Thread(target=self._speechCenterThread))
        for t in threadSet:
            t.start()
        self.threadSet = threadSet

    def close(self):
        """Stop the threads and closes the connection (socket)"""
        self.stop_sig = True
        for t in self.threadSet:
            t.join()
        self.conn.close()
        self.connected = False

    def _brokenConnection(self):
        """ 
        This method will start the _brokenConnHandler thread so that
        others thread may continue running and stoping.
        """
        if self.adr: pass
            #warnings.warn("Connection to {} broken !".format(self.adr))
        self.connected = False
        self.stop_sig = True
        threading.Thread(target=self._brokenConnHandler).start()

    def _brokenConnHandler(self):
        """
        Handles broken connections and tries to restart it if auto
        restart is enabled.
        """
        if self.auto_restart :
            #warnings.warn("Attempting connection restart")
            self.close()
            self.connect(*self.adr)
            #warnings.warn("finished")
        else :
            #warnings.warn("Closing connection")
            self.close()
        exit()
            
        
    def _outThread(self):
        """
        Get blocks when available and sends them
        """
        while not self.stop_sig:
            readable, writable, errored = select.select([], (self.conn,), [], STIMEOUT)
            for s in writable:
                if not self.out_block_q.empty():
                    s.sendall(self.out_block_q.get()+b'\x1F')
                else :
                    sleep(STIMEOUT)
        exit()
                
    def _inThread(self):
        """
        This thread listens on the connection and retieves any data that
        is sent on the socket. Then it assemble the data into 
        intelligible message named block. Those blocks are delimited by
        the Unit Separator character.
        Blocks are then put into the block_q to be processed by the 
        _listeningCenterThread.
        """
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
        exit()
        
    def _listeningCenterThread(self):
        """
        This thread controls the Input of this connection. It interprets 
        the data received (eg: commands). It partialy implements the 
        internal communication protocol.
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
        exit()
                    
            
    def _speechCenterThread(self):
        """
        This thread controls the Output of this connection. It partialy
        implements the internal communication protocol.
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
        exit()
                
    
    def getData(self, timeout=None):
        """
        Returns the received data in bytes
        Optional argument : timeout (default None)
        
        Will block until there is data or timeout is reached.
        On timeout will raise queue.Empty exception
        """
        return self.in_q.get(timeout=timeout)
    
    def sendData(self, data, mode=0, timeout=None):
        """
        Send the data over this connection following a mode.
        
        Optional timeout (in seconds [float]) may be specified. 
        May block for a maximum of 2*timeout.
        May raise raise queue.Full exception or return False on timeout
        ------
        mode 0 : send data, non-blocking
        mode 1 : send data, will block until acknoledgment or timeout
        mode 2 : similar to mode 0 but the data is encoded in base 85
        
        The mode will automatically switch to 2 if the datatype is bytes
        (to ensure control characters are not met)
        ------
        This method will convert some data types:
         - float OR int --> str
         - str --> bytes (following self.encoding)
        """
        if type(data) == float or type(data) == int:
            data = str(data)
        elif type(data) == bytes:
            mode = 2
        
        if type(data) == str:
            data = data.encode(self.encoding)
        
        if mode == 2:
            data = b85encode(data)
        
        if mode == 0 or mode == 2:
            self.out_q.put((data, mode), timeout=timeout)
            return
        
        elif mode == 1:
            self.ackEvent.clear()
            self.out_q.put((data, mode), timeout=timeout)
            return self.ackEvent.wait(timeout=timeout) #returns True if no timeout, else False
        
        return

    def enableRestart(self):
        """Enable auto restart when the connection is broken"""
        self.auto_restart = True
    
    def disableRestart(self):
        """Disable auto restart when the connection is broken"""
        self.auto_restart = False
    
    def isConnected(self):
        """Returns True if connected."""
        return self.connected
    
    def isDataAvailable(self):
        """
        Return True if there is new data available 
        (ie: in the input queue)
        """
        return not self.in_q.empty()




class Server:
    """
    A server that will accept connections making Connection objects.
    
    It creates a socket (socket.AF_INET, socket.SOCK_STREAM) on a given
    adress and port that will listen and accept connections. Each new
    socket is passed to a Connection object which is then started.
    The server remembers all Connection object it has created in a list.
    The server can accept at most nb_conn (default 5) concurent 
    connections.
    
    Usage :
     - To create a server:
        >>> s = Server(adr, port, nb_conn, encoding).start()
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

    def _serverThread(self):
        while not self.stop_sig:
            readable, writable, errored = select.select((self.serv,), [], [], STIMEOUT)
            for s in readable :
                conn, adr = s.accept()
                #warnings.warn("Connection to ", adr, " accepted")
                c = Connection(sock=conn, encoding=self.encoding)
                c.start()
                self.connections.append(c)
                self.newConn.put(c)
            for c in self.connections: #clear disconected connections
                if not c.connected:
                    self.connections.remove(c)
        exit()
    
    def start(self):
        """
        Start the server thread. Returns self (ie: the Server object)
        """
        self.tSer = threading.Thread(target=self._serverThread)
        self.tSer.start()
        return self
    
    def close(self):
        """
        Closes the server only. Its connections remain functionning.
        One can still get the connection list afterward.
        """
        self.stop_sig = True
        self.tSer.join()
        for c in self.connections :
            c.close()
        self.serv.close()
        
    def getConnection(self):
        """
        Gets a Connection object from new connections queue. This method
        will block if there is no new connection.
        """
        return self.newConn.get()

    def getConnectionsList(self):
        """
        Returns the list of all the Connection objects created by the 
        server.
        """
        return self.connections[:]
        
    def closeServer(self):
        """
        Closes the server and all of its connections
        """
        for c in self.connections:
            c.close()
        self.close()
        
    def readableConnections(self):
        """
        Returns the list of the child Connection objects which have data
        available to be read.
        """
        return [c for c in self.connections if c.isDataAvailable()]

def main(args):
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
