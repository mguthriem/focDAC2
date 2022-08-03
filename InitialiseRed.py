from mantid.simpleapi import *
import FocDACUtilities as DAC
import SNAPParMgr as prm 
import importlib
importlib.reload(DAC)
importlib.reload(prm)

#dictionary isn't used but needs to exist with blank entries
runRedPars={
  'maskFileName':'',
  'maskFileLoc':'',
  'runIPTS':''
}

TOF_rawVmB = DAC.makeRawVCorr(49833,49834,runRedPars)

#Create grouping workspaces to be used for all runs
gpString = TOF_rawVmB
for focGrp in prm.focGroupLst:
  CreateGroupingWorkspace(InstrumentName='SNAP',
  GroupDetectorsBy=focGrp,
  OutputWorkspace=f'SNAP{focGrp}Gp')
  gpString = gpString + ',' + f'SNAP{focGrp}Gp'

GroupWorkspaces(InputWorkspaces=gpString,
  OutputWorkspace='CommonRed'
  )

print('Initialisation complete')