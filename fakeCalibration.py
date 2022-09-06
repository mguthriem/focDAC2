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
calRun = 57251
now = date.today()

#state specific parameters (same for all runs)
stateRedPars={
'calibDate':now.strftime("%Y%m%d"),
'calibBy':'Malcolm',    
'stateID':stateID,
'tofMin':1500,
'tofBin':10,
'calFileName':'SNAP057251_calib_geom_20220831.h5',\
'tofMax':16600,
'CRun':[calRun],
'rawVCorrFileName':'RVMB57248.nxs', 
'rawVCorrMaskFileName':'',
'superPixEdge':8,
'wallClockTol':60,
#diffraction grouping set up
#includes temporary fix for arbitrary groupings of columes (for Bianca Ni data)
#these names are currently defined in FocDACUtilities.setupStateGrouping
'focGroupLst':['Column','Group','All'],#,'Gp01','Gp02'],
'focGroupNHst':[6,2,1],
# 'focGroupDMin':[[0.37,0.40,0.47,0.48,0.58,0.75],[0.48]],
# 'focGroupDMax':[[2.1,2.3,2.6,2.8,3.5,4.3],[2.8]],
# 'focGroupDBin':[[-0.001,-0.001,-0.001,-0.001,-0.001,-0.001],[-0.001]]
'focGroupDMin':[[0.37,0.40,0.47,0.48,0.58,0.75],[0.75,0.75],[0.75]],
'focGroupDMax':[[2.1,2.3,2.6,2.8,3.5,4.3],[2.8],[4.4,4.4],[4.4]],
'focGroupDBin':[[-0.001,-0.001,-0.001,-0.001,-0.001,-0.001],[-0.001]]
# 'focGroupDMin':[[0.338,0.377,0.428,0.458,0.535,0.697],[0.35,0.5],[0.4],[0.85],[0.85]],
# 'focGroupDMax':[[2.14,2.35,2.65,2.80,3.35,4.20],[2.7,4.6],[5.0],[2.75],[3.1]],
# 'focGroupDBin':[[-0.00086,-0.00096,-0.0013,-0.00117,-0.00147,-0.00186],[-0.001,-0.001],[-0.0008],[-0.001],[-0.001]]
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




