#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   test_serpy2_2_utils.py
#


"""
Utility functions used by both the client and the server in this
`test_serpy2_2` test.

Generate float32 image and convert to/from blobs of bytes.
"""

import numpy as np

# image dimensions
img_w = 512
img_l = 512


def float32_numpy_image(p: int):
    """
    Generate a parametric 2D image and return it as a float32 array.

    Parameters
    ----------
    p : int
        Parameter that changes the content of the image in a
        reproducible manner.

    Returns
    -------
    img32 : np.ndarray (dtype='float32')
        Data corresponding to the image.

    """
    
    x = np.linspace(0.0, p * np.pi, img_w)
    y = np.linspace(0.0, p * np.pi, img_l)
    
    xx, yy = np.meshgrid(x, y)
    
    img = np.cos(xx) * np.sin(yy)
    
    img32 = np.array(img, dtype = 'float32')
   
    return img32


def float32_to_bytes(arr):
    return arr.tobytes()


def bytes_to_float32img(b):
    arr1 = np.frombuffer(b, dtype = 'float32')
    arr = arr1.reshape((img_l,img_w))
    return arr



if __name__=='__main__':
    import matplotlib.pyplot as plt
    img32 = float32_numpy_image(3)
    plt.figure(1)
    plt.clf()
    plt.pcolormesh(img32)
    bbb = float32_to_bytes(img32)
    bimg = bytes_to_float32img(bbb)
    plt.figure(2)
    plt.clf()
    plt.pcolormesh(bimg)
    assert np.array_equal(img32, bimg), 'encoding/decoding error'
    print('OK')
    
