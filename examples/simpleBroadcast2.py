#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  simpleBroadcast.py
#       simpleBroadcast adapted to work with serpy2 (not compatible with serpy)
#  
#  Copyright 2018 Arthur Luciani <arthur@arthur-X550JD>
#  code modified by M. H. V. Werts, 2022, to work with serpy2 (new protocol)   
#
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
#TODO
#  - make more verbose concerning creation/destruction of Connections
#

"""
This server will broadcast every message it receives to all of its 
other connections.
To stop the server send '/KTHXBYE' as a string
"""


import sys
import warnings

sys.path.insert(0, '..')
import serpy2 as sp
from time import sleep

ADR = ''
PORT = 8000
NB_CONN = 100

def main(args):
    s = sp.Server(ADR, PORT, NB_CONN).start()
    print("Server started")
    stop_flag = False
    while not stop_flag:
        read_conn_list = s.readableConnections()
        conn_list = s.getConnectionsList()
        for rc in read_conn_list:
            data = rc.getData()
            print(data)
            if data == '/KTHXBYE':
                stop_flag = True
                break
            for c in conn_list:
                if c != rc:
                    with warnings.catch_warnings():
                        c.sendData(data)
        if not read_conn_list: sleep(0.01) # allow this thread to rest
    s.closeServer()
    print("Server closed")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
