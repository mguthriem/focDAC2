from mantid.simpleapi import *
import json
import numpy as np
import os
#import SNAPStateParMgr as prm
import SNAP_InstPrm as iPrm

def initPrm(run,case='before'):
  # This creates and returns a dictionary with all necessary run-specific parameters
  # All properties that can be determined soley from the run-number are populated, others
  # are just left empty.
  # 
  # It also looks up the state-specific parameters. for now, these are kept in separate dictionaries  

  iptsPath = GetIPTS(RunNumber=run, instrument=iPrm.inst)
  rPrm = {
    'RunNo':run,
    'maskFileName':'',
    'maskFileLoc':iptsPath + iPrm.sharedDirLoc,
    'runIPTS': iptsPath,
    'gsasFileLoc':iptsPath + iPrm.reducedDirLoc
  }

  return rPrm

def checkStateChange(run,sPrm):
  #checks if state of run is different from current state

  runStateID,runStateDict = StateFromRunFunction(run)
  return runStateID == sPrm['stateID']

def setupStateGrouping(sPrm):

  #Create grouping workspaces to be used for all runs
  gpString = 'TOF_rawVmB'
  for focGrp in sPrm['focGroupLst']:
    CreateGroupingWorkspace(InstrumentName=iPrm.inst,
    GroupDetectorsBy=focGrp,
    OutputWorkspace=f'{iPrm.inst}{focGrp}Gp')
    gpString = gpString + ',' + f'{iPrm.inst}{focGrp}Gp'

  GroupWorkspaces(InputWorkspaces=gpString,
    OutputWorkspace='CommonRed'
    )

  print('State groups initialised')


def getStatePrm(run,case='before'):
  #purpose: 
  # 1) shall determine state-ID the basis of run number. 
  # 2) shall determine corresponding state folder
  # 3) shall search this folder for calibration info files (meaning calibrations have been performed)
  # 4) if no calibration exists, exit gracefully.
  # 5) if calibration exists shall choose the most recent calibration preceding (or, if specified, following) run 
  # 6) shall read this and return a dictionary containing its values
  #
  # Parameters
  # run is an integer specifying the run number of the  measurement of interest
  # case is a string used to specify difference scenarios in which to operate. Allowed values are: 
  # case = 'before' where the calibration was measured before run (or is run)
  # case = 'after' where the calibration was measured after run (or is run)
  # case = 'manual' where calibration will be manually selected
  import SNAP_InstPrm as iPrm
  import json
  import yaml #
  import numpy as np 

  stateID,stateDict = StateFromRunFunction(run)

  calibPath = iPrm.stateLoc + stateID + '/'
  calibSearchPattern=f'{calibPath}{iPrm.calibFilePre}*.{iPrm.calibFileExt}'
  calibFileList = findMatchingFileList(calibSearchPattern)
  if len(calibFileList)==0:
    print(f'ERROR!: state {stateID} is uncalibrated')
    return

  #case manual
  if case.lower() == 'manual':
    print('Index - Calibration File')
    for i,str in enumerate(calibFileList):
      print(f'{i} - {str}\n')
    calIndx = int(input('Enter index of desired calibration file:'))
  else: 
    calibRunList = []
    for str in calibFileList:
      runStr = str[str.find(iPrm.calibFilePre)+len(iPrm.calibFilePre):].split('.')[0]
      calibRunList.append(int(runStr))

    relRuns = [ x-run for x in calibRunList ] 
    #this will have negative values for calibs in calibFileList measured before run
    #positive values for calibs measured after run and zero iff run was a calibration run. 
    
    #zer = [i for i,val in enumerate(relRuns)if val==0 ] #contains indices of all runs identical to run 
    pos  = [i for i,val in enumerate(relRuns)if val >= 0] #contains indices of all runs after and including run
    neg  = [i for i,val in enumerate(relRuns)if val <= 0] #contains indices of all runs before run including run

    #independent of case return calib run equal to run    
    # if len(zer)!=0:
    #   calIndx = zer[0]
    #   break

    if case.lower() == 'before':
      if len(neg) == 0:
        print(f'ERROR!: no calibration matching request available in state {stateID}')
        return
      else:
        closestBefore = max([calibRunList[i] for i in neg]) #closest run number
        calIndx = calibRunList.index(closestBefore) #its index
    elif case.lower() == 'after':
      if len(pos) == 0:
        print(f'ERROR!: no calibration matching request available in state {stateID}')
        return
      else:
        closestAfter = min([calibRunList[i] for i in pos])
        calIndx = calibRunList.index(closestAfter)

  #print(f'successfully found calibration file: \n {calibFileList[calIndx]}')
  
  #Now read this to populate the state dictionary
  with open(calibFileList[calIndx], "r") as json_file:
    dictIn = json.load(json_file)
  #print('got config dictionary')
  return dictIn

