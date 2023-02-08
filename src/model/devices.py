import serial
from serial.tools.list_ports import comports
from PyQt5 import QtCore
import time
import os
import numpy as np
import pandas as pd
import cv2


class SerialDeviceSignals(QtCore.QObject):

    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()
    port_found = QtCore.pyqtSignal(list)
    sampled = QtCore.pyqtSignal(bytes)


class SerialReadTask(QtCore.QRunnable):

    def __init__(self, read_func):
        QtCore.QRunnable.__init__(self)
        self.read_func = read_func
        self.__isRunning = False

    def run(self):
        self.__isRunning = True
        while self.__isRunning:
            self.read_func()

    def stop(self):
        self.__isRunning = False


class MicroscopeSignals(QtCore.QObject):

    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()
    sampled = QtCore.pyqtSignal(np.ndarray)


class MicroscopeReadTask(QtCore.QRunnable):

    def __init__(self, read_func):
        QtCore.QRunnable.__init__(self)
        self.read_func = read_func
        self.__isRunning = False

    def run(self):
        self.__isRunning = True
        while self.__isRunning:
            self.read_func()

    def stop(self):
        self.__isRunning = False


class Enose():

    def __init__(self):
        self.threadpool = QtCore.QThreadPool()
        self.serialDevice = serial.Serial()
        self.buffer = bytes()
        self.serialSignals = SerialDeviceSignals()
        self.serialTimer = QtCore.QTimer()
        self.serialTimer.timeout.connect(self.sampleSerial)
        self.serialReadTask = None
        self.serialSampleInterval = None
        self.isSerialRunning = False

        self.microscope = None
        self.microscopeSignals = MicroscopeSignals()
        self.microscopeTimer = QtCore.QTimer()
        self.microscopeTimer.timeout.connect(self.sampleMicroscope)
        self.microscopeReadTask = None
        self.imageBuffer = np.zeros((500, 500))
        self.isMicroscopeRunning = False

    def searchSerial(self):
        portinfos = comports()
        ports = [info.device for info in portinfos]
        self.serialSignals.port_found.emit(ports)

    def openSerial(self, deviceSettings):
        if not self.serialDevice.is_open:
            self.serialDevice.port = deviceSettings["port"]
            self.serialDevice.baudrate = deviceSettings["baudrate"]
            self.serialDevice.open()
            self.serialSignals.connected.emit()

    def closeSerial(self):
        if self.serialDevice.is_open:
            self.stopSerial()
            self.serialDevice.close()
            self.serialSignals.disconnected.emit()

    def readSerial(self):
        if self.serialDevice.is_open:
            self.buffer = self.serialDevice.readline()

    def writeSerial(self, string_data):
        if self.serialDevice.is_open:
            encoded_data = string_data.encode('utf-8')
            print("Data sent", encoded_data)
            self.serialDevice.write(encoded_data)

    def runSerial(self, sample_interval):
        if not self.isSerialRunning:
            self.serialSampleInterval = sample_interval
            self.serialReadTask = SerialReadTask(self.readSerial)
            self.threadpool.start(self.serialReadTask)
            self.serialTimer.start(self.serialSampleInterval * 1000)
            self.isSerialRunning = True

    def sampleSerial(self):
        if self.serialTimer.isActive():
            self.serialSignals.sampled.emit(self.buffer)
            self.serialTimer.start(self.serialSampleInterval * 1000)

    def stopSerial(self):
        self.isSerialRunning = False
        if self.serialReadTask:
            self.serialReadTask.stop()
        if self.serialTimer.isActive():
            self.serialTimer.stop()

    def openMicroscope(self, videoport):
        if not self.microscope:
            self.microscope = cv2.VideoCapture(videoport)
            self.microscopeSignals.connected.emit()

    def closeMicroscope(self):
        if self.microscope:
            self.microscope.release()
            self.microscope = None
            self.microscopeSignals.disconnected.emit()

    def readMicroscope(self):
        if self.microscope:
            ret, frame = self.microscope.read()
            if ret:
                self.imageBuffer = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB)
            else:
                self.imageBuffer = np.zeros((500, 500))

    def runMicroscope(self):
        if not self.isMicroscopeRunning:
            self.microscopeReadTask = MicroscopeReadTask(self.readMicroscope)
            self.threadpool.start(self.microscopeReadTask)
            self.microscopeTimer.start(1)
            self.isMicroscopeRunning = True

    def sampleMicroscope(self):
        if self.microscopeTimer.isActive():
            self.microscopeSignals.sampled.emit(self.imageBuffer)
            self.microscopeTimer.start(1)

    def stopMicroscope(self):
        self.isMicroscopeRunning = False
        if self.microscopeTimer.isActive():
            self.microscopeTimer.stop()
        if self.microscopeReadTask:
            self.microscopeReadTask.stop()


class SinglePoleFilter:

    def __init__(self, cutoff_frequency=0.01):
        x = np.exp(-2*np.pi*cutoff_frequency)
        self.a0 = 1-x
        self.b1 = x
        self.previous_output = 0

    def filter(self, new_sample):
        self.previous_output = self.a0 * new_sample \
            + self.b1 * self.previous_output
        return self.previous_output


