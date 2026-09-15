import os
import cv2
import numpy as np
import time
import sys
import ctypes
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QGridLayout, QFileDialog, QDialog

from utilities import get_info_from_txt, get_landmark_size, imread_unicode
from ProcessLandmarks import GetLandmarks

def safe_path(path):
    if os.name != 'nt':
        return path
    GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    GetShortPathNameW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
    GetShortPathNameW.restype = ctypes.c_uint
    buffer_size = GetShortPathNameW(path, None, 0)
    if buffer_size == 0:
        return path
    buffer = ctypes.create_unicode_buffer(buffer_size)
    GetShortPathNameW(path, buffer, buffer_size)
    return buffer.value

class PhotoObject(object):
    def __init__(self):
        self._photo = None
        self._file_name = None
        self._name = ''
        self._shape = None
        self._lefteye = None
        self._righteye = None
        self._points = None
        self._boundingbox = None
        self._landmark_size = None

class Patient(object):
    def __init__(self):
        self.FirstPhoto = PhotoObject()       
        self.SecondPhoto = PhotoObject()

class CreatePatient(QDialog):
    def __init__(self, parent=None, ModelName='iBUG'):
        super(CreatePatient, self).__init__(parent)
        
        self._Patient = None
        self._ExitFlag = False
        self._ModelName = ModelName
        self.thread_landmarks = QtCore.QThread()
        self._Photo = None
        self._file_name = None
        self._name = None
        self._PhotoPosition = None
        self._Scale = 1
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Выбрать фото пациента')
        if os.name == 'posix':
            scriptDir = os.path.dirname(sys.argv[0])
        else:
            scriptDir = os.getcwd()
        self.setWindowIcon(QtGui.QIcon(safe_path(scriptDir + os.path.sep + 'include' + os.path.sep + 'icon_color' + os.path.sep + 'patient_icon.ico')))
        
        spacerh = QtWidgets.QWidget(self)
        spacerh.setFixedSize(20, 0)
        spacerv = QtWidgets.QWidget(self)
        spacerv.setFixedSize(0, 20)
        
        self._Patient = Patient()
        
        FirstPhoto_label = QLabel('Первое фото:')
        self._loadFirstPhoto = QPushButton('Загрузить файл', self)
        self._loadFirstPhoto.setFixedWidth(150)
        self._loadFirstPhoto.clicked.connect(lambda: self.LoadImage('first'))
        FirstPhoto_name_label = QLabel('Имя файла:')
        self._FirstPhoto_name = QLineEdit(self)
        self._FirstPhoto_name.setReadOnly(True)
        
        SecondPhoto_label = QLabel('Второе фото:')
        self._loadSecondPhoto = QPushButton('Загрузить файл', self)
        self._loadSecondPhoto.setFixedWidth(150)
        self._loadSecondPhoto.clicked.connect(lambda: self.LoadImage('second'))
        SecondPhoto_name_label = QLabel('Имя файла:')
        self._SecondPhoto_name = QLineEdit(self)
        self._SecondPhoto_name.setReadOnly(True)
        
        DoneButton = QPushButton('&Готово', self)
        DoneButton.setFixedWidth(150)
        DoneButton.clicked.connect(self.Done)
        CancelButton = QPushButton('&Отмена', self)
        CancelButton.setFixedWidth(150)
        CancelButton.clicked.connect(self.Cancel)
        
        layout = QGridLayout()
        layout.addWidget(spacerh, 0, 1)
        layout.addWidget(FirstPhoto_label, 1, 1, 1, 1)
        layout.addWidget(self._loadFirstPhoto, 1, 3, 1, 1)
        layout.addWidget(FirstPhoto_name_label, 2, 1, 1, 1)
        layout.addWidget(self._FirstPhoto_name, 2, 3, 1, 1)
        
        layout.addWidget(spacerv, 3, 0)
        
        layout.addWidget(SecondPhoto_label, 4, 1, 1, 1)
        layout.addWidget(self._loadSecondPhoto, 4, 3, 1, 1)
        layout.addWidget(SecondPhoto_name_label, 5, 1, 1, 1)
        layout.addWidget(self._SecondPhoto_name, 5, 3, 1, 1)
        
        layout.addWidget(spacerv, 6, 0)
        layout.addWidget(DoneButton, 7, 3, 1, 1)
        layout.addWidget(CancelButton, 7, 5, 1, 1)
        
        self.setLayout(layout)
    
    def Cancel(self):
        self._ExitFlag = False
        self.close()
    
    def Done(self):
        if (self._Patient.FirstPhoto is None) or (self._Patient.SecondPhoto is None):
            QtWidgets.QMessageBox.warning(self, "Ошибка", 'Необходимо загрузить два фото')
            return
        if self._Patient.FirstPhoto._shape is None or self._Patient.SecondPhoto._shape is None:
            QtWidgets.QMessageBox.warning(self, "Ошибка", 'Одно из фото не содержит лица или загружено некорректно')
            return
        
        self._ExitFlag = True
        self.close()
    
    def closeEvent(self, event):
        if self._ExitFlag is False:
            self._Patient = None
        event.accept()
    
    def LoadImage(self, position):
        name, _ = QFileDialog.getOpenFileName(
            self, 'Загрузить изображение',
            '', "Image files (*.png *.jpg *.jpeg *.tif *.tiff *.PNG *.JPG *.JPEG *.TIF *.TIFF)")
        if not name:
            return
        name = os.path.normpath(name)
        self._Photo = imread_unicode(name)   # замена cv2.imread
        if self._Photo is None:
            QtWidgets.QMessageBox.warning(self, "Ошибка загрузки",
                "Не удалось прочитать файл. Возможно, путь содержит недопустимые символы.\n")
            return
        self._PhotoPosition = position
        delimiter = os.path.sep
        split_name = name.split(delimiter)
        self._file_name = name
        self._name = split_name[-1]
        
        file_txt = name[:-4] + '.txt'
        if os.path.isfile(file_txt):
            shape, lefteye, righteye, boundingbox = get_info_from_txt(safe_path(file_txt))
            temp_photo = PhotoObject()
            temp_photo._file_name = self._file_name
            temp_photo._name = self._name
            temp_photo._photo = self._Photo
            temp_photo._lefteye = lefteye
            temp_photo._righteye = righteye
            temp_photo._boundingbox = boundingbox
            temp_photo._shape = shape
            temp_photo._points = None
            temp_photo._landmark_size = get_landmark_size(shape)
            self.AssignPhoto(temp_photo, self._PhotoPosition, 1)
        else:
            h, w, d = self._Photo.shape
            self._Scale = 1
            if h > 1500 or w > 1500:
                if h >= w:
                    h_n = 1500
                    self._Scale = h / h_n
                    w_n = int(np.round(w / self._Scale, 0))
                    temp_image = cv2.resize(self._Photo, (w_n, h_n), interpolation=cv2.INTER_AREA)
                else:
                    w_n = 1500
                    self._Scale = w / w_n
                    h_n = int(np.round(h / self._Scale, 0))
                    temp_image = cv2.resize(self._Photo, (w_n, h_n), interpolation=cv2.INTER_AREA)
            else:
                temp_image = self._Photo.copy()
            
            self.landmarks = GetLandmarks(temp_image, self._ModelName)
            self.landmarks.moveToThread(self.thread_landmarks)
            self.thread_landmarks.start()
            self.thread_landmarks.started.connect(self.landmarks.getlandmarks)
            self.landmarks.landmarks.connect(self.ProcessShape)
            self.landmarks.finished.connect(self.thread_landmarks.quit)
    
    def ProcessShape(self, shape, numFaces, lefteye, righteye, boundingbox):
        temp_photo = PhotoObject()
        if numFaces == 1:
            if self._Scale != 1:
                for k in range(0, 68):
                    shape[k] = [int(np.round(shape[k, 0] * self._Scale, 0)),
                                int(np.round(shape[k, 1] * self._Scale, 0))]
                for k in range(0, 3):
                    lefteye[k] = int(np.round(lefteye[k] * self._Scale, 0))
                    righteye[k] = int(np.round(righteye[k] * self._Scale, 0))
                for k in range(0, 4):
                    boundingbox[k] = int(np.round(boundingbox[k] * self._Scale, 0))
            
            temp_photo._file_name = self._file_name
            temp_photo._name = self._name
            temp_photo._photo = self._Photo
            temp_photo._shape = shape
            temp_photo._lefteye = lefteye
            temp_photo._righteye = righteye
            temp_photo._boundingbox = boundingbox
            temp_photo._points = None
            temp_photo._landmark_size = get_landmark_size(shape)
            self.AssignPhoto(temp_photo, self._PhotoPosition, numFaces)
        else:
            self.AssignPhoto(temp_photo, self._PhotoPosition, numFaces)
    
    def AssignPhoto(self, photo_info, position, numFaces):
        if position == 'first':
            setattr(self._Patient, 'FirstPhoto', photo_info)
            if self._Patient.FirstPhoto._shape is not None:
                self._FirstPhoto_name.setText(photo_info._name)
            else:
                self._FirstPhoto_name.setText('Неверный файл')
                if numFaces == 0:
                    QtWidgets.QMessageBox.warning(self, "Предупреждение",
                        "На изображении нет лица.\nЕсли лицо есть, попробуйте изменить яркость.",
                        QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)
                elif numFaces > 1:
                    QtWidgets.QMessageBox.warning(self, "Предупреждение",
                        "На изображении несколько лиц.\nЗагрузите фото с одним лицом.",
                        QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)
        elif position == 'second':
            setattr(self._Patient, 'SecondPhoto', photo_info)
            if self._Patient.SecondPhoto._shape is not None:
                self._SecondPhoto_name.setText(photo_info._name)
            else:
                self._SecondPhoto_name.setText('Неверный файл')
                if numFaces == 0:
                    QtWidgets.QMessageBox.warning(self, "Предупреждение",
                        "На изображении нет лица.\nЕсли лицо есть, попробуйте изменить яркость.",
                        QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)
                elif numFaces > 1:
                    QtWidgets.QMessageBox.warning(self, "Предупреждение",
                        "На изображении несколько лиц.\nЗагрузите фото с одним лицом.",
                        QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    GUI = CreatePatient()
    app.exec_()
