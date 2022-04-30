import itfFunctions as itf
import cdoFunctions as cdof

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from dotenv import dotenv_values
import argparse
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import os
import pytest
import xarray as xr
import cftime


# explain
global z_w_bot
z_w_bot = xr.DataArray(
    data = np.array([  \
         1000.   ,   2000.   ,   3000.   ,   4000.   ,   5000.   ,   6000.   ,
         7000.   ,   8000.   ,   9000.   ,  10000.   ,  11000.   ,  12000.   ,
        13000.   ,  14000.   ,  15000.   ,  16000.   ,  17019.682,  18076.129,
        19182.125,  20349.932,  21592.344,  22923.312,  24358.453,  25915.58 ,
        27615.26 ,  29481.47 ,  31542.373,  33831.227,  36387.473,  39258.047,
        42498.887,  46176.656,  50370.688,  55174.91 ,  60699.668,  67072.86 ,
        74439.805,  82960.695,  92804.35 , 104136.82 , 117104.016, 131809.36 ,
       148290.08 , 166499.2  , 186301.44 , 207487.39 , 229803.9  , 252990.4  ,
       276809.84 , 301067.06 , 325613.84 , 350344.88 , 375189.2  , 400101.16 ,
       425052.47 , 450026.06 , 475012.   , 500004.7  , 525000.94 , 549999.06 ,
       574999.06 , 599999.06 ]),
    dims = ["z_w_bot"]
)

# explain
global GridFile
GridFile = './input/raw/uvel/B.E.13.BRCP85C5CN.ne120_t12.sehires38.003.sunway.CN_OFF.pop.h.UVEL.201501-201512.nc'

def gridFileHasMapExtents(inputGridFile, MapExtent): # Unit test checks if the "MapExtent" variable
                # is within the bounds of the GridFile, which is used for nearest neighbor
    raw = xr.open_dataset(inputGridFile)
    boxedGridFile = itf.LatLonBox( \
                        np.min(np.min(raw.TLONG.data[raw.TLONG.data != -1])), \
                        np.max(np.max(raw.TLONG.data[raw.TLONG.data != -1])), \
                        np.max(np.max(raw.TLAT.data[raw.TLAT.data != -1])), \
                        np.min(np.min(raw.TLAT.data[raw.TLAT.data != -1])))

    if  MapExtent.north <= boxedGridFile.north and \
        MapExtent.south >= boxedGridFile.south and \
        MapExtent.west >= boxedGridFile.west and \
        MapExtent.east <= boxedGridFile.east:
        return True
    else:
        return False

# def testGridFileHasMapExtents(): # Unit test checks if the "MapExtent" variable
#                 # is within the bounds of the GridFile, which is used for nearest neighbor
#     assert gridFileHasMapExtents(GridFile) == True

def CreatePointsOnLine(latitudes, longitudes, xyResolution): # x = Longitude; y = Latitude
    itf.PrintToConsole('INFO',\
    'Creating %.2f-spaced points with endpoints %.3f to %.3f latitude and %.3f to %.3f longitude'\
        % (xyResolution, latitudes[0], latitudes[-1], longitudes[0],longitudes[-1]))
    if len(latitudes) != len(longitudes):
        error = 'Inputted latitudes and longitudes are not the same size'
    outputLats = np.array([])
    outputLons = np.array([])
    
    for i in range(len(longitudes)-1):
        x0 = longitudes[i];      xF = longitudes[i+1]
        y0 = latitudes[i];       yF = latitudes[i+1]
        yDist = abs(yF - y0)
        xDist = abs(xF - x0)
#         if xDist < 0:
#             error = 'Inputted latitudes should be in order: [smaller bigger]'
#             return error
#         if yDist < 0:
#             error = 'Inputted latitudes should be in order: [smaller bigger]'
#             return error
        if xyResolution < 0:
            error = 'xyResolution should be positive'
            return error
        
        if xF == x0: # Vertical
            numberOfSegments = int(abs(np.floor(yDist/xyResolution)))
            xN = x0; yN = y0
            for j in range(numberOfSegments):
                outputLats = np.concatenate((outputLats,np.array([yN])))
                outputLons = np.concatenate((outputLons,np.array([xN])))
                yNm1 = yN # n-1
                if yF > y0:
                    yN = yNm1 + xyResolution
                else:
                    yN = yNm1 - xyResolution
                xN = xN # vertical line

        elif yF == y0: # Horizontal
            numberOfSegments = int(abs(np.floor(xDist/xyResolution)))
            xN = x0; yN = y0
            for j in range(numberOfSegments):
                outputLats = np.concatenate((outputLats,np.array([yN])))
                outputLons = np.concatenate((outputLons,np.array([xN])))
                xNm1 = xN # n-1
                if xF > x0:
                    xN = xNm1 + xyResolution
                else:
                    xN = xNm1 - xyResolution
                yN = yN # horizontal line
                
        else: # non-horizontal
            m = ((yF-y0)/(xF-x0))
            xN = x0; yN = y0
#             print('m = %f' % m)
            if yDist >= xDist:
                numberOfSegments = int(abs(np.floor(yDist/xyResolution)))
                if numberOfSegments == 0:
                    error = 'No segments generated: very low resolution?'
                    return error
                ResolutionNew = (yF - y0)/numberOfSegments
                
                for j in range(numberOfSegments):
                    outputLats = np.concatenate((outputLats,np.array([yN])))
                    outputLons = np.concatenate((outputLons,np.array([xN])))
                    yNm1 = yN # N-1
                    yN = yNm1 + ResolutionNew
                    xN = xN + (1/m) * (yN - yNm1)
            elif xDist > yDist:
                numberOfSegments = int(abs(np.floor(xDist/xyResolution)))
#                 print('Distance in x: %f' % xDist)
                numberOfSegments = int(abs(np.floor(xDist/xyResolution)))
#                 print('Dividing by inputted resolution %f, we get %d segments' \
#                       % (xyResolution, numberOfSegments))
                ResolutionNew = (xF - x0)/numberOfSegments
#                 print('New resolution, when dividing yDist by the number of segments: %f' \
#                       % (ResolutionNew))
                
                for j in range(numberOfSegments):
                    outputLats = np.concatenate((outputLats,np.array([yN])))
                    outputLons = np.concatenate((outputLons,np.array([xN])))
                    xNm1 = xN # N-1
                    xN = xNm1 + ResolutionNew
                    yN = yN + m * (xN - xNm1)
        
        error=''
        outputLats = np.concatenate((outputLats,np.array([yN])))
        outputLons = np.concatenate((outputLons,np.array([xN])))
    outputLats = np.concatenate((outputLats,np.array([latitudes[-1]])))
    outputLons = np.concatenate((outputLons,np.array([longitudes[-1]])))
    return outputLats, outputLons, error

