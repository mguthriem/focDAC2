# Test development of a Qt4 GUI for SNAPRed 
import utilities.FocDACUtilities as DAC 
import utilities.SNAP_InstPrm as iPrm
import sys 
from qtpy.QtCore import QProcess
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QTableWidgetItem,
    QWidget,
    QFileDialog)
from qtpy.uic import loadUi
import ui


class MainWindow(QMainWindow):

    def __init__(self, parent=None,processing_mode=None):

        QMainWindow.__init__(self, parent)

        self.ui = loadUi('ui/testWindow.ui',baseinstance=self)
        self.ui.runInputStr.editingFinished.connect(self.runStringEntered)
        self.ui.stateStatus.setVisible(False)
        self.ui.stateStatus.horizontalHeader().sectionResized.connect(self.ui.stateStatus.resizeRowsToContents)
        self.ui.errMsg.setVisible(False)
        self.ui.redSetBox.setVisible(False)
        self.ui.executeReduce.setVisible(False)
        self.ui.MskOpenFileButton.clicked.connect(self.getMskFile)
        self.ui.MskOpenFileButton.setVisible(False)
        self.ui.MskLabel.setVisible(False)
        self.ui.MskFileName.setVisible(False)

        self.rPrm = dict()
        self.sPrm = dict()

    def getMskFile(self):
        maskFile = QFileDialog.getOpenFileName(self,caption='Chooose Mask File',
                                    directory=self.rPrm['maskFileLoc'])#.setNameFilter(['msk','Msk'])
        self.ui.MskFileName.setText(maskFile[0])
        print(maskFile[0])


    def runStringEntered(self):
        text = self.ui.runInputStr.text() #get run number from input
        runs=text.strip().split(',')
        #
        #check valididty of state
        #
        stateID,sDict,errorState = DAC.StateFromRunFunction(runs[0]) #only checks state for first run
        if errorState["value"]==0:
            validState = True
            header = self.ui.stateStatus.horizontalHeader()
            # header.setResizeMode(0, GtGui.QHeaderView.Stretch)
            # header.setResizeMode(1, GtGui.QHeaderView.ResizeToContents)
            self.ui.stateStatus.setVisible(True)
            self.ui.errMsg.setVisible(False)
            self.ui.stateStatus.setItem(0,0,QTableWidgetItem('VALID STATE'))
            self.ui.stateStatus.setItem(1,0,QTableWidgetItem('ID'))
            self.ui.stateStatus.setItem(1,1,QTableWidgetItem(stateID))

            for row,key in enumerate(sDict):
                self.ui.stateStatus.setItem(row+2,0,QTableWidgetItem(key))
                self.ui.stateStatus.setItem(row+2,1,QTableWidgetItem(str(sDict[key])))
                lastRowUsed = row+2
        else:
            validState=False
            self.ui.errMsg.setStyleSheet("background-color: red")
            self.ui.stateStatus.setVisible(False)
            self.ui.errMsg.setVisible(True)
            self.ui.errMsg.setText(f'''An error has occurred in Function: {errorState['function']}
            Error: {errorState['value']} message: {errorState['message']}
            ''')
            self.ui.redSetBox.setVisible(False)
            self.ui.executeReduce.setVisible(False)
            self.ui.MskOpenFileButton.setVisible(False)
            self.ui.MskLabel.setVisible(False)
            self.ui.MskFileName.setVisible(False)
        #
        # If state is valid, check calibration status and get state parameters.
        #
        if validState:
            if self.ui.calibCondBefore.isChecked():
                calibState='before'
            else:
                calibState='after'
            # print('calibration state is: ',calibState)
            lite = self.ui.liteMode.isChecked()
            self.rPrm = DAC.initPrm(runs[0],calibState,lite) #initialise run parameters
            self.sPrm,errorState = DAC.getStatePrm(runs[0],self.rPrm)
            if errorState["value"]==0:
                validCalib = True 
                self.ui.stateStatus.setItem(lastRowUsed+1,
                    0,QTableWidgetItem('VALID CALIBRATION'))

                self.ui.stateStatus.setItem(lastRowUsed+2,
                    0,QTableWidgetItem('Calib Info File:')) 
                self.ui.stateStatus.setItem(lastRowUsed+2,
                    1,QTableWidgetItem(self.sPrm['calibInfoFile']))

                self.ui.stateStatus.setItem(lastRowUsed+3,
                    0,QTableWidgetItem('Geom File:')) 
                self.ui.stateStatus.setItem(lastRowUsed+3,
                    1,QTableWidgetItem(self.sPrm['calFileName']))

                self.ui.stateStatus.setItem(lastRowUsed+4,
                    0,QTableWidgetItem('Raw Vanadium File:')) 
                self.ui.stateStatus.setItem(lastRowUsed+4,
                    1,QTableWidgetItem(self.sPrm['rawVCorrFileName']))
            else:
                validCalib = False
                self.ui.errMsg.setStyleSheet("background-color: red")
                self.ui.stateStatus.setVisible(False)
                self.ui.errMsg.setVisible(True)
                self.ui.errMsg.setText(f'''ERROR: State is valid, but uncalibrated
                An error has occurred in Function: {errorState['function']}
                Error: {errorState['value']} message: {errorState['message']}
                Calibrate state to continue!
                ''')
                self.ui.redSetBox.setVisible(False)
                self.ui.executeReduce.setVisible(False)
                self.ui.MskOpenFileButton.setVisible(False)
                self.ui.MskLabel.setVisible(False)
                self.ui.MskFileName.setVisible(False)

        if validState and validCalib:
            self.ui.redSetBox.setVisible(True)
            self.ui.executeReduce.setVisible(True)
            self.ui.MskOpenFileButton.setVisible(True)
            self.ui.MskLabel.setVisible(True)
            self.ui.MskFileName.setVisible(True)
            self.ui.errMsg.setStyleSheet("background-color: green")
            # self.ui.stateStatus.setVisible(False)
            self.ui.errMsg.setVisible(True)
            self.ui.errMsg.setText(f'''State fully calibrated - ready to proceed
            ''')

def main():
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()