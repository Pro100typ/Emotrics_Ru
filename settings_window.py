import os
import sys
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
import numpy as np
import ctypes

from dlib import shape_predictor

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

QtWidgets.QFrame

class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        
class QVLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class LandMarksTab(QtWidgets.QWidget):
    def __init__(self, parent=None, size_landmarks=None, shape=None):
        super(LandMarksTab, self).__init__(parent)
        self._tab_name = 'Ориентиры'
        self._size_landmarks = size_landmarks
        
        self._label1 = QtWidgets.QLabel('Диаметр ориентиров (пикс):')
        self._Landmark_Size_Edit = QtWidgets.QLineEdit(self)
        self._Landmark_Size_Edit.setFixedWidth(50)
        validator = QtGui.QIntValidator(self)
        validator.setBottom(1)
        validator.setTop(99)
        self._Landmark_Size_Edit.setValidator(validator)
        self._label2 = QtWidgets.QLabel('px')
        
        if size_landmarks is not None:
            self._Landmark_Size_Edit.setText(str(size_landmarks))
        else:
            if shape is not None:
                if shape[36, 1] != -1 and shape[39, 1] != -1:
                    size_landmarks = np.round(0.025 * np.sqrt((shape[39, 0] - shape[36, 0])**2 + (shape[39, 1] - shape[36, 1])**2), 0)
                    size_landmarks = int(np.floor(size_landmarks))
                else:
                    size_landmarks = np.round(0.025 * np.sqrt((shape[42, 0] - shape[45, 0])**2 + (shape[42, 1] - shape[45, 1])**2), 0)
                    size_landmarks = int(np.floor(size_landmarks))
        
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self._label1, 0, 0, 1, 1)
        layout.addWidget(self._Landmark_Size_Edit, 0, 1, 1, 1)
        layout.addWidget(self._label2, 0, 2, 1, 1)
        self.setLayout(layout)

class CalibrationTab(QtWidgets.QWidget):
    def __init__(self, parent=None, CalibrationType='Iris', CalibrationValue=11.77):
        super(CalibrationTab, self).__init__(parent)
        self._tab_name = 'Калибровка'
        self._CalibrationType = CalibrationType
        self._CalibratioValue = CalibrationValue
        
        self._checkBox2 = QtWidgets.QCheckBox('Пользовательское значение', self)
        self._checkBox1 = QtWidgets.QCheckBox('Диаметр радужки', self)
        
        self._CheckButtonGroup = QtWidgets.QButtonGroup(self)
        self._CheckButtonGroup.addButton(self._checkBox1, 1)
        self._CheckButtonGroup.addButton(self._checkBox2, 2)
        
        self._Personalized_Edit = QtWidgets.QLineEdit(self)
        self._Personalized_Edit.setFixedWidth(100)
        self._label2a = QtWidgets.QLabel('мм/пикс')
        
        self._IrisDiameter_Edit = QtWidgets.QLineEdit(self)
        self._IrisDiameter_Edit.setFixedWidth(100)
        self._label1a = QtWidgets.QLabel('мм')
        
        if self._CalibrationType == 'Iris':
            self._checkBox1.setChecked(True)
            self._checkBox2.setChecked(False)
            self._Personalized_Edit.setText("")
            self._IrisDiameter_Edit.setText(str(self._CalibratioValue))
        else:
            self._checkBox1.setChecked(False) 
            self._checkBox2.setChecked(True)
            self._Personalized_Edit.setText(str(self._CalibratioValue))
            self._IrisDiameter_Edit.setText("")
        
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self._checkBox1, 0, 0, 1, 1)
        layout.addWidget(self._IrisDiameter_Edit, 1, 0, 1, 1)
        layout.addWidget(self._label1a, 1, 1, 1, 1)
        layout.addWidget(QHLine(), 2, 0)
        layout.addWidget(self._checkBox2, 3, 0, 1, 1)
        layout.addWidget(self._Personalized_Edit, 4, 0, 1, 1)
        layout.addWidget(self._label2a, 4, 1, 1, 1)
        self.setLayout(layout)

