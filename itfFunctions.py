#!/usr/bin/python3
import xarray as xr
from datetime import datetime
import numpy as np
import glob
import os
import hashlib
import sys

global ShowDebug # Boolean for whether to print "DEBUG" statements
ShowDebug = False 

class LatLonBox:
    def __init__(self, west, east, north, south):
        self.west = west
        self.east = east
        self.north = north
        self.south = south

def PrintToConsole(Level,Message):
    if ShowDebug==False and Level=='DEBUG':
        return
    print('%s %d [%s] %s' % (datetime.now(), os.getpid(), Level, Message), flush=True)
    return

def ComputeMD5(file):
    PrintToConsole('INFO','Generating md5sum for %s' % (file))
    try:
        os.remove('%s.md5' % file)
    except OSError:
        pass

    BUF_SIZE = 65536  # read in 64kb chunks (arbitrary number)
    md5 = hashlib.md5()
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    filehash = md5.hexdigest()
    with open('%s.md5' % (file), 'w') as f:
        f.write('%s\n' % (filehash))
    return filehash

def areAllVarsInDS(items, ds):
    PrintToConsole('DEBUG','Checking if %s in input dataset' % items)
    err = 'Not found in dataset: '
    items = items.split(',')
    check = [False for i in range(len(items))]
    # this^ is explaned here: https://www.geeksforgeeks.org/python-boolean-list-initialization/
    for i in range(len(items)):
        check[i] = hasattr(ds,items[i])
        if check[i] == False:
            err = err + "%s " % (items[i])

    if all(check) == False:
        return False, err
    else:
        return True, ''