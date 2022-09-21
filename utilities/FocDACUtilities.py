from mantid.simpleapi import *
from mantid import logger
config.setLogLevel(0, quiet=True)
import json
import numpy as np
import os
#import SNAPStateParMgr as prm
import utilities.SNAP_InstPrm as iPrm

def initPrm(run,case='before',liteMode=True):
  # This creates and returns a dictionary with all necessary run-specific parameters
  # All properties that can be determined soley from the run-number are populated, others
  # are just left empty.
  #
  # 20220908 M. Guthrie added 'lite' setting  

  iptsPath = GetIPTS(RunNumber=run, instrument=iPrm.inst)
  rPrm = {
    'RunNo':run,
    'maskFileName':'',
    'maskFileLoc':iptsPath + iPrm.sharedDirLoc,
    'runIPTS': iptsPath,
    'gsasFileLoc':iptsPath + iPrm.reducedDirLoc,
    'liteMode':liteMode,
    'calibState':case
  }

  return rPrm

def checkStateChange(run,sPrm):
  #checks if state of run is different from current state

  runStateID,runStateDict,errorState = StateFromRunFunction(run)
  return runStateID == sPrm['stateID']

def setupStateGrouping(rPrm,sPrm):

  #Create grouping workspaces to be used for all runs
  #
  #19 Aug 2022 M. Guthrie CreateGroupingWorkspace turns out to be costly, so 
  # have added check to not recreate existing workspaces
  gpString = 'TOF_rawVmB'

  #Currently a messy hack to allow an arbitrary grouping of columns
  #
  #20220824 M. Guthrie. discovered that CreateGroupingWorkspace is doing something very strange
  #the definition of groups Gp01 and Gp02 below takes 4.5 minutes each to run
  #after chatting with Andrei, he suggested to just manually create these grouping workspaces.
  # a quick test of this shows it runs almost instantly.
  # Here, I commented out the original code (a call to CreateGroupingWorkspace) and instead 
  # call ManualCreateGroupingWorkspace which I also just created in this file. 

  lite = rPrm['liteMode']

  if lite:
    LoadEventNexus(FileName='/SNS/SNAP/IPTS-24179/shared/lite/SNAP_48708.lite.nxs.h5',
    OutputWorkspace='lite')

  stdGroups=['All','Group','2_4Grouping','Column','bank']
  for focGrp in sPrm['focGroupLst']:
    if focGrp in stdGroups:
      try: 
        a = mtd[focGrp]
      except:
        if lite:
          CreateGroupingWorkspace(InputWorkspace='lite',
          GroupDetectorsBy=focGrp,
          OutputWorkspace=f'{iPrm.inst}{focGrp}Gp')
        else:
          CreateGroupingWorkspace(InstrumentName=iPrm.inst,
          GroupDetectorsBy=focGrp,
          OutputWorkspace=f'{iPrm.inst}{focGrp}Gp')
    elif focGrp == 'Gp01':
      try:
        a = mtd[focGrp]
      except: 
        CreateGroupingWorkspace(InstrumentName=iPrm.inst,
        ComponentName='East',
        CustomGroupingString='0-589823',
        OutputWorkspace=f'{iPrm.inst}{focGrp}Gp')
    elif focGrp == 'Gp02':
      try:
        a = mtd[focGrp]
      except:
        CreateGroupingWorkspace(InstrumentName=iPrm.inst,
        CustomGroupingString='786432-1179647',
        ComponentName='West',
        OutputWorkspace=f'{iPrm.inst}{focGrp}Gp')
    gpString = gpString + ',' + f'{iPrm.inst}{focGrp}Gp'

  GroupWorkspaces(InputWorkspaces=gpString,
    OutputWorkspace='CommonRed'
    )

  #print('State groups initialised')
def ManualCreateGroupingWorkspace(FirstPixelIDInGroup=0,
  LastPixelIDInGroup=10,Inst='SNAP',GpWSName=''):

  #Create empty instrument

  LoadEmptyInstrument(InstrumentName=Inst,
  OutputWorkspace=GpWSName)

  #for SNAP need to load detector positions for ShowInstrument to work (might not be necessary here)

  AddSampleLog(Workspace=GpWSName,LogName='det_arc1',LogText=arc1,LogType='Number Series')
  AddSampleLog(Workspace=GpWSName,LogName='det_lin1',LogText=lin1,LogType='Number Series')
  AddSampleLog(Workspace=GpWSName,LogName='det_arc2',LogText=arc2,LogType='Number Series')
  AddSampleLog(Workspace=GpWSName,LogName='det_lin2',LogText=lin2,LogType='Number Series')
  LoadInstrument(Workspace=GpWSName,MonitorList='-1,1179648', RewriteSpectraMap='False',InstrumentName='SNAP')