class ModelTab(QtWidgets.QWidget):
    def __init__(self, parent=None, ModelName='iBUG'):
        super(ModelTab, self).__init__(parent)
        
        if os.name == 'posix':
            scriptDir = os.path.dirname(sys.argv[0])
        else:
            scriptDir = os.getcwd()
        
        self._ModelName = ModelName
        self._tab_name = 'Модель'
        
        self._checkBox2 = QtWidgets.QCheckBox('База данных iBUG', self)
        self._checkBox1 = QtWidgets.QCheckBox('База данных MEEI', self)
        self._checkBox3 = QtWidgets.QCheckBox('Своя модель', self)
        
        if self._ModelName == 'iBUG':
            self._checkBox1.setChecked(False)
            self._checkBox2.setChecked(True)
            self._checkBox3.setChecked(False)
        elif self._ModelName == 'MEE':
            self._checkBox1.setChecked(True)
            self._checkBox2.setChecked(False)
            self._checkBox3.setChecked(False)
        else:
            self._checkBox1.setChecked(False)
            self._checkBox2.setChecked(False)
            self._checkBox3.setChecked(True)
        
        self._CheckButtonGroup = QtWidgets.QButtonGroup(self)
        self._CheckButtonGroup.addButton(self._checkBox1, 1)
        self._CheckButtonGroup.addButton(self._checkBox2, 2)
        self._CheckButtonGroup.addButton(self._checkBox3, 3)
        
        self._help_checkBox1 = QtWidgets.QPushButton('', self)
        self._help_checkBox1.setIcon(QtGui.QIcon(safe_path(scriptDir + os.path.sep + 'include' + os.path.sep + 'icon_color' + os.path.sep + 'question_icon.png')))
        self._help_checkBox1.clicked.connect(lambda: self.push_help_checkBox1())
        self._help_checkBox1.setIconSize(QtCore.QSize(20, 20))
        
        self._help_checkBox2 = QtWidgets.QPushButton('', self)
        self._help_checkBox2.setIcon(QtGui.QIcon(safe_path(scriptDir + os.path.sep + 'include' + os.path.sep + 'icon_color' + os.path.sep + 'question_icon.png')))
        self._help_checkBox2.clicked.connect(lambda: self.push_help_checkBox2())
        self._help_checkBox2.setIconSize(QtCore.QSize(20, 20))
        
        self._select_own_models = QtWidgets.QPushButton('Выбрать модель', self)
        self._select_own_models.clicked.connect(self.select_model)
        self._select_own_models.setIconSize(QtCore.QSize(55, 50))
        
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self._checkBox1, 0, 0)
        layout.addWidget(self._help_checkBox1, 0, 1)
        layout.addWidget(QHLine(), 1, 0, 1, 2)
        layout.addWidget(self._checkBox2, 2, 0, 1, 1)
        layout.addWidget(self._help_checkBox2, 2, 1, 1, 1)
        layout.addWidget(QHLine(), 3, 0, 1, 2)
        layout.addWidget(self._checkBox3, 4, 0, 1, 1)
        layout.addWidget(self._select_own_models, 4, 0, 1, 2)
        self.setLayout(layout)
    
    def select_model(self):
        name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Загрузить модель', '', "dat files (*.dat)")
        if not name:
            return
        else:
            self._ModelName = os.path.normpath(name)
            try:
                _ = shape_predictor(safe_path(self._ModelName))
                self._checkBox1.setChecked(False)
                self._checkBox2.setChecked(False)
                self._checkBox3.setChecked(True)
            except:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Information)
                msg.setText("Выбранная модель не может быть использована.")
                msg.setInformativeText("Emotrics будет использовать модель MEEI.")
                msg.setWindowTitle("Ошибка модели")
                msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg.exec_()
                self._checkBox1.setChecked(True)
                self._checkBox2.setChecked(False)
                self._checkBox3.setChecked(False)
    
    def push_help_checkBox1(self):
        QtWidgets.QMessageBox.information(self, 'База данных MEEI',
            'База данных создана с использованием фронтальных стандартных клинических фотографий пациентов с лицевым параличом.',
            QtWidgets.QMessageBox.Ok)
    
    def push_help_checkBox2(self):
        QtWidgets.QMessageBox.information(self, 'База данных iBUG',
            'База данных, созданная в рамках проекта iBUG, содержит тысячи изображений из реальной жизни и портреты из интернета.',
            QtWidgets.QMessageBox.Ok)

