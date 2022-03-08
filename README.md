# serpy
Serpy is intended to provide an easy-to-use and lightweight 'pure' Python module for direct, low-overhead TCP/IP communications. It provides two classes and methods for synchronous and asynchronous (ordered) communication. No more worries about sockets, threads, queues and sudden disconnections. These are handled silently by Serpy.

Our interest in developing serpy is to use it for transfer of data between scientific instrumentation and data processing workstations. It has successfully been used to interface home-built photon counting electronics to a distant data acquisition workstation.

## Two versions: serpy and serpy2
The `serpy2` module has been created on basis of the original `serpy`, conserving its philosophy, but implementing a different protocol that is not compatible with orginal `serpy`. The new protocol, which does not yet feature hand-shaking, aims to be more efficient in terms of bandwidth and processing power, and is geared towards transfer of 'binary large objects' (blobs of bytes), such as images.

At present, we keep both modules seperately. The ultimate goal is, of course, to have one single module that can be configured optimally for all use cases, and is fully student-proof.

## Installation
 - Make sure to have Python 3. Serpy only uses the Python standard library. `numpy` is needed for some of the `serpy2` test scripts.
 - Simply put the `serpy` and/or `serpy2` folders in the same folder of the Python script from which you want to import serpy (or serpy2).
 
## Usage

### Example scripts
There are at present two pairs of example scripts inside the `examples` folder. These act also as initial tests for the serpy/serpy2 code. `simpleBroadcast.py` / `simpleChat.py` work with the original `serpy`. `simpleBroadcast2.py` / `simpleChat2.py` work with `serpy2`. 

There are also pairs of client-server test scripts for `serpy2`.

***

The information below pertains to original `serpy`. Usage of `serpy2` is very similar. More documentation needed (#todo). For now, refer to the example scripts and the `serpy2` code.

### Using Server
```Python3
s = Server(adr, port, nb_conn, encoding).start()
```
### Retrieving the child Connection objects from the Server 
When a socket connects itself with the server, the server creates a connection object with the new socket it has created. To retrieve those Connection objects there are several methods
 - `Server.getConnection()` :
 Returns a new Connection object from the new connection queue. This method will block if there is no new connection in queue
 ```Python3
conn_list = s.getConnection()
```
 - `Server.getConnectionsList()` :
 Returns a copy of the list of all active child Connections
 ```Python3
conn_list = s.getConnectionsList()
```
 - `Server.readableConnections()` : 
 Returns the list of child Connection objects which have data available to be read
  ```Python3
conn_list = s.readableConnections()
```

### Closing the server
 - `Server.close()` method : Will close the server. Won't close any child Connection. Won't accept any new connection. Cannot be restarted. Won't cleanup broken connections out of the Connection list

 - `Server.closeServer()` method : Will close all the child Connection objects and then close itself.

### Making a connection to a server

```Python3
c = Connection().connect(adr, port)
```
If one wants the Connection object to try reconnecting itself to the server if the connection breaks, then use
```Python3
c = Connection(auto_restart=True).connect(adr, port)
```
or use the `Connection.enableRestart()` method

One can also specify the encoding it should use if string objects are passed to send data (default ascii)
```Python3
c = Connection(encoding='utf-8').connect(adr, port)
```

### Receiving data
Use the Connection.getData method. This method will block until either data is received or an optional timeout is met.The received data will be in bytes.
The optional timeout must be a number of seconds (float; int might work)
```Python3
c.getData(timeout=1.0)
```
On timeout will raise the queue.Empty exception

### Sending data
To send data use the Connection.sendData method. Several modes are available:
 - mode 0 (default) : the data will just be sent as is without blocking (except if the internal queue is full)
 - mode 1 : the data will be sent and the method will block until acknowledgment
 - mode 2 : similar to mode 0 but encodes data in base 85. Used to prevent encountering control characters. If data is of type *bytes* then the mode will automticaly change to 2.
 
An optional timeout may be specified. The method may block for up to 2\*timeout. On timeout may raise queue.Full exception or return False in mode 1.
```Python3
c.sendData(data, mode=0, timeout=None)
```

### Closing a connection
Use the `Connection.close()` method