def getStatePrm(runStr,rPrm):
  #purpose: 
  # 1) shall determine state-ID the basis of run number. 
  # 2) shall determine corresponding state folder
  # 3) shall search this folder for calibration info files (meaning calibrations have been performed)
  # 4) if no calibration exists, exit gracefully.
  # 5) if calibration exists shall choose the most recent calibration preceding (or, if specified, following) run 
  # 6) shall read this and return a dictionary containing its values
  #
  # Parameters
  # runStr is a string specifying the run number of the  measurement of interest
  # case is a string used to specify difference scenarios in which to operate. Allowed values are: 
  # case = 'before' where the calibration was measured before run (or is run)
  # case = 'after' where the calibration was measured after run (or is run)
  # case = 'manual' where calibration will be manually selected
  #import SNAP_InstPrm as iPrm
  import json
  import yaml #
  import numpy as np

  lite = rPrm['liteMode']
  case = rPrm['calibState']

  # print('getStatePrm thinks the case is: ',case)

  errorState = dict()
  errorState['value']=0
  errorState['function']='getStatePrm'

  run = int(runStr)

  stateID,stateDict,errorState = StateFromRunFunction(run)
  if errorState['value']!=0:
    return dict(),errorState


  calibPath = iPrm.stateLoc + stateID + '/'
  if lite:
    calibSearchPattern=f'{calibPath}{iPrm.calibFilePre}*.lite.{iPrm.calibFileExt}'
  else:
    calibSearchPattern=f'{calibPath}{iPrm.calibFilePre}*.{iPrm.calibFileExt}'
  logger.error(calibSearchPattern)  
  calibFileList = findMatchingFileList(calibSearchPattern)
  if len(calibFileList)==0:
    errorState['value']=1
    errorState['message']=f'state {stateID} has no available calibration info file'
    return dict(),errorState
  #case manual - needs to be handled in GUI
  # if case.lower() == 'manual':
  #   print('Index - Calibration File')
  #   for i,str in enumerate(calibFileList):
  #     print(f'{i} - {str}\n')
  #   calIndx = int(input('Enter index of desired calibration file:'))
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
        errorState['value']=2
        errorState['message']=f'no calibration matching request {case} available in state {stateID}'
        return dict(),errorState
      else:
        closestBefore = max([calibRunList[i] for i in neg]) #closest run number
        calIndx = calibRunList.index(closestBefore) #its index
    elif case.lower() == 'after':
      if len(pos) == 0:
        errorState['value']=2
        errorState['message']=f'no calibration matching request {case} available in state {stateID}'
        return dict(),errorState
      else:
        closestAfter = min([calibRunList[i] for i in pos])
        calIndx = calibRunList.index(closestAfter)

  #print(f'successfully found calibration file: \n {calibFileList[calIndx]}')
  
  #Now read this to populate the state dictionary
  logger.error(calibFileList[calIndx])
  with open(calibFileList[calIndx], "r") as json_file:
    dictIn = json.load(json_file)
  #print('got config dictionary')
  dictIn['calibInfoFile']=calibFileList[calIndx]
  return dictIn,errorState

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

