# import mantid algorithms, numpy and matplotlib
from mantid.simpleapi import *
#from mantidqt.widgets.instrumentview.api import get_instrumentview
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from mantid.plots.utility import MantidAxType
from mantid.api import AnalysisDataService as ADS
import numpy as np
import sys
from datetime import datetime, date
from os.path import exists
import FocDACUtilities as DAC
import mgutilities as mg
import importlib
importlib.reload(DAC)

#M. Guthrie 16 Dec 2021: added built in graphics to allow user to confirm input data quality 
#and resultant fit

#M. Guthrie 7 Sept 2022: added lite

class StopExecution(Exception):
    def _render_traceback_(self):
        pass

lite = True

#run = 51984
if len(sys.argv)==1:
    print('SNAPAutoCal syntax:\n SNAPAutoCal run calibrant\n')
    print('run can be single run, comma-separated list or range specified as firstun : last run\n')
    print('calibrant can be one of: diamond, ni, nacl or lab6 (case insensitive)\n')
    print('Enter these here:')
    [runstring,calibrant]=input('Enter run and calibrant:')
else:
    runstring= str(sys.argv[1])
    try: 
        print(sys.argv[2].lower)
        calibrant = str(sys.argv[2]).strip().lower()
    except:
        print('WARNING: need to specify calibrant after run number')
        calibrant = input('Enter now: (e.g. diamond):')
        calibrant = str(calibrant).strip().lower()

pixSum = 16

# tog = input(f'calibrant is: {calibrant} OK to continue ([y],n):?')
# tog = str(tog).strip().lower()
# #tog = 'y'
# if tog =='n':
#     print('OK. STOPPING!')
#     raise StopExecution

#print('Calibrant is: ',calibrant)
if calibrant =='diamond':
    print('Expecting a diamond powder dataset')
    peaksToFit = '2.0595,1.2612,1.0755, 0.8918, 0.8183, 0.7281'
    #need good statistics to fit shorter peaks: 0.6865, 0.6306,0.6029'
    #Diamond peak positions from Shikata et al J. Appl. Phys 57, 111301 (2018).
    #Reported lattice parameter is: 3.567095 ± 0.000017
elif calibrant =='lab6':
    peaksToFit = '4.1561,2.9388,2.3995,2.0781,1.8587,1.6967,1.3854,1.3143,1.0390,1.0080,0.9796'
    print('Expecting a LaB6 powder dataset')
    #Peak positions are taken from Booth et al PRB 63 2243021-2243028 (2001).
elif calibrant == ('ni' or 'nickel'):
    print('Expecting a Ni powder dataset')
    peaksToFit = '2.0346,1.7620,1.2459,1.0625,1.0173,0.8810,0.8085,0.7880'
    #lattice parameter a = 3.524 taken from webelements.com...CHECK!
elif calibrant =='nacl':
    print('Expecting a NaCl powder dataset')
    peaksToFit = '3.2527, 2.8169, 1.9918,1.6987,1.6263,1.4084,1.2925,1.2598,1.1500'
    peaksToFit = '2.8169'
    #lattice parameter a = 5.6338 (7) Lee, Seungyeol; Xu, Huifang; Xu, Hongwu; Neuefeind, Joerg, Minerals, (2021) 11 (3) p1-12
elif calibrant =='nac':
    print('Expecting a NAC powder dataset')
    peaksToFit = '2.4176,2.2935,2.1868,2.0116,1.8727,1.8132,1.6639'
    #structure from G. Courbion, JSol Stat Chem (1988)
elif calibrant == '':
    print('Must enter type of calibrant sample after run number')
    sys.exit()
else:
    print('Currently only works for diamond and LaB6!')
    sys.exit()

pks = peaksToFit.split(',')
nPks = len(pks)

#check situation where calibration measurement spans multiple runs
if ':' in runstring:
    #run string describes a range of runs
    firstrun = runstring.split(':')[0]
    lastrun = runstring.split(':')[1]
    runlist = [item for item in range(firstrun,lastrun+1)]
elif ',' in runstring:
    runlist = runstring.split(',')
else:
    runlist = [runstring]
print('runlist is: ',runlist)


