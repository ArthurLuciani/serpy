#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  simpleBroadcast.py
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

"""
This server will broadcast every message it receives to all of its 
others connections.
To stop the server send b'/KTHXBYE'
"""



import serpy as sp
from time import sleep

ADR = ''
PORT = 8000
NB_CONN = 100
ENCODING = 'utf-8' #probably useless

def main(args):
    s = sp.Server(ADR, PORT, NB_CONN, ENCODING).start()
    print("Server started")
    stop_flag = False
    while not stop_flag:
        read_conn_list = s.readableConnections()
        conn_list = s.getConnectionsList()
        for rc in read_conn_list:
            data =  rc.getData()
            print(data)
            if data == b'/KTHXBYE':
                stop_flag = True
                break
            for c in conn_list:
                if c != rc:
                    c.sendData(data)
        if not read_conn_list: sleep(0.01) # allow this thread to rest
    s.closeServer()
    print("Server closed")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