def preProcSNAP(Run,rPrm,sPrm,CU): 
  
  import os.path
  #initial steps of reduction
  #preliminary normalisation (to proton charge)
  #calibration, compression of events and summing neighbours to 8x8 superpixels 
  #input: Run: a single run number as integer
  #rPrm a dictionary with run parameters
  #sPrm a dictionary with state parameters
  #CU a flag if True, use convert units instead of applying a calibration
  
  #output: single mantid workspace in TOF
  #
  #19 Aug 2022 M. Guthrie added check if preProc workspace already exists
  #and to not reload if not necessary.

  # 6 sept 2022 M. Guthrie added variable `lite` if true then will trigger a workflow
  # where the original nexus file processed by `nexusLite` to create local file
  # where events have been re-labelled according to an 8x8 pixel scheme.
  # subsequently this "lite" file is read instead of the original. The lite file
  # has exactly the same size as the original, so this could rapidly lead to problems
  # with disk space, so this is just a temporary measure...

  runIPTS= rPrm['runIPTS']
  lite = rPrm['liteMode'] 
  
  try:
    a = mtd[f'TOF_{Run}']
  except:

    if lite:
      #First need to create local directory if it doesn't exist
      liteDir = f'{runIPTS}shared/lite/'
      if not os.path.exists(liteDir):
        os.makedirs(liteDir)
      inF = f'{runIPTS}{iPrm.nexusDirLoc}{iPrm.nexusFilePre}{Run}{iPrm.nexusFileExt}'
      outF = f'{runIPTS}shared/lite/{iPrm.nexusFilePre}{Run}.lite{iPrm.nexusFileExt}'
      makeLite(inFileName=inF,
      outFileName=outF)
      LoadEventNexus(f'{runIPTS}shared/lite/{iPrm.nexusFilePre}{Run}.lite{iPrm.nexusFileExt}',
      OutputWorkspace=f'TOF_{Run}',
      FilterByTofMin=sPrm['tofMin'], 
      FilterByTofMax=sPrm['tofMax'], Precount='1',
      LoadMonitors=True,
      LoadNexusInstrumentXML=True)
    else:
      LoadEventNexus(Filename=f'{runIPTS}{iPrm.nexusDirLoc}{iPrm.nexusFilePre}{Run}{iPrm.nexusFileExt}',
      OutputWorkspace=f'TOF_{Run}',
      FilterByTofMin=sPrm['tofMin'], 
      FilterByTofMax=sPrm['tofMax'], Precount='1',
      LoadMonitors=True,
      NumberOfBins=1)
    
    NormaliseByCurrent(InputWorkspace=f'TOF_{Run}',
    OutputWorkspace=f'TOF_{Run}')

    CompressEvents(InputWorkspace=f'TOF_{Run}',
    OutputWorkspace=f'TOF_{Run}',
    WallClockTolerance=sPrm['wallClockTol'])

    if not CU:
      ApplyDiffCal(InstrumentWorkspace=f'TOF_{Run}',
      CalibrationFile=iPrm.stateLoc+sPrm['stateID']+'/'+sPrm['calFileName'])

    if not lite:
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
#
# M. Guthrie 7/09/2022 modified to accept input arguments as dictionary and to 
# Store a copy of this dictionary in calibration directory as a record of how
# Vanadium correction was made.

def makeRawVCorr(vPrm):

  lite = vPrm['liteMode']
  VRun = vPrm['VRun']
  VBRun = vPrm['VBRun']
  case = vPrm['calibState']

  sPrm, errorState = getStatePrm(VRun,vPrm)
  rPrm = initPrm(VRun,case,lite)

  Vws = preProcSNAP(VRun,rPrm,sPrm,False)

  #by definition, state must be the same for V and VB, so don't update
  #TODO: create a script that returns true if two input runs
  #are in the same state
  #TODO: make able to handle VRun and VBRun being lists

  rPrm = initPrm(VBRun,case,lite) 
  VBws = preProcSNAP(VBRun,rPrm,sPrm, False)

  Minus(LHSWorkspace=Vws,
  RHSWorkspace=VBws,
  OutputWorkspace='TOF_rawVmB')

  #TODO: check different options for abs correction
  #Check out: https://github.com/neutrons/mantid_total_scattering/blob/next/total_scattering/reduction/total_scattering_reduction.py#:~:text=%23%20Get%20vanadium%20corrections,%2C%20van_mass_density)
  #TODO: check V dimensions and create a way to store these

  ConvertUnits(InputWorkspace='TOF_rawVmB',
  OutputWorkspace='Lam_rawVmB',
  Target='Wavelength')

  #with these settings takes about 60s...
  CylinderAbsorption(InputWorkspace='Lam_rawVmB', 
  OutputWorkspace='Vabs', 
  AttenuationXSection=5.08, 
  ScatteringXSection=5.10, 
  SampleNumberDensity=0.07188, 
  CylinderSampleHeight=vPrm['VHeight'], 
  CylinderSampleRadius=vPrm['VRad'], 
  NumberOfSlices=vPrm['NSlice'], 
  NumberOfAnnuli=vPrm['NAnnul'])

  Divide(LHSWorkspace='Lam_rawVmB',
  RHSWorkspace='Vabs',
  OutputWorkspace='Lam_rawVmB')

  ConvertUnits(InputWorkspace='Lam_rawVmB',
  OutputWorkspace='TOF_rawVmB',
  Target='TOF')  

  Rebin(InputWorkspace='TOF_rawVmB',
  OutputWorkspace='TOF_rawVmB',
  Params=[sPrm['tofMin'],sPrm['tofBin'],sPrm['tofMax']],
  PreserveEvents=False)
  
  #Output resultant raw correction as a nexus file to the calibration directory

  rawVCorrFilePre = 'RVMB'
  if lite:
    rawVCorrFileExt = '.lite.nxs'
  else:
    rawVCorrFileExt = '.nxs'
  rawVCorrPath = iPrm.stateLoc + sPrm['stateID'] + '/' + rawVCorrFilePre + str(VRun) + rawVCorrFileExt

  SaveNexus(InputWorkspace='TOF_rawVmB',
  Filename=rawVCorrPath,
  Title = 'Raw vanadium minus background, absorb corr,rebinned, histogrammed')

  print(f'wrote file: {rawVCorrPath}')
  #clean up
  #if requested, enter inspection mode
  inspect=True 
  if inspect:

    setupStateGrouping(vPrm,sPrm)
  
    ConvertUnits(InputWorkspace='TOF_rawVmB',
    OutputWorkspace=f'DSpac_rawVmB',
    Target='dSpacing',
    EMode='Elastic',
    ConvertFromPointData=True)

    #Focus the data and vanadium using DiffractionFocusing for each of requested groups
    
    for gpNo, focGrp in enumerate(sPrm['focGroupLst']):

      DiffractionFocussing(InputWorkspace=f'DSpac_rawVmB',
      OutputWorkspace=f'DSpac_rawVmB_{focGrp}',
      GroupingWorkspace=f'SNAP{focGrp}Gp')

      #make vanadium correction (complicated by mystery peaks)
      #(n.b. also no attenuation correction on V, but none on data either, this isn't quantatative)
      StripPeaks(InputWorkspace=f'DSpac_rawVmB_{focGrp}',
      OutputWorkspace=f'DSpac_rawVmB_{focGrp}_strp',
      FWHM=2, 
      #PeakPositions='1.22,2.04,2.11,2.19', 
      PeakPositions=vPrm['VPeaks'],
      BackgroundType='Quadratic')
      
      SmoothData(InputWorkspace=f'DSpac_rawVmB_{focGrp}_strp', 
      OutputWorkspace=f'DSpac_VCorr_{focGrp}',
      NPoints=vPrm['VSmoothPoints'])


  DeleteWorkspace(Vws)
  DeleteWorkspace(Vws+'_monitors')
  DeleteWorkspace(VBws)
  DeleteWorkspace(VBws+'_monitors')
  DeleteWorkspace('TOF_rawVmB')
  DeleteWorkspace('Vabs')
  DeleteWorkspace('Lam_rawVmB')
  return 

