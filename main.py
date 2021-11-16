from PyQt5 import QtWidgets, QtCore, QtGui
import EnoseUI
import EnoseDevices


def initializeDeliverySystem():
    enose.writeSerial(ui.referenceComboBox.currentText() + "\n")


def stopDeliverySystem():
    enose.writeSerial("0\n")


def baslineCallback():
    enose.writeSerial(ui.referenceComboBox.currentText() + "\n")
    ui.logBaselineStartPoint()


def adsorptionCallback():
    enose.writeSerial(ui.odorComboBox.currentText() + "\n")
    ui.logAdsorptionStartPoint()


def desorptionCallback():
    enose.writeSerial(ui.referenceComboBox.currentText() + "\n")
    ui.logDesorptionStartPoint()


app = QtWidgets.QApplication([])
ui = EnoseUI.UI()
enose = EnoseDevices.Enose()
dataBuffer = EnoseDevices.DataBuffer()
dataManager = EnoseDevices.DataManager()

ui.serial_requested.connect(enose.searchSerial)
ui.serial_opened.connect(enose.openSerial)
ui.serial_closed.connect(enose.closeSerial)
ui.serial_started.connect(enose.runSerial)
ui.serial_stopped.connect(enose.stopSerial)
ui.video_opened.connect(enose.openMicroscope)
ui.video_closed.connect(enose.closeMicroscope)
ui.video_started.connect(enose.runMicroscope)
ui.video_stopped.connect(enose.stopMicroscope)

ui.sampling_started.connect(dataBuffer.startRecording)
ui.sampling_stopped.connect(dataBuffer.stopRecording)
ui.delivery_started.connect(initializeDeliverySystem)
ui.delivery_stopped.connect(stopDeliverySystem)

ui.upped.connect(dataBuffer.moveRectangleUp)
ui.downed.connect(dataBuffer.moveRectangleDown)
ui.lefted.connect(dataBuffer.moveRectangleLeft)
ui.righted.connect(dataBuffer.moveRectangleRight)
ui.width_increased.connect(dataBuffer.increaseRectangleWidth)
ui.width_decreased.connect(dataBuffer.decreaseRectangleWidth)
ui.height_increased.connect(dataBuffer.increaseRectangleHeight)
ui.height_decreased.connect(dataBuffer.decreaseRectangleHeight)

enose.serialSignals.port_found.connect(ui.setPorts)
enose.serialSignals.connected.connect(ui.logConnectedSerialDevice)
enose.serialSignals.disconnected.connect(ui.logDisconnectedSerialDevice)
enose.serialSignals.sampled.connect(dataBuffer.receiveSerialData)

enose.microscopeSignals.connected.connect(ui.logConnectedMicroscope)
enose.microscopeSignals.disconnected.connect(ui.logDisconnectedMicroscope)
enose.microscopeSignals.sampled.connect(dataBuffer.receiveImageData)

dataBuffer.signals.serial_data_ready.connect(ui.showData)
dataBuffer.signals.microscope_data_ready.connect(ui.showImage)
dataBuffer.signals.sample_timer_timeout.connect(ui.setTimerValue)
dataBuffer.signals.sampling_completed.connect(dataManager.saveData)
dataBuffer.signals.sampling_completed.connect(ui.logCompleteSampling)
dataBuffer.signals.image_captured.connect(ui.logImageCaptured)
dataBuffer.signals.baseline_started.connect(baslineCallback)
dataBuffer.signals.adsorption_started.connect(adsorptionCallback)
dataBuffer.signals.desorption_started.connect(desorptionCallback)

ui.show()
app.exec_()
dataBuffer.stopRecording()
enose.writeSerial("0\n")
enose.stopSerial()
enose.closeSerial()
enose.stopMicroscope()
enose.closeMicroscope()