def findMatchingFileList(pattern):
  import glob
  import os

  fileList = []
  for fname in glob.glob(pattern, recursive=True):
    if os.path.isfile(fname):
      fileList.append(fname)
  return fileList 

# def setIPTS(Run,rPrm):
#   #updates 
#   IPTSLoc= GetIPTS(RunNumber=Run,Instrument=iPrm.inst)
#   return IPTSLoc

def preProcSNAP(Run,rPrm,sPrm,CU): #initial steps of reduction
  #preliminary normalisation (to proton charge)
  #calibration, compression of events and summing neighbours to 8x8 superpixels 
  #input: Run: a single run number as integer
  #rPrm a dictionary with run parameters
  #sPrm a dictionary with state parameters
  #CU a flag if True, use convert units instead of applying a calibration
  
  #output: single mantid workspace in TOF
  runIPTS= rPrm['runIPTS'] 
  
  LoadEventNexus(Filename=f'{runIPTS}{iPrm.nexusDirLoc}{iPrm.nexusFilePre}{Run}{iPrm.nexusFileExt}',
  OutputWorkspace=f'TOF_{Run}',
  FilterByTofMin=sPrm['tofMin'], 
  FilterByTofMax=sPrm['tofMax'], Precount='1',
  LoadMonitors=True)
  
  NormaliseByCurrent(InputWorkspace=f'TOF_{Run}',
  OutputWorkspace=f'TOF_{Run}')

  CompressEvents(InputWorkspace=f'TOF_{Run}',
  OutputWorkspace=f'TOF_{Run}',
  WallClockTolerance=sPrm['wallClockTol'])

  if not CU:
    ApplyDiffCal(InstrumentWorkspace=f'TOF_{Run}',
    CalibrationFile=iPrm.stateLoc+sPrm['stateID']+'/'+sPrm['calFileName'])

  SumNeighbours(InputWorkspace=f'TOF_{Run}',
  OutputWorkspace=f'TOF_{Run}',
  SumX=sPrm['superPixEdge'],
  SumY=sPrm['superPixEdge']
  )
  return f'TOF_{Run}'

####################################################################################
#Before processing runs, need to make a partial vanadium correction. This is currently an 
#approximation, but written in a way that a correct approach can be implemented in 
#the future.
#The goal here is to create and store a nexus file that contains V minus B in as a function 
#of wavelength, with full* instrument defintion (*subject to compression as defined in 
#loadandprepSNAP) and rebinned to remove events

def makeRawVCorr(VRun,VBRun,case):

  sPrm = getStatePrm(VRun,case)
  rPrm = initPrm(VRun,case) 
  Vws = preProcSNAP(VRun,rPrm,sPrm,False)

  #by definition, state must be the same for V and VB, so don't update
  #TODO: create a script that returns true if two input runs
  #are in the same state
  #
  #TODO: make able to handle VRun and VBRun being lists

  rPrm = initPrm(VBRun,case) 
  VBws = preProcSNAP(VBRun,rPrm,sPrm, False)

  #I'm aware that an attenuation correction should be done here, but not yet implemented.
  Minus(LHSWorkspace=Vws,
  RHSWorkspace=VBws,
  OutputWorkspace='TOF_rawVmB')

  Rebin(InputWorkspace='TOF_rawVmB',
  OutputWorkspace='TOF_rawVmB',
  Params=[sPrm['tofMin'],sPrm['tofBin'],sPrm['tofMax']],
  PreserveEvents=False)

  #Attenuation correction can follow: https://github.com/neutrons/mantid_total_scattering/blob/next/total_scattering/reduction/total_scattering_reduction.py#:~:text=%23%20Get%20vanadium%20corrections,%2C%20van_mass_density)

  #Output resultant raw correction as a nexus file to the calibration directory

  rawVCorrFilePre = 'RVMB'
  rawVCorrFileExt = '.nxs'
  rawVCorrPath = iPrm.stateLoc + sPrm['stateID'] + '/' + rawVCorrFilePre + str(VRun) + rawVCorrFileExt


  SaveNexus(InputWorkspace='TOF_rawVmB',
  Filename=rawVCorrPath,
  Title = 'Raw vanadium minus background, rebinned, histogrammed')

  print(f'wrote file: {rawVCorrPath}')
  #clean up

  DeleteWorkspace(Vws)
  DeleteWorkspace(Vws+'_monitors')
  DeleteWorkspace(VBws)
  DeleteWorkspace(VBws+'_monitors')
  #DeleteWorkspace('TOF_rawVmB')
  return 

