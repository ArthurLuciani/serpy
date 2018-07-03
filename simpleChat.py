#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  simpleChat.py
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
import serpy as sp
import threading

ENCODING = 'utf-8'
ADR = 'localhost'
PORT = 19876
NAME = "VOID"

lock = threading.Lock()
stop_flag = False

def recvThread(c):
    while not stop_flag:
        try: 
            lock.acquire()
            print(">>> "+c.getData(1).decode(encoding))
            lock.release()
        except sp.queue.Empty:
            pass

def main(args):
    c = sp.Connection(encoding=ENCODING, auto_restart=True).connect(ADR, PORT)
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
                    NAME = s.split(' ')[1]
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