def SNAPMsk(runWS,rPrm,sPrm):
  #Applies mask according to three different scenarios
  #1) msknm = '' - no masking
  #2) msknm = afile.xml - "traditional" mask, stored in an xml file, exludes entire pixels
  #3) msknm = afile.json - a file containing information on individual bin masking
  #
  #20221608 M. Guthrie: added information recording units that bin mask was created using
  #input runWS *has to match this* for things to work. Currently reduction workflow is sending runWS as
  #TOF and expects returned ws to also be in TOF. So, if units!= TOF then need a couple
  #of ConvertUnits


  msknm = rPrm['maskFileName']
  if len(msknm)==0:
    wsTag = 'noMsk'
    return runWS, wsTag

  mskFname = rPrm['maskFileLoc'] + msknm
  if os.path.exists(mskFname):
    pass
  else:
    logger.error(f'mask file not found here: {mskFname}')
    return
  ext = msknm.split('.')[1]
  
  #read mask from file
  if ext == 'json':
    mskMode=3
    logger.error('Reading Bin Mask file')
    with open(mskFname, "r") as json_file:
      mskBinsDict = json.load(json_file)
      mask_xmins = mskBinsDict['xmins']
      mask_xmaxs = mskBinsDict['xmaxs']
      mask_spectraLsts = mskBinsDict['spectraLsts']
      mask_units = mskBinsDict['units']
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

    #check units, change if necessary
    ws = mtd[mskRunWS]
    input_units=ws.getAxis(0).getUnit().caption()
    changedUnits=False 

    if mask_units != input_units:
      ConvertUnits(InputWorkspace=mskRunWS,
      OutputWorkspace=mskRunWS,
      Target=mask_units)
      changedUnits=True

    for kk in range(nmask_slice):
        logger.error(f'There are {nmask_slice} mask slices, masking bins for slice: {kk}')
        logger.error(f'minimum x: {mask_xmins[kk]} maximum x: {mask_xmaxs[kk]}')
        allSlice = mask_spectraLsts[kk].split(',')
        logger.error(f'there are {len(allSlice)} spectra in this slice')
        MaskBins(InputWorkspace=mskRunWS,
                InputWorkspaceIndexType='WorkspaceIndex',
                InputWorkspaceIndexSet=mask_spectraLsts[kk],
                OutputWorkspace=mskRunWS,
                XMin=mask_xmins[kk],
                XMax=mask_xmaxs[kk])

    if changedUnits:
      if input_units=='Time-of-flight':
        input_units='TOF' #well, that one is annoying...
      ConvertUnits(InputWorkspace=mskRunWS,
      OutputWorkspace=mskRunWS,
      Target=input_units)
      changedUnits=True
  #DeleteWorkspace(f'tof{Run}')  
  return mskRunWS,wsTag

