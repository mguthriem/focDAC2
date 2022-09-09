# script to read history of a workspace that has been subjected to a bin mask
# this is then stored as a python dictionary and saved so it can subsequently be applied to 
# other runs (e.g. to calculate vanadium correction)
#
# Steps to generate bin mask:
#
# 1) show instrument view
# 2) select xmin and xmax (using slider or input boxes)
# 3) draw mask as necessary between those limits
# 4) click Apply bin mask to view
# 5) repeat steps 1-4 until mask is defined
# 6) click apply to data
# 7) run this script on that workspace
# 8) the info on the masked bins is written to a json file
# 9) this can be applied by successive `MaskBins` operations on a second ws with identical binning to original (masked) ws
#
# 20220815 M. Guthrie added output recording units. This is important
#
from mantid.simpleapi import *
import matplotlib.pyplot as plt
import numpy as np
import json

inputWS = 'snap48746lite' #contains masked bins
outputLoc = '/SNS/SNAP/IPTS-24179/shared/'
outputName = 'snap48746lite'

ws = mtd[inputWS]
h = ws.getHistory()
xmins = []
xmaxs = []
spectraLsts = []
for hi in h:
    if hi.name() == 'MaskBins':
        #print(f'xmin: {hi.values()[4].value}')
        #print(f'xmax: {hi.values()[5].value}')
        #print(hi.getProperty('InputWorkspaceIndexSet').valueAsStr)
        xmins.append(hi.values()[4].value)
        xmaxs.append(hi.values()[5].value)
        spectraLsts.append(hi.getProperty('InputWorkspaceIndexSet').valueAsStr)
unit = ws.getAxis(0).getUnit().caption()
mskBinsDict = {'units':unit,'xmins':xmins, 'xmaxs':xmaxs, 'spectraLsts':spectraLsts}
print(f'Found {len(xmins)} MaskBins operations in history.')
newDictFile = outputLoc + outputName + '_binMskInfo.json'
with open(newDictFile, "w") as outfile:
    json.dump(mskBinsDict, outfile)
print('\nCreated:' + newDictFile)

#Apply same mask to another ws
#for i in range(len(xmins)):
#    MaskBins(InputWorkspace='VmB_8x8', InputWorkspaceIndexType='WorkspaceIndex',
#    InputWorkspaceIndexSet=spectraLsts[i],
#    OutputWorkspace='VmB_8x8_msk',
#    XMin=xmins[i],
#    XMax=xmaxs[i])
#print('done')
