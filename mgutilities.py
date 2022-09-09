# mgutilities is a collection of functions that are useful to have access to from
# multiple different applications

from mantid.simpleapi import *
import json
import numpy as np
import os

def d2Q(listOfd):
    #converts a list of d-spacings to Q and returns these. Should be able to handle multi-dimensional
    inQ = [2*np.pi/x for x in listOfd]
    return inQ

def workbench_MessageBox(text1,text2,text3,text4):
  from qtpy.QtWidgets import QMessageBox
  msg = QMessageBox()
  msg.setIcon(QMessageBox.Information)

  msg.setText(text1)
  msg.setInformativeText(text2)
  msg.setWindowTitle(text3)
  msg.setDetailedText(text4)
  msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
  #msg.buttonClicked.connect(msgbtn)
  retval = msg.exec_()
  print('value of pressed message box button:', retval)
  return retval


def workbench_input_fn(dTitle,dInstruction,inpType):
  from qtpy.QtWidgets import QInputDialog
  
  if inpType=='int':
    item, ok = QInputDialog.getInt(None, dTitle, dInstruction)
  elif inpType=='str': 
    item, ok = QInputDialog.getText(None, dTitle, dInstruction)
    
  if ok:
      return item
  else:
      raise ValueError("Error retrieving input")

def gridPlot(WSNames,xlims,SpectrumMap,inLegend,TickMarks,ROILims,plotName):

  # a script to automate plotting of multiple histograms in a single window
  # driver is to separately inspect the 6 columns on SNAP without the
  # unweildy manipulation of 6 different windows on the display   

  # import mantid algorithms, numpy and matplotlib

  #WSName is a list of one or more mantid workspace names to be plotted
  #WSs must have same number of spectra and these will be plotted according to the same
  #specified x-axis limits

  #xlims is a 2xnhst list of xlimits (min and max for each histogram in WS)

  #spectrumMap is a multi-dimensional list representing how spectra should be arranged.
  #e.g. if spectrumMap = [[1,2,3],[4,5,6]] display will contain 2 rows and 3 columns. The first
  # row will show spectra 1,2 and 3 from left to right and the bottom row will show spectra 4,5&6
  # I allowed for the possibility that number of columns in each row are different 

  #inLegend is a list of labels to use for the WS and should have equal length to WSNames

  #TickMarks is a list of d-spacings to plot as vertical lines on all plots

  #ROILims is a simple marker showing minimum and maximum limits on ROI on the x-axis it requires a
  #pair of limits for each histogram in the plot

  from mantid.simpleapi import mtd
  import matplotlib.pyplot as plt
  import numpy as np
  from mantid.api import AnalysisDataService as ADS
  from matplotlib import interactive
  #interactive(True)

  #print('version is 1.0')
  nWS = len(WSNames) #number of ws to plot
  ws = mtd[WSNames[0]]# first ws in list is considered the reference and all other ws 
  #must have matching number of histograms and matching x-axis units
  
  #print('inLegend:',inLegend,'len is:',len(inLegend))
  #print('WSNames: ',WSNames,'len is:',len(WSNames))
  #print('These are equal',len(inLegend)==len(WSNames))
  
  #print('In gridPlot')
  refnHst = ws.getNumberHistograms()
  refXAxisCaption = ws.getAxis(0).getUnit().caption()
  for i in range(nWS):
    ws = mtd[WSNames[i]]
    nHst = ws.getNumberHistograms()
    XAxisCaption = ws.getAxis(0).getUnit().caption()
    #print(i,'histograms:',nHst,'caption:',XAxisCaption)

  if plt.fignum_exists(plotName): 
    plt.close(plotName) #get rid of window if it already exists
  
  #########################################################################
  # plotting data 
  #########################################################################

  nrows = len(SpectrumMap)
  ncols = [None]*nrows
  for i in range(nrows):
    ncols[i] = len(SpectrumMap[i])
  maxCols = max(ncols)
  
  ColorPalette = ['#2ca02c','#ef2929','#3465a4','#9467bd','#f57900','#8f5902','#000000','#a40000','#888a85','#4e9a06']
  
  #create figure and axes to plot data in
  fig, axes = plt.subplots(figsize=[10, 6.5258],\
  nrows=nrows, ncols=maxCols, num=plotName, \
  #sharex = True,\
  subplot_kw={'projection': 'mantid'})
  #loop through data to plot
  wslab = 0
  for ws in WSNames:
    inWSName = ws
    #print('plotting:',ws)
    wsIn = mtd[ws]
    nhst = wsIn.getNumberHistograms()
    try:
      sampleColor = ColorPalette[wslab]
    except:
      sampleColor = ['#000000']
      print('only 10 colours defined and more than 10 overlays requested. Additional will be black')
    
    
    axisXLabel = wsIn.getAxis(0).getUnit().caption()
    axisYLabel = wsIn.getAxis(1).getUnit().caption()

    sample = ADS.retrieve(inWSName) # vanadium corrected sample diffraction data for all columns
    for i in range(nrows):
      for j in range(ncols[i]):
        SpecIndex = SpectrumMap[i][j]
        if len(inLegend)==len(WSNames):
          axes[i][j].plot(sample, color=sampleColor, wkspIndex=SpecIndex-1, label=inLegend[wslab])
        else:
          axes[i][j].plot(sample, color=sampleColor, wkspIndex=SpecIndex-1)
        subPlotYLims = axes[i][j].get_ylim()
        subPlotXLims = axes[i][j].get_xlim()
        if len(TickMarks)!=0:
          for k in range(len(TickMarks)):
            axes[i][j].plot([TickMarks[k],TickMarks[k]],[subPlotYLims[0],subPlotYLims[1]],color='#888a85')
        if len(ROILims)!=0:
          ROImin = ROILims[SpecIndex-1][0]
          ROImax = ROILims[SpecIndex-1][1]
          #print('Spec:',SpecIndex,'ROI lims:',ROImin,ROImax)
          axes[i][j].plot([ROImin,ROImin],[subPlotYLims[0],subPlotYLims[1],],color='#000000',linestyle='--', linewidth=0.5)
          axes[i][j].plot([ROImax,ROImax],[subPlotYLims[0],subPlotYLims[1],],color='#000000',linestyle='--', linewidth=0.5)
        axes[i][j].set_title('Spec '+str(SpectrumMap[i][j]))
        axes[i][j].set_xlim(subPlotXLims[0],subPlotXLims[1])
    wslab = wslab + 1
  
  
  #set axis ranges and labels
  
  if len(xlims) != 0:
   for i in range(nrows):
     for j in range(maxCols):
        axes[i][j].set_xlim(xlims[0], xlims[1])
        #axes[i][j].set_ylim(0.0,250)

  for i in range(nrows):
    for j in range(maxCols):
      axes[i][0].set_ylabel(axisYLabel)
      axes[i][1].set_ylabel('')
      axes[i][2].set_ylabel('')

  for j in range(maxCols):
    axes[0][j].set_xlabel('')
    axes[1][j].set_xlabel(axisXLabel)

  #legend = axes[0][0].legend(fontsize=8.0).draggable().legend
  #print('NOTICE: Close plot window to continue')
  plt.show()
  #tog = input('enter anything to continue:')    
  return