class ShowSettings(QtWidgets.QDialog):
    def __init__(self, parent=None, ModelName='iBUG', CalibrationType='Iris', CalibrationValue=11.77,
                 size_landmarks=None, shape=None):
        super(ShowSettings, self).__init__(parent)
        
        self.setWindowTitle('Настройки')
        if os.name == 'posix':
            scriptDir = os.path.dirname(sys.argv[0])
        else:
            scriptDir = os.getcwd()
        self.setWindowIcon(QtGui.QIcon(safe_path(scriptDir + os.path.sep + 'include' + os.path.sep + 'icon_color' + os.path.sep + 'settings_icon.ico')))
        
        self.isCanceled = False
        self._ModelName = ModelName
        self._CalibrationType = CalibrationType
        self._CalibrationValue = CalibrationValue
        self._size_landmarks = size_landmarks
        self._shape = shape
        
        self.tab1 = CalibrationTab(self, self._CalibrationType, self._CalibrationValue)
        self.tab2 = ModelTab(self, self._ModelName)
        self.tab3 = LandMarksTab(self, self._size_landmarks, self._shape)
        
        self.main_Widget = QtWidgets.QTabWidget(self)
        self.tab1.setAutoFillBackground(True)
        self.tab2.setAutoFillBackground(True)
        self.tab3.setAutoFillBackground(True)
        self.main_Widget.addTab(self.tab1, self.tab1._tab_name)
        self.main_Widget.addTab(self.tab2, self.tab2._tab_name)
        self.main_Widget.addTab(self.tab3, self.tab3._tab_name)
        
        self.buttonDone = QtWidgets.QPushButton('Готово', self)
        self.buttonDone.clicked.connect(self.handleReturn)
        self.buttonCancel = QtWidgets.QPushButton('Отмена', self)
        self.buttonCancel.clicked.connect(self.pressCanceled)
        
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.main_Widget, 0, 0, 2, 2)
        layout.addWidget(self.buttonDone, 2, 0, 1, 1)
        layout.addWidget(self.buttonCancel, 2, 1, 1, 1)
        self.setLayout(layout)
    
    def pressCanceled(self):
        self.isCanceled = True
        self.handleClose()
    
    def handleClose(self):
        self.close()
    
    def handleReturn(self):
        if self.tab1._checkBox1.isChecked():
            IrisDiameter = self.tab1._IrisDiameter_Edit.text()
            if not IrisDiameter:
                QtWidgets.QMessageBox.information(self, 'Ошибка',
                    'Диаметр радужки должен быть больше нуля',
                    QtWidgets.QMessageBox.Ok)
            else:
                IrisDiameter = float(IrisDiameter)
                if IrisDiameter <= 0:
                    QtWidgets.QMessageBox.information(self, 'Ошибка',
                        'Диаметр радужки должен быть больше нуля',
                        QtWidgets.QMessageBox.Ok)
                else:
                    self.close()
        elif self.tab1._checkBox2.isChecked():
            PersonalizedValue = self.tab1._Personalized_Edit.text()
            if not PersonalizedValue:
                QtWidgets.QMessageBox.information(self, 'Ошибка',
                    'Пользовательское калибровочное значение должно быть больше нуля',
                    QtWidgets.QMessageBox.Ok)
            else:
                PersonalizedValue = float(PersonalizedValue)
                if PersonalizedValue <= 0:
                    QtWidgets.QMessageBox.information(self, 'Ошибка',
                        'Пользовательское калибровочное значение должно быть больше нуля',
                        QtWidgets.QMessageBox.Ok)
                else:
                    self.close()
        else:
            self.close()

if __name__ == '__main__':
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    GUI = ShowSettings()
    app.exec_()
