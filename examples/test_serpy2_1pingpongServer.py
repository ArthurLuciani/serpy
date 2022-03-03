#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   test_serpy2_1pingpongServer.py
#


"""
This test server receives data from clients, decodes them, recodes them and
sends them back to the sender.

To stop the server send '/KTHXBYE' as a string
"""

import sys
sys.path.insert(0, '..')

#import warnings

import serpy2 as sp
from time import sleep

ADR = ''
PORT = 8000
NB_CONN = 3 # if number of connections too low, crashes the Server


s = sp.Server(ADR, PORT, NB_CONN).start()
print("Server started (ping-pong)")
stop_flag = False
while not stop_flag:
    read_conn_list = s.readableConnections()
    # conn_list = s.getConnectionsList()
    for rc in read_conn_list:
        data = rc.getData()
        print('type: ',type(data),end=' ')
        if type(data) is not bytes:
            print('data = ',data)
        else:
            print()
        if data == '/KTHXBYE':
            stop_flag = True
            break
        rc.sendData(data)
    if len(read_conn_list)==0:
        sleep(0.01) # allow this thread to rest
print('closing server...')
s.closeServer()
print("Server closed")