def genHstNameLst(rootName,nHst):
  str = '%s%s,'%(rootName,0)
  for i in range(nHst-2):
    str = str+'%s%s,'%(rootName,i+1)
  str = str + '%s%s'%(rootName,nHst-1)
  return str

def getConfigDict(FName):
    #print('attempting to open file:',FName)
    if os.path.exists(FName):
        with open(FName, "r") as json_file:
            dictIn = json.load(json_file)
        #print('got config dictionary')
        return dictIn
    else:
        print('file not found')

def loadAndPrep(run,msknm,configDict,mode,modeSet): #initial steps of reduction
  #preliminary normalisation (to proton charge)
  #calibration (currently via detCal or modifying sample logs)
  
  #run = INT a single run number
  #msknm = STRING the name of a mask. If empty, no mask is applied.
  #configDict = DICT dictionary containing the current configuration
  #mode = INT a historical setting controlling how data are processed (TO BE REMOVED AT SOME POINT SOON)
  #modeSet = LIST of INT is also enables passing of options controlling how data are proceed:
      #modeSet[0] = Apply vanadium correction [NOT USED HERE]
      #modeSet[1] = Mask: 0 = don't use mask; 1 use mask in workspace; 2 use mask read from file
      #modeSet[2] = 1 load monitor data, = 0 don't load monitor data 
      #modeSet[3] = label for location of neutron data either 0 = dataDir,1  = VDir or 2 = VBDir 

  tag = configDict['instrumentTag']
  #sharedDir = configDict['sharedDir']
  extn = configDict['extn']
  MonTBinning = configDict['MonTBinning']
  TBinning = configDict['TBinning']
  tlims = TBinning.split(',')
  tof_min = tlims[0]
  tof_max = tlims[2]
  detCalName = configDict['detCalName']
  detLogVal = configDict['detLogVal']
  MonTBinning = configDict['MonTBinning']

  # Set up column grouping workspace if it doesn't yet exist
  try:
      a = mtd['SNAPColGp'] #if workspace already exists, don't reload
  except:
      CreateGroupingWorkspace(InstrumentFilename=configDict['instFileLoc'], \
      GroupDetectorsBy='Column', OutputWorkspace='SNAPColGp')
  
  if modeSet[3]==0:
      dataDir = configDict['dataDir']
  elif modeSet[3]==1:
      dataDir = configDict['VDir']
  elif modeSet[3]==2:
      dataDir = configDict['VBDir']

  #BASIC LOADING AND NORMALISATION
  if modeSet[2]==1:
      try:
        mtd['%s%s'%(tag,run)] #try/except prevents re-loading of event data if ws already exists
      except:
        LoadEventNexus(Filename=r'%s%s_%s.%s'%(dataDir,tag,run,extn),OutputWorkspace='%s%s'%(tag,run),
        FilterByTofMin=tof_min, FilterByTofMax=tof_max, Precount='1', LoadMonitors=True)
        NormaliseByCurrent(InputWorkspace='%s%s'%(tag,run),OutputWorkspace='%s%s'%(tag,run))  
        CompressEvents(InputWorkspace='%s%s'%(tag,run),OutputWorkspace='%s%s'%(tag,run))
        Rebin(InputWorkspace='%s%s'%(tag,run),OutputWorkspace='%s%s'%(tag,run),Params=TBinning,FullBinsOnly=True)
        NormaliseByCurrent(InputWorkspace='%s%s_monitors'%(tag,run),OutputWorkspace='%s%s_monitors'%(tag,run))
        Rebin(InputWorkspace='%s%s_monitors'%(tag,run),OutputWorkspace='%s%s_monitors'%(tag,run),Params=MonTBinning,FullBinsOnly=True)
  elif modeSet[2] == 0:
      try:
        mtd['%s%s'%(tag,run)]
      except:
        LoadEventNexus(Filename=r'%s%s_%s.%s'%(dataDir,tag,run,extn),OutputWorkspace='%s%s'%(tag,run),
        FilterByTofMin=tof_min, FilterByTofMax=tof_max, Precount='1', LoadMonitors=False)
  #POSTIONAL CALIBRATION =(currently via either an ISAW detcal or changelogs)
  if detCalName.lower() == 'changelogs':
    AddSampleLog(Workspace='SNAP%s'%run,LogName='det_arc1',LogText=detLogVal.split(",")[0],LogType='Number Series')
    AddSampleLog(Workspace='SNAP%s'%run,LogName='det_lin1',LogText=detLogVal.split(",")[1],LogType='Number Series')
    AddSampleLog(Workspace='SNAP%s'%run,LogName='det_arc2',LogText=detLogVal.split(",")[2],LogType='Number Series')
    AddSampleLog(Workspace='SNAP%s'%run,LogName='det_lin2',LogText=detLogVal.split(",")[3],LogType='Number Series')
    LoadInstrument(Workspace='SNAP%s'%run,MonitorList='-1,1179648', RewriteSpectraMap='False',InstrumentName='SNAP')
  elif (detCalName.lower() != 'none' and detCalName.lower() !='changelogs'):
    LoadIsawDetCal(InputWorkspace='%s%s'%(tag,run), Filename=detCalName)
  
  #MASK DETECTORS (Need to do prior to any groupoing if mask read from file
  CloneWorkspace(InputWorkspace='%s%s'%(tag,run),OutputWorkspace='%s%s_msk'%(tag,run))
  if modeSet[1] == 2 and mode !=1: # mask detectors here if mask read in from file (currently always the case for mode 2 and 3
      MaskDetectors(Workspace='%s%s_msk'%(tag,run),MaskedWorkspace='%s'%(msknm))
  return