def StateFromRunFunction(runNum):
  #returns stateID and info given a run numner
  #
  #20220809 - modified error handling. Instead of requesting input from within
  #function, added an additional variable errorState, with the following meaning
  #
  #errorState = 0 : all is well in the World
  #errorState = 1 : GetIPTS failed. IPTS doesn't exist
  #errorState = 2 : Insufficient log information in nexus file to determine instrument state
  #errorState = 3 :  

  import h5py
  from os.path import exists
  import sys
 # import SNAP_InstPrm as iPrm

  #print(iPrm.inst)
  errorState=dict()
  errorState['value']=0
  errorState['function']='StateFromRunFunction'
  errorState['message']=''
  errorState['parameters']=[]

  inst= iPrm.inst
  nexusLoc = iPrm.nexusDirLoc
  nexusExt = iPrm.nexusFileExt

  try:
    IPTSLoc = GetIPTS(RunNumber=int(runNum),Instrument=inst)
  except:
    errorState['value']=1
    errorState['message']='mantid GetIPTS algorithm failed'
    errorState['parameters']=[runNum]
    return '00000-00',dict(),errorState

  fName = IPTSLoc + nexusLoc + '/SNAP_' + str(runNum) + nexusExt
  #print(fName)
  if exists(fName):
    f = h5py.File(fName, 'r')
  else:
    errorState['value']=2
    errorState['message']='error opening run nexus file'
    errorState['parameters']=[fName]
    return '00000-00',dict(),errorState

  fail = False

  stateDict = dict() #dictionary to store state variable values

  missingLogVal = []

  try:
    det_arc1 = f.get('entry/DASlogs/det_arc1/value')[0]
    stateDict['det_arc1']=det_arc1
  except:
    missingLogVal.append('det_arc1')
    fail = True
  try:    
    det_arc2 = f.get('entry/DASlogs/det_arc2/value')[0]
    stateDict['det_arc2']=det_arc2
  except:
    missingLogVal.append('det_arc2')
    fail = True
  try:
    wav = f.get('entry/DASlogs/BL3:Chop:Skf1:WavelengthUserReq/value')[0]
    stateDict['wav']=wav
  except:
    missingLogVal.append('wav')
    fail = True
  try:
    freq = f.get('entry/DASlogs/BL3:Det:TH:BL:Frequency/value')[0]
    stateDict['freq']=freq
  except:
    missingLogVal.append('freq')
    fail = True
  try:
    GuideIn = f.get('entry/DASlogs/BL3:Mot:OpticsPos:Pos/value')[0]
    stateDict['GuideStat']=GuideIn
  except:
    missingLogVal.append('GuideStat')
    fail = True

  if not fail:
    stateID,errorState = checkSNAPState([det_arc1,det_arc2,wav,freq,0.0],[GuideIn,0])
  else:
    errorState['value']=3
    errorState['message']='Insufficient log data, can\'t determine state'
    errorState['parameters']=missingLogVal
    return '00000-00',dict(),errorState

  return stateID,stateDict,errorState


def checkSNAPState(floatPar,intPar):
  #This function will find the most recent SNAP StateList, make a copy,
  # with the new state appended. 
  #8 Dec modified to include frequency, retaining spare float
  #
  #20220803 M. Guthrie updated to remove all output to screen in case where state is 
  #successfully identified.
  #
  #20220809 M. Guthrie removed all requested user input within this function and added
  # additional errorState dictionary that is returned when something goes wrong. 
  # errorState needs several keys: 
  # "value" an integer that together with "function" creates a unique ID for for the error
  # "function" the name of the function where error occured 
  # "message" a short string describing the error
  # "parameters" a list of parameters that may aid in fixing the problem.
  
  import os
  import time
  from os.path import exists 
  from datetime import datetime, date
  
  errorState=dict()
  errorState['value']=0
  errorState['message']='All is well'
  errorState['function']='checkSNAPState'
  errorState['parameters']=[]

  #Find the most recent StateDict and read it
  #print('\nLooking up most recent State Dictionary...')

  fPattern = iPrm.stateLoc + 'SNAPStateDict*.json'
  fname,errorState = findMostRecentFile(fPattern) #returns most recent file matching arg
  if errorState['value']!= 0:
    return '00000-00',errorState

  if exists(fname):
    stateDict = getConfigDict(fname)
  else:
    errorState['value']=1
    errorState['message']='Error opening State Dictionary'
    errorState['parameters']=[fname]
    return '00000-00',errorState
  #step through float variables in order, check for a match, if this isn't found append new value
  #while processing generate stateID and check if it's a new one.

  stateStr = []
  floatStateID = ''
  newStatePar = 0
  #for purposes of error reporting, it's possible that multiple float parameters don't match
  #these should be recorded along with the nearest matching value I will use a list to 
  # store these instances that can then be passed on up as an error parameter

  nonDictPar = [[]] 
  for i in range(len(floatPar)): 
    key = stateDict["floatParameterOrder"][i] #should be key of i-th parameter
    matchVar = floatPar[i]
    matchingKeyPars,keyDiff = hitWithinTol(stateDict,key,matchVar)
    #matchingKeyPars is a boolean array of length keyLen that will be true for
    #an element that matches matchVar within tolerance specified in stateDict 
    if np.any(matchingKeyPars):
      #case where there is a matching float parameter in dictionary 
      keyID = np.where(matchingKeyPars)[0][0]
      stateStr.append('%.1f'%(stateDict[key][keyID]))
    else:
      #case where there is no matching float parameter in dictionary
      stateDict[key].append(matchVar) #append as new value to state item
      keyID = keyDiff.shape[0]
      closestMatchIndx = np.argmin(keyDiff)
      errorState['value']=2
      errorState['message']='at least one state parameter does not match state dictionary'
      nonDictPar.append([key,matchVar,stateDict[key][closestMatchIndx],keyDiff[closestMatchIndx]])
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
      errorState['value']=2
      errorState['message']='at least one state parameter does not match state dictionary'
      nonDictPar.append([key,matchVar,0,0]) #dummy values for now
      print('ERROR: Undefined value for integer state parameter:', key)
    
    if i==0:
      guideStatus = keyID
    intStateID += str(keyID)

