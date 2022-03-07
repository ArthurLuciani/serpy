#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   test_serpy2_2instrumentServer.py
#


"""
This test server receives requests from clients (e.g. if it were a camera
server, this would be a request to return an image, or to change a acquisition
setting)

At present, the accepted requests are extremely simple. If an integer value
is received, it will generate an image in a numpy array and send it back to
the client in a binary blob.

To stop the server send '/KTHXBYE' as a string
"""

import sys
sys.path.insert(0, '..')

#import warnings

import serpy2 as sp
from time import sleep

ADR = ''
PORT = 8000
NB_CONN = 3


s = sp.Server(ADR, PORT, NB_CONN).start()
print("Server started (instrument-style)")
stop_flag = False
while not stop_flag:
    read_conn_list = s.readableConnections()
    # conn_list = s.getConnectionsList()
    for rc in read_conn_list:
        # get incoming data
        data = rc.getData()

        #print('type: ',type(data),end=' ')
        if type(data) is not bytes:
            print('data = ',data)
        else:
            print()
        
        #decode it and react
        if data == '/KTHXBYE':
            stop_flag = True
            break
        elif type(data) == int:
            rc.sendData('This will become an image... '+\
                        'ha'*data)            
        else:
            print('(data ignored)')

    if len(read_conn_list)==0:
        sleep(0.01) # allow this thread to rest
print('closing server...')
s.closeServer()
print("Server closed")