def loadAndPrep2(redPrmDict_state,redPrmDict_user,mode,modeSet): #initial steps of reduction
  #modified version of original function for preliminary normalisation (to proton charge)
  #calibration is via a (.h5) cal file
  
  #run = INT a single run number
  #msknm = STRING the name of a mask. If empty, no mask is applied.
  #configDict = DICT dictionary containing the current configuration
  #mode = INT a historical setting controlling how data are processed (TO BE REMOVED AT SOME POINT SOON)
  #modeSet = LIST of INT is also enables passing of options controlling how data are proceed:
      #modeSet[0] = Apply vanadium correction [NOT USED HERE]
      #modeSet[1] = Mask: 0 = don't use mask; 1 use mask in workspace; 2 use mask read from file
      #modeSet[2] = 1 load monitor data, = 0 don't load monitor data 
      #modeSet[3] = label for location of neutron data either 0 = dataDir,1  = VDir or 2 = VBDir 

  MonTBinning = redPrmDict_state['MonTBinning']
  TBinning = redPrmDict_state['TBinning']
  tlims = TBinning.split(',')
  tof_min = tlims[0]
  tof_max = tlims[2]
  stateGeomCalibFile = redPrmDict_state['stateGeomCalibFile']
  stateGroupingFile = redPrmDict_state['stateGroupingFile']
  MonTBinning = redPrmDict_state['MonTBinning']

  # Set up grouping workspace if it doesn't yet exist
  LoadDetectorsGroupingFile(InputFile=stateGroupingFile,OutputWorkspace=SNAPGpWS)
  
  if modeSet[3]==0:
      dataFile = redPrmDict_user['SData']
      run = redPrmDict_user['SRun']
  elif modeSet[3]==1:
      dataFile = redPrmDict_state['VData']
      run = redPrmDict_state['VRun']
  elif modeSet[3]==2:
      dataFile = redPrmDict_state['VBData']
      run = redPrmDict_state['VBRun']

  tag
  #BASIC LOADING AND NORMALISATION
  if modeSet[2]==1:
      try:
        mtd['%s%s'%(tag,run)] #try/except prevents re-loading of event data if ws already exists
      except:
        LoadEventNexus(Filename=r'%s%s_%s.%s'%(dataDir,tag,run,extn),OutputWorkspace='%s%s'%(tag,run),
        FilterByTofMin=tof_min, FilterByTofMax=tof_max, Precount='1', LoadMonitors=True)
        NormaliseByCurrent(InputWorkspace='%s%s'%(tag,run),OutputWorkspace='%s%s'%(tag,run))  
        CompressEvents(InputWorkspace='%s%s'%(tag,run),OutputWorkspace='%s%s'%(tag,run))
        Rebin(InputWorkspace='%s%s'%(tag,run),OutputWorkspace='%s%s'%(tag,run),Params=TBinning,FullBinsOnly=True)
        NormaliseByCurrent(InputWorkspace='%s%s_monitors'%(tag,run),OutputWorkspace='%s%s_monitors'%(tag,run))
        Rebin(InputWorkspace='%s%s_monitors'%(tag,run),OutputWorkspace='%s%s_monitors'%(tag,run),Params=MonTBinning,FullBinsOnly=True)
  elif modeSet[2] == 0:
      try:
        mtd['%s%s'%(tag,run)]
      except:
        LoadEventNexus(Filename=r'%s%s_%s.%s'%(dataDir,tag,run,extn),OutputWorkspace='%s%s'%(tag,run),
        FilterByTofMin=tof_min, FilterByTofMax=tof_max, Precount='1', LoadMonitors=False)
  #POSTIONAL CALIBRATION =(currently via either an ISAW detcal or changelogs)
  if detCalName.lower() == 'changelogs':
    AddSampleLog(Workspace='SNAP%s'%run,LogName='det_arc1',LogText=detLogVal.split(",")[0],LogType='Number Series')
    AddSampleLog(Workspace='SNAP%s'%run,LogName='det_lin1',LogText=detLogVal.split(",")[1],LogType='Number Series')
    AddSampleLog(Workspace='SNAP%s'%run,LogName='det_arc2',LogText=detLogVal.split(",")[2],LogType='Number Series')
    AddSampleLog(Workspace='SNAP%s'%run,LogName='det_lin2',LogText=detLogVal.split(",")[3],LogType='Number Series')
    LoadInstrument(Workspace='SNAP%s'%run,MonitorList='-1,1179648', RewriteSpectraMap='False',InstrumentName='SNAP')
  elif (detCalName.lower() != 'none' and detCalName.lower() !='changelogs'):
    LoadIsawDetCal(InputWorkspace='%s%s'%(tag,run), Filename=detCalName)
  
  #MASK DETECTORS (Need to do prior to any groupoing if mask read from file
  CloneWorkspace(InputWorkspace='%s%s'%(tag,run),OutputWorkspace='%s%s_msk'%(tag,run))
  if modeSet[1] == 2 and mode !=1: # mask detectors here if mask read in from file (currently always the case for mode 2 and 3
      MaskDetectors(Workspace='%s%s_msk'%(tag,run),MaskedWorkspace='%s'%(msknm))
  return