class FourStageLowPassFilter:

    def __init__(self, cutoff_frequency=0.01):
        x = np.exp(-14.445 * cutoff_frequency)
        self.a0 = (1-x)**4
        self.b1 = 4 * x
        self.b2 = -6 * x**2
        self.b3 = 4 * x**3
        self.b4 = -1 * x**4
        self.y = np.zeros(5)

    def filter(self, input_sample):
        self.y[0] = self.a0 * input_sample \
            + self.b1 * self.y[1] + self.b2 * self.y[2] \
            + self.b3 * self.y[3] + self.b4 * self.y[4]
        for i in range(4):
            self.y[4-i] = self.y[3-i]
        return self.y[0]


class BufferSignals(QtCore.QObject):

    serial_data_ready = QtCore.pyqtSignal(list)
    microscope_data_ready = QtCore.pyqtSignal(np.ndarray)
    sample_timer_timeout = QtCore.pyqtSignal(int)
    sampling_completed = QtCore.pyqtSignal(tuple)
    baseline_started = QtCore.pyqtSignal()
    adsorption_started = QtCore.pyqtSignal()
    desorption_started = QtCore.pyqtSignal()
    image_captured = QtCore.pyqtSignal(int)


class DataBuffer():

    def __init__(self):
        self.signals = BufferSignals()
        self.float_list_data = list()
        self.number_of_arrays = 0
        self.isArrayCreated = False
        self.timeCount = 0
        self.sampleTimer = QtCore.QTimer()
        self.sampleTimer.timeout.connect(self.sampleTimeoutCallback)
        self.baselineTimer = QtCore.QTimer()
        self.baselineTimer.timeout.connect(self.baselineTimeOutCallback)
        self.adsorptionTimer = QtCore.QTimer()
        self.adsorptionTimer.timeout.connect(self.adsorptionTimeOutCallback)
        self.sampleSettings = dict()
        self.isRecording = False

        self.imageBuffer = None
        self.rectangleTopLeft = tuple()
        self.rectangleBottomRight = tuple()
        self.rectangleCenter = tuple()
        self.isRectangleCreated = False
        self.moveStep = 5
        self.image_buffer_array = list()
        self.imageTimer = QtCore.QTimer()
        self.imageTimer.timeout.connect(self.imageTimerCallback)
        self.rectangleShiftX = 0
        self.rectangleShiftY = 0
        self.rectangleWidth = 400
        self.rectangleHeight = 400
        self.rectangleFrameTopLeft = (50, 50)
        self.rectangleFrameBottomRight = (450, 450)

    def receiveSerialData(self, enconded_bytes_data=None, seperator=","):
        if enconded_bytes_data:
            decoded_list_data = enconded_bytes_data.decode().split(seperator)
            float_list_data = [float(data) for data in decoded_list_data]
            if not self.isArrayCreated:
                if len(float_list_data) != self.number_of_arrays:
                    self.number_of_arrays = len(float_list_data)
                    self.isArrayCreated = False
                else:
                    self.serial_buffer_array = [
                        list() for i in range(len(float_list_data))]
                    self.isArrayCreated = True
            else:
                for data, buffer in zip(float_list_data,
                                        self.serial_buffer_array):
                    buffer.append(data)
                self.signals.serial_data_ready.emit(
                    self.serial_buffer_array)

    def flushSerial(self):
        if self.isArrayCreated:
            self.serial_buffer_array = [list()
                                        for i in range(
                                            self.number_of_arrays)]
        else:
            self.serial_buffer_array = list()

    def startRecording(self, sample_settings):
        if not self.isRecording:
            self.timeCount = 0
            self.flushSerial()
            self.flushVideo()
            self.sampleSettings = sample_settings
            self.isRecording = True
            self.baselineTimer.start(
                1000 * self.sampleSettings["baseline_duration"])
            self.signals.baseline_started.emit()
            self.imageTimerCallback()
            self.sampleTimeoutCallback()
            self.sampleTimer.start(1000)
            self.imageTimer.start(1000 * self.sampleSettings[
                "video_interval"])

    def stopRecording(self):
        if self.isRecording:
            if self.sampleTimer.isActive():
                self.timeCount = 0
                self.sampleTimer.stop()
            if self.baselineTimer.isActive():
                self.baselineTimer.stop()
            if self.adsorptionTimer.isActive():
                self.adsorptionTimer.stop()
            if self.imageTimer.isActive():
                self.imageTimer.stop()
            self.isRecording = False
            self.signals.sampling_completed.emit(
                (self.sampleSettings["sample_name"],
                 self.serial_buffer_array,
                 self.image_buffer_array))

    def sampleTimeoutCallback(self):
        self.signals.sample_timer_timeout.emit(self.timeCount)
        if self.timeCount < self.sampleSettings["sample_duration"]:
            self.timeCount = self.timeCount + 1
        else:
            self.stopRecording()

    def baselineTimeOutCallback(self):
        self.baselineTimer.stop()
        self.signals.adsorption_started.emit()
        self.adsorptionTimer.start(
            self.sampleSettings["adsorption_duration"] * 1000)

    def adsorptionTimeOutCallback(self):
        self.adsorptionTimer.stop()
        self.signals.desorption_started.emit()

    def receiveImageData(self, image):
        rows = image.shape[0]
        columns = image.shape[1]
        rectangleFrameCenter = (
            int(rows/2) + self.rectangleShiftY,
            int(columns/2) + self.rectangleShiftX)
        rectangleFrameTopLeft = (
            rectangleFrameCenter[1] - self.rectangleWidth//2,
            rectangleFrameCenter[0] - self.rectangleHeight//2)
        rectangleFrameBottomRight = (
            rectangleFrameCenter[1] + self.rectangleWidth//2,
            rectangleFrameCenter[0] + self.rectangleHeight//2)

        self.imageBuffer = image.copy()
        self.imageBuffer = self.imageBuffer[
            rectangleFrameTopLeft[1]:rectangleFrameBottomRight[1],
            rectangleFrameTopLeft[0]:rectangleFrameBottomRight[0]]
        cv2.rectangle(image,
                      rectangleFrameTopLeft,
                      rectangleFrameBottomRight,
                      color=(255, 83, 112),
                      thickness=2)

        cropped_reference_img = self.__cropByCentre(
            image, centre=(columns // 4, rows // 4), frame_size=50)
        mean_of_reference = self.__normalizeColorValue(
            self.__mean(cv2.cvtColor(
                cropped_reference_img,
                cv2.COLOR_RGB2HSV)
            ), colorModel="HSV")[2]
        mean_of_reference = int(mean_of_reference*100)
        cv2.putText(image,
                    text="Brightness: " + str(mean_of_reference),
                    org=(30, 30),
                    color=(23, 23, 23),
                    thickness=2,
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.8)
        self.signals.microscope_data_ready.emit(image)

    def __cropByCentre(self, img=None, centre=(0, 0), frame_size=100):
        return img[
            centre[1] - frame_size // 2:centre[1] + frame_size // 2,
            centre[0] - frame_size // 2:centre[0] + frame_size // 2]

    def __mean(self, img=None):
        return cv2.mean(img)[:3]

    def __normalizeColorValue(self, value, colorModel="HSV"):
        if colorModel == "RGB":
            return (value[0]/255, value[1]/255, value[2]/255)
        elif colorModel == "HSV":
            return (value[0]/179, value[1]/255, value[2]/255)
        else:
            return value

    def flushVideo(self):
        self.image_buffer_array = list()

    def imageTimerCallback(self):
        self.image_buffer_array.append(
            self.imageBuffer)
        self.signals.image_captured.emit(self.timeCount)

    def moveRectangleUp(self):
        self.rectangleShiftY -= self.moveStep

    def moveRectangleDown(self):
        self.rectangleShiftY += self.moveStep

    def moveRectangleLeft(self):
        self.rectangleShiftX -= self.moveStep

    def moveRectangleRight(self):
        self.rectangleShiftX += self.moveStep

    def increaseRectangleWidth(self):
        self.rectangleWidth += self.moveStep

    def decreaseRectangleWidth(self):
        self.rectangleWidth -= self.moveStep

    def increaseRectangleHeight(self):
        self.rectangleHeight += self.moveStep

    def decreaseRectangleHeight(self):
        self.rectangleHeight -= self.moveStep


class DataManager():

    CHANNEL_NAMES = ["Channel 1",
                     "Channel 2",
                     "Channel 3",
                     "Channel 4",
                     "Channel 5",
                     "Channel 6",
                     "Channel 7",
                     "Channel 8"]

    def __init__(self):
        self.currentPath = os.getcwd()
        self.datasetName = "datasets"
        self.datasetPath = os.path.join(self.currentPath,
                                        self.datasetName)
        if not os.path.exists(self.datasetPath):
            os.makedirs(self.datasetPath)

    def saveData(self, sample_info):
        sample_name = sample_info[0]
        sample_path = os.path.join(self.datasetPath,
                                   sample_name)
        if not os.path.exists(sample_path):
            os.makedirs(sample_path)
        serial_data = sample_info[1]
        dataset = pd.DataFrame()
        for data, channelName in zip(serial_data,
                                     self.CHANNEL_NAMES):
            dataset[channelName] = data

        with open(os.path.join(sample_path,
                               "serialdata.csv"),
                  'w') as file:
            dataset.to_csv(path_or_buf=file)

        image_folder_name = "images"
        image_folder_path = os.path.join(sample_path,
                                         image_folder_name)
        if not os.path.exists(image_folder_path):
            os.makedirs(image_folder_path)
        images = sample_info[2]
        for i in range(len(images)):
            fileName = os.path.join(image_folder_path,
                                    f"{i+1}" + ".jpg")
            img = cv2.cvtColor(images[i],
                               cv2.COLOR_BGR2RGB)
            cv2.imwrite(fileName, img)


if __name__ == "__main__":
    dm = DataManager()
