# focDAC2
a state-aware mantid-based workflow for reducing TOF-neutron powder diffraction data on the SNAP instrument at the SNS.

## Overview

This project contains several python modules that, together with mantid (mantidproject.org) algorithms are scripted to convert raw neutron diffraction data (collected on the SNAP instrument at the SNS, Spallation Source) into fully reduced files suitable for subsequent refinement using Rietveld approaches.

It is developed for the most common SNAP use case: reducing the data from a single experimental run, contained in a single nexus-format data file, assuming the sample state is constant during the measurement. As such, the measured neutron-event data are not used. This case contrasts with other instruments, where the sample state varies during a single experimental run, and the event data are then binned according to some parameter (time, strain, temperature etc) that varies during the measurement. 

Would be interesting to add this capability but, for now this isn't being done.

### Initial Features: 

1) The workflow shall identify the operating state of the instrument and use this information to obtain pre-determined set of calibration information and data reduction parameters

2) The workflow shall allow diffraction focusing for arbitrary pixel groupings

3) The workflow shall allow the application of full 3d Q-dependent bin masking

4) The workflow shall implement established reduction methods to correctly normalise the measured intensities

5) The workflow shall allow output of files for Rietveld refinement using a standardised folder structure, reflecting grouping of pixels

6) A complete set of reduction parameters shall be stored with the reduced data enable easy repetition of the workflow at a future point in time. 

### Planned Features:

1) The workflow shall be operable on live data.

2) The workflow shall be optimised for speed and minimal memory usage

...