if runlist != '00000': #allow for case where data are loaded manually
    for run in runlist:
        IPTSLoc = GetIPTS(RunNumber=run,Instrument='SNAP')
        if lite:
        #First need to create local directory if it doesn't exist
            liteDir = f'{IPTSLoc}shared/lite/'
            if not os.path.exists(liteDir):
                os.makedirs(liteDir)
            inF = f'{IPTSLoc}/nexus/SNAP_{run}.nxs.h5'
            outF = f'{liteDir}SNAP_{run}.lite.nxs.h5'
            DAC.makeLite(inFileName=inF,
            outFileName=outF)
            LoadEventNexus(f'{liteDir}SNAP_{run}.lite.nxs.h5',
            OutputWorkspace=f'{run}')
        else:
            IPTSLoc = GetIPTS(RunNumber=run,Instrument='SNAP')
            inputFile = IPTSLoc + '/nexus/SNAP_%s'%(run) + '.nxs.h5'
            # check file exists
            if not exists(inputFile):
                print('error! input nexus file does not exist')
                raise StopExecution
                #sys.exit() #terminate
            # load nexus file and determine instrument state
            LoadEventNexus(Filename=inputFile, OutputWorkspace=f'{run}')
    MergeRuns(InputWorkspaces=runlist,OutputWorkspace='calFile')
else:
    print('looking for manually prepared ws: calFile')
    
stateID = mg.getSNAPPars('calFile')

# Fit DIFCs and Zeros
if lite:
    CloneWorkspace(InputWorkspace='calFile',OutputWorkspace='calFile_8x8')
else:
    SumNeighbours(InputWorkspace='calFile', OutputWorkspace='calFile_8x8', SumX=pixSum, SumY=pixSum)
Rebin(InputWorkspace='calFile_8x8',OutputWorkspace='calFile_8x8',Params='1500,10,15500',PreserveEvents=False,FullBinsOnly=True)

#Show user plot of input data to allow inspection (and sanity check)

if pixSum == 16:
    mg.gridPlot(['calFile_8x8'],[],[[442,1192,1912],[4215,3463,2696]],[],[],[],'Sample spectra')
elif pixSum ==8:
    mg.gridPlot(['calFile_8x8'],[],[[1584,2786,7567],[16851,13808,10802]],[],[],[],'Sample spectra')
#plt.show(block=False)
tog = input('Do input data look OK to continue ([y],n):?')
tog = str(tog).strip().lower()
#tog = 'y'
if tog =='n':
    print('OK. STOPPING!')
    raise StopExecution

#print('starting to fit spectra...')

PDCalibration(InputWorkspace='calFile_8x8', TofBinning='1500,10,16000',\
    PeakFunction='Gaussian',BackgroundType='Linear',\
    PeakPositions=peaksToFit, CalibrationParameters='DIFC', OutputCalibrationTable='_cal',\
    DiagnosticWorkspaces='_diag',MaxChiSq=7)

if pixSum == 16:
    mg.gridPlot(['calFile_8x8','_diag_fitted'],[],[[442,1192,1912],[4215,3463,2696]],[],[],[],'Sample spectra')
elif pixSum ==8:
    mg.gridPlot(['calFile_8x8','_diag_fitted'],[],[[1584,2786,7567],[16851,13808,10802]],[],[],[],'Sample spectra')

# Save temp copy of calibration File to correct State folder.
# option to inspect and make permanent copy later
stateFolder = '/SNS/SNAP/shared/Calibration/%s/'%(stateID)
now = date.today()
calibFilename = stateFolder + 'temp.h5' #SNAP_calibrate_d%s_'%(run)+ now.strftime("%Y%m%d") + '.h5'
SaveDiffCal(CalibrationWorkspace='_cal',Filename=calibFilename)

# Check calibration by using SNAPReduce to create focused detector columns

