# This module is used to define "fixed" instrument pars - these shall change very infrequently. This is also
# used to specify file and folder structure, to make global changes easier. Note this also allows
# a way to manage some of the highly-specific local set up here at the SNS. 

inst = 'SNAP'
nexusFileExt='.nxs.h5'
nexusFilePre='SNAP_'
stateLoc='/SNS/SNAP/shared/Calibration/' #location of all statefolders
calibFilePre='SNAPcalibLog'
calibFileExt='json'
# relative paths from main IPTS folder. Full paths generated from these for specific runs
sharedDirLoc='shared/'
nexusDirLoc='nexus/' #relative to ipts directory 
reducedDirLoc='shared/test/reduced/' #temporary location