def SNAPMsk(runWS,rPrm,sPrm):
  #Applies mask according to three different scenarios
  #1) msknm = '' - no masking
  #2) msknm = afile.xml - "traditional" mask, stored in an xml file, exludes entire pixels
  #3) msknm = afile.json - a file containing information on individual bin masking

  msknm = rPrm['maskFileName']
  if len(msknm)==0:
    wsTag = 'noMsk'
    return runWS, wsTag

  mskFname = rPrm['maskFileLoc'] + msknm
  if os.path.exists(mskFname):
    pass
  else:
    print(f'ERROR cant open: {mskFname}')
  ext = msknm.split('.')[1]
  
  #read mask from file
  if ext == 'json':
    mskMode=3
    with open(mskFname, "r") as json_file:
      mskBinsDict = json.load(json_file)
      mask_xmins = mskBinsDict['xmins']
      mask_xmaxs = mskBinsDict['xmaxs']
      mask_spectraLsts = mskBinsDict['spectraLsts']
      nmask_slice = len(mask_xmins)
    #print(f'got MaskBin dictionary with {nmask_slice} slices')
    mskRunWS=f'{runWS}_binMsk'
    wsTag='binMsk'
  elif ext == 'xml':
    mskMode=2
    LoadMask(Instrument='SNAP',
    InputFile=mskFname,
    OutputWorkspace='pixMsk')
    mskRunWS=f'{runWS}_pixMsk'
    wsTag='pixMsk'
  
  #apply mask 
  if mskMode == 2:
    CloneWorkspace(InputWorkspace=runWS,OutputWorkspace=mskRunWS)
    MaskDetectors(Workspace=mskRunWS,
    MaskedWorkspace='pixMsk')
  #Apply swiss cheese mask if this is called  
  if mskMode == 3:
    CloneWorkspace(InputWorkspace=runWS,
    OutputWorkspace=mskRunWS)
    for kk in range(nmask_slice):
        MaskBins(InputWorkspace=mskRunWS,
                InputWorkspaceIndexType='WorkspaceIndex',
                InputWorkspaceIndexSet=mask_spectraLsts[kk],
                OutputWorkspace=mskRunWS,
                XMin=mask_xmins[kk],
                XMax=mask_xmaxs[kk])
  #DeleteWorkspace(f'tof{Run}')  
  return mskRunWS,wsTag

def StateFromRunFunction(runNum):
  #returns stateID and info given a run numner

  import h5py
  from os.path import exists
  import sys
  import SNAP_InstPrm as iPrm

  #print(iPrm.inst)

  inst= iPrm.inst
  nexusLoc = iPrm.nexusDirLoc
  nexusExt = iPrm.nexusFileExt
  IPTSLoc = GetIPTS(RunNumber=int(runNum),Instrument=inst)
  fName = IPTSLoc + nexusLoc + '/SNAP_' + str(runNum) + nexusExt
  #print(fName)
  if exists(fName):
    f = h5py.File(fName, 'r')
  else:
    print(f'ERROR: file:{fName} does not exist')
    return '00000-00',dict()

  fail = False

  stateDict = dict() #dictionary to store state variable values
  try:
      det_arc1 = f.get('entry/DASlogs/det_arc1/value')[0]
      stateDict['det_arc1']=det_arc1
  except:
      print('ERROR: no value for det_arc1 in nexus file')
      fail = True
  try:    
      det_arc2 = f.get('entry/DASlogs/det_arc2/value')[0]
      stateDict['det_arc2']=det_arc2
  except:
      print('ERROR: Nexus file doesn\'t contain value for det_arc2')
      fail = True
  try:
      wav = f.get('entry/DASlogs/BL3:Chop:Skf1:WavelengthUserReq/value')[0]
      stateDict['wav']=wav
  except:
      print('ERROR: Nexus file doesn\'t contain value for central wavelength')
      fail = True
  try:
      freq = f.get('entry/DASlogs/BL3:Det:TH:BL:Frequency/value')[0]
      stateDict['freq']=freq
  except:
      print('ERROR: Nexus file doesn\'t contain value for frequency')
      fail = True
  try:
      GuideIn = f.get('entry/DASlogs/BL3:Mot:OpticsPos:Pos/value')[0]
      stateDict['GuideStat']=GuideIn
  except:
      print('ERROR: Nexus file doesn\'t contain guide status')
      fail = True

  if not fail:
      stateID = checkSNAPState([det_arc1,det_arc2,wav,freq,0.0],[GuideIn,0])
  else:
      print('ERROR: Insufficient log data, can\'t determine state')
      stateID='00000-00'

  return stateID,stateDict