class TestCreatePointsOnLine:
    def testCreatePointsOnLine_vertical_repeat(self):
        lats = np.array([-16, -15]) 
        lons = np.array([115, 115])
        xyResolution = 1
        lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
        
        assert Err == ''
        assert all(lnPtsLat == np.array([-16., -15., -15.]))
        assert all(lnPtsLon == np.array([115., 115., 115.]))

    def testCreatePointsOnLine_vertical_norepeat(self):
        lats = np.array([-16, -14.5]) 
        lons = np.array([115, 115])
        xyResolution = 1
        lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
        
        assert Err == ''
        assert all(lnPtsLat == np.array([-16., -15., -14.5]))
        assert all(lnPtsLon == np.array([115., 115., 115.]))

    def testCreatePointsOnLine_vertical_norepeat_backward(self):
        lats = np.array([-14.5, -16.]) 
        lons = np.array([115, 115.])
        xyResolution = 1
        lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
        
        assert Err == ''
        assert all(lnPtsLat == np.array([-14.5, -15.5, -16. ]))
        assert all(lnPtsLon == np.array([115., 115., 115.]))

    def testCreatePointsOnLine_horizontal_repeat(self):
        lats = np.array([-15., -15.]) 
        lons = np.array([110., 112])
        xyResolution = 1
        lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
        
        assert Err == ''
        assert all(lnPtsLat == np.array([-15., -15., -15., -15.]))
        assert all(lnPtsLon == np.array([110., 111., 112., 112.]))
    
    def testCreatePointsOnLine_horizontal_norepeat(self):
        lats = np.array([-15., -15.]) 
        lons = np.array([110., 112.4])
        xyResolution = 1
        lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
        
        assert Err == ''
        assert all(lnPtsLat == np.array([-15., -15., -15., -15.]))
        assert all(lnPtsLon == np.array([110. , 111. , 112. , 112.4]))
        
    def testCreatePointsOnLine_horizontal_norepeat_backward(self):
        lats = np.array([-15., -15.]) 
        lons = np.array([112.4, 110.])
        xyResolution = 1
        lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
        
        assert Err == ''
        assert all(lnPtsLat == np.array([-15., -15., -15., -15.]))
        assert all(lnPtsLon == np.array([112.4, 111.4, 110.4, 110. ]))
        
    def testCreatePointsOnLine_diagonal_positiveslope_repeat(self): # always repeats given logic
        lats = np.array([-16., -14.]) 
        lons = np.array([110., 111.])
        xyResolution = 0.8
        lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
        
        assert Err == ''
        assert all(lnPtsLat == np.array([-16., -15., -14., -14.]))
        assert all(lnPtsLon == np.array([110. , 110.5, 111. , 111. ]))
    
    def testCreatePointsOnLine_diagonal_positiveslope_backward(self):
        lats = np.array([-14., -16.]) 
        lons = np.array([111., 110.])
        xyResolution = 0.8
        lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
        
        assert Err == ''
        assert all(lnPtsLat == np.array([-14., -15., -16., -16.]))
        assert all(lnPtsLon == np.array([111. , 110.5, 110. , 110. ]))
        
    def testCreatePointsOnLine_diagonal_negativeslope_repeat(self): # always repeats given logic
        lats = np.array([-14., -16.]) 
        lons = np.array([110., 111.])
        xyResolution = 0.8
        lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
        
        assert Err == ''
        assert all(lnPtsLat == np.array([-14., -15., -16., -16.]))
        assert all(lnPtsLon == np.array([110. , 110.5, 111. , 111. ]))
    
    def testCreatePointsOnLine_diagonal_negativeslope_backward(self): # always repeats given logic
        lats = np.array([-16., -14.]) 
        lons = np.array([111., 110])
        xyResolution = 0.8
        lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
        
        assert Err == ''
        assert all(lnPtsLat == np.array([-16., -15., -14., -14.]))
        assert all(lnPtsLon == np.array([111. , 110.5, 110. , 110. ]))

def nearestNeighborLookUp(lnPtsLat, lnPtsLon, inputDS):
    itf.PrintToConsole('INFO','Performing nearest neighbor for %d points'%(len(lnPtsLat)))
    raw = inputDS
    lnIndLat = np.array([])
    lnIndLon = np.array([])
    for pt in range(len(lnPtsLat)): # --- Nearest-neighbor look-up
        abslat = np.abs(raw.TLAT  - lnPtsLat[pt])
        abslon = np.abs(raw.TLONG - lnPtsLon[pt]) # x = Longitude; y = Latitude
        c = np.maximum(abslon,abslat) # --- taking the element-wise maximum of the two arrays
        #print(np.where(c == np.min(c)))
        (yTemp,xTemp) = np.where(c == np.min(c)) # should be y,x not x,y
        lnIndLon = np.concatenate((lnIndLon,xTemp)) # sometimes different lengths, because it can have 2 nearest-neighbors
        lnIndLat = np.concatenate((lnIndLat,yTemp))
        
    itf.PrintToConsole('DEBUG','Done with nearest neighbor calculation.')
    
    StartLon = raw.TLONG.data[int(lnIndLat[0]),int(lnIndLon[0])]
    EndLon   = raw.TLONG.data[int(lnIndLat[-1]),int(lnIndLon[-1])]
    StartLat = raw.TLAT.data[int(lnIndLat[0]),int(lnIndLon[0])]
    EndLat   = raw.TLAT.data[int(lnIndLat[-1]),int(lnIndLon[-1])]
    
    if StartLat == EndLat:
        outputSlop = 0
    elif StartLon == EndLon:
        outputSlop = np.nan
    else:
        outputSlop = (EndLat-StartLat)/(EndLon-StartLon)
    
    # --- save lnIndLat & lnIndLat
    ToDs = xr.DataArray(
        data = lnIndLon.data,
        dims = ["coords"]
    )
    saveDs = ToDs.to_dataset(name = 'xInd')
    saveDs['yInd'] = (("coords"), lnIndLat.data)
    saveDs['xPt']  = (("ptCoords"), lnPtsLon)
    saveDs['yPt']  = (("ptCoords"), lnPtsLat)
    saveDs['slope'] = (outputSlop)

    return saveDs

def testNearestNeighborLookUps(): 
    inputGridFile = './input/raw/uvel/B.E.13.BRCP85C5CN.ne120_t12.sehires38.003.sunway.CN_OFF.pop.h.UVEL.201501-201512.nc'
    raw = xr.open_dataset(inputGridFile)
    ds = nearestNeighborLookUp([90.1], [110.47], raw)
    assert ds.slope == 0
    assert raw.TLAT.data[int(ds.yInd.data),int(ds.xInd.data)] == 89.58695569492419
    assert raw.TLONG.data[int(ds.yInd.data),int(ds.xInd.data)] == 110.2533072722824