tog = input('Run SNAPReduce to inspect columns (y,[n]):?')
tog = str(tog).strip().lower()
#tog = 'n'
if tog =='y':
    SNAPReduce(RunNumbers=str(run),\
    Calibration='Calibration File', CalibrationFilename=calibFilename,\
    Binning='0.5,-0.002,4', GroupDetectorsBy='Column')

    ##SCRIPT TO PLOT OUTPUT SPECTRA FROM SNAPREDUCE
    SNAPRedWSName = 'SNAP_' + str(run) + '_Column_red'
    SNAPredOut = ADS.retrieve(SNAPRedWSName)

    fig, axes = plt.subplots(num='SNAPreduce Output', subplot_kw={'projection': 'mantid'})
    axes.plot(SNAPredOut, color='#1f77b4', label='SNAPredOut: spec 1', wkspIndex=0)
    axes.plot(SNAPredOut, color='#ff7f0e', label='SNAPredOut: spec 2', wkspIndex=1)
    axes.plot(SNAPredOut, color='#2ca02c', label='SNAPredOut: spec 3', wkspIndex=2)
    axes.plot(SNAPredOut, color='#d62728', label='SNAPredOut: spec 4', wkspIndex=3)
    axes.plot(SNAPredOut, color='#9467bd', label='SNAPredOut: spec 5', wkspIndex=4)
    axes.plot(SNAPredOut, color='#8c564b', label='SNAPredOut: spec 6', wkspIndex=5)
    axes.tick_params(axis='x', which='major', **{'gridOn': False, 'tick1On': True, 'tick2On': False, 'label1On': True, 'label2On': False, 'size': 6, 'tickdir': 'out', 'width': 1})
    axes.tick_params(axis='y', which='major', **{'gridOn': False, 'tick1On': True, 'tick2On': False, 'label1On': True, 'label2On': False, 'size': 6, 'tickdir': 'out', 'width': 1})
    axes.set_title('SNAPredOut')
    axes.set_xlabel('d-Spacing ($\\AA$)')
    axes.set_ylabel('Counts (microAmp.hour $\\AA$)$^{-1}$')
    #legend = axes.legend(fontsize=8.0).set_draggable(True).legend
    legend = axes.legend(fontsize=8.0).draggable()
    plt.show()

#Option to inspect fitting data versus scattering angle

tog = input('Inspect fitted peak widths (y,[n]):?')
tog = str(tog).strip().lower()
#tog = 'y'
if tog =='y':
    #get 2theta info from detector table
    CreateDetectorTable(InputWorkspace='calFile',DetectorTableWorkspace='calFile_detectorInfo')
    #get 2theta info from detector table for SumNeighbours output
    CreateDetectorTable(InputWorkspace='calFile_8x8',DetectorTableWorkspace='calFile_detectorInfo_8x8')
    # get ttheta values for full detector and SumNeighbours (SN) instrument 
    ws = mtd['calFile_detectorInfo_8x8']
    tableData = ws.toDict()
    ttSN = np.array(tableData['Theta']) #why isn't it called ttheta!!?
    ksortSN = np.argsort(ttSN) #index to sort values in order of increasing ttheta

    ws = mtd['calFile_detectorInfo']
    tableData = ws.toDict()
    tt = np.array(tableData['Theta']) #why isn't it called ttheta!!?
    ksort = np.argsort(tt) #index to sort values in order of increasing ttheta   

    # get chi2 and store as function of ordered tt in workspace
    ws = mtd['_diag_fitparam']
    tableData = ws.toDict()
    chi2 = np.array(tableData['chi2'])# np array of chi2 sorted with increasing ttheta
    CreateWorkspace(OutputWorkspace='Chi2AngularInfo',DataX=ttSN[ksortSN],DataY=chi2[ksortSN])
    #plot chi


    Chi2AngularInfo = ADS.retrieve('Chi2AngularInfo')

    fig, axes = plt.subplots(num='Chi2AngularInfo-11', subplot_kw={'projection': 'mantid'})
    axes.plot(Chi2AngularInfo, color='#1f77b4', label='Chi2AngularInfo: spec 1', wkspIndex=0)
    axes.tick_params(axis='x', which='major', **{'gridOn': False, 'tick1On': True, 'tick2On': False, 'label1On': True, 'label2On': False, 'size': 6, 'tickdir': 'out', 'width': 1})
    axes.tick_params(axis='y', which='major', **{'gridOn': False, 'tick1On': True, 'tick2On': False, 'label1On': True, 'label2On': False, 'size': 6, 'tickdir': 'out', 'width': 1})
    axes.set_title('Chi2AngularInfo')
    axes.set_xlabel('ttheta (deg)')
    axes.set_ylabel('chi2')
    axes.set_ylim([0.0, 5.0])
    #legend = axes.legend(fontsize=8.0).set_draggable(True).legend
    plt.show()

    # get widths for all fitted peaks
    ws = mtd['_diag_width']
    tableData = ws.toDict()
    xData = [] 
    yData = []
    fitted_pks = []
    interpx = np.linspace(40.0,120.0,20)
    nSpec=0
    for i in range(nPks):
        
        dictVal = '@' + pks[i].replace(" ","")    
        try:
            tmpY = np.array(tableData[dictVal])
            tmpY = tmpY[ksort]
            fitted_pks.append(float(pks[i])) #only d-spacings for peaks that have been successfully fitted
            print('Got data for peak: ',i,' name: ',dictVal)
            interpy = np.interp(interpx,tt[ksort],tmpY)
            xData.append(np.ndarray.tolist(interpx))
            yData.append(np.ndarray.tolist(interpy))
        except:
            print('Couldn\'t find data for peak', i,dictVal)
        
    print('size of xData=',len(xData))
    nSpec = len(fitted_pks)
    print('number of peaks with fitted data: ',nSpec)
    xData = np.array(xData)
    yData = np.array(yData)
    CreateWorkspace(OutputWorkspace='GaussWidths_vs_tt',DataX=xData,DataY=yData,NSpec=nSpec)
    nfitted,ntt=xData.shape
    # parse peak widths into array as a function of d-spacing for each ttheta bin
    #xData = np.array(pks).astype(np.float) #new array with d-spacings in it
    yData = np.transpose(yData)
    xData = []
    for i in range(ntt):
        xData.append(fitted_pks) #x values are now all d-spacings for peaks at this ttheta
    xData=np.array(xData)    
    CreateWorkspace(OutputWorkspace='GaussWidths_vs_d',DataX=xData,DataY=yData,NSpec=ntt,UnitX='dspacing',\
        YUnitLabel='sigma')    

    GaussWidths_vs_d = ADS.retrieve('GaussWidths_vs_d')

    fig, axes = plt.subplots(num='GaussWidths_vs_d-12', subplot_kw={'projection': 'mantid'})
    axes.plot(GaussWidths_vs_d, color='#1f77b4', label='GaussWidths_vs_d: spec 1', marker='o', wkspIndex=0)
    axes.plot(GaussWidths_vs_d, color='#ff7f0e', label='GaussWidths_vs_d: spec 2', marker='o', wkspIndex=1)
    axes.plot(GaussWidths_vs_d, color='#2ca02c', label='GaussWidths_vs_d: spec 3', marker='o', wkspIndex=2)
    axes.plot(GaussWidths_vs_d, color='#d62728', label='GaussWidths_vs_d: spec 4', marker='o', wkspIndex=3)
    axes.plot(GaussWidths_vs_d, color='#9467bd', label='GaussWidths_vs_d: spec 5', marker='o', wkspIndex=4)
    axes.plot(GaussWidths_vs_d, color='#8c564b', label='GaussWidths_vs_d: spec 6', marker='o', wkspIndex=5)
    axes.tick_params(axis='x', which='major', **{'gridOn': False, 'tick1On': True, 'tick2On': False, 'label1On': True, 'label2On': False, 'size': 6, 'tickdir': 'out', 'width': 1})
    axes.tick_params(axis='y', which='major', **{'gridOn': False, 'tick1On': True, 'tick2On': False, 'label1On': True, 'label2On': False, 'size': 6, 'tickdir': 'out', 'width': 1})
    axes.set_title('GaussWidths_vs_d')
    axes.set_xlabel('d-spacing (Ang)')
    axes.set_ylabel('Gauss sigma')
    #legend = axes.legend(fontsize=8.0).set_draggable(True).legend

    plt.show()
