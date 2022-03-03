#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  simpleChat2.py
#       simpleChat adapted to work with serpy2 (not compatible with serpy)
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
#  
#
#TODO
#  The client should detect when there is no server anymore. And not send
#  anything without server present. The server should broadcast an "server shutting
#  down" message.
#  Investigate robustness towards random deconnection/reconnection.
#

import sys
sys.path.insert(0, '..')
import serpy2 as sp
import threading

ADR = 'localhost'
PORT = 8000
NAME = "no name (use /name=NAME)"

lock = threading.Lock()
stop_flag = False


def recvThread(c):
    global stop_flag
    while not stop_flag:
        lock.acquire()
        try:
            print(">>> "+c.getData(timeout=1))
            lock.release()
        except sp.queue.Empty:
            lock.release()


def main(args):
    global stop_flag, NAME
    c = sp.Connection(auto_restart=True).connect(ADR, PORT)
    print("-------------- Connected --------------")
    th = threading.Thread(target=recvThread, args=(c,))
    th.start()
    while not stop_flag:
        s = input()
        if s:
            if s.startswith("/"):
                if s.lower() == "/stop":
                    stop_flag = True
                    break
                elif s.lower().startswith("/name"):
                    NAME = s[6:]
                elif s == "/KTHXBYE":
                    c.sendData(s)
                else :
                    lock.acquire()
                    print("WARNING : Command not recognized")
                    lock.release()
            else :
                c.sendData(NAME+' : '+s)
    th.join()
    c.close()
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
