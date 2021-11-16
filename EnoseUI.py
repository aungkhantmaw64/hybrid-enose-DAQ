import numpy as np
import cv2
from PyQt5 import QtWidgets, QtCore, QtGui, uic
import pyqtgraph
pyqtgraph.setConfigOptions(imageAxisOrder="row-major")


class UI(QtWidgets.QMainWindow):

    serial_opened = QtCore.pyqtSignal(dict)
    serial_closed = QtCore.pyqtSignal()
    serial_requested = QtCore.pyqtSignal()
    serial_started = QtCore.pyqtSignal(int)
    serial_stopped = QtCore.pyqtSignal()

    video_opened = QtCore.pyqtSignal(int)
    video_closed = QtCore.pyqtSignal()
    video_started = QtCore.pyqtSignal()
    video_stopped = QtCore.pyqtSignal()

    delivery_started = QtCore.pyqtSignal()
    delivery_stopped = QtCore.pyqtSignal()
    sampling_started = QtCore.pyqtSignal(dict)
    sampling_stopped = QtCore.pyqtSignal()

    upped = QtCore.pyqtSignal()
    downed = QtCore.pyqtSignal()
    lefted = QtCore.pyqtSignal()
    righted = QtCore.pyqtSignal()
    width_increased = QtCore.pyqtSignal()
    width_decreased = QtCore.pyqtSignal()
    height_increased = QtCore.pyqtSignal()
    height_decreased = QtCore.pyqtSignal()

    ChannelNames = ["Channel " + str(i+1) for i in range(8)]
    ChannelColors = ["#FF0000",
                     "#FFFF00",
                     "#FF00FF",
                     "#00FF00",
                     "#0000FF",
                     "#00FFFF",
                     "#F56729",
                     "#9979FF"]

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        # widgets
        uic.loadUi("main_window.ui", self)
        self.graphWidget = pyqtgraph.PlotWidget()
        self.imageWidget = pyqtgraph.GraphicsLayoutWidget()
        self.imageViewBox = self.imageWidget.addViewBox(
            row=0, col=0, invertY=True, invertX=False)
        self.imageItem = pyqtgraph.ImageItem()
        self.imageViewBox.addItem(self.imageItem)

        self.graphSettingsOkButton.clicked.connect(
            self.__graphSettingsOkCallback)
        self.graphSettingsResetButton.clicked.connect(
            self.__graphSettingsResetCallback)
        self.serialConnectButton.clicked.connect(
            self.__serialConnectCallback)
        self.serialDisconnectButton.clicked.connect(
            self.__serialDisconnectCallback)
        self.serialRunButton.clicked.connect(self.__serialRunCallback)
        self.serialStopButton.clicked.connect(self.__serialStopCallback)
        self.refreshButton.clicked.connect(self.__refreshCallback)

        self.videoConnectButton.clicked.connect(self.__videoConnectCallback)
        self.videoDisconnectButton.clicked.connect(
            self.__videoDisconnectCallback)
        self.videoRunButton.clicked.connect(self.__videoRunCallback)
        self.videoStopButton.clicked.connect(self.__videoStopCallback)

        self.upButton.clicked.connect(self.__upCallback)
        self.downButton.clicked.connect(self.__downCallback)
        self.leftButton.clicked.connect(self.__leftCallback)
        self.rightButton.clicked.connect(self.__rightCallback)
        self.widthPlusButton.clicked.connect(self.__widthPlusCallback)
        self.widthMinusButton.clicked.connect(self.__widthMinusCallback)
        self.heightPlusButton.clicked.connect(self.__heightPlusCallback)
        self.heightMinusButton.clicked.connect(self.__heightMinusCallback)

        self.deliveryBeginButton.clicked.connect(self.__deliveryBeginCallback)
        self.deliveryStopButton.clicked.connect(self.__deliveryStopCallback)
        self.sampleStartButton.clicked.connect(self.__sampleStartCallback)
        self.sampleStopButton.clicked.connect(self.__sampleStopCallback)
        self.__setupUI()
        self.__graphSettingsOkCallback()

        # variables

    def showData(self, data_array):
        for i in range(len(data_array)):
            self.lines[i].setData(data_array[i])

    def showImage(self, img):
        self.imageItem.setImage(img)

    def setPorts(self, ports):
        self.serialComboBox.clear()
        self.serialComboBox.addItems(ports)

    def setTimerValue(self, value):
        self.timerLCD.display(value)

    def logConnectedSerialDevice(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Serial Device Connected\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)

    def logDisconnectedSerialDevice(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Serial Device Disconnected\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)

    def logConnectedMicroscope(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Microscope Connected\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)

    def logDisconnectedMicroscope(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Microscope Disconnected\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)

    def logImageCaptured(self, timeCount):
        self.logPlainTextEdit.insertPlainText(
            f"(Event) Image Captured at ({timeCount}) seconds\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)

    def logBaselineStartPoint(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Baseline Started\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)

    def logAdsorptionStartPoint(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Adsorption Started\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)

    def logDesorptionStartPoint(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Desorption Started\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)

    def logCompleteSampling(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Sampling Complete\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)

    def __setupUI(self):
        self.setWindowTitle("Hybrid Electronic Nose")
        self.setWindowIcon(QtGui.QIcon(r"icons\\sigma.svg"))
        self.serialLayout.addWidget(self.graphWidget)
        self.microscopeLayout.addWidget(self.imageWidget)
        self.upButton.setIcon(QtGui.QIcon(r"icons\\up.svg"))
        self.leftButton.setIcon(QtGui.QIcon(r"icons\\left.svg"))
        self.rightButton.setIcon(QtGui.QIcon(r"icons\\right.svg"))
        self.downButton.setIcon(QtGui.QIcon(r"icons\\down.svg"))
        self.widthPlusButton.setIcon(QtGui.QIcon(r"icons\\plus.svg"))
        self.widthMinusButton.setIcon(QtGui.QIcon(r"icons\\minus.svg"))
        self.heightPlusButton.setIcon(QtGui.QIcon(r"icons\\plus.svg"))
        self.heightMinusButton.setIcon(QtGui.QIcon(r"icons\\minus.svg"))

        self.videoConnectButton.setIcon(QtGui.QIcon(r"icons\\play.svg"))
        self.videoDisconnectButton.setIcon(QtGui.QIcon(r"icons\\stop.svg"))
        self.videoRunButton.setIcon(QtGui.QIcon(r"icons\\play.svg"))
        self.videoStopButton.setIcon(QtGui.QIcon(r"icons\\stop.svg"))

        self.serialConnectButton.setIcon(QtGui.QIcon(r"icons\\play.svg"))
        self.serialDisconnectButton.setIcon(QtGui.QIcon(r"icons\\stop.svg"))
        self.serialRunButton.setIcon(QtGui.QIcon(r"icons\\play.svg"))
        self.serialStopButton.setIcon(QtGui.QIcon(r"icons\\stop.svg"))

    def __graphSettingsOkCallback(self):
        self.graphWidget.clear()
        self.graphWidget.setTitle(self.titleLineEdit.text())
        self.graphWidget.setLabel("bottom",
                                  self.xLabelLineEdit.text())
        self.graphWidget.setLabel("left",
                                  self.yLabelLineEdit.text())
        self.graphWidget.showGrid(
            x=self.gridCheckBox.isChecked(),
            y=self.gridCheckBox.isChecked(),
            alpha=0.3)
        self.graphWidget.setYRange(0, 5)
        self.graphWidget.addLegend(labelTextColor=(255, 255, 255),
                                   pen=pyqtgraph.mkPen(width=2))
        self.lines = [self.graphWidget.plot([],
                                            name=channelName,
                                            pen=pyqtgraph.mkPen(
                                                color=channelColor))
                      for channelName, channelColor in zip(
                          self.ChannelNames,
                          self.ChannelColors)]

    def __graphSettingsResetCallback(self):
        self.graphWidget.clear()

    def __serialConnectCallback(self):
        if self.serialComboBox.currentText():
            self.serial_opened.emit(
                {"port": self.serialComboBox.currentText(),
                 "baudrate": int(self.baudrateComboBox.currentText())})

    def __serialDisconnectCallback(self):
        self.serial_closed.emit()

    def __serialRunCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Data Transfer Started\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.serial_started.emit(self.serialSamplingIntervalSpinBox.value())

    def __serialStopCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Data Transfer Stopped\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.serial_stopped.emit()

    def __refreshCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Search Available Ports\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.serial_requested.emit()

    def __deliveryBeginCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Delivery Begun\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.delivery_started.emit()

    def __deliveryStopCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Delivery Stop\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.delivery_stopped.emit()

    def __videoConnectCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Connect Microscope\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.video_opened.emit(int(self.videoComboBox.currentText()))

    def __videoDisconnectCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Disconnect Microscope\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.video_closed.emit()

    def __videoRunCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Video Capture Started\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.video_started.emit()

    def __videoStopCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Video Capture Stopped\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.video_stopped.emit()

    def __upCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Move Rectangle Up\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.upped.emit()

    def __downCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Move Rectangle Down\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.downed.emit()

    def __leftCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Move Rectangle Left\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.lefted.emit()

    def __rightCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Move Rectangle Right\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.righted.emit()

    def __widthPlusCallback(self):
        self.width_increased.emit()

    def __widthMinusCallback(self):
        self.width_decreased.emit()

    def __heightPlusCallback(self):
        self.height_increased.emit()

    def __heightMinusCallback(self):
        self.height_decreased.emit()

    def __sampleStartCallback(self):
        if self.sampleNameLineEdit.text():
            self.logPlainTextEdit.insertPlainText(
                "(Event) Sampling Started\n")
            self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
            self.sampling_started.emit({
                "sample_name": self.sampleNameLineEdit.text(),
                "sample_duration": self.sampleDurationSpinBox.value(),
                "baseline_duration": self.baselineSpinBox.value(),
                "adsorption_duration": self.adsorptionSpinBox.value(),
                "video_interval": self.videoSamplingIntevalSpinBox.value()
            })
        else:
            self.logPlainTextEdit.insertPlainText(
                "(Warning) Please Add Sample Name!\n")
            self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)

    def __sampleStopCallback(self):
        self.logPlainTextEdit.insertPlainText(
            "(Event) Sampling Stopped\n")
        self.logPlainTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.sampling_stopped.emit()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    ui = UI()
    data = [np.ones(10),
            2*np.ones(10),
            3*np.ones(10),
            4*np.ones(10),
            5*np.ones(10),
            6*np.ones(10),
            7*np.ones(10),
            8*np.ones(10)]
    ui.showData(data)
    ui.show()
    app.exec_()
