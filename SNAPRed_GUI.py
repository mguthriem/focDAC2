from mantid.simpleapi import *
from mantid import config
config.setLogLevel(0, quiet=True)
import time

import FocDACUtilities as DAC
import SNAP_InstPrm as iPrm 
import importlib
importlib.reload(DAC)

importlib.reload(iPrm)
import panel as pn
from panel.template import DarkTheme

import matplotlib

# %matplotlib widgets

#pn.extension(template='material')
pn.widgets.Select.sizing_mode = 'stretch_both'

import pandas as pd

#bootstrap = pn.template.BootstrapTemplate(title = 'SNAPReduce 2.0')
#set up some widgets
#Tab1:
#column1:
stat = pn.pane.Markdown("")
runInput = pn.widgets.TextInput(name='Run Number')
mask_Toggle = pn.widgets.Checkbox(name='Is mask required?',value=False)
maskName = pn.widgets.TextInput(name='Pixel Mask FileName',value='snap48741msk.xml',disabled=True)
red_Button = pn.widgets.Button(name='Reduce',button_type='primary',disabled=True)
calibState_Toggle = pn.widgets.RadioButtonGroup(name='Calib. status relative to run ?',
                                               options=['Before','After','Manual'],value='Before')
red_Status = pn.widgets.TextInput(name='Reduction Status',value='idle')

#column2
abutton = pn.widgets.Button(name='Something went wrong press me!',button_type='danger',visible=False)
someMarkdown = pn.pane.Markdown("One day this button will actually do something")
someMarkdown.visible=False
#Tab2:
CU_Toggle = pn.widgets.Checkbox(name='ConvertUnits')
GSASOut_Toggle = pn.widgets.Checkbox(name='Output to GSAS')
AsciiOut_Toggle = pn.widgets.Checkbox(name='Output Ascii as csv')
rebin_FloatSlider = pn.widgets.FloatSlider(name='Down Sample Binning',start = 0.0, end = 10.0, step = 1,value=0)

#Tab3:
groupSelect_Toggle = pn.widgets.RadioButtonGroup(name='Detector Grouping',
                                                 options=['Column','Bank','All'],value='Column')
#mskNameInput_wgt= pn.widgets.FileSelector('/SNS/SNAP/shared')
png = pn.panel('https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png', width=500)

def stateStatus(target, event):

    stateID,sDict,errorState = DAC.StateFromRunFunction(event.new)
    # there are a great number of ways that the above function can fail.
    # I have edited it (and all sub functions) to pass errorState a dictionary
    # with sufficient informations to handle exceptions
    
    if errorState['value']==0:
        # stateString = (f'''
        # State Validated!
        
        # State calibration folder: 
        # {iPrm.stateLoc}{stateID}/
        # ''')
        stateString = (f'''

        ### State ID: {stateID}


        |Parameter    | Value                 | 
        |-------------|-----------------------|
        |det1         | {sDict["det_arc1"]:.1f}  |
        |det_arc2     | {sDict["det_arc2"]:.1f}   |
        |wav          | {sDict["wav"]:.2f}        |
        |freq         | {sDict["freq"]:.2f}    |
        |guide status:| {sDict["GuideStat"]}  |

        State calibration folder: 
        {iPrm.stateLoc}{stateID}/
        
                      ''')
        target.object = stateString
    
        sPrm = DAC.getStatePrm(int(event.new),calibState_Toggle.value)
        red_Button.disabled = False
        abutton.visible=False
        someMarkdown.visible=False
        sPrm_df = pd.DataFrame.from_dict(sPrm)
        prm_df = pn.pane.DataFrame(sPrm_df,width=400)
        col1b = pn.Column(abutton,prm_df)
    else:
        stateString = (f'''
        
        ###An error has occurred: 
        
        * function: {errorState['function']} failed
        * ERROR: {errorState['value']} - {errorState['message']}
        * details: {errorState['parameters']} 
        
        
        ''')
        target.object = stateString
        red_Button.disabled = True
        abutton.visible=True
        someMarkdown.visible=True


runInput.link(stat,callbacks={'value': stateStatus})

def showData(run2plot,focGrp,UseSpec):

    wsName = f'DSpac{run2plot}_pixMsk_Columns'
    run = str(AllRuns[0])# = 'gp2'
    figTitle = f'All histograms for run: {run}'
    offset = 0.5
    fig, ax = plt.subplots()
    for kk in range(6):
        #wsName = dataFileNamePrepend+run+dataFileNameAppend
        ConvertToPointData(InputWorkspace=wsName,OutputWorkspace='pts')
        ws = mtd['pts']
        x = ws.readX(kk)
        y = ws.readY(kk)+kk*offset
        ax.plot(x,y,label=f'hist {kk}')
    ax.set_title(figTitle)
    plt.xlim(0.9,2.1)
    plt.ylim(-0.3,3)
    plt.legend()
    plt.xlabel('d-spacing, d (Ang)')
    plt.ylabel('Arb. Intensity')
    return fig

col1a = pn.Column(runInput,red_Button,red_Status,stat)
col1b = pn.Column(abutton,someMarkdown)
row1 = pn.Row(col1a,col1b)
col2 = pn.Column(pn.pane.Str('Select calibration mode:'),calibState_Toggle,mask_Toggle,maskName,CU_Toggle,GSASOut_Toggle,AsciiOut_Toggle)
col3 = pn.Column(groupSelect_Toggle,rebin_FloatSlider, png)

tabs = pn.Tabs()
tabs.append(('Main',row1))
tabs.append(('Advanced Settings',col2))
tabs.append(('Visualisation',col3))

#define action when reduce button is pressed

def b(event):
    red_Status.value = 'Working'
    settings = dict()
    settings['calibState']=calibState_Toggle.value
    settings['GSASOut']=GSASOut_Toggle.value
    settings['ConvertUnits']=CU_Toggle.value
    DAC.SNAPRed(runInput.value,maskName.value,settings)
    red_Status.value = 'Complete - data available on visualisation tab'
    

red_Button.on_click(b)
    
tabs.servable()