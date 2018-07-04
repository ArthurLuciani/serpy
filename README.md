# serpy


## Installation
 - Make sure to have python 3. Serpy only uses the standard library.
 - Simply download serpy.py and put it in the same folder of the python script from which you want to import serpy.
 
## Usage
### Using Server
```Python3
s = Server(adr, port, nb_conn, encoding).start()
```
### Retrieving the child Connection objects from the Server
When a socket connets itself with the server, the sever creates a connection object with the new socket it has created. To retrieve those Connection objects there are several methods
 - getConnection() :
 Returns a new Connection object from the new connection queue. This method will block if there is no new connection in queue
 ```Python3
c = s.getConnection()
```
 - getConnectionsList()
 Returns the list of all active child Connections


### Making a connection to a server

```Python3
c = Connection().connect(adr, port)
```
If one wants the Connection object to try reconnecting itself to the server if the connection breaks then use
```Python3
c = Connection(auto_restart=True).connect(adr, port)
```
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
