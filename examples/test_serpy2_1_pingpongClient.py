#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   test_serpy2_2_pingpong0Client.py
#


"""
This test client sends various types of data to server, and checks if it 
receives the same data back.

To stop the server, it sends '/KTHXBYE' as a string at the end of the test cycle.
"""

#TODO
# make this a real (pytest compatible?) test
# should test a greater variety of data

import sys
sys.path.insert(0, '..')

import serpy2 as sp
from queue import Empty
from time import sleep, time

ADR = 'localhost'
PORT = 8000
Ncycles = 10

t0 = time()
pperr = 0

for i in range(Ncycles):
    c = sp.Connection(auto_restart=True).connect(ADR, PORT)
    print("-------------- Connected --------------")
    # In the current configuration,
    # this list must not be longer than queue length, I guess...
    # #TODO check
    sendlist = [123, 'hello', 12.35, -1e6, 600000, 'yes µù']
    for s in sendlist :
        print('sending...', s)
        c.sendData(s)

    for s in sendlist:
        try:
            t = c.getData(timeout=10)
        except Empty:
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