def generateVCorr(msknm,mskLoc,configDict,inQ,showFit): #generates vanadium correction from two runs and metadata in configDict


  #msknm = STRING can either be a file name (without the assumed XML extension, which MUST be stored in the shared folder)
  #   or it can be the name of a pre-stored mantid workspace containing a mask
  #   or it can be an empty string if no mask is needed
  #mskLoc = INT = 0 don't use mask, = 1 mask is in workspace, = 2 mask is stored in file in shared directory
  #configDict = DICT contains configuration.
  #inQ = INT = 1 output in Q, otherwise will output in d-spacing
  #showfit = INT = 1 shows progress using gridPlot

  import sys

  vanPeakFWHM = configDict['vanPeakFWHM'].split(',')
  vanPeakTol = configDict['vanPeakTol'].split(',')
  vanHeight = configDict['vanHeight']
  vanRadius = configDict['vanRadius']
  vanSmoothing = configDict['vanSmoothing'].split(',')
  VPeaks = configDict['VPeaks']
  TBinning = configDict['TBinning']
  tlims = TBinning.split(',')
  tof_min = tlims[0]
  tof_max = tlims[2]
  #tag = configDict['instrumentTag']
  dminsStr = configDict['dmins'].split(',')
  dmaxsStr = configDict['dmaxs'].split(',')
  dmins = [float(x) for x in dminsStr]
  dmaxs = [float(x) for x in dmaxsStr]
  c = VPeaks.split(',')
  allPeaksToStrip = [float(x) for x in c]
  dBinSize = configDict['dBinSize']
  QBinSize = configDict['QBinSize']

  #print(allPeaksToStrip)
  #There are some costly steps in here, which can be ignored if there is no change in masking
  #this will definitely be the case when vanadium parameters are being optimised during set up
  #
  #this is likely the case when showFit == 1 so use this as a flag to speed up where possible.
  #Also using showFit to control interactions: 
  #showFit =2 - strip peaks
  #        =3 - set smoothing

  Vrun = configDict['Vrun']
  VDataDir = configDict['VDir']
  VBrun = configDict['VBrun']
  VBDataDir = configDict['VBDir']
  #mskloc = configDict['mskloc']
  #msknm = configDict['msknm']
  dStart = min(dmins)
  dEnd = max(dmaxs)
  QStart = 2*np.pi/dEnd
  QEnd = 2*np.pi/dStart
  print('ragged parameters:')
  RebinParams = str(dStart)+','+ dBinSize + ',' + str(dEnd)
  print('d-space binning parameters are:',RebinParams)

  
  if showFit >= 1 and mtd.doesExist('VCorr_VmB'):
    pass
  else:
    loadAndPrep(Vrun,msknm,configDict,2,[0,mskLoc,1,1])
    ConvertUnits(InputWorkspace='%s%s_msk'%(tag,Vrun),OutputWorkspace='%s%s_d'%(tag,Vrun),Target='dSpacing')
    DiffractionFocussing(InputWorkspace='%s%s_d'%(tag,Vrun), OutputWorkspace='%s%s_d6'%(tag,Vrun), GroupingWorkspace='SNAPColGp')
    loadAndPrep(VBrun,msknm,configDict,2,[0,mskLoc,1,2])
    ConvertUnits(InputWorkspace='%s%s_msk'%(tag,VBrun),OutputWorkspace='%s%s_d'%(tag,VBrun),Target='dSpacing')
    DiffractionFocussing(InputWorkspace='%s%s_d'%(tag,VBrun), OutputWorkspace='%s%s_d6'%(tag,VBrun), GroupingWorkspace='SNAPColGp')
    Minus(LHSWorkspace='SNAP'+str(Vrun)+'_d6', RHSWorkspace='SNAP'+str(VBrun)+'_d6', OutputWorkspace='VCorr_VmB')
  ws = mtd['SNAP'+str(Vrun)+'_d6']
  #Conduct angle dependent corrections on a per-spectrum basis
  nHst = ws.getNumberHistograms()
  for i in range(nHst):
    #print('working on spectrum:',i+1)
    ExtractSingleSpectrum(InputWorkspace='VCorr_VmB',OutputWorkspace='VCorr_VmB%s'%(i),WorkspaceIndex=i)
    if len(VPeaks) != 0:       
        StripPeaks(InputWorkspace='VCorr_VmB%s'%(i), OutputWorkspace='VCorr_VmB_strp%s'%(i), \
        FWHM=vanPeakFWHM[i], PeakPositions=VPeaks, PeakPositionTolerance=vanPeakTol[i])
    FFTSmooth(InputWorkspace='VCorr_VmB_strp%s'%(i),\
                         OutputWorkspace='VCorr_VmB_strp_sm%s'%(i),\
                         Filter="Butterworth",\
                         Params=str(vanSmoothing[i]+',2'),\
                         IgnoreXBins=True,
                         AllSpectra=True)
    SetSampleMaterial(InputWorkspace='VCorr_VmB_strp_sm%s'%(i), ChemicalFormula='V')
    ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm%s'%(i), OutputWorkspace='VCorr_VmB_strp_sm%s'%(i), Target='Wavelength')
    CylinderAbsorption(InputWorkspace='VCorr_VmB_strp_sm%s'%(i), OutputWorkspace='VCorr_a', AttenuationXSection=5.08, \
    ScatteringXSection=5.10, CylinderSampleHeight=vanHeight, CylinderSampleRadius=vanRadius, CylinderAxis='0,0,1')
    Divide(LHSWorkspace='VCorr_VmB_strp_sm%s'%(i), RHSWorkspace='VCorr_a', OutputWorkspace='VCorr_VmB_strp_sm_a%s'%(i))
    ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm_a%s'%(i), OutputWorkspace='VCorr_VmB_strp_sm_a%s'%(i), Target='dSpacing')
    Rebin(InputWorkspace='VCorr_VmB_strp_sm_a%s'%(i), OutputWorkspace='VCorr_VmB_strp_sm_a%s'%(i), Params=RebinParams,FullBinsOnly=True)

  #conjoin original spectra into a single workspace again
  root = 'VCorr_VmB_strp'
  ConjoinSpectra(InputWorkspaces=genHstNameLst(root,6), OutputWorkspace=root, LabelUsing=genHstNameLst('spec ',6))
  DeleteWorkspaces(genHstNameLst(root,6))
  root = 'VCorr_VmB_strp_sm'
  ConjoinSpectra(InputWorkspaces=genHstNameLst(root,6), OutputWorkspace=root)
  DeleteWorkspaces(genHstNameLst(root,6))
  root = 'VCorr_VmB_strp_sm_a'
  ConjoinSpectra(InputWorkspaces=genHstNameLst(root,6), OutputWorkspace='VCorr_VmB_strp_sm_a_afterConjoin')
  #DeleteWorkspaces(genHstNameLst(root,6))
  root = 'VCorr_VmB'
  DeleteWorkspaces(genHstNameLst(root,6))
  DeleteWorkspace(Workspace='VCorr_a')

  #ConvertUnits(InputWorkspace='VCorr_VmB',OutputWorkspace='VCorr_VmB', Target='dSpacing')
  #ConvertUnits(InputWorkspace='VCorr_VmB_strp',OutputWorkspace='VCorr_VmB_strp', Target='dSpacing')
  ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm',OutputWorkspace='VCorr_VmB_strp_sm',Target='dSpacing')
  #ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm_a',OutputWorkspace='VCorr_VmB_strp_sm_a', Target='dSpacing')
  
  ROILims=[ [dmins[0],dmaxs[0]],[dmins[1],dmaxs[1]],[dmins[2],dmaxs[2]],[dmins[3],dmaxs[3]],[dmins[4],dmaxs[4]],[dmins[5],dmaxs[5]] ]
  if inQ ==1:
      
      allPeaksToStripQ = d2Q(allPeaksToStrip)
      for i in range(len(ROILims)):
            ROILims[i] = [2*np.pi/x for x in ROILims[i]] #convert ROI limits to Q
      ConvertUnits(InputWorkspace='VCorr_VmB', OutputWorkspace='VCorr_VmB_Q', Target='MomentumTransfer')
      ConvertUnits(InputWorkspace='VCorr_VmB_strp', OutputWorkspace='VCorr_VmB_strp_Q', Target='MomentumTransfer')
      ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm', OutputWorkspace='VCorr_VmB_strp_sm_Q', Target='MomentumTransfer')
      ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm_a', OutputWorkspace='VCorr_VmB_strp_sm_a_Q', Target='MomentumTransfer')
      if showFit == 2:
        gridPlot(['VCorr_VmB_Q','VCorr_VmB_strp_Q','VCorr_VmB_strp_sm_Q'],[],[[1,2,3],[4,5,6]],['Raw','Peaks stripped','Smoothed'],allPeaksToStripQ,ROILims,'Vanadium Setup')
      elif showFit == 3:
        gridPlot(['VCorr_VmB_strp_Q','VCorr_VmB_strp_sm_Q'],[],[[1,2,3],[4,5,6]],['Peaks stripped','smoothed'],[],ROILims,'Vanadium Setup')
      elif showFit == 4:
        gridPlot(['VCorr_VmB_strp_sm_Q','VCorr_VmB_strp_sm_a_Q'],[],[[1,2,3],[4,5,6]],['Smoothed','Att corrected'],[],[],'Vanadium Setup')
      else:
        DeleteWorkspace(Workspace='VCorr_VmB')
        DeleteWorkspace(Workspace='VCorr_VmB_strp')
        DeleteWorkspace(Workspace='VCorr_VmB_strp_sm')
        DeleteWorkspace(Workspace='VCorr_VmB_strp_sm_a')
  else:
    if showFit == 2:
        gridPlot(['VCorr_VmB','VCorr_VmB_strp','VCorr_VmB_strp_sm'],[],[[1,2,3],[4,5,6]],['Raw','Peaks stripped','Smoothed'],allPeaksToStrip,ROILims,'Vanadium Setup')
    elif showFit == 3:
        ROILims=[ [dmins[0],dmaxs[0]],[dmins[1],dmaxs[1]],[dmins[2],dmaxs[2]],[dmins[3],dmaxs[3]],[dmins[4],dmaxs[4]],[dmins[5],dmaxs[5]] ]
        gridPlot(['VCorr_VmB_strp','VCorr_VmB_strp_sm'],[],[[1,2,3],[4,5,6]],['Peaks stripped','smoothed'],[],ROILims,'Vanadium Setup')
    elif showFit == 4:
        gridPlot(['VCorr_VmB_strp_sm','VCorr_VmB_strp_sm_a'],[],[[1,2,3],[4,5,6]],['Smoothed','Att corrected'],[],'Vanadium Setup')
    else:
        DeleteWorkspace(Workspace='VCorr_VmB')
        DeleteWorkspace(Workspace='VCorr_VmB_strp')
        DeleteWorkspace(Workspace='VCorr_VmB_strp_sm')
        DeleteWorkspace(Workspace='VCorr_VmB_strp_sm_a')

  
  for i in range(nHst):
    print(i,dmins[i],dmaxs[i])
  CropWorkspaceRagged(InputWorkspace='VCorr_VmB_strp_sm_a_afterConjoin',OutputWorkspace='VCorr_d06',Xmin=dmins,Xmax=dmaxs)

  ws=mtd['VCorr_d06']
  ax = ws.getAxis(1)
  for i in range(nHst):
    ax.setLabel(i,'Spec %s'%(i+1))
  #Rebin operation is creating artifacts at the edge of spectra where data drops to zero. 
  #SumSpectra(InputWorkspace='VCorr_d06', OutputWorkspace='VCorr_dEast', ListOfWorkspaceIndices='0-2')
  #SumSpectra(InputWorkspace='VCorr_d06', OutputWorkspace='VCorr_dWest', ListOfWorkspaceIndices='3-5')
  #AppendSpectra(InputWorkspace1='VCorr_dEast', InputWorkspace2='VCorr_dWest', OutputWorkspace='VCorr_dEastWest')
  #DeleteWorkspace(Workspace='VCorr_dEast')
  #DeleteWorkspace(Workspace='VCorr_dWest')
  #SumSpectra(InputWorkspace='VCorr_d06', OutputWorkspace='VCorr_dAll', ListOfWorkspaceIndices='0-5')
  
  if inQ ==1:
      RebinParams = str(QStart)+','+ QBinSize + ',' + str(QEnd)
      print('d-space binning parameters are:',RebinParams)
      Rebin(InputWorkspace='VCorr_VmB_strp_sm_a_Q', OutputWorkspace='VCorr_Q6', Params=RebinParams,FullBinsOnly=True)
      SumSpectra(InputWorkspace='VCorr_Q6', OutputWorkspace='VCorr_QEast', ListOfWorkspaceIndices='0-2')
      SumSpectra(InputWorkspace='VCorr_Q6', OutputWorkspace='VCorr_QWest', ListOfWorkspaceIndices='3-5')
      AppendSpectra(InputWorkspace1='VCorr_QEast', InputWorkspace2='VCorr_QWest', OutputWorkspace='VCorr_QEastWest')
      DeleteWorkspace(Workspace='VCorr_QEast')
      DeleteWorkspace(Workspace='VCorr_QWest')
      SumSpectra(InputWorkspace='VCorr_Q6', OutputWorkspace='VCorr_QAll', ListOfWorkspaceIndices='0-5')
  return

