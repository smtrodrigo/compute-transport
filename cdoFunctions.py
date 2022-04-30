#!/usr/bin/python3
import itfFunctions as itf
import xarray as xr
from cdo import Cdo
from datetime import datetime
import numpy as np
import glob
import os
import hashlib
import sys

cdo = Cdo()

def GenerateMakeBoxSavePath(filename, bounds, boxdir):
    name, ext = os.path.splitext(filename)
    bwest = bounds.west
    beast = bounds.east
    bnorth = bounds.north
    bsouth = bounds.south
    savedir = '%s/%0.3f_%0.3f_%0.3f_%0.3f/' % (boxdir, bwest,beast,bsouth,bnorth)
    savename = '%s%s.%0.3f_%0.3f_%0.3f_%0.3f%s' % (savedir,os.path.basename(name),bwest,beast,bsouth,bnorth,ext)

    return savename

# bounds precision only up to 0.001 deg
def MakeBoxIndex(inputFile, bounds, toInclude='', outputFile = ''):
    itf.PrintToConsole('INFO','Extracting data from %s'% (inputFile))

    itf.PrintToConsole('DEBUG',\
                   'Setting bounds to bwest = %0.3f, beast = %0.3f, bsouth = %0.3f, bnorth = %0.3f,'\
                       % (bounds.west, bounds.east, bounds.south, bounds.north))

    ds = xr.open_dataset(inputFile)
    tLatMask  = ds.TLAT.where(ds.TLAT != -1.)
    tLongMask = ds.TLONG.where(ds.TLONG != -1.)

    indices = np.argwhere( \
        (tLatMask <= bounds.north).values & \
        (tLatMask >= bounds.south).values & \
        (tLongMask <= bounds.east).values & \
        (tLongMask >= bounds.west).values \
    )

    # cdo -h sellonlatbox
    # [..]
    # idx1  INTEGER  Index of first longitude (1 - nlon)
    # idx2  INTEGER  Index of last longitude (1 - nlon)
    # idy1  INTEGER  Index of first latitude (1 - nlat)
    # idy2  INTEGER  Index of last latitude (1 - nlat)

    ixd1 = indices[:,1].min()
    ixd2 = indices[:,1].max()
    iyd1 = indices[:,0].min()
    iyd2 = indices[:,0].max()

    bwest = ixd1
    beast = ixd2
    bnorth = iyd2
    bsouth = iyd1
    
    itf.PrintToConsole('DEBUG',\
                   'Setting bounds to ixd1 = %d, ixd2 = %d, iyd1 = %d, iyd2 = %d,'\
                       % (ixd1, ixd2, iyd1, iyd2))
    cdo.cleanTempDir() # --- Clean tempDir
    
    if toInclude == '':
        inputParams = inputFile
    else:
        inputParams = "-selname,%s %s" %(toInclude,inputFile)
    
    savename=""

    # --- Output to named output file, "savename", then load via xarray
    boundsPrint = '%d,%d,%d,%d' % (ixd1, ixd2, iyd1, iyd2)

    name, ext = os.path.splitext(inputFile)

    savename = outputFile
    savedir = os.path.dirname(outputFile)

    os.makedirs(savedir, exist_ok = True)

    itf.PrintToConsole('INFO','Running: cdo -selindexbox,%s -selname,%s %s %s' % \
                   (boundsPrint, toInclude, inputFile, savename)) # (bounds, toInclude ,inputFile, savename)) # copied from above      
    cdo.selindexbox(boundsPrint, input = inputParams, output = savename)
    
    itf.ComputeMD5(savename)

    itf.PrintToConsole('INFO','Data extracted.')

    datasmall = xr.open_dataset(savename)
    long_min = datasmall.ULONG.where(datasmall.ULONG!=-1).min().data
    long_max = datasmall.ULONG.where(datasmall.ULONG!=-1).max().data
    lat_min  = datasmall.ULAT.where(datasmall.ULAT!=-1).min().data
    lat_max  = datasmall.ULAT.where(datasmall.ULAT!=-1).max().data
    itf.PrintToConsole('DEBUG','Minimum longitude: %f; Maximum longitude: %f; Minimum latitude: %f, Maximum latitude: %f' % (long_min, long_max, lat_min, lat_max))
    
    return savename