#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   test_serpy2_1_pingpongClient.py
#


"""
This test client sends various types of data to server, and checks if it 
receives the same data back.

To stop the server, it sends '/KTHXBYE' as a string at the end of the test cycle.
"""

#TODO
# Make this a real (pytest compatible?!) test.
# It should test a greater variety of data, but it is OK for initial
# development.

import sys
sys.path.insert(0, '..')

from time import sleep, time

import serpy2 as sp


ADR = 'localhost'
PORT = 8000
Ncycles = 10

t0 = time()
pperr = 0

for i in range(Ncycles):
    c = sp.Connection(auto_restart=True).connect(ADR, PORT)
    print("-------------- Connected --------------")
    # We send a sequence of different types of data to the server in one go,
    # before reading out the response. 
    # The sequence is in `sendlist`. In the current configuration,
    # this list should not be longer than serpy2 queue length.
    sendlist = [123, 'hello', 12.35, -1e6, 600000, 'yes µù']
    for s in sendlist :
        print('sending...', s)
        c.sendData(s)

    for s in sendlist:
        try:
            t = c.getData(timeout=10)
        except sp.queue.Empty:
            t = '*** timeout ***'
        print('recv....', t)
        if not (s==t):
            print('ping pong error')
            pperr += 1
    c.close()
    print('cycle OK')

print()
print('***************************************')
print(Ncycles, 'cycles in', time()-t0, 'seconds')
print(pperr,'ping-pong errors')
print('***************************************')
    
c = sp.Connection(auto_restart=False).connect(ADR, PORT)
c.sendData('/KTHXBYE')
sleep(1)
c.close()