def generateVCorr2(redPrmDict_state,redPrmDict_user,inQ,showFit): #generates vanadium correction from two runs and metadata in configDict
  
  # 8/Feb/2022 M. Guthrie
  # Updated version for mode where state ID exists and reduction parameters are
  # fully specified by the two dictionaries: redPrmDict_state and redPrmDict_user
  #  
  #inQ = INT = 1 output in Q, otherwise will output in d-spacing
  #showfit = INT = 1 shows progress using gridPlot

  import sys

  vanPeakFWHM = RedPrmDict_state['vanPeakFWHM'].split(',')
  vanPeakTol = RedPrmDict_state['vanPeakTol'].split(',')
  vanHeight = RedPrmDict_state['vanHeight']
  vanRadius = RedPrmDict_state['vanRadius']
  vanSmoothing = RedPrmDict_state['vanSmoothing'].split(',')
  VPeaks = RedPrmDict_state['VPeaks']
  TBinning = RedPrmDict_state['TBinning']
  tlims = TBinning.split(',')
  tof_min = tlims[0]
  tof_max = tlims[2]
  #tag = RedPrmDict_state['instrumentTag']
  dminsStr = RedPrmDict_state['dmins'].split(',')
  dmaxsStr = RedPrmDict_state['dmaxs'].split(',')
  dmins = [float(x) for x in dminsStr]
  dmaxs = [float(x) for x in dmaxsStr]
  c = VPeaks.split(',')
  allPeaksToStrip = [float(x) for x in c]
  dBinSize = RedPrmDict_state['dBinSize']
  QBinSize = RedPrmDict_state['QBinSize']

  #print(allPeaksToStrip)
  #There are some costly steps in here, which can be ignored if there is no change in masking
  #this will definitely be the case when vanadium parameters are being optimised during set up
  #
  #this is likely the case when showFit == 1 so use this as a flag to speed up where possible.
  #Also using showFit to control interactions: 
  #showFit =2 - strip peaks
  #        =3 - set smoothing


  VData = RedPrmDict_state['VData']
  VBData = RedPrmDict_state['VBData']
  mskLoc = RedPrmDict_user['mskLoc']
  mskName = RedPrmDict_user['mskName']
  dStart = min(dmins)
  dEnd = max(dmaxs)
  QStart = 2*np.pi/dEnd
  QEnd = 2*np.pi/dStart
  print('ragged parameters:')
  RebinParams = str(dStart)+','+ dBinSize + ',' + str(dEnd)
  print('d-space binning parameters are:',RebinParams)

  
  if showFit >= 1 and mtd.doesExist('VCorr_VmB'):
    pass
  else:
    loadAndPrep(Vrun,mskName,configDict,2,[0,mskLoc,1,1])
    ConvertUnits(InputWorkspace='%s%s_msk'%(tag,Vrun),OutputWorkspace='%s%s_d'%(tag,Vrun),Target='dSpacing')
    DiffractionFocussing(InputWorkspace='%s%s_d'%(tag,Vrun), OutputWorkspace='%s%s_d6'%(tag,Vrun), GroupingWorkspace='SNAPColGp')
    loadAndPrep(VBrun,mskName,configDict,2,[0,mskLoc,1,2])
    ConvertUnits(InputWorkspace='%s%s_msk'%(tag,VBrun),OutputWorkspace='%s%s_d'%(tag,VBrun),Target='dSpacing')
    DiffractionFocussing(InputWorkspace='%s%s_d'%(tag,VBrun), OutputWorkspace='%s%s_d6'%(tag,VBrun), GroupingWorkspace='SNAPColGp')
    Minus(LHSWorkspace='SNAP'+str(Vrun)+'_d6', RHSWorkspace='SNAP'+str(VBrun)+'_d6', OutputWorkspace='VCorr_VmB')
  ws = mtd['SNAP'+str(Vrun)+'_d6']
  #Conduct angle dependent corrections on a per-spectrum basis
  nHst = ws.getNumberHistograms()
  for i in range(nHst):
    #print('working on spectrum:',i+1)
    ExtractSingleSpectrum(InputWorkspace='VCorr_VmB',OutputWorkspace='VCorr_VmB%s'%(i),WorkspaceIndex=i)
    if len(VPeaks) != 0:       
        StripPeaks(InputWorkspace='VCorr_VmB%s'%(i), OutputWorkspace='VCorr_VmB_strp%s'%(i), \
        FWHM=vanPeakFWHM[i], PeakPositions=VPeaks, PeakPositionTolerance=vanPeakTol[i])
    FFTSmooth(InputWorkspace='VCorr_VmB_strp%s'%(i),\
                         OutputWorkspace='VCorr_VmB_strp_sm%s'%(i),\
                         Filter="Butterworth",\
                         Params=str(vanSmoothing[i]+',2'),\
                         IgnoreXBins=True,
                         AllSpectra=True)
    SetSampleMaterial(InputWorkspace='VCorr_VmB_strp_sm%s'%(i), ChemicalFormula='V')
    ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm%s'%(i), OutputWorkspace='VCorr_VmB_strp_sm%s'%(i), Target='Wavelength')
    CylinderAbsorption(InputWorkspace='VCorr_VmB_strp_sm%s'%(i), OutputWorkspace='VCorr_a', AttenuationXSection=5.08, \
    ScatteringXSection=5.10, CylinderSampleHeight=vanHeight, CylinderSampleRadius=vanRadius, CylinderAxis='0,0,1')
    Divide(LHSWorkspace='VCorr_VmB_strp_sm%s'%(i), RHSWorkspace='VCorr_a', OutputWorkspace='VCorr_VmB_strp_sm_a%s'%(i))
    ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm_a%s'%(i), OutputWorkspace='VCorr_VmB_strp_sm_a%s'%(i), Target='dSpacing')
    Rebin(InputWorkspace='VCorr_VmB_strp_sm_a%s'%(i), OutputWorkspace='VCorr_VmB_strp_sm_a%s'%(i), Params=RebinParams,FullBinsOnly=True)

  #conjoin original spectra into a single workspace again
  root = 'VCorr_VmB_strp'
  ConjoinSpectra(InputWorkspaces=genHstNameLst(root,6), OutputWorkspace=root, LabelUsing=genHstNameLst('spec ',6))
  DeleteWorkspaces(genHstNameLst(root,6))
  root = 'VCorr_VmB_strp_sm'
  ConjoinSpectra(InputWorkspaces=genHstNameLst(root,6), OutputWorkspace=root)
  DeleteWorkspaces(genHstNameLst(root,6))
  root = 'VCorr_VmB_strp_sm_a'
  ConjoinSpectra(InputWorkspaces=genHstNameLst(root,6), OutputWorkspace='VCorr_VmB_strp_sm_a_afterConjoin')
  #DeleteWorkspaces(genHstNameLst(root,6))
  root = 'VCorr_VmB'
  DeleteWorkspaces(genHstNameLst(root,6))
  DeleteWorkspace(Workspace='VCorr_a')

  #ConvertUnits(InputWorkspace='VCorr_VmB',OutputWorkspace='VCorr_VmB', Target='dSpacing')
  #ConvertUnits(InputWorkspace='VCorr_VmB_strp',OutputWorkspace='VCorr_VmB_strp', Target='dSpacing')
  ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm',OutputWorkspace='VCorr_VmB_strp_sm',Target='dSpacing')
  #ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm_a',OutputWorkspace='VCorr_VmB_strp_sm_a', Target='dSpacing')
  
  ROILims=[ [dmins[0],dmaxs[0]],[dmins[1],dmaxs[1]],[dmins[2],dmaxs[2]],[dmins[3],dmaxs[3]],[dmins[4],dmaxs[4]],[dmins[5],dmaxs[5]] ]
  if inQ ==1:
      
      allPeaksToStripQ = d2Q(allPeaksToStrip)
      for i in range(len(ROILims)):
            ROILims[i] = [2*np.pi/x for x in ROILims[i]] #convert ROI limits to Q
      ConvertUnits(InputWorkspace='VCorr_VmB', OutputWorkspace='VCorr_VmB_Q', Target='MomentumTransfer')
      ConvertUnits(InputWorkspace='VCorr_VmB_strp', OutputWorkspace='VCorr_VmB_strp_Q', Target='MomentumTransfer')
      ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm', OutputWorkspace='VCorr_VmB_strp_sm_Q', Target='MomentumTransfer')
      ConvertUnits(InputWorkspace='VCorr_VmB_strp_sm_a', OutputWorkspace='VCorr_VmB_strp_sm_a_Q', Target='MomentumTransfer')
      if showFit == 2:
        gridPlot(['VCorr_VmB_Q','VCorr_VmB_strp_Q','VCorr_VmB_strp_sm_Q'],[],[[1,2,3],[4,5,6]],['Raw','Peaks stripped','Smoothed'],allPeaksToStripQ,ROILims,'Vanadium Setup')
      elif showFit == 3:
        gridPlot(['VCorr_VmB_strp_Q','VCorr_VmB_strp_sm_Q'],[],[[1,2,3],[4,5,6]],['Peaks stripped','smoothed'],[],ROILims,'Vanadium Setup')
      elif showFit == 4:
        gridPlot(['VCorr_VmB_strp_sm_Q','VCorr_VmB_strp_sm_a_Q'],[],[[1,2,3],[4,5,6]],['Smoothed','Att corrected'],[],[],'Vanadium Setup')
      else:
        DeleteWorkspace(Workspace='VCorr_VmB')
        DeleteWorkspace(Workspace='VCorr_VmB_strp')
        DeleteWorkspace(Workspace='VCorr_VmB_strp_sm')
        DeleteWorkspace(Workspace='VCorr_VmB_strp_sm_a')
  else:
    if showFit == 2:
        gridPlot(['VCorr_VmB','VCorr_VmB_strp','VCorr_VmB_strp_sm'],[],[[1,2,3],[4,5,6]],['Raw','Peaks stripped','Smoothed'],allPeaksToStrip,ROILims,'Vanadium Setup')
    elif showFit == 3:
        ROILims=[ [dmins[0],dmaxs[0]],[dmins[1],dmaxs[1]],[dmins[2],dmaxs[2]],[dmins[3],dmaxs[3]],[dmins[4],dmaxs[4]],[dmins[5],dmaxs[5]] ]
        gridPlot(['VCorr_VmB_strp','VCorr_VmB_strp_sm'],[],[[1,2,3],[4,5,6]],['Peaks stripped','smoothed'],[],ROILims,'Vanadium Setup')
    elif showFit == 4:
        gridPlot(['VCorr_VmB_strp_sm','VCorr_VmB_strp_sm_a'],[],[[1,2,3],[4,5,6]],['Smoothed','Att corrected'],[],'Vanadium Setup')
    else:
        DeleteWorkspace(Workspace='VCorr_VmB')
        DeleteWorkspace(Workspace='VCorr_VmB_strp')
        DeleteWorkspace(Workspace='VCorr_VmB_strp_sm')
        DeleteWorkspace(Workspace='VCorr_VmB_strp_sm_a')

  
  for i in range(nHst):
    print(i,dmins[i],dmaxs[i])
  CropWorkspaceRagged(InputWorkspace='VCorr_VmB_strp_sm_a_afterConjoin',OutputWorkspace='VCorr_d06',Xmin=dmins,Xmax=dmaxs)

  ws=mtd['VCorr_d06']
  ax = ws.getAxis(1)
  for i in range(nHst):
    ax.setLabel(i,'Spec %s'%(i+1))
  #Rebin operation is creating artifacts at the edge of spectra where data drops to zero. 
  #SumSpectra(InputWorkspace='VCorr_d06', OutputWorkspace='VCorr_dEast', ListOfWorkspaceIndices='0-2')
  #SumSpectra(InputWorkspace='VCorr_d06', OutputWorkspace='VCorr_dWest', ListOfWorkspaceIndices='3-5')
  #AppendSpectra(InputWorkspace1='VCorr_dEast', InputWorkspace2='VCorr_dWest', OutputWorkspace='VCorr_dEastWest')
  #DeleteWorkspace(Workspace='VCorr_dEast')
  #DeleteWorkspace(Workspace='VCorr_dWest')
  #SumSpectra(InputWorkspace='VCorr_d06', OutputWorkspace='VCorr_dAll', ListOfWorkspaceIndices='0-5')
  
  if inQ ==1:
      RebinParams = str(QStart)+','+ QBinSize + ',' + str(QEnd)
      print('d-space binning parameters are:',RebinParams)
      Rebin(InputWorkspace='VCorr_VmB_strp_sm_a_Q', OutputWorkspace='VCorr_Q6', Params=RebinParams,FullBinsOnly=True)
      SumSpectra(InputWorkspace='VCorr_Q6', OutputWorkspace='VCorr_QEast', ListOfWorkspaceIndices='0-2')
      SumSpectra(InputWorkspace='VCorr_Q6', OutputWorkspace='VCorr_QWest', ListOfWorkspaceIndices='3-5')
      AppendSpectra(InputWorkspace1='VCorr_QEast', InputWorkspace2='VCorr_QWest', OutputWorkspace='VCorr_QEastWest')
      DeleteWorkspace(Workspace='VCorr_QEast')
      DeleteWorkspace(Workspace='VCorr_QWest')
      SumSpectra(InputWorkspace='VCorr_Q6', OutputWorkspace='VCorr_QAll', ListOfWorkspaceIndices='0-5')
  return