def checkSNAPState(floatPar,intPar):
  #This function will find the most recent SNAP StateList, make a copy,
  # with the new state appended. 
  #8 Dec modified to include frequency, retaining spare float
  #
  #20220803 M. Guthrie updated to remove all output to screen in case where state is 
  #successfully identified.

  import os
  import time 
  from datetime import datetime, date
  import builtins #bug whereby a different piece of code (not mine) redefined built in function input 
  
  
  #Find the most recent StateDict and read it
  #print('\nLooking up most recent State Dictionary...')
  fname = findMostRecentFile('/SNS/SNAP/shared/Calibration/SNAPStateDict*.json') #returns most recent file matching arg
  stateDict = getConfigDict(fname)
  #step through float variables in order, check for a match, if this isn't found append new value
  #while processing generate stateID and check if it's a new one.

  stateStr = []
  floatStateID = ''
  newStatePar = 0
  for i in range(len(floatPar)): 
    key = stateDict["floatParameterOrder"][i] #should be key of i-th parameter
    matchVar = floatPar[i]
    matchingKeyPars,keyDiff = hitWithinTol(stateDict,key,matchVar)
    #matchingKeyPars is a boolean array of length keyLen that will be true for
    #an element that matches matchVar within tolerance specified in stateDict 
    if np.any(matchingKeyPars):
      #case where there is a matching value 
      keyID = np.where(matchingKeyPars)[0][0]
      #print('Found match:',keyID)
      #totalHits += 1
      stateStr.append('%.1f'%(stateDict[key][keyID]))
    else:
      #case where no matching values
      stateDict[key].append(matchVar) #append as new value to state item
      keyID = keyDiff.shape[0]
      closestMatchIndx = np.argmin(keyDiff)
      print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
      print('WARNING: no matching value for %s found in SNAP Dictionary'%(key))
      print('Input value:%.2f. Closest match: %.2f, differing by %.4f'%(matchVar,stateDict[key][closestMatchIndx],keyDiff[closestMatchIndx]))
      print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
      #print('No match created new state parameter value:',keyID)
      stateStr.append('%.1f'%(matchVar))
      newStatePar += 1
    floatStateID += str(keyID)
 
  # now step through integer parameters and check for matches, which must be exact
  # they must also be defined, so if there's no match something's gone wrong
  
  intStateID = ''
  for i in range(len(intPar)): 
    key = stateDict["intParameterOrder"][i] 
    matchVar = intPar[i]
    matchingKeyPars,keyLen = hitExact(stateDict,key,matchVar)
    if np.any(matchingKeyPars):
      keyID = np.where(matchingKeyPars)[0][0]
      #totalHits += 1
    else:
      print('ERROR: Undefined value for integer state parameter:', key)
    
    if i==0:
      guideStatus = keyID
    intStateID += str(keyID)

# This is where the guide status is set...
  if guideStatus == 0:
    stateStr.append('FlightTube')
  elif guideStatus ==1:
    stateStr.append('NEW guide')
  elif guideStatus ==2:
    stateStr.append('OLD guide')    
  provisionalStateID = floatStateID + '-' + intStateID

  #If supplied values don't match SNAP Dictionary, may want to create new dictionary with these included 

  if newStatePar == 0:
    pass#print('State consistent with SNAP Dictionary\n')
  else:
    #need to add check that there more than 10 parameters will be created
    togCreateNewDict = builtins.input('\nNon-Dictionary values found. Add new values to SNAP Dictionary? (y/[n])\n'\
      '(n.b. only possible if you are an instrument scientist): ')
    if togCreateNewDict.lower() == 'y':
      #print('Adding new default values to SNAP Dictionary')
      now = date.today()
      newDictFile = '/SNS/SNAP/shared/Calibration/SNAPStateDict_' + now.strftime("%Y%m%d") + '.json'
      with open(newDictFile, "w") as outfile:
        json.dump(stateDict, outfile)
      print('\nCreated:' + newDictFile)
    else:
      pass #default is to move on without doing anything.
  
