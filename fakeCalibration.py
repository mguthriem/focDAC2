import yaml
import json
import SNAP_InstPrm as iPrm
from datetime import datetime, date

#idea here is that there will be an automated "calibration workflow" at some point that will generate the
#file that is being created here with so it can be accessed during the reduction workflow. The contents
#of this file are strictly state dependent and should be constant for all runs reduced.

#some variables (e.g. calibration runs) will be updated when there is a new calibration. Most of the time this
# is the only thing that will change, but it's possible other parameters might change too. So, my idea
# is that a new calibration file (like the one being created here would be created every time the instrument
# is calibrated 
# 

stateID = '13500-20'
now = date.today()

#state specific parameters (same for all runs)
stateRedPars={
'calibDate':now.strftime("%Y%m%d"),
'calibBy':'Malcolm',    
'stateID':stateID,
'tofMin':4600,
'tofBin':10,
'calFileName':'SNAP051374_calib_geom_20220805.h5',\
'tofMax':16600,
'CRun':[51374],
'rawVCorrFileName':'RVMB57242.nxs', 
'rawVCorrMaskFileName':'',
'superPixEdge':8,
'wallClockTol':60,
#diffraction grouping set up
'focGroupLst':['Column','Group','All'],
'focGroupNHst':[6,2,1],
# 'focGroupDMin':[[0.37,0.40,0.47,0.48,0.58,0.75],[0.48]],
# 'focGroupDMax':[[2.1,2.3,2.6,2.8,3.5,4.3],[2.8]],
# 'focGroupDBin':[[-0.001,-0.001,-0.001,-0.001,-0.001,-0.001],[-0.001]]
'focGroupDMin':[[0.80,0.90,1.05,0.95,1.15,1.48],[0.90,1.15],[1.01]],
'focGroupDMax':[[2.6,2.9,3.5,3.15,3.85,5.0],[3.75,5.8],[5.8]],
'focGroupDBin':[[-0.001,-0.001,-0.001,-0.001,-0.001,-0.001],[-0.001,-0.001],[-0.001]]
}

#Use run number of geometric calibration run to generate name of file and write this as both
#yaml and json 
 
fullCalPath = iPrm.stateLoc+stateID+'/'+iPrm.inst +'calibLog'+str(stateRedPars['CRun'][0]) + '.yaml'

with open(fullCalPath,'w') as file:
    docs = yaml.dump(stateRedPars, file)
print(f'created calibLog at: {fullCalPath}')


fullCalPath = iPrm.stateLoc+stateID+'/'+iPrm.inst +'calibLog'+str(stateRedPars['CRun'][0]) + '.json'
with open(fullCalPath, "w") as file:
    json.dump(stateRedPars, file)
print(f'created calibLog at: {fullCalPath}')