#def GetConfig(ConfigFileName):
#    with open(ConfigFileName, "r") as json_file:
#        dictIn = json.load(json_file)
#    return dictIn

def iceVol(a):

#UNTITLED calculates ice VII molar volume based on lattice parameter 
# if lattice negative is given as negative number, assumes it's the 110
# then gives estimate of pressure based on fit to Hemley EOS 1987
  if a>=0:
    vm = a**3*0.5*0.6022
  elif a<0:
    a = -np.sqrt(2)*a
    vm = a**3*0.5*0.6022

  ad = 6/a**3; # 6 atoms in unit cell

  print('molar volume is : ' +str(vm)+ ' cm^3')
 # disp(['atom. density is: ' +str(ad) + ' atom/A^3'])


  p_hem = 1490.05895-558.82463*vm+81.14429*vm**2-5.3341*vm**3+0.13258*vm**4
  p_zul = 2202.87622-898.92604*vm+141.2403*vm**2-10.02239*vm**3+0.26903*vm**4
  #print('*correct* Pressure (Hemley EOS): ' + str(p_hem) + ' GPa')
  #print('*correct* Pressure (Zulu radial EOS): ' + str(p_zul) + ' GPa')

  return p_hem


def checkSNAPState(floatPar,intPar):
  #This function will find the most recent SNAP StateList, make a copy,
  # with the new state appended. 
  #8 Dec modified to include frequency, retaining spare float

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
    print('State consistent with SNAP Dictionary\n')
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
        print('\nMatch found for state: %s\n\n'%(stateID),line,'\n')
        stateIDMatch = True
        fin.close()
        break
  
  

  if not stateIDMatch:
    print('')
    togCreateNewList=builtins.input('WARNING: Current state does not exist in State List! Create new state (y/[n])?')
    #togCreateNewList
    if togCreateNewList.lower()=='y':
      now = date.today()
      newListFile = '/SNS/SNAP/shared/Calibration/SNAPStateList_' + now.strftime("%Y%m%d") + '.txt'
      fout = open(newListFile,'w')
      fout.writelines(lines)#copy existing state ID's to new file
      acceptableName = False
      while not acceptableName:
        shortTitle = builtins.input('provide short (up to 15 character) title for state: ')
        shortTitle = shortTitle[0:15].ljust(15)
        confirm = builtins.input('confirm title: '+shortTitle+' ([y]/n): ')
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