def createMask(nlatnlon, inputDS):
    m = nlatnlon.slope
    x = nlatnlon.xInd
    y = nlatnlon.yInd
    itf.PrintToConsole('INFO','Creating mask for %d points'%(len(x)))
    raw = inputDS
    xDim,yDim = raw.ULONG.shape
    yBot = np.array([])
    xBot = np.array([])
    if np.isnan(m): # if vertical line, don't take bottom segment
        yBot = np.array([])
        xBot = np.array([])
    else:    
        for i in range(xDim):
            yToCheck = x==i
            if any(yToCheck):
                yBot = np.concatenate((yBot, np.array([np.min(y[yToCheck])])))
                xBot = np.concatenate((xBot, np.array([i])))
    
    xSide = np.array([])
    ySide = np.array([])
    if m == 0:    # horizontal line
        xSide = np.array([]) # check if okay in the future
        ySide = np.array([])
    elif m > 0:
        for i in range(yDim):
            xToCheck = y==i
            if any(xToCheck):
                xSide = np.concatenate((xSide, np.array([np.max(x[xToCheck])]))) # max: take the right side
                ySide = np.concatenate((ySide, np.array([i])))
    elif m<0 or np.isnan(m): # vertical line or (-) slope: take left
        for i in range(yDim):
            xToCheck = y==i
            if any(xToCheck):
                xSide = np.concatenate((xSide, np.array([np.min(x[xToCheck])])))
                ySide = np.concatenate((ySide, np.array([i])))
    itf.PrintToConsole('DEBUG','Done creating mask.')
    MaskRaw = raw.ULONG
    AllZero = (np.zeros(raw.ULONG.shape))
    AllZero[:] = np.nan
    MaskRaw['sideEdge'] = (("nlat","nlon"),np.copy(AllZero)) # --- Source of bug: was not an np.copy before
    MaskRaw['bottEdge'] = (("nlat","nlon"),np.copy(AllZero))

    MaskRaw.bottEdge.data[yBot.astype(int), xBot.astype(int)]  = 1
    MaskRaw.sideEdge.data[ySide.astype(int),xSide.astype(int)] = 1
    
    MaskDs = MaskRaw.to_dataset(name = 'ULONG_random')
    MaskDs['xBottom'] = (('coorBot'), xBot)
    MaskDs['yBottom'] = (('coorBot'), yBot)
    MaskDs['xLeftRi'] = (('coorSide'), xSide)
    MaskDs['yLeftRi'] = (('coorSide'), ySide)
    MaskDs['slope'] = m
    
    return MaskDs.copy()

class TestCreateMask:
    def testCreateMask_vertical(self):
        inputGridFile = './input/raw/uvel/B.E.13.BRCP85C5CN.ne120_t12.sehires38.003.sunway.CN_OFF.pop.h.UVEL.201501-201512.nc'
        inputDS = xr.open_dataset(inputGridFile)
        xTemp = np.array([2239, 2239, 2239, 2239])
        yTemp = np.array([ 961,  962,  963,  964])
        slopeTemp = np.nan
        
        ToDs = xr.DataArray(
                data = xTemp,
                dims = ["coords"]
        )
        saveDs = ToDs.to_dataset(name = 'xInd')
        saveDs['yInd'] = (("coords"),  yTemp)
        saveDs['slope'] = (slopeTemp)
        
        MaskTemp = createMask(saveDs, inputDS)
        
        assert MaskTemp.yBottom.size == 0
        assert all(MaskTemp.yLeftRi.data == np.array([961., 962., 963., 964.]))
        assert all(MaskTemp.xLeftRi.data == np.array([2239., 2239., 2239., 2239.]))
        
    def testCreateMask_horizontal(self):
        inputGridFile = './input/raw/uvel/B.E.13.BRCP85C5CN.ne120_t12.sehires38.003.sunway.CN_OFF.pop.h.UVEL.201501-201512.nc'
        inputDS = xr.open_dataset(inputGridFile)
        xTemp = np.array([2239, 2240, 2241, 2242])
        yTemp = np.array([ 961,  961,  961,  961])
        slopeTemp = 0
        
        ToDs = xr.DataArray(
                data = xTemp,
                dims = ["coords"]
        )
        saveDs = ToDs.to_dataset(name = 'xInd')
        saveDs['yInd'] = (("coords"),  yTemp)
        saveDs['slope'] = (slopeTemp)
        
        MaskTemp = createMask(saveDs, inputDS)
        
        assert MaskTemp.yLeftRi.size == 0
        assert all(MaskTemp.yBottom.data == np.array([961., 961., 961., 961.]))
        assert all(MaskTemp.xBottom.data == np.array([2239., 2240., 2241., 2242.]))
        
    def testCreateMask_positiveSlope(self):
        inputGridFile = './input/raw/uvel/B.E.13.BRCP85C5CN.ne120_t12.sehires38.003.sunway.CN_OFF.pop.h.UVEL.201501-201512.nc'
        inputDS = xr.open_dataset(inputGridFile)
        xTemp = np.array([2239, 2239, 2240, 2241, 2242])
        yTemp = np.array([ 961,  962,  962,  962,  963])
        slopeTemp = 1
        
        ToDs = xr.DataArray(
                data = xTemp,
                dims = ["coords"]
        )
        saveDs = ToDs.to_dataset(name = 'xInd')
        saveDs['yInd'] = (("coords"),  yTemp)
        saveDs['slope'] = (slopeTemp)
        
        MaskTemp = createMask(saveDs, inputDS)
        
        assert all(MaskTemp.yLeftRi.data == np.array([ 961.,  962.,  963.]))
        assert all(MaskTemp.xLeftRi.data == np.array([2239., 2241., 2242.]))
        assert all(MaskTemp.yBottom.data == np.array([ 961.,  962.,  962.,  963.]))
        assert all(MaskTemp.xBottom.data == np.array([2239., 2240., 2241., 2242.]))
    
    def testCreateMask_negativeSlope(self):
        inputGridFile = './input/raw/uvel/B.E.13.BRCP85C5CN.ne120_t12.sehires38.003.sunway.CN_OFF.pop.h.UVEL.201501-201512.nc'
        inputDS = xr.open_dataset(inputGridFile)
        xTemp = np.array([2239, 2239, 2240, 2240, 2240, 2241])
        yTemp = np.array([ 965,  964,  964,  963,  962,  961])
        slopeTemp = -1
        
        ToDs = xr.DataArray(
                data = xTemp,
                dims = ["coords"]
        )
        saveDs = ToDs.to_dataset(name = 'xInd')
        saveDs['yInd'] = (("coords"),  yTemp)
        saveDs['slope'] = (slopeTemp)
        
        MaskTemp = createMask(saveDs, inputDS)
        
        assert all(MaskTemp.yLeftRi.data == np.array([ 961.,  962.,  963.,  964.,  965.]))
        assert all(MaskTemp.xLeftRi.data == np.array([2241., 2240., 2240., 2239., 2239.]))
        assert all(MaskTemp.yBottom.data == np.array([ 964.,  962.,  961.]))
        assert all(MaskTemp.xBottom.data == np.array([2239., 2240., 2241.]))

