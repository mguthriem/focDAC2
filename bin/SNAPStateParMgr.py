def SNAPStateParMgr(run):

#SNAPParMGr module to identify state and load Reduction parameters from specified corresponding
#location

    #state specific parameters (same for all runs)
    stateRedPars={
    'stateID':'14100-10',
    'tofMin':3000,
    'tofMax':16800,
    'calFile':'/SNS/SNAP/shared/Calibration/14100-10/SNAP049835_calib_geom_20220726.h5',\
    'superPixEdge':8,
    'wallClockTol':60,
    #diffraction grouping set up
    'focGroupLst':['Column','All'],
    'focGroupNHst':[6,1],
    'focGroupDMin':[[0.5,0.5,0.5,0.5,0.65,0.8],[0.5]],
    'focGroupDMax':[[2.1,2.3,2.6,2.8,3.5,4.5],[4.5]],
    'focGroupDBin':[[-0.001,-0.001,-0.001,-0.001,-0.001,-0.001],[-0.001]]
    }

    return instRedPars.update(stateRedPars) #combined dictionary with all pars

    #populate variables from the dictionary values

    stateID = stateRedPars['stateID']
    tofMin = stateRedPars['tofMin']
    tofMax = stateRedPars['tofMax']
    calFile = stateRedPars['calFile']
    superPixEdge = stateRedPars['superPixEdge']
    wallClockTol = stateRedPars['wallClockTol']
    focGroupLst = stateRedPars['focGroupLst']
    focGroupDMin = stateRedPars['focGroupDMin']
    focGroupDMax = stateRedPars['focGroupDMax']
    focGroupDBin = stateRedPars['focGroupDBin']