def getSNAPPars(wsName):
#returns stateID for an existing mantid workspace (which must contain logs)
  from mantid.simpleapi import mtd
  
  ws = mtd[wsName]
  logRun = ws.getRun()

  # get log data from nexus file
  print('\n/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_')
  print('Log Values:')
  fail = False
  try:
      det_arc1 = logRun.getLogData('det_arc1').value[0]
      print('det_arc1 is:',det_arc1)
  except:
      print('ERROR: Nexus file doesn\'t contain value for det_arc1')
      fail = True

  try:    
      det_arc2 = logRun.getLogData('det_arc2').value[0]
      print('det_arc2 is:',det_arc2)
  except:
      print('ERROR: Nexus file doesn\'t contain value for det_arc2')
      fail = True

  try:
      wav = logRun.getLogData('BL3:Chop:Skf1:WavelengthUserReq').value[0]
      print('wav Skf1 wavelengthUserReq is:',wav, 'Ang.')
  except:
      print('ERROR: Nexus file doesn\'t contain value for central wavelength')
      fail = True

  try:
      freq = logRun.getLogData('BL3:Det:TH:BL:Frequency').value[0]
      print('frequency setting is:',freq, 'Hz')
  except:
      print('ERROR: Nexus file doesn\'t contain value for central wavelength')
      fail = True

  try:
      GuideIn = logRun.getLogData('BL3:Mot:OpticsPos:Pos').value[0]
      print('guide status is:',GuideIn)
  except:
      print('ERROR: Nexus file doesn\'t contain guide status')
      fail = True
  print('/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_')


  if not fail:
      stateID = checkSNAPState([det_arc1,det_arc2,wav,freq,0.0],[GuideIn,0])
  else:
      print('Insufficient log data, can\'t determine state')
      stateID='00000-00'
  #DeleteWorkspace(Workspace='Dummy2')
  return stateID