def sortingIndices(BotSideMask):
    itf.PrintToConsole('INFO','Sorting indices to figure out velocity sides.')
    xBot  = BotSideMask.xBottom.data 
    yBot  = BotSideMask.yBottom.data
    xSide = BotSideMask.xLeftRi.data
    ySide = BotSideMask.yLeftRi.data
    m = BotSideMask.slope.data
    
    # --- Stack and choose correct order for side
    Bot = np.stack((xBot, yBot))
    if m < 0: # --- vertical or m = np.nan will give runtime warning
        Side = np.stack((np.flip(xSide), np.flip(ySide)))
    else:
        Side = np.stack((xSide, ySide))
    # --- Concatinating the two
    a = np.concatenate((Bot, Side), axis = 1)
    # --- Transforming for sorting
    a = a.T
    # --- Use "unique" to take out repeats
    Uniqued = np.unique(a,axis=0)
    
    # --- Find 'starting point' depending on slope: always leftmost
    minX = np.min(Uniqued[:,0])
    if m < 0: # --- vertical or m = np.nan will give runtime warning
        extY = np.max(Uniqued[:,1]) # left & top for a (-) slope
    else:
        extY = np.min(Uniqued[:,1]) # left & bottom for a (+) slope, vertical, or horizontal
    # --- Find distance from 'starting point'
    Dist = np.sqrt((Uniqued[:,0]-minX)**2 + (Uniqued[:,1]-extY)**2)
    
    # --- Stack 'Dist' onto the 'Uniqued' 2-column array
    All = np.concatenate((Uniqued.T, [Dist]), axis = 0).T
    # --- Sort all by distance
    Arrange = All[All[:,2].argsort()]
    sortedInds = Arrange[:,:2].astype(int)
    
    bot_T = Bot.T
    side_T = Side.T
    if bot_T.size == 0: # empty, like in a vertical line
        BotUniqued = bot_T # just return empty array; pass by reference!
    else:
        BotUniqued = np.unique(bot_T, axis = 0)
    if side_T.size == 0: # empty, like in a horizontal line
        SideUniqued = side_T # just return empty array; pass by reference!
    else:
        SideUniqued = np.unique(side_T, axis = 0)
    BotUniqued = BotUniqued.astype(int)
    SideUniqued = SideUniqued.astype(int)
    
    return sortedInds, BotUniqued, SideUniqued

class TestSortingIndices:
    def testSortingIndices_vertical(self):
        xSideTemp = np.array([2239, 2239, 2239, 2239, 2239, 2239])
        ySideTemp = np.array([ 964,  961,  962,  963,  962,  963])
        xBottTemp = np.array([])
        yBottTemp = np.array([])
        slopeTemp = np.nan
        
        ToDs = xr.DataArray(
                data = xSideTemp,
                dims = ["coorSide"]
        )
        saveDs = ToDs.to_dataset(name = 'xLeftRi')
        saveDs['yLeftRi'] = (("coorSide"),  ySideTemp)
        saveDs['xBottom'] = (("coorBot"),  xBottTemp)
        saveDs['yBottom'] = (("coorBot"),  yBottTemp)
        saveDs['slope'] = (slopeTemp)
        
        sortedInds, BotUniqued, SideUniqued = sortingIndices(saveDs)
        
        assert all(sortedInds[:,0] == np.array([2239, 2239, 2239, 2239]))
        assert all(sortedInds[:,1] == np.array([ 961,  962,  963,  964]))
        assert BotUniqued.size == 0
        assert all(SideUniqued[:,0] == np.array([2239, 2239, 2239, 2239]))
        assert all(SideUniqued[:,1] == np.array([ 961,  962,  963,  964]))

    def testSortingIndices_horizontal(self):
        xSideTemp = np.array([])
        ySideTemp = np.array([])
        xBottTemp = np.array([2240, 2239, 2241, 2239, 2242, 2241])
        yBottTemp = np.array([ 961,  961,  961,  961,  961,  961])
        slopeTemp = 0
        
        ToDs = xr.DataArray(
                data = xSideTemp,
                dims = ["coorSide"]
        )
        saveDs = ToDs.to_dataset(name = 'xLeftRi')
        saveDs['yLeftRi'] = (("coorSide"),  ySideTemp)
        saveDs['xBottom'] = (("coorBot"),  xBottTemp)
        saveDs['yBottom'] = (("coorBot"),  yBottTemp)
        saveDs['slope'] = (slopeTemp)
        
        sortedInds, BotUniqued, SideUniqued = sortingIndices(saveDs)
        
        assert all(sortedInds[:,0] == np.array([2239, 2240, 2241, 2242]))
        assert all(sortedInds[:,1] == np.array([ 961,  961,  961,  961]))
        assert all(BotUniqued[:,0] == np.array([2239, 2240, 2241, 2242]))
        assert all(BotUniqued[:,1] == np.array([ 961,  961,  961,  961]))
        assert SideUniqued.size == 0
        
    def testSortingIndices_positiveSlope(self):
        xSideTemp = np.array([2239, 2241, 2239, 2241])
        ySideTemp = np.array([ 961,  962,  961,  962])
        xBottTemp = np.array([2240, 2241, 2239, 2240, 2241])
        yBottTemp = np.array([ 962,  962,  961,  962,  962])
        slopeTemp = 1
        
        ToDs = xr.DataArray(
                data = xSideTemp,
                dims = ["coorSide"]
        )
        saveDs = ToDs.to_dataset(name = 'xLeftRi')
        saveDs['yLeftRi'] = (("coorSide"),  ySideTemp)
        saveDs['xBottom'] = (("coorBot"),  xBottTemp)
        saveDs['yBottom'] = (("coorBot"),  yBottTemp)
        saveDs['slope'] = (slopeTemp)
        
        sortedInds, BotUniqued, SideUniqued = sortingIndices(saveDs)
        
        assert all(sortedInds[:,0] == np.array([2239, 2240, 2241]))
        assert all(sortedInds[:,1] == np.array([ 961,  962,  962]))
        assert all(BotUniqued[:,0] == np.array([2239, 2240, 2241]))
        assert all(BotUniqued[:,1] == np.array([ 961,  962,  962]))
        assert all(SideUniqued[:,0] == np.array([2239, 2241]))
        assert all(SideUniqued[:,1] == np.array([ 961,  962]))

    def testSortingIndices_negativeSlope(self):
        xSideTemp = np.array([2239, 2239, 2239, 2241, 2240])
        ySideTemp = np.array([ 964,  963,  963,  961,  962])
        xBottTemp = np.array([2239, 2240, 2239, 2241])
        yBottTemp = np.array([ 963,  962,  963,  961])
        slopeTemp = -1
        
        ToDs = xr.DataArray(
                data = xSideTemp,
                dims = ["coorSide"]
        )
        saveDs = ToDs.to_dataset(name = 'xLeftRi')
        saveDs['yLeftRi'] = (("coorSide"),  ySideTemp)
        saveDs['xBottom'] = (("coorBot"),  xBottTemp)
        saveDs['yBottom'] = (("coorBot"),  yBottTemp)
        saveDs['slope'] = (slopeTemp)
        
        sortedInds, BotUniqued, SideUniqued = sortingIndices(saveDs)
        
        assert all(sortedInds[:,0] == np.array([2239, 2239, 2240, 2241]))
        assert all(sortedInds[:,1] == np.array([ 964,  963,  962,  961]))
        assert all(BotUniqued[:,0] == np.array([2239, 2240, 2241]))
        assert all(BotUniqued[:,1] == np.array([ 963,  962,  961]))
        assert all(SideUniqued[:,0] == np.array([2239, 2239, 2240, 2241]))
        assert all(SideUniqued[:,1] == np.array([ 963,  964,  962,  961]))

