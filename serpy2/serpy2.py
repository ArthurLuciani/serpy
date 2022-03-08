#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  serpy2.py
#  
#      serpy with a new protocol (not compatible with original protocol)
#
#
#  Copyright 2018 Arthur Luciani <arthur@arthur-X550JD>
#  Further work by M. H. V. Werts (mhvwerts@github), 2022
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
#
#  UNDER DEVELOPMENT
#  This code is in a beta-version state. It contains many assert statements
#  to ensure that situations that should not occur actually do not occur.
#  Use at your own risk for the good of mankind.
#   
#TODO
#   - further check robustness of code against transmission errors /
#     disconnection/reconnection incidents
#   - stress test (server + several clients)
#   - final clean up of initial version
#   - data transfer performance tweaking
#   - better handling of really big blobs[^1]?
#
# [^1]: blob = binary large object


import socket
import threading
import queue
import select
from time import sleep
import warnings



STIMEOUT = 0.010 # This delay (in seconds) limits the rate with which new
                 # blocks are sent/received/processed. Reducing it further
                 # may speed up the rate of blocks sent/recvd, but will
                 # likely increase processor usage. It is not clear if there is
                 # a lower limit. 
                 # 
                 #
#STIMEOUT = 2.0   # SLOW DEBUGGING MODE 

QUEUELEN = 20

BLOCKIDCODE = b'\xDE\xCA\xFE\xCA\xFE'
INTTYPECODE = b'\x01'
FLOATTYPECODE = b'\x11'
STRTYPECODE = b'\x21'
RAWBYTESTYPECODE = b'\x81'
HEADLEN = 14 # calculated by hand (5 + 1 + 4 + 4 bytes)