# This is where the guide status written to the descritor state Str...
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
    errorState['parameters']=nonDictPar #list of all non-dictionary parameters, their values, nearest dict values and differences
    return '00000-00',errorState
    #need to add check that there more than 10 parameters will be created
    # togCreateNewDict = builtins.input('\nNon-Dictionary values found. Add new values to SNAP Dictionary? (y/[n])\n'\
    #   '(n.b. only possible if you are an instrument scientist): ')
    # if togCreateNewDict.lower() == 'y':
    #   #print('Adding new default values to SNAP Dictionary')
    #   now = date.today()
    #   newDictFile = '/SNS/SNAP/shared/Calibration/SNAPStateDict_' + now.strftime("%Y%m%d") + '.json'
    #   with open(newDictFile, "w") as outfile:
    #     json.dump(stateDict, outfile)
    #   print('\nCreated:' + newDictFile)
    # else:
    #   pass #default is to move on without doing anything.
  
# -- testing editing from guest end --- #

  #As a final step, confirm if present state is a defined SNAP state and, if not, allow option to create new state
  fnameStateList,errorState = findMostRecentFile('/SNS/SNAP/shared/Calibration/SNAPStateList_*.txt')
  if errorState['value']!= 0:
    return '00000-00',errorState

  if exists(fnameStateList):
    fin = open(fnameStateList,'r')
    lines = fin.readlines()
  else:
    errorState['value']=3
    errorState['message']='error: SNAP state list file does not exist.'
    errorState['parameters']=fnameStateList
    return '00000-00',errorState

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
    errorState['value']=4
    errorState['message']='Current state consistent with SNAP Dictionary but does not exist in State List'
    errorState['parameters']=[stateStr]
    return '00000-00',errorState
    # print('')
    # togCreateNewList=input('WARNING: Current state does not exist in State List! Create new state (y/[n])?')
    # #togCreateNewList
    # if togCreateNewList.lower()=='y':
    #   now = date.today()
    #   newListFile = '/SNS/SNAP/shared/Calibration/SNAPStateList_' + now.strftime("%Y%m%d") + '.txt'
    #   fout = open(newListFile,'w')
    #   fout.writelines(lines)#copy existing state ID's to new file
    #   acceptableName = False
    #   while not acceptableName:
    #     shortTitle = input('provide short (up to 15 character) title for state: ')
    #     shortTitle = shortTitle[0:15].ljust(15)
    #     confirm = input('confirm title: '+shortTitle+' ([y]/n): ')
    #     if confirm.lower()=='y':
    #       acceptableName=True
      
    #   newStateStr = provisionalStateID + '::' + \
    #                 shortTitle + '::' + \
    #                 'W%s/E%s::'%(stateStr[0],stateStr[1]) + \
    #                 'wavelength=%s::'%(stateStr[2]) + \
    #                 'Freq=%s::'%(stateStr[3]) + \
    #                 stateStr[5] + '\n'
    #   fout.write(newStateStr)
    #   fout.close()
    #   print('Created updated state list:',newListFile)
    #   print('New state:',newStateStr)
    # provisionalStateID = '' #no match and no new ID created


  return provisionalStateID,errorState  

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

  errorState=dict()
  errorState['value']=0
  errorState['function']='findMostRecentFile'
  errorState['message']='All is well'
  errorState['parameters']=[]

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
    errorState['value']=1
    errorState['message']='No matching file found'
    errorState['parameters']=[pattern]
  else:
    #print('Most recent matching file:',mostRecentFile)
    #print('Created: %s'% time.ctime(os.path.getctime(mostRecentFile)))
    pass

  return mostRecentFile,errorState