def UvTransport(uBox, vBox, Dz, Hte, Htn, zMask, BotUniqued, SideUniqued,\
                m):
    itf.PrintToConsole('INFO','Computing transport using u and v.')

    uRaw = uBox
    vRaw = vBox
    
    itf.PrintToConsole('DEBUG','Creating velsSide')   
    # Takes a while -- 2 mins?
    # side
    if m > 0: # positive slope
        velsSide = uRaw.UVEL.data[:, :, SideUniqued[:,1],  SideUniqued[:,0]] * 0.5 + \
                   uRaw.UVEL.data[:, :, SideUniqued[:,1]-1,  SideUniqued[:,0]] * 0.5  #  u_ij then uDown
    elif m == 0: # horizontal
        velsSide = np.nan
    else: # vertical (where m is a nan) or negative:
        velsSide = uRaw.UVEL.data[:, :, SideUniqued[:,1],  SideUniqued[:,0]-1] * 0.5 + \
                   uRaw.UVEL.data[:, :, SideUniqued[:,1]-1,  SideUniqued[:,0]-1] * 0.5 # uLeft then uLeftDown
    
    # bottom
    itf.PrintToConsole('DEBUG','Creating velsBott')
    if np.isnan(m): # vertical
        velsBott = np.nan
    else: # positive slope, vertical, negative slope
        velsBott = vRaw.VVEL.data[:, :, BotUniqued[:,1]-1, BotUniqued[:,0]] * 0.5 + \
                   vRaw.VVEL.data[:, :, BotUniqued[:,1]-1, BotUniqued[:,0]-1] * 0.5 # vDown then vLeftDown

    itf.PrintToConsole('DEBUG','Removing unused z data and removing unused land data')

    # Run mask when slope is not vertical
    if not np.isnan(m):
        bottLandMask = uRaw.REGION_MASK.data[BotUniqued[:,1],   BotUniqued[:,0]]  == -1
        velsBott = velsBott[:,zMask.data,:]
        velsBott[:,:,bottLandMask] = np.nan

    # Run mask when slope is not horizontal
    if np.isnan(m) or m != 0:
        sideLandMask = uRaw.REGION_MASK.data[SideUniqued[:,1],  SideUniqued[:,0]] == -1
        velsSide = velsSide[:,zMask.data,:]
        velsSide[:,:,sideLandMask] = np.nan
    
    itf.PrintToConsole('DEBUG','Multiplying SideZX=dz*dy')     
    SideZ = velsSide * Dz.data[:,None] # u(0) * dz(0)
    SideZX = SideZ * Hte               # u(0) * dz(0) * dy(0)
    
    itf.PrintToConsole('DEBUG','Multiplying BottZX=dz*dx')   
    BottZ = velsBott * Dz.data[:,None] # v(0) * dz(0)
    BottZX = BottZ * Htn               # v(0) * dz(0) * dx(0)
    
    units = 10**(-12)  # cm^3/s to m^3/s to Sv

    itf.PrintToConsole('DEBUG','Removing nans from SideZX and BottZX')       
    SideZX[np.isnan(SideZX)] = 0   # --- safe to set nans to zero, because summing will make them zero
    BottZX[np.isnan(BottZX)] = 0

    itf.PrintToConsole('DEBUG','Summing SideZX and BottZX')
    if np.isnan(m): #vertical so velsBott is empty
        bottSum = np.sum(BottZX) * units # zero
        
        sideSumOverZ = np.sum(SideZX, axis = 1)
        sideSum_time = np.sum(sideSumOverZ, axis = 1)
        sideSum = sideSum_time * units
    elif m == 0: # horizontal so velsSide is empty
        sideSum = np.sum(SideZX) * units # zero
        
        bottSumOverZ = np.sum(BottZX, axis = 1)
        bottSum_time = np.sum(bottSumOverZ, axis = 1)
        bottSum = bottSum_time * units
    else: # positive or negative: do both!
        sideSumOverZ = np.sum(SideZX, axis = 1)
        sideSum_time = np.sum(sideSumOverZ, axis = 1)
        sideSum = sideSum_time * units

        bottSumOverZ = np.sum(BottZX, axis = 1)
        bottSum_time = np.sum(bottSumOverZ, axis = 1)
        bottSum = bottSum_time * units

    if m > 0:
        AllSum = sideSum-bottSum
    else: # vertical, horizontal, or negative sloping
        AllSum = bottSum + sideSum
    
    tPt = ToDsPt(AllSum, uRaw.time_bnds[:,0], 'tPt')

    itf.PrintToConsole('INFO','Computed transport: %s' % tPt.tPt.data)     
    return tPt

def ToDsPt(Arr,Dict1,ArrName):
    ToDs = xr.DataArray(
        data = Arr,
        dims = ["time"],
        coords = dict(
            time = Dict1
        ),
    )
    tTot = ToDs.to_dataset(name = ArrName)
    tTot.attrs['title'] = 'Total transport (Sv) computed using the IX1 transect'
    tTot.attrs['time'] = 'taken from time_bnd variable'
    return tTot

