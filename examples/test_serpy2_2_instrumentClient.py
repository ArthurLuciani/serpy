#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   test_serpy2_2instrumentClient.py
#


"""
This test client sends various types of data to server, and checks if it 
receives the expected response back.

FIRST VERSION JUST TO GET THINGS STARTED
TO BE FURTHER ADAPTED

To stop the server, it sends '/KTHXBYE' as a string at the end of the test cycle.
"""

import sys
sys.path.insert(0, '..')
import serpy2 as sp

from queue import Empty

from time import sleep, time

ADR = 'localhost'
PORT = 8000


t0 = time()


for i in range(10):
    c = sp.Connection(auto_restart=True).connect(ADR, PORT)
    print("-------------- Connected --------------")
    # this list must not be longer than queue length I guess...
    # #TODO check
    sendlist = [1, 'hello', 12.35, -1e6, 12, 30, 'yes µù']
    for s in sendlist :
        print('sending...', s)
        c.sendData(s)

    for s in sendlist:
        try:
            t = c.getData(timeout=0.2)
        except Empty:
            t = '*** timeout ***'
        print('recv....', t)
        #TODO: check reception, decode image etc.
        
    print('end OK')
    # keep server alive for now
    # c.sendData('/KTHXBYE')
    # sleep(1)
    c.close()
    # sleep(0.1)
    
c = sp.Connection(auto_restart=False).connect(ADR, PORT)
c.sendData('/KTHXBYE')
sleep(1)
c.close()