def getConfigDict(FName):
    #print('attempting to open file:',FName)
    if os.path.exists(FName):
        with open(FName, "r") as json_file:
            dictIn = json.load(json_file)
        #print('got config dictionary')
        return dictIn
    else:
        print('file not found')

#This was originally a script. Now converted to a function that can be called from a
#GUI

def SNAPRed(inputRunString,inputMaskString,redSettings):

  # from mantid.simpleapi import *
  #import FocDACUtilities as DAC
  #import SNAP_InstPrm as iPrm 
  import importlib
  #importlib.reload(DAC)
  importlib.reload(iPrm)
  import yaml

  #TODO need to keep a log of run-specific parameters so, created a 
  #dictionary of dictionaries, which is now returned

  #parameters:
  # inputRunString - a comma separated list of runs (TODO: enable interpretation of hyphens
  # to denote range of values)
  # inputMaskString - a string with the name of a masking file. TODO: enable possiblity
  # of different masks for different runs in list
  # redSettings - a dictionary to allow the control of some reduction options 


  AllRuns = [int(x) for x in inputRunString.split(',')]
 
  maskFileName=[inputMaskString]
  cleanUp = redSettings['cleanUp'] 
  GSASOut = redSettings['GSASOut']
  CU = redSettings['ConvertUnits'] #switch to convert units instead of calibration  
  lite = redSettings['liteMode']

  ########################################
  # MAIN Workflow
  #######################################
  
  #maskFileName='snap49870_8x8_binMskInfo.json'
  calibState = redSettings['calibState']#'before' #describes whether calibration was conducted before or after sample runs

  for runidx,run in enumerate(AllRuns):

    #initialise reduction parameters happens for every run
    rPrm = initPrm(run,calibState,lite)
    if len(maskFileName)==1:
      rPrm['maskFileName']=maskFileName[0]
    else:
      rPrm['maskFileName']=maskFileName[runidx]
      

    #if state hasn't been initialised, initialise state reduction parameters and load raw VCorr
    if runidx == 0:
      logger.error(f'getting state parameters for run: {run}')
      sPrm,errorState = getStatePrm(run,rPrm)
      rawvc = sPrm['rawVCorrFileName']
      logger.error(f'Loading raw VCorr: {rawvc}')
      LoadNexus(Filename=iPrm.stateLoc + sPrm['stateID'] + '/' + sPrm['rawVCorrFileName'],
      OutputWorkspace='TOF_rawVmB')

      setupStateGrouping(rPrm,sPrm)

    #also reinitialise if state changes 
    if not checkStateChange(run,sPrm):
      print('State changed, initialising new state')
      sPrm,errorState = getStatePrm(run,calibState)

      LoadNexus(Filename=iPrm.stateLoc + sPrm['stateID'] + '/' + sPrm['rawVCorrFileName'],
      OutputWorkspace='TOF_rawVmB')

      setupStateGrouping(sPrm)
    logger.error(f'pre processing run: {run}')
    TOF_runWS = preProcSNAP(run,rPrm,sPrm,CU)  
    gpString = TOF_runWS + '_monitors' #a list of all ws to group
    
    #write reduction parameters to file for posterity

    # fullParPath='RedPrm.yaml'
    # redDict = sPrm.update(rPrm)
    # with open(fullCalPath,'w') as file:
    #   docs = yaml.dump(redDict, file)
    # print(f'created calibLog at: {fullParPath}')

    #masking
    logger.error(f'masking run: {run}')
    TOF_runWS_msk,mskTag = SNAPMsk(TOF_runWS,rPrm,sPrm) #mask run workspace
    logger.error(f'masking VCorr')
    TOF_rawVmB_msk,mskTag = SNAPMsk('TOF_rawVmB',rPrm,sPrm)

    #convert to d-spacing
    logger.error('converting run to d')
    DSpac_runWS_msk = f'DSpac_{run}_{mskTag}'
    ConvertUnits(InputWorkspace=TOF_runWS_msk,
    OutputWorkspace=DSpac_runWS_msk,
    Target='dSpacing',
    EMode='Elastic',
    ConvertFromPointData=True)

    logger.error('converting VCorr to d')
    DSpac_VmB_msk = f'DSpac_rawVmB_{mskTag}'
    ConvertUnits(InputWorkspace=TOF_rawVmB_msk,
    OutputWorkspace=f'DSpac_rawVmB_{mskTag}',
    Target='dSpacing',
    EMode='Elastic',
    ConvertFromPointData=True)

    #Focus the data and vanadium using DiffractionFocusing for each of requested groups
    
    logger.error('Diffraction focusing by group')
    for gpNo, focGrp in enumerate(sPrm['focGroupLst']):
      DiffractionFocussing(InputWorkspace=DSpac_runWS_msk,
      OutputWorkspace=f'{DSpac_runWS_msk}_{focGrp}',
      GroupingWorkspace=f'SNAP{focGrp}Gp')

      DiffractionFocussing(InputWorkspace=f'DSpac_rawVmB_{mskTag}',
      OutputWorkspace=f'DSpac_rawVmB_{mskTag}_{focGrp}',
      GroupingWorkspace=f'SNAP{focGrp}Gp')

      #make vanadium correction (complicated by mystery peaks)
      #(n.b. also no attenuation correction on V, but none on data either, this isn't quantatative)
      StripPeaks(InputWorkspace=f'DSpac_rawVmB_{mskTag}_{focGrp}',
      OutputWorkspace=f'DSpac_rawVmB_{mskTag}_{focGrp}_strp',
      FWHM=2, 
      PeakPositions='1.22,2.04,2.11,2.19', 
      #PeakPositions='1.2356,1.5133,2.1401',
      BackgroundType='Quadratic')
      
      SmoothData(InputWorkspace=f'DSpac_rawVmB_{mskTag}_{focGrp}_strp', 
      OutputWorkspace=f'DSpac_VCorr_{mskTag}_{focGrp}',
      NPoints='40')

  #Apply vanadium correction, and trim to usable limits

      Divide(LHSWorkspace=f'{DSpac_runWS_msk}_{focGrp}', 
      RHSWorkspace=f'DSpac_VCorr_{mskTag}_{focGrp}', 
      OutputWorkspace=f'{DSpac_runWS_msk}_{focGrp}_V')

      Rebin(InputWorkspace=f'{DSpac_runWS_msk}_{focGrp}_V', #skip V correction.
      #Rebin(InputWorkspace=f'{DSpac_runWS_msk}_{focGrp}', 
      OutputWorkspace=f'{DSpac_runWS_msk}_{focGrp}_VR',
      Params='0.5,-0.001,4.5', PreserveEvents=False)

      CropWorkspaceRagged(InputWorkspace=f'{DSpac_runWS_msk}_{focGrp}_VR', 
      OutputWorkspace=f'{DSpac_runWS_msk}_{focGrp}_VRT', 
      XMin=sPrm['focGroupDMin'][gpNo], 
      XMax=sPrm['focGroupDMax'][gpNo])

      gpString = gpString+ f',{DSpac_runWS_msk}_{focGrp}_VRT'

      if cleanUp:
          DeleteWorkspaces(WorkspaceList=f'DSpac_rawVmB_{mskTag}_{focGrp},'\
          f'DSpac_rawVmB_{mskTag}_{focGrp}_strp,'
          f'DSpac_VCorr_{mskTag}_{focGrp},'
          f'{DSpac_runWS_msk}_{focGrp},'
          f'{DSpac_runWS_msk}_{focGrp}_V,'
          f'{DSpac_runWS_msk}_{focGrp}_VR')    
      
    GroupWorkspaces(InputWorkspaces=gpString,
        OutputWorkspace=f'SNAP{run}_Red')

    if cleanUp:      
      DeleteWorkspaces(WorkspaceList=TOF_runWS_msk + \
      ','+TOF_runWS+\
      f',DSpac_rawVmB_{mskTag},'\
      f'DSpac_{run}_{mskTag}'    
      ) 
    

  if cleanUp:
    DeleteWorkspaces(WorkspaceList=TOF_rawVmB_msk)
  
  #return reduction parameters. THis is 

def makeLite(inFileName,outFileName):    
    import numpy as np
    import h5py
    import shutil
    import time
    print('h5py version:',h5py.__version__)

    time_0 = time.time()

    sumNeigh = [8,8]
    # inFileName = f'SNAP_{run}.nxs.h5'
    # outFileName = f'SNAP_{run}.lite.nxs.h5'

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
    h5IDF[...]=newXMLString#.encode(encoding='ascii')
    h5obj.close()
    #
    # Finish up
    #
    stepTime = time.time() - time_0
    totTime += stepTime
    print(f'    Time to complete step: {stepTime:.4f} sec. Total time to execute: {totTime:.4f}')
    return 

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
