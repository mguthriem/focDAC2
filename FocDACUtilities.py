from mantid.simpleapi import *
import json
import numpy as np
import os
import SNAPParMgr as prm

def setIPTS(Run,parDict):
  parDict['runIPTS']= GetIPTS(RunNumber=Run,Instrument='SNAP')
  return

def preProcSNAP(Run,parDict): #initial steps of reduction
  #preliminary normalisation (to proton charge)
  #calibration, compression of events and summing neighbours to 8x8 superpixels
  import SNAPParMgr as prm  
  #input: Run: a single run number as integer
  
  #output: single mantid workspace in TOF
  runIPTS= parDict['runIPTS'] #GetIPTS(RunNumber=Run,Instrument='SNAP')
  #parDict['runIPTS']=runIPTS
  
  LoadEventNexus(Filename=runIPTS+f'nexus/SNAP_{Run}.nxs.h5',
  OutputWorkspace=f'TOF_{Run}',
  FilterByTofMin=prm.tofMin, 
  FilterByTofMax=prm.tofMax, Precount='1',
  LoadMonitors=True)
  
  NormaliseByCurrent(InputWorkspace=f'TOF_{Run}',
  OutputWorkspace=f'TOF_{Run}')

  CompressEvents(InputWorkspace=f'TOF_{Run}',
  OutputWorkspace=f'TOF_{Run}',
  WallClockTolerance=prm.wallClockTol)

  ApplyDiffCal(InstrumentWorkspace=f'TOF_{Run}',
  CalibrationFile=prm.calFile)

  SumNeighbours(InputWorkspace=f'TOF_{Run}',
  OutputWorkspace=f'TOF_{Run}',
  SumX=prm.superPixEdge,
  SumY=prm.superPixEdge
  )
  return f'TOF_{Run}'

####################################################################################
#Before processing runs, need to make a partial vanadium correction. This is currently an 
#approximation, but written in a way that a correct approach can be implemented in 
#the future.
#The goal here is to create and store a nexus file that contains V minus B in as a function 
#of wavelength, with full* instrument defintion (*subject to compression as defined in 
#loadandprepSNAP

def makeRawVCorr(VRun,VBRun,runRedPars):


  setIPTS(VRun,runRedPars)
  Vws = preProcSNAP(VRun,runRedPars)
  setIPTS(VBRun,runRedPars)
  VBws = preProcSNAP(VBRun,runRedPars)

  #I'm aware that an attenuation 
  Minus(LHSWorkspace=Vws,
  RHSWorkspace=VBws,
  OutputWorkspace='TOF_rawVmB')

  DeleteWorkspace(Vws)
  DeleteWorkspace(Vws+'_monitors')
  DeleteWorkspace(VBws)
  DeleteWorkspace(VBws+'_monitors')

  return 'TOF_rawVmB'

def SNAPMsk(runWS,runRedPars):
  #Applies mask according to three different scenarios
  #1) msknm = '' - no masking
  #2) msknm = afile.xml - "traditional" mask, stored in an xml file, exludes entire pixels
  #3) msknm = afile.json - a file containing information on individual bin masking

  msknm = runRedPars['maskFileName']
  if len(msknm)==0:
    wsTag = 'noMsk'
    return runWS, wsTag

  mskFname = runRedPars['maskFileLoc'] + msknm
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


