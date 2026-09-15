import os 
import sys
import cv2
import numpy as np
import ctypes
import ctypes.wintypes

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from results_window import ShowResults
from results_window import CustomTabResult

from ImageViewerandProcess import ImageViewer
from patient_window import CreatePatient

from measurements import get_measurements_from_data

from utilities import estimate_lines
from utilities import get_info_from_txt
from utilities import mark_picture
from utilities import save_snaptshot_to_file
from utilities import save_txt_file
from utilities import get_landmark_size

from ProcessLandmarks import GetLandmarks

from save_window import SaveWindow, SavePatientWindow
from settings_window import ShowSettings
from utilities import (estimate_lines, get_info_from_txt, mark_picture,
                       save_snaptshot_to_file, save_txt_file, get_landmark_size,
                       imread_unicode, imwrite_unicode)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

class window(QtWidgets.QWidget):
    
    def __init__(self):
        super(window, self).__init__()
        
        self.setWindowTitle('Emotrics')    
        
        if os.name == 'posix': # macOS или Linux
            scriptDir = os.path.dirname(sys.argv[0])
        else: # Windows
            scriptDir = os.getcwd()

        self.setWindowIcon(QtGui.QIcon(safe_path(scriptDir + os.path.sep + 'include' + os.path.sep + 'icon_color' + os.path.sep + 'meei_3WR_icon.ico')))
        
        self._new_window = None
        self._file_name = None
        self._Patient = None
        self._tab1_results = None
        self._tab2_results = None         
        self._tab3_results = None    
        self._toggle_landmaks = True
        self._toggle_lines = True
        
        self._whichPhotofromPatient = None
        
        self._Scale = 1
        
        self.thread_landmarks = QtCore.QThread()
        
        self.threadFirstPhoto = QtCore.QThread()
        self.threadSecondPhoto = QtCore.QThread()
        
        self._CalibrationType = 'Iris'
        self._CalibrationValue = 11.77
        
        self._ModelName = 'MEE'
        
        self.initUI()
        
    def initUI(self):
        if os.name == 'posix':
            scriptDir = os.path.dirname(sys.argv[0])
        else:
            scriptDir = os.getcwd()
        
        img_Qt = QtGui.QImage(resource_path(os.path.join('include', 'icon_color', 'background.jpg')))
        img_show = QtGui.QPixmap.fromImage(img_Qt)
        
        self.displayImage = ImageViewer()      
        self.displayImage.setPhoto(img_show) 

        loadAction = QtWidgets.QAction('Загрузить изображение', self)
        loadAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'load_icon.png'))))
        loadAction.triggered.connect(self.load_file)
        
        createPatientAction = QtWidgets.QAction('Выбрать фотографии пациента', self)
        createPatientAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'patient_icon.png'))))
        createPatientAction.triggered.connect(self.CreatePatient)
        
        self.changephotoAction = QtWidgets.QAction('Сменить фото', self)
        self.changephotoAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'change_photo_icon.png'))))
        self.changephotoAction.setEnabled(False)
        self.changephotoAction.triggered.connect(self.ChangePhoto)
        
        fitAction = QtWidgets.QAction('Подогнать под окно', self)
        fitAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'fit_to_size_icon.png'))))
        fitAction.triggered.connect(self.displayImage.show_entire_image)
        
        eyeAction = QtWidgets.QAction('Выровнять диаметр радужки', self)
        eyeAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'eye_icon.png'))))
        eyeAction.triggered.connect(self.match_iris)
        
        centerAction = QtWidgets.QAction('Найти центр лица', self)
        centerAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'center_icon.png'))))
        centerAction.triggered.connect(self.face_center)
        
        toggleAction = QtWidgets.QAction('Показать/скрыть ориентиры', self)
        toggleAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'toggle-icon.png'))))
        toggleAction.triggered.connect(self.toggle_landmarks)
        
        measuresAction = QtWidgets.QAction('Лицевые метрики', self)
        measuresAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'ruler_icon.png'))))
        measuresAction.triggered.connect(self.create_new_window)
        
        saveAction = QtWidgets.QAction('Сохранить результаты', self)
        saveAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'save_icon.png'))))
        saveAction.triggered.connect(self.save_results)
        
        snapshotAction = QtWidgets.QAction('Сохранить разметку лица', self)
        snapshotAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'snapshot_icon.png'))))
        snapshotAction.triggered.connect(self.save_snapshot)
        
        settingsAction = QtWidgets.QAction('Настройки', self)
        settingsAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'settings-icon.png'))))
        settingsAction.triggered.connect(self.settings)
        
        AboutAction = QtWidgets.QAction('О программе', self)
        AboutAction.setIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'question_icon.png'))))
        AboutAction.triggered.connect(self.about_app)
        
        self.toolBar = QtWidgets.QToolBar(self)
        self.toolBar.addActions((loadAction, createPatientAction, self.changephotoAction, 
                                 fitAction, eyeAction, centerAction, toggleAction,
                                 measuresAction, snapshotAction, saveAction, settingsAction, 
                                 AboutAction))
        
        self.toolBar.setIconSize(QtCore.QSize(50,50))
        
        for action in self.toolBar.actions():
            widget = self.toolBar.widgetForAction(action)
            widget.setFixedSize(50, 50)
           
        self.toolBar.setMinimumSize(self.toolBar.sizeHint())
        self.toolBar.setStyleSheet('QToolBar{spacing:5px;}')
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolBar)
        layout.addWidget(self.displayImage)
        self.setLayout(layout)
        
        self.show()
        
    def CreatePatient(self):
        if self._new_window is not None:
            self._new_window.close()
            
        temp = CreatePatient(self, self._ModelName)
        temp.exec_()
        
        if temp._Patient is not None:
            self._Patient = temp._Patient 
            self.changephotoAction.setEnabled(True)
            
            self._file_name = self._Patient.FirstPhoto._file_name
            self.displayImage._opencvimage = self._Patient.FirstPhoto._photo
            self.displayImage._lefteye = self._Patient.FirstPhoto._lefteye 
            self.displayImage._righteye = self._Patient.FirstPhoto._righteye
            self.displayImage._shape = self._Patient.FirstPhoto._shape
            self.displayImage._points = self._Patient.FirstPhoto._points
            self.displayImage._boundingbox = self._Patient.FirstPhoto._boundingbox
            if self.displayImage._landmark_size is None:
                self.displayImage._landmark_size = get_landmark_size(self.displayImage._shape)
            
            self.displayImage.update_view()
            self.setWindowTitle('Emotrics - ' + self._file_name.split(os.path.sep)[-1])
        
    def ChangePhoto(self):
        self._toggle_lines = True
        if self._file_name == self._Patient.FirstPhoto._file_name:
            self._Patient.FirstPhoto._lefteye = self.displayImage._lefteye
            self._Patient.FirstPhoto._righteye = self.displayImage._righteye
            self._Patient.FirstPhoto._shape = self.displayImage._shape
            self._Patient.FirstPhoto._points = self.displayImage._points
            
            self._file_name = self._Patient.SecondPhoto._file_name
            self.displayImage._opencvimage = self._Patient.SecondPhoto._photo
            self.displayImage._lefteye = self._Patient.SecondPhoto._lefteye 
            self.displayImage._righteye = self._Patient.SecondPhoto._righteye
            self.displayImage._shape = self._Patient.SecondPhoto._shape
            self.displayImage._points = self._Patient.SecondPhoto._points
            self.displayImage._boundingbox = self._Patient.SecondPhoto._boundingbox
            if self.displayImage._landmark_size is None:
                self.displayImage._landmark_size = get_landmark_size(self.displayImage._shape)
            
        elif self._file_name == self._Patient.SecondPhoto._file_name:
            self._Patient.SecondPhoto._lefteye = self.displayImage._lefteye
            self._Patient.SecondPhoto._righteye = self.displayImage._righteye
            self._Patient.SecondPhoto._shape = self.displayImage._shape
            self._Patient.SecondPhoto._points = self.displayImage._points
            
            self._file_name = self._Patient.FirstPhoto._file_name
            self.displayImage._opencvimage = self._Patient.FirstPhoto._photo
            self.displayImage._lefteye = self._Patient.FirstPhoto._lefteye 
            self.displayImage._righteye = self._Patient.FirstPhoto._righteye
            self.displayImage._shape = self._Patient.FirstPhoto._shape
            self.displayImage._points = self._Patient.FirstPhoto._points
            self.displayImage._boundingbox = self._Patient.FirstPhoto._boundingbox
            if self.displayImage._landmark_size is None:
                self.displayImage._landmark_size = get_landmark_size(self.displayImage._shape)
      
        self.displayImage.update_view()
        self.setWindowTitle('Emotrics - ' + self._file_name.split(os.path.sep)[-1])
        
    def create_new_window(self):
        if self._Patient is None:
            if self.displayImage._shape is not None:
                if self._new_window is not None:
                    self._new_window.close()
                    self._new_window = None
                
                MeasurementsLeft, MeasurementsRight, MeasurementsDeviation, MeasurementsPercentual = get_measurements_from_data(
                    self.displayImage._shape, self.displayImage._lefteye, self.displayImage._righteye, 
                    self._CalibrationType, self._CalibrationValue)
                
                self._tab1_results = CustomTabResult()
                
                self._tab1_results._CE_right.setText('{0:.2f}'.format(MeasurementsRight.CommissureExcursion))
                self._tab1_results._SA_right.setText('{0:.2f}'.format(MeasurementsRight.SmileAngle))
                self._tab1_results._DS_right.setText('{0:.2f}'.format(MeasurementsRight.DentalShow))
                self._tab1_results._MRD1_right.setText('{0:.2f}'.format(MeasurementsRight.MarginalReflexDistance1))
                self._tab1_results._MRD2_right.setText('{0:.2f}'.format(MeasurementsRight.MarginalReflexDistance2))
                self._tab1_results._BH_right.setText('{0:.2f}'.format(MeasurementsRight.BrowHeight))
                self._tab1_results._PFH_right.setText('{0:.2f}'.format(MeasurementsRight.PalpebralFissureHeight))
                
                self._tab1_results._CE_left.setText('{0:.2f}'.format(MeasurementsLeft.CommissureExcursion))
                self._tab1_results._SA_left.setText('{0:.2f}'.format(MeasurementsLeft.SmileAngle))
                self._tab1_results._DS_left.setText('{0:.2f}'.format(MeasurementsLeft.DentalShow))
                self._tab1_results._MRD1_left.setText('{0:.2f}'.format(MeasurementsLeft.MarginalReflexDistance1))
                self._tab1_results._MRD2_left.setText('{0:.2f}'.format(MeasurementsLeft.MarginalReflexDistance2))
                self._tab1_results._BH_left.setText('{0:.2f}'.format(MeasurementsLeft.BrowHeight))
                self._tab1_results._PFH_left.setText('{0:.2f}'.format(MeasurementsLeft.PalpebralFissureHeight))
                
                self._tab1_results._CE_dev.setText('{0:.2f}'.format(MeasurementsDeviation.CommissureExcursion))
                self._tab1_results._SA_dev.setText('{0:.2f}'.format(MeasurementsDeviation.SmileAngle))
                self._tab1_results._MRD1_dev.setText('{0:.2f}'.format(MeasurementsDeviation.MarginalReflexDistance1))
                self._tab1_results._MRD2_dev.setText('{0:.2f}'.format(MeasurementsDeviation.MarginalReflexDistance2))
                self._tab1_results._BH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.BrowHeight))
                self._tab1_results._DS_dev.setText('{0:.2f}'.format(MeasurementsDeviation.DentalShow))
                self._tab1_results._CH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.CommisureHeightDeviation))
                self._tab1_results._UVH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.UpperLipHeightDeviation))
                self._tab1_results._LVH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.LowerLipHeightDeviation))
                self._tab1_results._PFH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.PalpebralFissureHeight))
                
                self._tab1_results._CE_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.CommissureExcursion))
                self._tab1_results._SA_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.SmileAngle))
                self._tab1_results._MRD1_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.MarginalReflexDistance1))
                self._tab1_results._MRD2_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.MarginalReflexDistance2))
                self._tab1_results._BH_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.BrowHeight))
                self._tab1_results._DS_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.DentalShow))
                self._tab1_results._PFH_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.PalpebralFissureHeight))

                delimiter = os.path.sep
                temp = self._file_name.split(delimiter)
                photo_name = temp[-1]
                photo_name = os.path.splitext(photo_name)[0]
                self._tab1_results._tab_name = photo_name
                
                self._new_window = ShowResults(self._tab1_results)
                self._new_window.show()
        else:
            if (self._Patient.FirstPhoto._shape is not None) and (self._Patient.SecondPhoto._shape is not None):
                if self._new_window is not None:
                    self._new_window.close()
                    self._new_window = None
                    
                if self._file_name == self._Patient.FirstPhoto._file_name:
                    self._Patient.FirstPhoto._lefteye = self.displayImage._lefteye
                    self._Patient.FirstPhoto._righteye = self.displayImage._righteye
                    self._Patient.FirstPhoto._shape = self.displayImage._shape
                    self._Patient.FirstPhoto._points = self.displayImage._points
                elif self._file_name == self._Patient.SecondPhoto._file_name:
                    self._Patient.SecondPhoto._lefteye = self.displayImage._lefteye
                    self._Patient.SecondPhoto._righteye = self.displayImage._righteye
                    self._Patient.SecondPhoto._shape = self.displayImage._shape
                    self._Patient.SecondPhoto._points = self.displayImage._points

                MeasurementsLeftFirst, MeasurementsRightFirst, MeasurementsDeviation, MeasurementsPercentual = get_measurements_from_data(
                    self._Patient.FirstPhoto._shape, self._Patient.FirstPhoto._lefteye, self._Patient.FirstPhoto._righteye,
                    self._CalibrationType, self._CalibrationValue)
                
                self._tab1_results = CustomTabResult()
                self._tab1_results._CE_right.setText('{0:.2f}'.format(MeasurementsRightFirst.CommissureExcursion))
                self._tab1_results._SA_right.setText('{0:.2f}'.format(MeasurementsRightFirst.SmileAngle))
                self._tab1_results._DS_right.setText('{0:.2f}'.format(MeasurementsRightFirst.DentalShow))
                self._tab1_results._MRD1_right.setText('{0:.2f}'.format(MeasurementsRightFirst.MarginalReflexDistance1))
                self._tab1_results._MRD2_right.setText('{0:.2f}'.format(MeasurementsRightFirst.MarginalReflexDistance2))
                self._tab1_results._BH_right.setText('{0:.2f}'.format(MeasurementsRightFirst.BrowHeight))
                self._tab1_results._PFH_right.setText('{0:.2f}'.format(MeasurementsRightFirst.PalpebralFissureHeight))
                self._tab1_results._CE_left.setText('{0:.2f}'.format(MeasurementsLeftFirst.CommissureExcursion))
                self._tab1_results._SA_left.setText('{0:.2f}'.format(MeasurementsLeftFirst.SmileAngle))
                self._tab1_results._DS_left.setText('{0:.2f}'.format(MeasurementsLeftFirst.DentalShow))
                self._tab1_results._MRD1_left.setText('{0:.2f}'.format(MeasurementsLeftFirst.MarginalReflexDistance1))
                self._tab1_results._MRD2_left.setText('{0:.2f}'.format(MeasurementsLeftFirst.MarginalReflexDistance2))
                self._tab1_results._BH_left.setText('{0:.2f}'.format(MeasurementsLeftFirst.BrowHeight))
                self._tab1_results._PFH_left.setText('{0:.2f}'.format(MeasurementsLeftFirst.PalpebralFissureHeight))
                self._tab1_results._CE_dev.setText('{0:.2f}'.format(MeasurementsDeviation.CommissureExcursion))
                self._tab1_results._SA_dev.setText('{0:.2f}'.format(MeasurementsDeviation.SmileAngle))
                self._tab1_results._MRD1_dev.setText('{0:.2f}'.format(MeasurementsDeviation.MarginalReflexDistance1))
                self._tab1_results._MRD2_dev.setText('{0:.2f}'.format(MeasurementsDeviation.MarginalReflexDistance2))
                self._tab1_results._BH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.BrowHeight))
                self._tab1_results._DS_dev.setText('{0:.2f}'.format(MeasurementsDeviation.DentalShow))
                self._tab1_results._CH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.CommisureHeightDeviation))
                self._tab1_results._UVH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.UpperLipHeightDeviation))
                self._tab1_results._LVH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.LowerLipHeightDeviation))
                self._tab1_results._PFH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.PalpebralFissureHeight))
                self._tab1_results._CE_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.CommissureExcursion))
                self._tab1_results._SA_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.SmileAngle))
                self._tab1_results._MRD1_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.MarginalReflexDistance1))
                self._tab1_results._MRD2_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.MarginalReflexDistance2))
                self._tab1_results._BH_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.BrowHeight))
                self._tab1_results._DS_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.DentalShow))
                self._tab1_results._PFH_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.PalpebralFissureHeight))

                MeasurementsLeftSecond, MeasurementsRightSecond, MeasurementsDeviation, MeasurementsPercentual = get_measurements_from_data(
                    self._Patient.SecondPhoto._shape, self._Patient.SecondPhoto._lefteye, self._Patient.SecondPhoto._righteye,
                    self._CalibrationType, self._CalibrationValue)
                
                self._tab2_results = CustomTabResult()
                self._tab2_results._CE_right.setText('{0:.2f}'.format(MeasurementsRightSecond.CommissureExcursion))
                self._tab2_results._SA_right.setText('{0:.2f}'.format(MeasurementsRightSecond.SmileAngle))
                self._tab2_results._DS_right.setText('{0:.2f}'.format(MeasurementsRightSecond.DentalShow))
                self._tab2_results._MRD1_right.setText('{0:.2f}'.format(MeasurementsRightSecond.MarginalReflexDistance1))
                self._tab2_results._MRD2_right.setText('{0:.2f}'.format(MeasurementsRightSecond.MarginalReflexDistance2))
                self._tab2_results._BH_right.setText('{0:.2f}'.format(MeasurementsRightSecond.BrowHeight))
                self._tab2_results._PFH_right.setText('{0:.2f}'.format(MeasurementsRightSecond.PalpebralFissureHeight))
                self._tab2_results._CE_left.setText('{0:.2f}'.format(MeasurementsLeftSecond.CommissureExcursion))
                self._tab2_results._SA_left.setText('{0:.2f}'.format(MeasurementsLeftSecond.SmileAngle))
                self._tab2_results._DS_left.setText('{0:.2f}'.format(MeasurementsLeftSecond.DentalShow))
                self._tab2_results._MRD1_left.setText('{0:.2f}'.format(MeasurementsLeftSecond.MarginalReflexDistance1))
                self._tab2_results._MRD2_left.setText('{0:.2f}'.format(MeasurementsLeftSecond.MarginalReflexDistance2))
                self._tab2_results._BH_left.setText('{0:.2f}'.format(MeasurementsLeftSecond.BrowHeight))
                self._tab2_results._PFH_left.setText('{0:.2f}'.format(MeasurementsLeftSecond.PalpebralFissureHeight))
                self._tab2_results._CE_dev.setText('{0:.2f}'.format(MeasurementsDeviation.CommissureExcursion))
                self._tab2_results._SA_dev.setText('{0:.2f}'.format(MeasurementsDeviation.SmileAngle))
                self._tab2_results._MRD1_dev.setText('{0:.2f}'.format(MeasurementsDeviation.MarginalReflexDistance1))
                self._tab2_results._MRD2_dev.setText('{0:.2f}'.format(MeasurementsDeviation.MarginalReflexDistance2))
                self._tab2_results._BH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.BrowHeight))
                self._tab2_results._DS_dev.setText('{0:.2f}'.format(MeasurementsDeviation.DentalShow))
                self._tab2_results._CH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.CommisureHeightDeviation))
                self._tab2_results._UVH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.UpperLipHeightDeviation))
                self._tab2_results._LVH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.LowerLipHeightDeviation))
                self._tab2_results._PFH_dev.setText('{0:.2f}'.format(MeasurementsDeviation.PalpebralFissureHeight))
                self._tab2_results._CE_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.CommissureExcursion))
                self._tab2_results._SA_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.SmileAngle))
                self._tab2_results._MRD1_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.MarginalReflexDistance1))
                self._tab2_results._MRD2_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.MarginalReflexDistance2))
                self._tab2_results._BH_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.BrowHeight))
                self._tab2_results._DS_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.DentalShow))
                self._tab2_results._PFH_dev_p.setText('{0:.2f}'.format(MeasurementsPercentual.PalpebralFissureHeight))

                self._tab3_results = CustomTabResult()
                self._tab3_results._CE_right.setText('{0:.2f}'.format(-MeasurementsRightFirst.CommissureExcursion + MeasurementsRightSecond.CommissureExcursion))
                self._tab3_results._SA_right.setText('{0:.2f}'.format(-MeasurementsRightFirst.SmileAngle + MeasurementsRightSecond.SmileAngle))
                self._tab3_results._DS_right.setText('{0:.2f}'.format(-MeasurementsRightFirst.DentalShow + MeasurementsRightSecond.DentalShow))
                self._tab3_results._MRD1_right.setText('{0:.2f}'.format(-MeasurementsRightFirst.MarginalReflexDistance1 + MeasurementsRightSecond.MarginalReflexDistance1))
                self._tab3_results._MRD2_right.setText('{0:.2f}'.format(-MeasurementsRightFirst.MarginalReflexDistance2 + MeasurementsRightSecond.MarginalReflexDistance2))
                self._tab3_results._BH_right.setText('{0:.2f}'.format(-MeasurementsRightFirst.BrowHeight + MeasurementsRightSecond.BrowHeight))
                self._tab3_results._PFH_right.setText('{0:.2f}'.format(-MeasurementsRightFirst.PalpebralFissureHeight + MeasurementsRightSecond.PalpebralFissureHeight))
                self._tab3_results._CE_left.setText('{0:.2f}'.format(-MeasurementsLeftFirst.CommissureExcursion + MeasurementsLeftSecond.CommissureExcursion))
                self._tab3_results._SA_left.setText('{0:.2f}'.format(-MeasurementsLeftFirst.SmileAngle + MeasurementsLeftSecond.SmileAngle))
                self._tab3_results._DS_left.setText('{0:.2f}'.format(-MeasurementsLeftFirst.DentalShow + MeasurementsLeftSecond.DentalShow))
                self._tab3_results._MRD1_left.setText('{0:.2f}'.format(-MeasurementsLeftFirst.MarginalReflexDistance1 + MeasurementsLeftSecond.MarginalReflexDistance1))
                self._tab3_results._MRD2_left.setText('{0:.2f}'.format(-MeasurementsLeftFirst.MarginalReflexDistance2 + MeasurementsLeftSecond.MarginalReflexDistance2))
                self._tab3_results._BH_left.setText('{0:.2f}'.format(-MeasurementsLeftFirst.BrowHeight + MeasurementsLeftSecond.BrowHeight))
                self._tab3_results._PFH_left.setText('{0:.2f}'.format(-MeasurementsLeftFirst.PalpebralFissureHeight + MeasurementsLeftSecond.PalpebralFissureHeight))

                name1 = os.path.splitext(self._Patient.FirstPhoto._name)[0]
                name2 = os.path.splitext(self._Patient.SecondPhoto._name)[0]
                self._tab1_results._tab_name = name1
                self._tab2_results._tab_name = name2)
                
                self._new_window = ShowResults(self._tab1_results, self._tab2_results, self._tab3_results)
                self._new_window.show()
        
    def match_iris(self):
        if self.displayImage._lefteye is not None:
            if self.displayImage._lefteye[2] < self.displayImage._righteye[2]:
                self.displayImage._lefteye[2] = self.displayImage._righteye[2]
            elif self.displayImage._lefteye[2] > self.displayImage._righteye[2]:
                self.displayImage._righteye[2] = self.displayImage._lefteye[2]
            
            self._toggle_lines = True 
            self.displayImage._points = None
            self.displayImage.set_update_photo()  
        
    def face_center(self):
        if self.displayImage._shape is not None:
            if self._toggle_lines == True:
                self._toggle_lines = False
                points = estimate_lines(self.displayImage._opencvimage, 
                                        self.displayImage._lefteye, 
                                        self.displayImage._righteye)
                self.displayImage._points = points
                self.displayImage.set_update_photo()
            else:
                self.displayImage._points = None
                self.displayImage.set_update_photo()
                self._toggle_lines = True    
            
    def load_file(self):
        name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Загрузить изображение',
            '', "Image files (*.png *.jpg *.jpeg *.tif *.tiff *.PNG *.JPG *.JPEG *.TIF *.TIFF)")
        
        if not name:
            return
        else:
            self._Patient = None
            self.changephotoAction.setEnabled(False)
            
            name = os.path.normpath(name)
            self._file_name = name
            if self._new_window is not None:
                self._new_window.close()

            safe_name = safe_path(name)
            self.displayImage._opencvimage = imread_unicode(name)
            if self.displayImage._opencvimage is None:
                QtWidgets.QMessageBox.warning(self, "Ошибка загрузки", "Не удалось прочитать файл.")
                return
            if self.displayImage._opencvimage is None:
                QtWidgets.QMessageBox.warning(self, "Ошибка загрузки",
                    "Не удалось прочитать файл.\nВозможные причины:\n"
                    "- Файл повреждён\n- Путь содержит недопустимые символы\n"
                    "- Недостаточно прав доступа\n\n")
                return

            file_txt = name[:-4] + '.txt'
            if os.path.isfile(file_txt):
                shape, lefteye, righteye, boundingbox = get_info_from_txt(safe_path(file_txt))
                self.displayImage._lefteye = lefteye
                self.displayImage._righteye = righteye 
                self.displayImage._shape = shape
                self.displayImage._boundingbox = boundingbox
                self.displayImage._points = None
                self.displayImage._landmark_size = get_landmark_size(self.displayImage._shape)
                
                self.displayImage.update_view()
                self.setWindowTitle('Emotrics - ' + self._file_name.split(os.path.sep)[-1])
            else:
                self.getShapefromImage()
    
    def getShapefromImage(self, update=False):
        if self.displayImage._opencvimage is None:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Нет загруженного изображения.")
            return
        h, w, d = self.displayImage._opencvimage.shape

        self._Scale = 1
        if h > 1500 or w > 1500:
            if h >= w:
                h_n = 1500
                self._Scale = h / h_n
                w_n = int(np.round(w / self._Scale, 0))
                temp_image = cv2.resize(self.displayImage._opencvimage, (w_n, h_n), interpolation=cv2.INTER_AREA)
            else:
                w_n = 1500
                self._Scale = w / w_n
                h_n = int(np.round(h / self._Scale, 0))
                temp_image = cv2.resize(self.displayImage._opencvimage, (w_n, h_n), interpolation=cv2.INTER_AREA)
        else:
            temp_image = self.displayImage._opencvimage.copy()

        self.landmarks = GetLandmarks(temp_image, self._ModelName)
        self.landmarks.moveToThread(self.thread_landmarks)
        self.thread_landmarks.start()
        self.thread_landmarks.started.connect(self.landmarks.getlandmarks)
        
        if update:
            self.landmarks.landmarks.connect(self.ProcessShape_update)
        else:
            self.landmarks.landmarks.connect(self.ProcessShape)
                        
        self.landmarks.finished.connect(self.thread_landmarks.quit)

    def ProcessShape(self, shape, numFaces, lefteye, righteye, boundingbox):
        if numFaces == 1:
            if self._Scale != 1:
                for k in range(0, 68):
                    shape[k] = [int(np.round(shape[k,0] * self._Scale, 0)),
                                int(np.round(shape[k,1] * self._Scale, 0))]
                for k in range(0, 3):
                    lefteye[k] = int(np.round(lefteye[k] * self._Scale, 0))
                    righteye[k] = int(np.round(righteye[k] * self._Scale, 0))
                for k in range(0, 4):
                    boundingbox[k] = int(np.round(boundingbox[k] * self._Scale, 0))
            
            self.displayImage._shape = shape
            self.displayImage._boundingbox = boundingbox
            self.displayImage._lefteye = lefteye
            self.displayImage._righteye = righteye
            if self.displayImage._landmark_size is None:
                self.displayImage._landmark_size = get_landmark_size(self.displayImage._shape)
            
            self.displayImage._points = None
            self.setWindowTitle('Emotrics - ' + self._file_name.split(os.path.sep)[-1])
        elif numFaces == 0:
            self.displayImage._shape = None
            QtWidgets.QMessageBox.warning(self, "Предупреждение",
                "На изображении не найдено лицо.\nЕсли лицо есть, попробуйте изменить яркость изображения.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)
        elif numFaces > 1:
            self.displayImage._shape = None
            QtWidgets.QMessageBox.warning(self, "Предупреждение",
                "На изображении несколько лиц.\nЗагрузите изображение с одним лицом.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)
          
        self.displayImage.update_view()
        
    def ProcessShape_update(self, shape, numFaces, lefteye, righteye, boundingbox):
        if self._Scale != 1:
            for k in range(0, 68):
                shape[k] = [int(np.round(shape[k,0] * self._Scale, 0)),
                            int(np.round(shape[k,1] * self._Scale, 0))]
            for k in range(0, 3):
                lefteye[k] = int(np.round(lefteye[k] * self._Scale, 0))
                righteye[k] = int(np.round(righteye[k] * self._Scale, 0))
            for k in range(0, 4):
                boundingbox[k] = int(np.round(boundingbox[k] * self._Scale, 0))
                
        self.displayImage._shape = shape
        self.displayImage._boundingbox = boundingbox
        self.displayImage.set_update_photo() 
    
    def toggle_landmarks(self):
        if self._toggle_landmaks is True:
            self._toggle_landmaks = False
            self.displayImage.set_update_photo(self._toggle_landmaks)
        else:
            self._toggle_landmaks = True
            self.displayImage.set_update_photo(self._toggle_landmaks)
                        
    def save_snapshot(self):
        if self.displayImage._opencvimage is not None:
            proposed_name = self._file_name[:-4] + '-разметка'
            name, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, 'Сохранить разметку лица', proposed_name,
                'png (*.png);;jpg (*.jpg);;jpeg (*.jpeg)'
            )
            if not name:
                return
            temp_image = self.displayImage._opencvimage.copy()
            if self.displayImage._shape is not None:
                temp_image = mark_picture(
                    temp_image,
                    self.displayImage._shape,
                    self.displayImage._lefteye,
                    self.displayImage._righteye,
                    self.displayImage._points,
                    self.displayImage._landmark_size
                )
            ext = os.path.splitext(name)[1].lower()
            if ext == '.jpg':
                encode_ext = '.jpg'
            elif ext == '.jpeg':
                encode_ext = '.jpeg'
            else:
                encode_ext = '.png'
            success, encoded = cv2.imencode(encode_ext, temp_image)
            if success:
                with open(safe_path(name), 'wb') as f:
                    f.write(encoded.tobytes())
            else:
                QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Не удалось сохранить размеченное изображение')

    def save_results(self):
        if self._Patient is None:  # одиночное фото
            if self._file_name is not None and self.displayImage._shape is not None:
                MeasurementsLeft, MeasurementsRight, MeasurementsDeviation, MeasurementsPercentual = get_measurements_from_data(
                    self.displayImage._shape, self.displayImage._lefteye, self.displayImage._righteye,
                    self._CalibrationType, self._CalibrationValue)
                
                temp = SaveWindow(
                    self,
                    file_name=self._file_name,
                    MeasurementsLeft=MeasurementsLeft,
                    MeasurementsRight=MeasurementsRight,
                    MeasurementsDeviation=MeasurementsDeviation,
                    MeasurementsPercentual=MeasurementsPercentual,
                    image_path=self._file_name,
                    shape=self.displayImage._shape,
                    left_eye=self.displayImage._lefteye,
                    right_eye=self.displayImage._righteye,
                    boundingbox=self.displayImage._boundingbox,
                    points=self.displayImage._points,
                    landmark_size=self.displayImage._landmark_size
                )
                temp.exec_()
        else:  # пациент (две фотографии)
            first_path = self._Patient.FirstPhoto._file_name
            second_path = self._Patient.SecondPhoto._file_name
            dlg = SavePatientWindow(
                self,
                patient=self._Patient,
                calibration_type=self._CalibrationType,
                calibration_value=self._CalibrationValue,
                first_image_path=first_path,
                second_image_path=second_path
            )
            dlg.exec_()

    def settings(self):
        Settings = ShowSettings(self, self._ModelName, self._CalibrationType, self._CalibrationValue,
                                size_landmarks=self.displayImage._landmark_size, shape=self.displayImage._shape)
        Settings.exec_()
        
        if Settings.isCanceled:
            return
        else:
            if Settings.tab1._checkBox1.isChecked():
                self._CalibrationType = 'Iris'
                self._CalibrationValue = float(Settings.tab1._IrisDiameter_Edit.text())
            elif Settings.tab1._checkBox2.isChecked():
                self._CalibrationType = 'Manual'
                self._CalibrationValue = float(Settings.tab1._Personalized_Edit.text())
             
            old_modelName = self._ModelName
            is_model_changed = False
            if Settings.tab2._checkBox2.isChecked():
                self._ModelName = 'iBUG'
            elif Settings.tab2._checkBox1.isChecked():
                self._ModelName = 'MEE'
            elif Settings.tab2._checkBox2.isChecked() == False and Settings.tab2._checkBox1.isChecked() == False:
                self._ModelName = Settings.tab2._ModelName
                
            if old_modelName != self._ModelName:
                is_model_changed = True
                
            user_size_landmark = Settings.tab3._Landmark_Size_Edit.text()
            old_size_landmark = self.displayImage._landmark_size
            is_landmark_changed = False
            if user_size_landmark == "":
                size_landmarks = old_size_landmark
            elif int(user_size_landmark) == 0:
                size_landmarks = old_size_landmark
            else:
                size_landmarks = int(user_size_landmark)
                
            if size_landmarks != old_size_landmark:
                is_landmark_changed = True
                self.displayImage._landmark_size = size_landmarks
            
            if is_landmark_changed and not is_model_changed:
                self.displayImage.set_update_photo()
                
            if is_model_changed:
                if self.displayImage._shape is not None:
                    if self._Patient is None:
                        self.getShapefromImage(update=True)
                    else:
                        self.UpdateFirstPhoto_Patient()
                    
    def UpdateFirstPhoto_Patient(self):
        h, w, d = self._Patient.FirstPhoto._photo.shape
        self._Scale = 1
        if h > 1500 or w > 1500:
            if h >= w:
                h_n = 1500
                self._Scale = h / h_n
                w_n = int(np.round(w / self._Scale, 0))
                temp_image = cv2.resize(self._Patient.FirstPhoto._photo, (w_n, h_n), interpolation=cv2.INTER_AREA)
            else:
                w_n = 1500
                self._Scale = w / w_n
                h_n = int(np.round(h / self._Scale, 0))
                temp_image = cv2.resize(self._Patient.FirstPhoto._photo, (w_n, h_n), interpolation=cv2.INTER_AREA)
        else:
            temp_image = self._Patient.FirstPhoto._photo.copy()
        
        self.landmarksFirstPhoto = GetLandmarks(temp_image, self._ModelName)
        self.landmarksFirstPhoto.moveToThread(self.threadFirstPhoto)
        self.threadFirstPhoto.start()
        self.threadFirstPhoto.started.connect(self.landmarksFirstPhoto.getlandmarks)
        self.landmarksFirstPhoto.landmarks.connect(self.ProcessShape_UpdateFirstPhoto)
        self.landmarksFirstPhoto.finished.connect(self.threadFirstPhoto.quit)
        
    def ProcessShape_UpdateFirstPhoto(self, shape, numFaces, lefteye, righteye, boundingbox):
        if self._Scale != 1:
            for k in range(0, 68):
                shape[k] = [int(np.round(shape[k,0] * self._Scale, 0)),
                            int(np.round(shape[k,1] * self._Scale, 0))]
            for k in range(0, 3):
                lefteye[k] = int(np.round(lefteye[k] * self._Scale, 0))
                righteye[k] = int(np.round(righteye[k] * self._Scale, 0))
            for k in range(0, 4):
                boundingbox[k] = int(np.round(boundingbox[k] * self._Scale, 0))
                
        self._Patient.FirstPhoto._shape = shape
        self._Patient.FirstPhoto._boundingbox = boundingbox
        
        if self._file_name == self._Patient.FirstPhoto._file_name:
            self.displayImage._shape = shape
            self.displayImage._boundingbox = boundingbox
            self.displayImage.set_update_photo()
            
        self.UpdateSecondPhoto_Patient()
        
    def UpdateSecondPhoto_Patient(self):
        h, w, d = self._Patient.SecondPhoto._photo.shape
        self._Scale = 1
        if h > 1500 or w > 1500:
            if h >= w:
                h_n = 1500
                self._Scale = h / h_n
                w_n = int(np.round(w / self._Scale, 0))
                temp_image = cv2.resize(self._Patient.SecondPhoto._photo, (w_n, h_n), interpolation=cv2.INTER_AREA)
            else:
                w_n = 1500
                self._Scale = w / w_n
                h_n = int(np.round(h / self._Scale, 0))
                temp_image = cv2.resize(self._Patient.SecondPhoto._photo, (w_n, h_n), interpolation=cv2.INTER_AREA)
        else:
            temp_image = self._Patient.SecondPhoto._photo.copy()
        
        self.landmarksSecondPhoto = GetLandmarks(temp_image, self._ModelName)
        self.landmarksSecondPhoto.moveToThread(self.threadSecondPhoto)
        self.threadSecondPhoto.start()
        self.threadSecondPhoto.started.connect(self.landmarksSecondPhoto.getlandmarks)
        self.landmarksSecondPhoto.landmarks.connect(self.ProcessShape_UpdateSecondPhoto)
        self.landmarksSecondPhoto.finished.connect(self.threadSecondPhoto.quit)
        
    def ProcessShape_UpdateSecondPhoto(self, shape, numFaces, lefteye, righteye, boundingbox):
        if self._Scale != 1:
            for k in range(0, 68):
                shape[k] = [int(np.round(shape[k,0] * self._Scale, 0)),
                            int(np.round(shape[k,1] * self._Scale, 0))]
            for k in range(0, 3):
                lefteye[k] = int(np.round(lefteye[k] * self._Scale, 0))
                righteye[k] = int(np.round(righteye[k] * self._Scale, 0))
            for k in range(0, 4):
                boundingbox[k] = int(np.round(boundingbox[k] * self._Scale, 0))
                
        self._Patient.SecondPhoto._shape = shape
        self._Patient.SecondPhoto._boundingbox = boundingbox
        
        if self._file_name == self._Patient.SecondPhoto._file_name:
            self.displayImage._shape = shape
            self.displayImage._boundingbox = boundingbox
            self.displayImage.set_update_photo()

    def about_app(self):
        QtWidgets.QMessageBox.information(self, 'Emotrics',
            'Emotrics — это инструмент для объективной оценки лицевых измерений.\n\n'
            'Разработчик: Diego L. Guarin, PhD. Facial Nerve Centre, Massachusetts Eye and Ear Infirmary, Harvard Medical School.\n\n'
            'Доработка и перевод на русский язык: Шеремет В.М., НГТУ.\n\n'
            'Документация и исходный код: https://github.com/dguari1/Emotrics\n\n'
            'Это свободное программное обеспечение, распространяемое под лицензией GNU General Public License.',
            QtWidgets.QMessageBox.Ok)
        
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(
            self, 'Выход',
            'Вы действительно хотите выйти?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            if self._new_window is not None:
                self._new_window.close()
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    
    app.setStyle(QtWidgets.QStyleFactory.create('Cleanlooks'))
    GUI = window()
    app.exec_()