class Connection:
    """
    Handles the connection over a TCP/IP socket and provides some tools.
    
    This object can either 'inherit' an existing connected socket or 
    create its own via the connect method.
    
    ------
    Usage:
     - To create a Connection with socket inheritance :
        >>> c = Connection(sock=socket)
        >>> c.start()
    
     - To create a Connection and connect it:
        >>> c = Connection(auto_restart).connect(adr, port)
    """
    def __init__(self, sock=None, auto_restart=False):
        self.conn = sock
        self.auto_restart = auto_restart
        self.connected = sock != None
        self.adr = 0
        self.in_q = queue.Queue(QUEUELEN)
        self.out_q = queue.Queue(QUEUELEN)
        self.block_q = queue.Queue(QUEUELEN)
        self.out_block_q = queue.Queue(QUEUELEN)
        self.stop_sig = False
        self.ackEvent = threading.Event() 
    
    def __iter__(self):
        """
        Iterates over all available data. When data is read it cannot be
        read again (reading removes from storage)
        """
        try:
            while True:
                yield self.in_q.get(timeout=STIMEOUT)
        except queue.Empty:
            pass

    def connect(self, adr, port):
        """
        Connects this Connection to a remote socket at adr (address) and
        port then start the connection by calling self.start().
        If the Connection was already connected, this method will first
        close this connection (socket)
        """
        self.adr = (adr, port)
        if self.connected:
            warnings.warn("Already connected !! -> Closing connection")
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
        """Stop the threads and closes the connection (socket)
        
        #TODO: check if this requires the Connection to do further cleaning up:
        stop threads etc.
        """
        self.stop_sig = True
        self.ackEvent.set() #setting events to free the threads
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
            warnings.warn("Attempting connection restart")
            for i in range(1000):
                try:
                    self.close()
                    self.connect(*self.adr)
                except:
                    sleep(0.5) #TODO replace this magic number with a defined constant
                else:
                    break
            #warnings.warn("finished")
        else :
            #warnings.warn("Closing connection")
            self.close()

        
    def _outThread(self):
        """
        Get blocks when available and sends them
        """
        while not self.stop_sig:
            readable, writable, errored = select.select([], (self.conn,), [], STIMEOUT)
            assert len(writable) < 2,\
                "Unexpectedly have two connections to write to. I don't understand!"
            for s in writable:
                if not self.out_block_q.empty():
                    s.sendall(self.out_block_q.get())
                else :
                    sleep(STIMEOUT)
                
    def _inThread(self):
        """
        This thread listens on the connection and retrieves any data that
        is sent on the socket. Then it assembles the data into 
        intelligible messages named blocks.
        
        Blocks are then put into the block_q to be processed by the 
        _listeningCenterThread.
        """
        data = bytes()
        bdata = bytes()
        instate = 1 
        while not self.stop_sig:
            readable, writable, errored = select.select((self.conn,), [], (self.conn,), STIMEOUT)

            assert len(readable) < 2,\
                "Unexpectedly have several connections to read from. I don't understand! It will lead to problems reconstructing data blocks using present code."

            if errored :
                self._brokenConnection()
                continue
            
            for s in readable:
                if not self.block_q.full():
                    try:
                        chunk = self.conn.recv(4096)
                    except ConnectionResetError:
                        self._brokenConnection()
                    else:
                        if chunk:
                            data += chunk
                        else :
                            self._brokenConnection()
                            
            # A two-state machine handles the assembly of the blocks
            # from the incoming chunks of data.
            if instate == 1:
                # waiting for a fresh block
                # received data is expected to start with
                # BLOCKIDCODE
                if (len(data)>=HEADLEN) and data.startswith(BLOCKIDCODE):
                    # decode header                    
                    bheader = data[0:HEADLEN]
                    btype = bheader[5:6] #this gives a bytes object
                    checksum = int.from_bytes(bheader[6:10],
                                              'little', signed=False)
                    datalenb = int.from_bytes(bheader[10:14],
                                              'little', signed=False)
                    # prepare for state 2: receive block
                    bdata = bytes()
                    data = data[HEADLEN:]
                    instate = 2 # switch state
                else:
                    if (len(data) >= HEADLEN):
                        # In case the received data is not a header:
                        # Reset input buffer, and wait for new data.
                        #
                        # This should actually never happen. If it happens,
                        # we might need to do some kind of reset on the
                        # connection, and the reception queues
                        # 
                        #TODO Emit warning using warning.Warning
                        print('WARNING: Resetting chunk input buffer on Connection._inThread in serpy2.')
                        data = bytes() 
            
            # state machine can switch from state 1 to state 2 within same
            # cycle
            # since we have only two states, we can do this
            if instate == 2:
                # In the process of receiving a block...
                bdata_remaining = datalenb - len(bdata)
                if (len(data) > bdata_remaining):
                    # more incoming data than needed, split data
                    # just take what is needed
                    bdata += data[0:bdata_remaining] 

                    # Consistency check.
                    if len(bdata)!=datalenb:
                        print('len bdata = ',len(bdata))
                        print('bdata_remaining = ',bdata_remaining)
                        print('len data =',len(data))
                        print('datalenb =',datalenb)
                    assert len(bdata)==datalenb, 'Programmer Error. Incorrect length calculations.'

                    # and put the rest in updated databuffer
                    data = data[bdata_remaining:]
                else:
                    # Too little data or just enough data to fill block:
                    # Add all received data to block.
                    bdata += data
                    assert len(bdata)<=datalenb, 'Programmer error. Something wrong with data size calculations.'
                    data = bytes() # empty data input buffer

                if len(bdata) == datalenb:
                    # Full and complete block received!
                    # Check the checksum.
                    incoming_checksum = sum(bdata) & 0xFFFFFFFF
                    if incoming_checksum == checksum:
                        # Put block in received blocks queue.
                        # The block is here just the data preceded with one byte
                        # indicating the datatype.
                        # Rest of header is not used anymore.
                        block = btype + bdata
                        self.block_q.put(block)
                    else:
                        # Data error.
                        # How should we handle this correctly? 
                        #TODO
                        # For now, we print a warning and ignore, we do not
                        # put any information in the queue. Later, we could
                        # push a None or some ErrorType? which is then
                        # picked up in getData.
                        print('WARNING: Wrong checksum on incoming data.')
                    instate = 1

        
    def _listeningCenterThread(self):
        """
        This thread controls the Input of this connection. It interprets 
        the data received (decoding blocks). It partialy implements the 
        internal communication protocol.
        """
        while not self.stop_sig:
            # this while loop ensures fastest as possible processing
            # of incoming blocks
            while not self.block_q.empty():
                block = self.block_q.get()
                
                # decode block
                btype = block[0:1] # need bytes
                bdata = block[1:]
                
                if btype == FLOATTYPECODE:
                    data = float.fromhex(bdata.decode('ascii'))
                elif btype == INTTYPECODE:
                    data = int.from_bytes(bdata, 
                                          'little', signed = True)
                elif btype == STRTYPECODE:
                    data = bdata.decode('utf-8')
                elif btype == RAWBYTESTYPECODE:
                    data = bdata
                else:
                    raise TypeError("Received data of unsupported type")
                
                self.in_q.put(data)
            sleep(STIMEOUT)
                    
            
    def _speechCenterThread(self):
        """
        This thread controls the Output of this connection. It partialy
        implements the internal communication protocol.
        """
        while not self.stop_sig:
            # In contrast to _listeningCenterThread, which empties the
            # queue as fast as possbile, blocks are sent separated by 
            # at least STIMEOUT
            if not self.out_q.empty():
                bdata, btype = self.out_q.get()
                # Following conserved from serpy original and commentized
                # illustrating handshaking via events
                #
                # if mode != self.out_mode :
                #     self.modeChangeEvent.clear()
                #     self.out_block_q.put(b"\x01SETMODE" +
                #                         str(mode).encode(self.encoding))
                #     self.modeChangeEvent.wait()
                #     self.out_mode = mode
                
                # The only implemented mode in serpy2:
                # non-blocking/no-handshake                
                #TODO introduce send with handshake?
                
                # encode header
                checksum = sum(bdata) & 0xFFFFFFFF
                datacheckb = checksum.to_bytes(4, 'little', signed = False)
                datalenb = len(bdata).to_bytes(4, 'little', signed = False)

                bhead = BLOCKIDCODE + btype + datacheckb + datalenb
                assert len(bhead) == HEADLEN, 'HEADLEN incorrect'
                block = bhead + bdata
                
                self.out_block_q.put(block)
            else:
                sleep(STIMEOUT)
                
    
    def getData(self, timeout=None):
        """
        Returns the received data in the original data type
        Optional argument : timeout (default None)
        
        Will block until there is data or timeout is reached.
        On timeout will raise queue.Empty exception
        """
        return self.in_q.get(timeout=timeout)
    
    def sendData(self, data, timeout=None):
        """
        Send the data over this connection following a mode.
        
        Optional timeout (in seconds [float]) may be specified. 
        May block for a maximum of 2*timeout.
        May raise raise queue.Full exception or return False on timeout
        ------
        
        Currently supports the following types of data
        
        str  : sent as utf-8 encoded bytes
        int  : sent as signed 64-bit integer encoded with int.to_bytes()
        float: sent as ascii-encoded bytes after representation with float.hex()
        bytes: sent as raw data
        """
        
        # `if type(data) is` vs `isinstance()`...
        # See: https://switowski.com/blog/type-vs-isinstance
        # Thanks to Arthur for pointing this out.
        # Here, we choose the data to be necessarily *exactly* of the unmodified class.
        # Subclasses not accepted. This behaviour can always be changed later on if required.
        if type(data) is float:
            flhex = data.hex()
            bdata = flhex.encode('ascii')
            btype = FLOATTYPECODE
        elif type(data) is int:
            bdata = data.to_bytes(8, 'little', signed = True)
            btype = INTTYPECODE
        elif type(data) is str:
            bdata = data.encode('utf-8')
            btype = STRTYPECODE
        elif type(data) is bytes:
            bdata = data
            btype = RAWBYTESTYPECODE
        else:
            raise TypeError("Unsupported data type. Cannot Send")
        
        # --- putting data in queue ---
        self.out_q.put((bdata, btype), timeout=timeout)
        
        # The following code was preserved from serpy (and commentized)
        # It demonstrates how to use events to implement handshaking in
        # data sending (i.e wait for acknowledgment)
        #
        # elif mode == 1 or mode == 3 or mode == 5:
        #     self.ackEvent.clear()
        #     self.out_q.put((data, mode), timeout=timeout)
        #     return self.ackEvent.wait(timeout=timeout) #returns True if no timeout, else False
        
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
    address and port that will listen and accept connections. Each new
    socket is passed to a Connection object which is then started.
    The server remembers all Connection object it has created in a list.
    The server can accept at most nb_conn (default 5) concurent 
    connections.
    
    Usage :
     - To create a server:
        >>> s = Server(adr, port, nb_conn).start()
    """
    def __init__(self, adr, port, nb_conn=5):
        self.adr = adr
        self.port = port
        self.nb_conn = nb_conn
        self.lock = threading.Lock()
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serv.bind((adr,port))
        self.serv.listen(nb_conn)
        self.connections = []
        self.stop_sig = False

    def _serverThread(self):
        while not self.stop_sig:
            readable, writable, errored = select.select((self.serv,),
                                                        [], [], STIMEOUT)
            for s in readable :
                #TODO: handle the following as a proper Exception
                # or have a better way of reacting to too many requests.
                # At present, the server just completely gives up.
                assert len(self.connections) <= self.nb_conn,\
                    "Too many connections on this Server! Aborting..."
                conn, adr = s.accept()
                #warnings.warn("Connection to ", adr, " accepted")
                c = Connection(sock=conn)
                c.start()
                self.connections.append(c)
            for c in self.connections: #clear disconected connections
                if not c.connected:
                    self.connections.remove(c)
    
    def __iter__(self):
        """
        Yield active connections (generator).
        """
        yield from self.connections
        
    def __len__(self):
        """
        The lenght of Server is the number of active connections which
        are iterable over.
        """
        return len(self.connections)

    def start(self):
        """
        Start the server thread. Returns self (ie: the Server object)
        """
        self.tSer = threading.Thread(target=self._serverThread)
        self.tSer.start()
        return self
    
    def close(self):
        """
        Closes the server only. Its connections remain functioning.
        One can still get the connection list afterward.
        """
        self.stop_sig = True
        self.tSer.join()
        for c in self.connections :
            c.close()
        self.serv.close()

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
