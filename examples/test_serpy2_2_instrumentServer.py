#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   test_serpy2_2_instrumentServer.py
#


"""
This test server receives requests from clients (e.g. if it were a camera
server, this would be a request to return an image, or to change an acquisition
parameter setting).

At present, the accepted 'requests' are extremely simple. If an integer value
is received by the server, it will generate image-like data (2D array) in a
numpy array and send it to the client in a binary blob.

More precisely, the 2D array is a float32 image, whose dimensions
are set inside `test_serpy2_2_utils.py`; later we may extend the simple
client-image server protocol to have the client set image dimensions on the
server, so that we can test different image size and how they affect
performance. But this should be done if we arrive at a stage where performance
should be tweaked. Setting image size too big will lead to serious time-out
issues and severely reduced througput.

Any other 'request' will be ignored, except the string '/KTHXBYE' which will
tell the server process to stop. 
"""

import sys
sys.path.insert(0, '..')

import serpy2 as sp
from time import sleep

from test_serpy2_2_utils import float32_numpy_image, float32_to_bytes


ADR = ''
PORT = 8000
NB_CONN = 3


s = sp.Server(ADR, PORT, NB_CONN).start()
print("Server started (instrument-style)")


stop_flag = False
while not stop_flag:
    read_conn_list = s.readableConnections()
    for rc in read_conn_list:
        # get incoming data
        data = rc.getData()
        if type(data) is not bytes:
            print('data = ',data)
        else:
            print('data = <bytes>')
        
        #decode data and react
        if data == '/KTHXBYE':
            stop_flag = True
            break
        elif type(data) == int:
            # make image based on value of 'data'
            # and send it encoded as bytes
            img32 = float32_numpy_image(data)
            bb = float32_to_bytes(img32)
            rc.sendData(bb)
        else:
            print('--> data ignored')
    if len(read_conn_list)==0:
        sleep(0.01) # allow this thread to rest
        
        
print('Closing server...')
s.closeServer()
print("Server closed")
