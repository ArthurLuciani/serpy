## encoding int to bytes

```python
a_int = 5

nbytes = 2
byteorder = 'big' # always use the same

a_bytes = a_int.to_bytes(nbytes, byteorder, signed = True)
```

and vice-versa: from_bytes

Finally:

```python
a = -17
ab = a.to_bytes(8, 'big', signed=True) #64-bit signed int
aa = int.from_bytes(ab, 'big', signed=True)
```

## float?

does not have a `to_bytes` method

use `.hex()` even though not very efficient

and `.from_hex()`

```python
c = 15.1
ch = c.hex()
cc = float.from_hex(ch)
```


## only four types?

- bytes ('raw data')
- str (encoded as utf-8) => bytes
- int (to_bytes) =>
- float (hex) => str (utf-8) => bytes

`header = 0xDECAFEFE + <type 1 byte> + <length 2 bytes> + <data>`