# Scripting Plots in Mantid:
# https://docs.mantidproject.org/tutorials/python_in_mantid/plotting/02_scripting_plots.html


#check if all is OK then output final calibration...
## (n.b. sometime before reaching run 100,000 fix formating of name)
if lite:
    calibFilename = stateFolder + 'SNAP0%s_'%(run)+ 'calib_geom_' + now.strftime("%Y%m%d") + '.lite.h5'
else:
    calibFilename = stateFolder + 'SNAP0%s_'%(run)+ 'calib_geom_' + now.strftime("%Y%m%d") + '.h5'
tog = input('Happy with calibration? Save file (y,[n] or tmp)?\n(tmp will store in /SNS/SNAP/shared/temp): ')
tog = str(tog).strip().lower()
if tog =='y':
    print(calibFilename)
    SaveDiffCal(CalibrationWorkspace='_cal',Filename=calibFilename)
if tog =='tmp':
    print('Saving file to /SNS/SNAP/shared/temp/')
    calibFilename = '/SNS/SNAP/shared/temp/' + 'SNAP0%s_'%(run)+ '_calib_geom' + now.strftime("%Y%m%d") + '.h5'
    SaveDiffCal(CalibrationWorkspace='_cal',Filename=calibFilename)
else:
    print('Finished')
    sys.exit()

#Lastly clean up unused workspaces
##DeleteWorkspace('_cal')
#DeleteWorkspace('_cal_mask')
#DeleteWorkspace('calFile')
#DeleteWorkspace('calFile_8x8')
#DeleteWorkspace('Column')
#myiv = get_instrumentview('calFile')
#myiv.show_view()
