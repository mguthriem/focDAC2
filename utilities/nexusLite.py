def superID(nativeID,xdim,ydim):
    import numpy as np
    #accepts a numpy array of native ID from standard SNAP nexus file and returns a numpy array with 
    # super pixel ID according to 
    #provided dimensions xdim and ydim of the super pixel. xdim and ydim shall be multiples of 2
    #

    Nx = 256 #native number of horizontal pixels 
    Ny = 256 #native number of vertical pixels 
    NNat = Nx*Ny #native number of pixels per panel
    
    firstPix = (nativeID // NNat)*NNat
    redID = nativeID % NNat #reduced ID beginning at zero in each panel
    
    (i,j) = divmod(redID,Ny) #native (reduced) coordinates on pixel face
    superi = divmod(i,xdim)[0]
    superj = divmod(j,ydim)[0]

    #some basics of the super panel   
    superNx = Nx/xdim #32 running from 0 to 31
    superNy = Ny/ydim
    superN = superNx*superNy

    superFirstPix = (firstPix/NNat)*superN
    
    super = superi*superNy+superj+superFirstPix
    super = super.astype('int')

#     print('native ids: ',nativeID)
#     print('first pixels: ',firstPix)
#     print('super first pixels: ',superFirstPix)
    
    
    return super
    
import numpy as np
import h5py
import shutil
import time
print('h5py version:',h5py.__version__)

time_0 = time.time()

run = 48746
sumNeigh = [8,8]
inFileName = f'SNAP_{run}.nxs.h5'
outFileName = f'SNAP_{run}.lite.nxs.h5'

#
# Step 1) make a copy of the original file
#

print(f'Copying file: {inFileName}')
shutil.copyfile(inFileName,outFileName)

stepTime = time.time() - time_0
totTime = stepTime
print(f'    Time to complete step: {stepTime:.4f} sec. Total time to execute: {totTime:.4f}')


print('Relabelling pixel IDs')
h5obj = h5py.File(outFileName,'r+')

#
# Step 2) Relabel pixel IDs
#
time_0 = time.time()

#Create list of SNAP panel IDs
detpanel = []
for i in range(1,7):
    for j in range(1,4):
        detpanel.append(str(i)+str(j))
        
#Relabel pixel IDs and write to copied file
for panel in detpanel:
    h5eventIDs = h5obj[f'entry/bank{panel}_events/event_id']
    eventIDs = np.array(h5eventIDs[:])
    superEventIDs = superID(eventIDs,sumNeigh[0],sumNeigh[0])
    h5eventIDs[...]=superEventIDs

stepTime = time.time() - time_0
totTime += stepTime
print(f'    Time to complete step: {stepTime:.4f} sec. Total time to execute: {totTime:.4f}')

#
# Step 3: Update instrument definition in nxs file
#
time_0 = time.time()

print('Updating instrument definition')
h5IDF = h5obj['entry/instrument/instrument_xml/data']
stringIDF = str(h5IDF[0],encoding='ascii')#[:] #a string containing the IDF
lines = stringIDF.split('\n')
newLines = []
for line in lines:
    if '<component type="panel"' in line:
        splitLine = line.split("\"")
#        print('Original pixel numbering:',int(splitLine[3]),'step by row:',int(splitLine[7]))
        idstart = int(splitLine[3])
        idstepbyrow = int(splitLine[7])
        newidstart=str(int((idstart/65536)*32**2))
        newidstepbyrow = str(int(idstepbyrow/sumNeigh[0]))
        splitLine[3]=newidstart
        splitLine[7]=newidstepbyrow
        newLines.append("\"".join(splitLine))
#        print('New line:\n',"\"".join(splitLine))
    elif 'xpixels=' in line:
        splitLine = line.split("\"")
        splitLine[1]="32"
        splitLine[3]="-0.076632"
        splitLine[5]="+0.004944"
        newLines.append("\"".join(splitLine))
    elif 'ypixels=' in line:
        splitLine = line.split("\"")
        splitLine[1]="32"
        splitLine[3]="-0.076632"
        splitLine[5]="+0.004944"
        newLines.append("\"".join(splitLine))
    elif 'left-front-bottom-point' in line:
        splitLine = line.split("\"")
        splitLine[1]='-0.002472'
        splitLine[3]='-0.002472'
        newLines.append("\"".join(splitLine))
    elif 'left-front-top-point' in line:
        splitLine = line.split("\"")
        splitLine[1]='0.002472'
        splitLine[3]='-0.002472'
        newLines.append("\"".join(splitLine))
    elif 'left-back-bottom-point' in line:
        splitLine = line.split("\"")
        splitLine[1]='-0.002472'
        splitLine[3]='-0.002472'
        newLines.append("\"".join(splitLine))
    elif 'right-front-bottom-point' in line:
        splitLine = line.split("\"")
        splitLine[1]='0.002472'
        splitLine[3]='-0.002472'
        newLines.append("\"".join(splitLine))        
    else:
        newLines.append(line)
        
newXMLString = "\n".join(newLines)
#print(f'Created edited string of length: {len(newXMLString)}')
#print(f'isascii returns {newXMLString.isascii()}')

h5IDF[...]=newXMLString#.encode(encoding='ascii')
h5obj.close()

#n.b. this is done crudely and dangerously...but taking too long to figure out properly
#will only work for 

#
# Finish up
#
stepTime = time.time() - time_0
totTime += stepTime
print(f'    Time to complete step: {stepTime:.4f} sec. Total time to execute: {totTime:.4f}')