# -- testing editing from guest end --- #

  #As a final step, confirm if present state is a defined SNAP state and, if not, allow option to create new state
  fnameStateList = findMostRecentFile('/SNS/SNAP/shared/Calibration/SNAPStateList_*.txt')

  fin = open(fnameStateList,'r')
  lines = fin.readlines()
  stateIDMatch = False
  for index,line in enumerate(lines):
    if index == 0:
      pass # Version number of state list, not used
    elif line.strip()[0]=='#':
      pass # This is just a comment, not used.
    elif len(line) == 0:
      pass # The last line in the file is empty
    else:
      stateID = line.strip()[0:8] #this is a line describing a state ID and beginning with the ID.
      if provisionalStateID==stateID:
        #print('\nMatch found for state: %s\n\n'%(stateID),line,'\n')
        stateIDMatch = True
        fin.close()
        break
  
  

  if not stateIDMatch:
    print('')
    togCreateNewList=input('WARNING: Current state does not exist in State List! Create new state (y/[n])?')
    #togCreateNewList
    if togCreateNewList.lower()=='y':
      now = date.today()
      newListFile = '/SNS/SNAP/shared/Calibration/SNAPStateList_' + now.strftime("%Y%m%d") + '.txt'
      fout = open(newListFile,'w')
      fout.writelines(lines)#copy existing state ID's to new file
      acceptableName = False
      while not acceptableName:
        shortTitle = input('provide short (up to 15 character) title for state: ')
        shortTitle = shortTitle[0:15].ljust(15)
        confirm = input('confirm title: '+shortTitle+' ([y]/n): ')
        if confirm.lower()=='y':
          acceptableName=True
      
      newStateStr = provisionalStateID + '::' + \
                    shortTitle + '::' + \
                    'W%s/E%s::'%(stateStr[0],stateStr[1]) + \
                    'wavelength=%s::'%(stateStr[2]) + \
                    'Freq=%s::'%(stateStr[3]) + \
                    stateStr[5] + '\n'
      fout.write(newStateStr)
      fout.close()
      print('Created updated state list:',newListFile)
      print('New state:',newStateStr)
    provisionalStateID = '' #no match and no new ID created


  return provisionalStateID  

def hitWithinTol(stateDict,key,matchPar):
#checks list item "key" in stateDict for values that match 'matchPar' within
# tolerance that is specified in stateDict.
# returns a boolean array of size equal to list item "key" that is true where
#there is a hit.
  keyPars = np.array(stateDict[key])
  keyLen = keyPars.shape[0]
  keyOrder = stateDict['floatParameterOrder'].index(key)
  keyTol = stateDict['tolerance'][keyOrder]
  #print('HitWithinTol#############################')
  #print('for key:',key)
  #print('keyPars:',keyPars)
  #print('tol:',keyTol)
  keyDiff = np.abs(matchPar-keyPars)
  keyDiffTol = keyTol-keyDiff #shall be negative if keyPar is > keyTol
  #print(keyDiff)
  matchingKeyPars = keyDiffTol>=0
  
  return matchingKeyPars,keyDiff

def hitExact(stateDict,key,matchPar):
#checks list item "key" in stateDict for values that exactly match 'matchPar' 
#returns a boolean array of size equal to list item "key" that is true where
#there is a hit.
  keyPars = np.array(stateDict[key])
  keyLen = keyPars.shape[0]
  #keyOrder = stateDict['floatParameterOrder'].index(key)
  #keyTol = stateDict['tolerance'][keyOrder]
  #print('hitExact#############################')
  #print('for key:',key)
  #print('keyPars:',keyPars)
  #print('tol:',keyTol)
  keyDiff = np.abs(matchPar-keyPars) #shall be exactly zero if keyPar matches matchPar
  #print(keyDiff)
  matchingKeyPars = keyDiff==0
  #print(matchingKeyPars)
  return matchingKeyPars,keyLen

def findMostRecentFile(pattern):
  import glob
  import os
  import time
  #import os.path, time
  from datetime import datetime
  ShortestTimeDifference = 10000000000 # a large number of seconds
  refDate = datetime.now().timestamp()
  for fname in glob.glob(pattern, recursive=True):
    
    if os.path.isfile(fname):
      #print(fname)
      #print("Created: %s" % time.ctime(os.path.getctime(fname)))
      #print('epoch:',os.path.getctime(fname))
      #print('refdate epoch:',refDate)
      delta = refDate - os.path.getctime(fname)
      #print('difference:',delta)
      if delta <= ShortestTimeDifference:
        mostRecentFile = fname
        ShortestTimeDifference = delta
  if ShortestTimeDifference == 10000000000:
    print('no matching file found')
    mostRecentFile=''
  else:
    #print('Most recent matching file:',mostRecentFile)
    #print('Created: %s'% time.ctime(os.path.getctime(mostRecentFile)))
    pass

  return mostRecentFile

def getConfigDict(FName):
    #print('attempting to open file:',FName)
    if os.path.exists(FName):
        with open(FName, "r") as json_file:
            dictIn = json.load(json_file)
        #print('got config dictionary')
        return dictIn
    else:
        print('file not found')