def StateFromRunFunction(runNum):
  #returns stateID and info given a run numner
#  #from mantid.simpleapi import mtd
#  from mantid.simpleapi import *
  import h5py
  import sys
  #from datetime import datetime, date
  #from os.path import exists
#  import mgutilities as mg
#  import importlib
#  importlib.reload(mg)

#  runNum = sys.argv[1]
  inst= 'SNAP'
  nexusLoc = 'nexus'
  nexusExt = '.nxs.h5'
  IPTSLoc = GetIPTS(RunNumber=int(runNum),Instrument=inst)
  fName = IPTSLoc + nexusLoc + '/SNAP_' + runNum + nexusExt
  print(fName)
  f = h5py.File(fName, 'r')
  fail = False
  try:
      det_arc1 = f.get('entry/DASlogs/det_arc1/value')[0]
  except:
      print('ERROR: Nexus file doesn\'t contain value for det_arc1')
      fail = True
  try:    
      det_arc2 = f.get('entry/DASlogs/det_arc2/value')[0]
  except:
      print('ERROR: Nexus file doesn\'t contain value for det_arc2')
      fail = True
  try:
      wav = f.get('entry/DASlogs/BL3:Chop:Skf1:WavelengthUserReq/value')[0]
  except:
      print('ERROR: Nexus file doesn\'t contain value for central wavelength')
      fail = True
  try:
      freq = f.get('entry/DASlogs/BL3:Det:TH:BL:Frequency/value')[0]
  except:
      print('ERROR: Nexus file doesn\'t contain value for frequency')
      fail = True
  try:
      GuideIn = f.get('entry/DASlogs/BL3:Mot:OpticsPos:Pos/value')[0]
  except:
      print('ERROR: Nexus file doesn\'t contain guide status')
      fail = True

  if not fail:
      stateID = checkSNAPState([det_arc1,det_arc2,wav,freq,0.0],[GuideIn,0])
  else:
      print('ERROR: Insufficient log data, can\'t determine state')
      stateID='00000-00'

  return stateID

def Vinet(V,V0,K,Kp):
  p = 3*K*(V/V0)**(-2/3)*(1-(V/V0)**(1/3))*np.exp((3/2)*(Kp-1)*(1-(V/V0)**(1/3)))
  return p

def BM(V,V0,K,Kp):
  r = V0/V
  p = 1.5*K*(r**(7/3)-r**(5/3))*(1 + 0.75*(Kp-4)*(r**(2/3)-1))
  return p  
