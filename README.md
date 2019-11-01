# serpy
Serpy is intended to provide an easy-to-use Python module for TCP/IP communications. It provides two classes and methods for synchronous and asynchronous (ordered) communication. No more worries about sockets, threads, queues and sudden disconnections. These are handled silently by Serpy.

## Installation
 - Make sure to have Python 3. Serpy only uses the Python standard library.
 - Simply download the serpy folder and put it in the same folder of the python script from which you want to import serpy.
 
## Usage
### Using Server
```Python3
s = Server(adr, port, nb_conn, encoding).start()
```
### Retrieving the child Connection objects from the Server
When a socket connets itself with the server, the sever creates a connection object with the new socket it has created. To retrieve those Connection objects there are several methods
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
 - mode 1 : the data will be sent and the method will block until acknoledgment
 - mode 2 : similar to mode 0 but encodes data in base 85. Used to prevent encountering control characters. If data is of type *bytes* then the mode will automticaly change to 2.
 
An optional timeout may be specified. The method may block for up to 2\*timeout. On timeout may raise queue.Full exception or return False in mode 1.
```Python3
c.sendData(data, mode=0, timeout=None)
```

### Closing a connection
Use the `Connection.close()` method


