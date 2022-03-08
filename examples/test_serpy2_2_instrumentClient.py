#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   test_serpy2_2_instrumentClient.py
#


"""
This test client sends various types of data to the server, and checks if it 
receives the expected response back.

In this case, not all data sent will lead to a response, only when sending an
integer, a blob of bytes will be received in return, which can be converted 
into a 2D numpy array representing an image.

More precisely, the 2D array is a float32 image, whose dimensions
are set inside `test_serpy2_2_utils.py`; later we may extend the simple
client-image server protocol to have the client set image dimensions on the
server, so that we can test different image size and how they affect
performance. But this should be done if we arrive at a stage where performance
should be tweaked. Setting image size too big will lead to serious time-out
issues and severely reduced througput.

To stop the server, the script sends '/KTHXBYE' as a string at the end
of the test cycle.
"""

import sys
sys.path.insert(0, '..')

from time import sleep, time
import numpy as np

import serpy2 as sp

from test_serpy2_2_utils import float32_numpy_image, bytes_to_float32img


ADR = 'localhost'
PORT = 8000
DATATIMEOUT = 10. # Time-out for waiting for data. Here it should be very long,
                  # since it will only occur in case of a transfer problem

t0 = time()
bytesrcvd = 0
frmrcvd = 0
Nerr = 0
Ncycles = 10
for i in range(10):
    c = sp.Connection(auto_restart=True).connect(ADR, PORT)
    print("-------------- Connected --------------")
    
    # We send a sequence of several types of data to the server at once,
    # specified in the list below.
    # This list should not be longer than serpy2 queue length...
    # We deliberately include data that will not lead to a response from the
    # server.
    #
    sendlist = [1, 'hello', 12.35, -1e6, 12, 30, 'yes éµù utf8']
    
    expectlist = []
    for s in sendlist :
        print('sending...', s)
        c.sendData(s)
        if type(s) is int: # only expect a reply for the ints
            expectlist.append(s)

    for expect in expectlist:
        try:
            t = c.getData(timeout=DATATIMEOUT)
        except sp.queue.Empty:
            print('*** TIMEOUT ERROR ***')
            Nerr += 1
        if type(t) is not bytes:
            print('*** DATA RECEPTION ERROR ***')
            Nerr += 1  
        else:
            print('recv.... <',len(t),'bytes>')
            bytesrcvd += len(t)
            print('p data: ', expect, end=' : ')
            gotimg32 = bytes_to_float32img(t) # decode the received image
            expimg32 = float32_numpy_image(expect) # generate the expected image
            if np.array_equal(gotimg32, expimg32):
                print('DATA OK')
                frmrcvd +=1
            else:
                print('*** DATA CONTENT ERROR ***')
                Nerr += 1            
    print("-------------------------------------")
    print()
    c.close()
tt = time()-t0

print("-------------------------------------")    
print('Received',bytesrcvd,'bytes in',tt,'seconds')
print((bytesrcvd/1000000)/tt, 'Mbytes per second')
print(frmrcvd/tt, 'frames per second')
print('frame dimensions: ',expimg32.shape[1], 'x', expimg32.shape[0],
      '(32 bits per pixel)')
print(Nerr, 'errors')
print("-------------------------------------")                  

c = sp.Connection(auto_restart=False).connect(ADR, PORT)
c.sendData('/KTHXBYE')
sleep(1)
c.close()