def testUvTransport():
                    # time: 1, z: 3, x: 4, y = 5
    uBox = xr.Dataset(
        data_vars = dict(
            UVEL = (["time","z_t","nlat","nlon"], np.ones(((1, 3, 4, 5)))),
            ULONG = (["nlat","nlon"], np.ones((4,5))),
            ULAT  = (["nlat","nlon"], np.ones((4,5))),
            TLONG = (["nlat","nlon"], np.ones((4,5))),
            TLAT  = (["nlat","nlon"], np.ones((4,5))),
            REGION_MASK  = (["nlat","nlon"], np.ones((4,5))),
            time_bnds = (["time","d2"],np.array([[cftime.DatetimeNoLeap(2015, 1, 1, 0, 0, 0, 0),cftime.DatetimeNoLeap(2015, 2, 1, 0, 0, 0, 0)]]))
        ),
        coords = dict(
            time = np.array([0]),
            z_t    = np.array([0,1,2]),
            nlat = np.array([0,1,2,3]),
            nlon = np.array([0,1,2,3,4]),
            d2 = np.array([0,1])
        ),
        attrs=dict(
            title = 'Test dataset for testUvTransport'
        ),
    )
    vBox = xr.Dataset(
        data_vars = dict(
            VVEL = (["time","z_t","nlat","nlon"], np.ones(((1, 3, 4, 5)))),
            ULONG = (["nlat","nlon"], np.ones((4,5))),
            ULAT  = (["nlat","nlon"], np.ones((4,5))),
            TLONG = (["nlat","nlon"], np.ones((4,5))),
            TLAT  = (["nlat","nlon"], np.ones((4,5))),
            REGION_MASK  = (["nlat","nlon"], np.ones((4,5))),
            time_bnds = (["time","d2"],np.array([[cftime.DatetimeNoLeap(2015, 1, 1, 0, 0, 0, 0),cftime.DatetimeNoLeap(2015, 2, 1, 0, 0, 0, 0)]]))
        ),
        coords = dict(
            time = np.array([0]),
            z_t    = np.array([0,1,2]),
            nlat = np.array([0,1,2,3]),
            nlon = np.array([0,1,2,3,4]),
            d2 = np.array([0,1])
        ),
        attrs=dict(
            title = 'Test dataset for testUvTransport'
        ),
    )

    Dz = xr.DataArray(
        data = np.array([1,1,1]),
        dims = ["z_t"],
        coords = dict(
            z_t = np.array([0,1,2])
        ),
    )

    Hte = np.ones(4)
    Htn = np.ones(5)
    zMask = np.array([True, True, True]) # 3 in depth
    BotUniqued = np.array(([0,1,2,3,4],[0,1,2,3,3]))
    BotUniqued = BotUniqued.T
    SideUniqued = np.array(([0,1,2,4],[0,1,2,3]))
    SideUniqued = SideUniqued.T
    m = 1
    
    tPt = UvTransport(uBox, vBox, Dz, Hte, Htn, zMask, BotUniqued, SideUniqued, m)

    assert tPt.tPt.data[0] == -2.9999999999999993e-12

def testHorizontalTransect():
                    # time: 1, z: 3, x: 4, y = 5
    uBox = xr.Dataset(
        data_vars = dict(
            UVEL = (["time","z_t","nlat","nlon"], np.ones(((1, 3, 4, 5)))),
            ULONG = (["nlat","nlon"], np.ones((4,5))),
            ULAT  = (["nlat","nlon"], np.ones((4,5))),
            TLONG = (["nlat","nlon"], np.ones((4,5))),
            TLAT  = (["nlat","nlon"], np.ones((4,5))),
            REGION_MASK  = (["nlat","nlon"], np.ones((4,5))),
            time_bnds = (["time","d2"],np.array([[cftime.DatetimeNoLeap(2015, 1, 1, 0, 0, 0, 0),cftime.DatetimeNoLeap(2015, 2, 1, 0, 0, 0, 0)]]))
        ),
        coords = dict(
            time = np.array([0]),
            z_t    = np.array([0,1,2]),
            nlat = np.array([0,1,2,3]),
            nlon = np.array([0,1,2,3,4]),
            d2 = np.array([0,1])
        ),
        attrs=dict(
            title = 'Test dataset for testUvTransport'
        ),
    )
    vBox = xr.Dataset(
        data_vars = dict(
            VVEL = (["time","z_t","nlat","nlon"], np.ones(((1, 3, 4, 5)))),
            ULONG = (["nlat","nlon"], np.ones((4,5))),
            ULAT  = (["nlat","nlon"], np.ones((4,5))),
            TLONG = (["nlat","nlon"], np.ones((4,5))),
            TLAT  = (["nlat","nlon"], np.ones((4,5))),
            REGION_MASK  = (["nlat","nlon"], np.ones((4,5))),
            time_bnds = (["time","d2"],np.array([[cftime.DatetimeNoLeap(2015, 1, 1, 0, 0, 0, 0),cftime.DatetimeNoLeap(2015, 2, 1, 0, 0, 0, 0)]]))
        ),
        coords = dict(
            time = np.array([0]),
            z_t    = np.array([0,1,2]),
            nlat = np.array([0,1,2,3]),
            nlon = np.array([0,1,2,3,4]),
            d2 = np.array([0,1])
        ),
        attrs=dict(
            title = 'Test dataset for testUvTransport'
        ),
    )

    Dz = xr.DataArray(
        data = np.array([1,1,1]),
        dims = ["z_t"],
        coords = dict(
            z_t = np.array([0,1,2])
        ),
    )

    Hte = np.array([np.nan])
    Htn = np.ones(5)
    zMask = np.array([True, True, True]) # 3 in depth
    BotUniqued = np.array(([0,1,2,3,4],[1,1,1,1,1]))
    BotUniqued = BotUniqued.T
    SideUniqued = np.array(([],[])) # SideUniqued is empty bec horizontal line
    SideUniqued = SideUniqued.T
    m = 0
    
    tPt = UvTransport(uBox, vBox, Dz, Hte, Htn, zMask, BotUniqued, SideUniqued, m)

    assert round(tPt.tPt.data[0],13) == 1.5e-11
 
