#This was originally a script. Now converted to a function that can be called from a
#GUI

def SNAPRed(inputRunString,inputMaskString,redSettings):

  # from mantid.simpleapi import *
  import FocDACUtilities as DAC
  import SNAP_InstPrm as iPrm 
  import importlib
  importlib.reload(DAC)
  importlib.reload(iPrm)

  #parameters:
  # inputRunString - a comma separated list of runs (TODO: enable interpretation of hyphens
  # to denote range of values)
  # inputMaskString - a string with the name of a masking file. TODO: enable possiblity
  # of different masks for different runs in list
  # redSettings - a dictionary to allow the control of some reduction options 


  AllRuns = [int(x) for x in inputRunString.split(',')]
  maskFileName=[inputMaskString]
  # 'snap48741msk.xml',
  # 'snap49870msk.xml'
  # 

  cleanUp = False
  GSASOut = False
  CU = True #switch to convert units instead of calibration  

  ########################################
  # MAIN Workflow
  #######################################
  
  #maskFileName='snap49870_8x8_binMskInfo.json'
  calibState = redSettings['calibState']#'before' #describes whether calibration was conducted before or after sample runs

  for runidx,run in enumerate(AllRuns):

    #initialise reduction parameters happens for every run
    rPrm = DAC.initPrm(run,calibState)
    if len(maskFileName)==1:
      rPrm['maskFileName']=maskFileName[0]
    else:
      rPrm['maskFileName']=maskFileName[runidx]
      

    #if state hasn't been initialised, initialise state reduction parameters and load raw VCorr
    if runidx == 0:

      sPrm,errorState = DAC.getStatePrm(run,calibState)

      LoadNexus(Filename=iPrm.stateLoc + sPrm['stateID'] + '/' + sPrm['rawVCorrFileName'],
      OutputWorkspace='TOF_rawVmB')

      DAC.setupStateGrouping(sPrm)

    #also reinitialise if state changes 
    if DAC.checkStateChange(run,sPrm):

      sPrm,errorState = DAC.getStatePrm(run,calibState)

      LoadNexus(Filename=iPrm.stateLoc + sPrm['stateID'] + '/' + sPrm['rawVCorrFileName'],
      OutputWorkspace='TOF_rawVmB')

      DAC.setupStateGrouping(sPrm)

    TOF_runWS = DAC.preProcSNAP(run,rPrm,sPrm,CU)  
    gpString = TOF_runWS + '_monitors' #a list of all ws to group
    
    #masking
    
    TOF_runWS_msk,mskTag = DAC.SNAPMsk(TOF_runWS,rPrm,sPrm) #mask run workspace
    TOF_rawVmB_msk,mskTag = DAC.SNAPMsk('TOF_rawVmB',rPrm,sPrm)

    #convert to d-spacing

    DSpac_runWS_msk = f'DSpac_{run}_{mskTag}'
    ConvertUnits(InputWorkspace=TOF_runWS_msk,
    OutputWorkspace=DSpac_runWS_msk,
    Target='dSpacing',
    EMode='Elastic',
    ConvertFromPointData=True)

    DSpac_VmB_msk = f'DSpac_rawVmB_{mskTag}'
    ConvertUnits(InputWorkspace=TOF_rawVmB_msk,
    OutputWorkspace=f'DSpac_rawVmB_{mskTag}',
    Target='dSpacing',
    EMode='Elastic',
    ConvertFromPointData=True)

    #Focus the data and vanadium using DiffractionFocusing for each of requested groups
    
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
      #PeakPositions='1.22,2.04,2.11,2.19', 
      PeakPositions='1.2356,1.5133,2.1401',
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

  print('SNAPRed complete')
    #Group workspaces according to run number
  #GroupWorkspaces(GlobExpression=str(run))