def main():
    # --- Defining input arguments using the argparse library
    parser = argparse.ArgumentParser(description='Compute transport on transect line using iHESP CESM1.3 HighRes NetCDF input using python and CDO (Climate Data Operators)')
    parser.add_argument('-d','--debug', action = 'store_true',
                        help='Enable DEBUG outputs')
    parser.add_argument('-g','--generate-intermediates-only', action = 'store_true',
                        help='Only generate the intermidiate files, *_nearestNeighbors.nc and *_maskBotAndSideEdges.nc, then exit')
    parser.add_argument('-f','--force', action = 'store_true',
                        help='Always regenerate all files (default: skip recomputing existing files)')
    parser.add_argument('-b','--box', action = 'store_true',
                        help='Generate smaller input files from UFILE_FILE and VFILE_FILE using "cdo selindexbox"')
    parser.add_argument('-u','--ufile', metavar = 'UFILE_FILE',
                         help='CF compliant iHESP CESM1.3 HighRes file that contains U velocities')
    parser.add_argument('-v','--vfile', metavar = 'VFILE_FILE',
                         help='CF compliant iHESP CESM1.3 HighRes file that contains V velocities')
    parser.add_argument('-t','--tag', metavar = 'TAG',
                         help='String to append at the end the output file, i.e.: *_totalUV_TAG.nc ')
    parser.add_argument('transect_file', metavar='TRANSECT_FILE',
                        help='File that contains input parameters for this transect. TRANSECT_FILE is also used for intermidiate and output file prefixes, e.g. TRANSECT_FILE_totalUV.nc')
    
    args = parser.parse_args() # ['-d']

    # --- Input arguments into variables
    itf.ShowDebug = args.debug
    
    itf.PrintToConsole('INFO','Starting')
    if args.debug == True:
        itf.PrintToConsole('DEBUG','Debug mode detected')
    if args.generate_intermediates_only == True:
        itf.PrintToConsole('INFO','--generate-input-only is set, will not compute transport, only generate files')
    else:
        if args.ufile is None or args.vfile is None:
            itf.PrintToConsole('ERROR','--generate-input-only is not set, so --ufile and --vfile must be set')
            return

    if args.ufile is not None:
        itf.PrintToConsole('INFO','ufile: %s' % args.ufile)
    if args.vfile is not None:
        itf.PrintToConsole('INFO','vfile: %s' % args.ufile)
    if args.tag is not None:
        itf.PrintToConsole('INFO','tag: "%s" detected, will create "*_totalUV_%s.nc" output if able' % (args.tag, args.tag))
    
    # --- Treat input text file as .env and save to variables
    transectFileContents = dotenv_values(args.transect_file)  
    lats = np.fromstring(transectFileContents["lats"], sep=',')
    lons = np.fromstring(transectFileContents["lons"], sep=',')
    xyResolution = float(transectFileContents["xyResolution"])
    MapExtent = itf.LatLonBox( \
        north = float(transectFileContents["north"]),\
        south = float(transectFileContents["south"]),\
        east = float(transectFileContents["east"]),\
        west = float(transectFileContents["west"])\
    )

    boxDir = transectFileContents["boxDir"]

    # For example, 'outputDir=./output/transects/Transect01/'
    outputDir = transectFileContents["outputDir"]
    # transectDirPath = './output/transects/Transect01/'
    transectDirPath = outputDir
    # create folder if it doesn't exist
    os.makedirs(transectDirPath, exist_ok = True)
    
    # transectFilePrefix = 'Transect01' which is the basename of Transect01.txt which is the name of the input file.
    transectFilePrefix = os.path.splitext(os.path.basename(args.transect_file))[0]
    # transectSavePath is './output/transects/Transect01/Transect01'
    transectSavePath = "%s/%s" % (transectDirPath, transectFilePrefix)
    
    # Create filename from transectSavePath
    # for example, './output/transects/Transect01/Transect01_totalUV.nc' if no tag, or adds tag before '.nc'
    filename = "%s_totalUV.nc" % (transectSavePath)
    if args.tag is not None:
        filename = "%s_totalUV_%s.nc" % (transectSavePath, args.tag)
    # Skip entire code if totalUV file already exists
    fileExists = os.path.isfile('%s'%(filename))
    if fileExists == True and args.force == False:
        itf.PrintToConsole('INFO','%s already exists, exiting' % filename)
        return


    # --- Main logic    

    # --- 1. Create points on line
    lnPtsLat, lnPtsLon, Err = CreatePointsOnLine(lats, lons, xyResolution)
    
    if Err != '' :
        # checking CreatePointsOnLine errors
        itf.PrintToConsole('ERROR','Got error from CreatePointsOnLine: %s' % Err)
        return
    
    # --- 2. Cut away excess area in u,v files 
    ToInclude='TLONG,TLAT,ULONG,ULAT,HTE,HTN,dz,REGION_MASK'

    # --- 2.1 Check if U file exists
    uFile = args.ufile
    if gridFileHasMapExtents(uFile, MapExtent) == False:
        itf.PrintToConsole('ERROR','%s does not contain [%f, %f, %f, %f]' % (uFile, MapExtent.west, MapExtent.east, MapExtent.south, MapExtent.north))
        return

    # --- 2.2 Check if V file exists
    vFile = args.vfile
    if gridFileHasMapExtents(vFile, MapExtent) == False:
        itf.PrintToConsole('ERROR','%s does not contain [%f, %f, %f, %f]', uFile, MapExtents.west, MapExtents.east, MapExtents.south, MapExtents.north)
        return

    if args.box == True:
        itf.PrintToConsole('DEBUG','--box detected')
       
        # Because of resultion spacing, we add an offset and use this when actually doing cdo
        MapExtentWithOffset = itf.LatLonBox( \
            north = MapExtent.north + 0.5, \
            south = MapExtent.south - 0.5, \
            west = MapExtent.west - 0.5, \
            east = MapExtent.east + 0.5 \
        )

        itf.PrintToConsole('DEBUG','Original bounds of run was [%f, %f, %f, %f]' % ( MapExtent.west, MapExtent.east, MapExtent.south, MapExtent.north))
        itf.PrintToConsole('DEBUG','Original bounds of run with offsets is [%f, %f, %f, %f]' % ( MapExtentWithOffset.west, MapExtentWithOffset.east, MapExtentWithOffset.south, MapExtentWithOffset.north))
        
        # --- 2.3 Check if U cdo-cut files exists and have expected variables
        ToIncludeU = 'UVEL,%s' % ToInclude
        uBoxFilename = cdof.GenerateMakeBoxSavePath(uFile, MapExtent, boxDir)
        fileExists = os.path.isfile('%s'%(uBoxFilename))
        willRecomputeUbox = False

        if fileExists == True:
            itf.PrintToConsole('DEBUG', '%s exists' % uBoxFilename)
            uBox = xr.open_dataset(uBoxFilename)
            areAllUVarsInDS, err = itf.areAllVarsInDS(ToIncludeU, uBox)
            if areAllUVarsInDS == False:
                itf.PrintToConsole('ERROR', 'itf.areAllVarsInDS error: %s' % err)
                return
            else:
                willRecomputeUbox = False
                itf.PrintToConsole('INFO', '%s is detected in uBox' % ToIncludeU)
        else:
            itf.PrintToConsole('DEBUG', '%s does not exist yet' % uBoxFilename)
            willRecomputeUbox = True

        if willRecomputeUbox == True or args.force == True:
            if args.force==True:
                itf.PrintToConsole('INFO', 'Force flat detected.')

            uBoxFilename = cdof.MakeBoxIndex(inputFile = uFile, bounds = MapExtentWithOffset, toInclude = ToIncludeU, outputFile = uBoxFilename)

            uBox = xr.open_dataset(uBoxFilename)
            areAllUVarsInDS, err = itf.areAllVarsInDS(ToIncludeU, uBox)
            if areAllUVarsInDS == False:
                itf.PrintToConsole('ERROR', 'itf.areAllVarsInDS error: %s' % err)
                return
            else:
                itf.PrintToConsole('INFO', '%s is detected in uBox' % ToIncludeU)

        # --- 2.4 Check if V cdo-cut files exists and have expected variables
        ToIncludeV = 'VVEL,%s' % ToInclude
        vBoxFilename = cdof.GenerateMakeBoxSavePath(vFile, MapExtent, boxDir)
        fileExists = os.path.isfile('%s'%(vBoxFilename))
        willRecomputeVbox = False

        if fileExists == True:
            vBox = xr.open_dataset(vBoxFilename)
            areAllVVarsInDS, err = itf.areAllVarsInDS(ToIncludeV, vBox)
            if areAllVVarsInDS == False:
                itf.PrintToConsole('ERROR', 'itf.areAllVarsInDS error: %s' % err)
                return
            else:
                willRecomputeVbox = False
                itf.PrintToConsole('INFO', '%s is detected in vBox' % ToIncludeV)
        else:
            willRecomputeVbox = True

        if willRecomputeVbox == True or args.force == True:
            if args.force == True:
                itf.PrintToConsole('INFO', 'Force flag detected.')

            vBoxFilename = cdof.MakeBoxIndex(inputFile = vFile, bounds = MapExtentWithOffset, toInclude = ToIncludeV, outputFile = vBoxFilename)
            
            vBox = xr.open_dataset(vBoxFilename)
            areAllVVarsInDS, err = itf.areAllVarsInDS(ToIncludeV, vBox)
            if areAllVVarsInDS == False:
                itf.PrintToConsole('ERROR', 'itf.areAllVarsInDS error: %s' % err)
                return
            else:
                itf.PrintToConsole('INFO', '%s is detected in vBox' % ToIncludeV)

    else:
        vBox = xr.open_dataset(vFile)
        uBox = xr.open_dataset(uFile)

    # --- 3. Check existing nearest neighbor hash if needs to be regenerated
    compute_nearestneighbor = False
    filename = "%s_nearestNeighbors.nc" % transectSavePath
    fileExists = os.path.isfile('%s'%(filename))
    if fileExists == True and "nearestNeighborsMD5" in transectFileContents:
        itf.PrintToConsole('INFO','%s detected, checking if hash matches hash found on transect_file input txt' % filename)
        filenamehash = itf.ComputeMD5(filename)
        expectedhash = transectFileContents["nearestNeighborsMD5"]
        if filenamehash != expectedhash:
            itf.PrintToConsole('INFO', 'Computed: %s does not match expected: %s' % (filenamehash, expectedhash))
            compute_nearestneighbor = True
        else:
            itf.PrintToConsole('INFO', 'Computed: %s matches expected: %s' % (filenamehash, expectedhash))
            nlatnlon = xr.open_dataset(filename)
    else:
        itf.PrintToConsole('INFO','%s does not exist, and/or "nearestNeighborsMD5" is not set on %s' % (filename, args.transect_file))
        compute_nearestneighbor = True

    # --- 3.1 Do nearest neighbor look-up using smaller u and v files
    if compute_nearestneighbor == True or args.force == True:
        if args.force == True:
            itf.PrintToConsole('INFO', 'Force flag detected.')
        # --- arbitrary choice of uBox: vBox can also work
        nlatnlon = nearestNeighborLookUp(lnPtsLat, lnPtsLon, uBox)

        itf.PrintToConsole('INFO','Creating %s' % filename)
        nlatnlon.to_netcdf(filename)
        nearestNeighborsMD5 = itf.ComputeMD5(filename)

    # --- 4. Check existing mask hash if needs to be regenerated
    compute_mask = False
    filename = "%s_maskBotAndSideEdges.nc" % transectSavePath
    fileExists = os.path.isfile('%s'%(filename))
    if fileExists == True and "maskBotAndSideEdgesMD5" in transectFileContents:
        itf.PrintToConsole('INFO','%s detected, checking if hash matches hash found on transect_file input txt' % filename)
        filenamehash = itf.ComputeMD5(filename)
        expectedhash = transectFileContents["maskBotAndSideEdgesMD5"]
        if filenamehash != expectedhash:
            itf.PrintToConsole('INFO', 'Computed: %s does not match expected: %s' % (filenamehash, expectedhash))
            compute_mask = True
        else:
            itf.PrintToConsole('INFO', 'Computed: %s matches expected: %s' % (filenamehash, expectedhash))
            BotSideMask = xr.open_dataset(filename)
    else:
        itf.PrintToConsole('INFO','%s does not exist, and/or "maskBotAndSideEdgesMD5" is not set on %s' % (filename, args.transect_file))
        compute_mask = True
        
    # --- 4.1 Do createMask function, which determines if points are at the 'bottom' or 'side'
    if compute_mask == True or args.force == True:
        if args.force == True:
            itf.PrintToConsole('INFO', 'Force flag detected.')
        # --- arbitrary choice of uBox: vBox can also work
        BotSideMask = createMask(nlatnlon, uBox) # this can also be loaded
        
        itf.PrintToConsole('INFO','Creating %s' % filename)
        BotSideMask.to_netcdf(filename)
        nearestNeighborsMD5 = itf.ComputeMD5(filename)

    # --- 5. Exit if --generate-input-only is set
    if args.generate_intermediates_only == True:
        itf.PrintToConsole('INFO','--generate-input-only is set, exiting')
        return

    # --- 6. Sort indices
    sortedInds, BotUniqued, SideUniqued = sortingIndices(BotSideMask)

    # --- 7. Prepare UvTransport input variables for depth, deltaX, deltaY
    maxDepthofObs = 400*100

    # used hard coded z_w_bot that is only applicable for datasets under iHESP CESM1.3 High res
    zMask = z_w_bot < maxDepthofObs # mask in z
    deltaZ = uBox.dz[zMask.data]
    
    slope = BotSideMask.slope.data
    
    # HTE is for the side
    if slope > 0: # positive slope: HTE of i,j
        hteTemp = uBox.HTE.data[SideUniqued[:,1],  SideUniqued[:,0]]
    elif slope == 0: # horizontal
        hteTemp = np.nan
    else: # vertical (m is a nan) or negative: HTE of i-1,j
        hteTemp = uBox.HTE.data[SideUniqued[:,1],  SideUniqued[:,0]-1]
    
    # HTN is for the bottom
    if np.isnan(slope): # vertical
        htnTemp = np.nan
    else: # positive slope, vertical, negative slope
        htnTemp = vBox.HTN.data[BotUniqued[:,1]-1, BotUniqued[:,0]]
        
    bottLandMask = uBox.TLONG.data[BotUniqued[:,1]-1, BotUniqued[:,0]] == -1
    sideLandMask = uBox.TLONG.data[SideUniqued[:,1],  SideUniqued[:,0]] == -1    
    
    if args.tag is not None:
        itf.PrintToConsole('INFO','Processing run tagged: %s' % (args.tag))
    
    # --- 7.1 Compute transport
    tPt = UvTransport(uBox, vBox, deltaZ, hteTemp, htnTemp, zMask, BotUniqued, \
                      SideUniqued, slope)

    filename = "%s_totalUV.nc" % (transectSavePath)
    if args.tag is not None:
        filename = "%s_totalUV_%s.nc" % (transectSavePath, args.tag)
        
    itf.PrintToConsole('INFO','Creating %s' % filename)
    tPt.to_netcdf(filename)
    nearestNeighborsMD5 = itf.ComputeMD5(filename)
    
    itf.PrintToConsole('INFO','Done.')
    return 0

if __name__ == "__main__":
    main()
