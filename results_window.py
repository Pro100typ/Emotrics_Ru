# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 15:42:31 2017

@author: Diego L.Guarin -- diego_guarin at meei.harvard.edu
"""

import os
import sys
import ctypes
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from example_window import ShowExample

# ------------------ Функция для безопасного пути (портативность) ------------------
def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу, работает как в разработке, так и в собранном EXE."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ----------------------------------------------------------------

class CustomTabResult(QtWidgets.QWidget):
    def __init__(self):
        super(CustomTabResult, self).__init__()

        spacerh = QtWidgets.QWidget(self)
        spacerh.setFixedSize(10, 0)
        spacerv = QtWidgets.QWidget(self)
        spacerv.setFixedSize(0, 10)
        
        self._tab_name = 'Вкладка'
        
        # Заголовки столбцов
        self._label0a = QtWidgets.QLabel('Правая сторона')
        self._label0b = QtWidgets.QLabel('Левая сторона')
        self._label0c = QtWidgets.QLabel('Разница (абс.)')
        self._label0d = QtWidgets.QLabel('Разница (%)')
        
        # Метрики (новые названия)
        self._BH = QtWidgets.QLabel('Высота брови (мм):')
        self._MRD1 = QtWidgets.QLabel('Расстояние от зрачка до верхнего века (мм):')
        self._MRD2 = QtWidgets.QLabel('Расстояние от зрачка до нижнего века (мм):')
        self._PFH = QtWidgets.QLabel('Высота глазной щели (мм):')
        self._CE = QtWidgets.QLabel('Расстояние от средней линии губы до угла рта (мм):')
        self._CH = QtWidgets.QLabel('Асимметрия стояния углов рта (мм):')
        self._SA = QtWidgets.QLabel('Угол улыбки (град):')
        self._UVH = QtWidgets.QLabel('Асимметрия стояния верхней губы (мм):')
        self._DS = QtWidgets.QLabel('Высота обнажения зубов при улыбке (мм):')
        self._LVH = QtWidgets.QLabel('Асимметрия стояния нижней губы (мм):')
        
        # Поля ввода для значений
        self._BH_right = QtWidgets.QLineEdit(self)
        self._BH_right.setText("-")
        self._BH_left = QtWidgets.QLineEdit(self)
        self._BH_left.setText("-")
        self._BH_dev = QtWidgets.QLineEdit(self)
        self._BH_dev.setText("-")
        self._BH_dev_p = QtWidgets.QLineEdit(self)
        self._BH_dev_p.setText("-")
        
        self._MRD1_right = QtWidgets.QLineEdit(self)
        self._MRD1_right.setText("-")
        self._MRD1_left = QtWidgets.QLineEdit(self)
        self._MRD1_left.setText("-")
        self._MRD1_dev = QtWidgets.QLineEdit(self)
        self._MRD1_dev.setText("-")
        self._MRD1_dev_p = QtWidgets.QLineEdit(self)
        self._MRD1_dev_p.setText("-")
        
        self._MRD2_right = QtWidgets.QLineEdit(self)
        self._MRD2_right.setText("-")
        self._MRD2_left = QtWidgets.QLineEdit(self)
        self._MRD2_left.setText("-")
        self._MRD2_dev = QtWidgets.QLineEdit(self)
        self._MRD2_dev.setText("-")
        self._MRD2_dev_p = QtWidgets.QLineEdit(self)
        self._MRD2_dev_p.setText("-")
        
        self._PFH_right = QtWidgets.QLineEdit(self)
        self._PFH_right.setText("-")
        self._PFH_left = QtWidgets.QLineEdit(self)
        self._PFH_left.setText("-")
        self._PFH_dev = QtWidgets.QLineEdit(self)
        self._PFH_dev.setText("-")
        self._PFH_dev_p = QtWidgets.QLineEdit(self)
        self._PFH_dev_p.setText("-")
        
        self._CE_right = QtWidgets.QLineEdit(self)
        self._CE_right.setText("-")
        self._CE_left = QtWidgets.QLineEdit(self)
        self._CE_left.setText("-")
        self._CE_dev = QtWidgets.QLineEdit(self)
        self._CE_dev.setText("-")
        self._CE_dev_p = QtWidgets.QLineEdit(self)
        self._CE_dev_p.setText("-")
        
        self._CH_right = QtWidgets.QLineEdit(self)
        self._CH_right.setText("-")
        self._CH_left = QtWidgets.QLineEdit(self)
        self._CH_left.setText("-")
        self._CH_dev = QtWidgets.QLineEdit(self)
        self._CH_dev.setText("-")
        self._CH_dev_p = QtWidgets.QLineEdit(self)
        self._CH_dev_p.setText("-")
        
        self._SA_right = QtWidgets.QLineEdit(self)
        self._SA_right.setText("-")
        self._SA_left = QtWidgets.QLineEdit(self)
        self._SA_left.setText("-")
        self._SA_dev = QtWidgets.QLineEdit(self)
        self._SA_dev.setText("-")
        self._SA_dev_p = QtWidgets.QLineEdit(self)
        self._SA_dev_p.setText("-")
        
        self._UVH_right = QtWidgets.QLineEdit(self)
        self._UVH_right.setText("-")
        self._UVH_left = QtWidgets.QLineEdit(self)
        self._UVH_left.setText("-")
        self._UVH_dev = QtWidgets.QLineEdit(self)
        self._UVH_dev.setText("-")
        self._UVH_dev_p = QtWidgets.QLineEdit(self)
        self._UVH_dev_p.setText("-")
        
        self._DS_right = QtWidgets.QLineEdit(self)
        self._DS_right.setText("-")
        self._DS_left = QtWidgets.QLineEdit(self)
        self._DS_left.setText("-")
        self._DS_dev = QtWidgets.QLineEdit(self)
        self._DS_dev.setText("-")
        self._DS_dev_p = QtWidgets.QLineEdit(self)
        self._DS_dev_p.setText("-")
        
        self._LVH_right = QtWidgets.QLineEdit(self)
        self._LVH_right.setText("-")
        self._LVH_left = QtWidgets.QLineEdit(self)
        self._LVH_left.setText("-")
        self._LVH_dev = QtWidgets.QLineEdit(self)
        self._LVH_dev.setText("-")
        self._LVH_dev_p = QtWidgets.QLineEdit(self)
        self._LVH_dev_p.setText("-")
        
        # --- Кнопки помощи с иконками (исправленные пути) ---
        # Вспомогательная функция для загрузки иконки вопроса
        def question_icon():
            return QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'question_icon.png')))
        
        # Высота брови
        self._help_BH = QtWidgets.QPushButton('', self)
        self._help_BH.setIcon(question_icon())
        pixmap_BH = QtGui.QPixmap.fromImage(QtGui.QImage(resource_path(os.path.join('include', 'measures', 'brow_height_focus.png'))))
        text_BH_title = 'Высота брови:'
        text_BH_content = 'Вертикальное расстояние от центра зрачка до верхней границы брови'
        self._help_BH.clicked.connect(lambda: self.push_help(pixmap_BH, text_BH_title, text_BH_content))
        self._help_BH.setIconSize(QtCore.QSize(20, 20))
        
        # MRD1
        self._help_MRD1 = QtWidgets.QPushButton('', self)
        self._help_MRD1.setIcon(question_icon())
        pixmap_MRD1 = QtGui.QPixmap.fromImage(QtGui.QImage(resource_path(os.path.join('include', 'measures', 'marginal_reflex_distance_1_focus.png'))))
        text_MRD1_title = 'Расстояние от зрачка до верхнего века:'
        text_MRD1_content = 'Вертикальное расстояние от центра зрачка до верхнего века'
        self._help_MRD1.clicked.connect(lambda: self.push_help(pixmap_MRD1, text_MRD1_title, text_MRD1_content))
        self._help_MRD1.setIconSize(QtCore.QSize(20, 20))
        
        # MRD2
        self._help_MRD2 = QtWidgets.QPushButton('', self)
        self._help_MRD2.setIcon(question_icon())
        pixmap_MRD2 = QtGui.QPixmap.fromImage(QtGui.QImage(resource_path(os.path.join('include', 'measures', 'marginal_reflex_distance_2_focus.png'))))
        text_MRD2_title = 'Расстояние от зрачка до нижнего века:'
        text_MRD2_content = 'Вертикальное расстояние от центра зрачка до нижнего века'
        self._help_MRD2.clicked.connect(lambda: self.push_help(pixmap_MRD2, text_MRD2_title, text_MRD2_content))
        self._help_MRD2.setIconSize(QtCore.QSize(20, 20))
        
        # Высота глазной щели
        self._help_PFH = QtWidgets.QPushButton('', self)
        self._help_PFH.setIcon(question_icon())
        pixmap_PFH = QtGui.QPixmap.fromImage(QtGui.QImage(resource_path(os.path.join('include', 'measures', 'palpebral_fissure_height_focus.png'))))
        text_PFH_title = 'Высота глазной щели:'
        text_PFH_content = 'Вертикальное расстояние между веками открытого глаза'
        self._help_PFH.clicked.connect(lambda: self.push_help(pixmap_PFH, text_PFH_title, text_PFH_content))
        self._help_PFH.setIconSize(QtCore.QSize(20, 20))
        
        # Смещение комиссуры (новое название)
        self._help_CE = QtWidgets.QPushButton('', self)
        self._help_CE.setIcon(question_icon())
        pixmap_CE = QtGui.QPixmap.fromImage(QtGui.QImage(resource_path(os.path.join('include', 'measures', 'commissure_excursion_focus.png'))))
        text_CE_title = 'Расстояние от средней линии губы до угла рта:'
        text_CE_content = 'Расстояние от срединной вертикали / точки соединения нижней губы до угла рта'
        self._help_CE.clicked.connect(lambda: self.push_help(pixmap_CE, text_CE_title, text_CE_content))
        self._help_CE.setIconSize(QtCore.QSize(20, 20))
        
        # Асимметрия стояния углов рта
        self._help_CH = QtWidgets.QPushButton('', self)
        self._help_CH.setIcon(question_icon())
        pixmap_CH = QtGui.QPixmap.fromImage(QtGui.QImage(resource_path(os.path.join('include', 'measures', 'commissure_deviation_focus.png'))))
        text_CH_title = 'Асимметрия стояния углов рта:'
        text_CH_content = 'Вертикальное расстояние между горизонтальными плоскостями левого и правого углов рта'
        self._help_CH.clicked.connect(lambda: self.push_help(pixmap_CH, text_CH_title, text_CH_content))
        self._help_CH.setIconSize(QtCore.QSize(20, 20))
        
        # Угол улыбки
        self._help_SA = QtWidgets.QPushButton('', self)
        self._help_SA.setIcon(question_icon())
        pixmap_SA = QtGui.QPixmap.fromImage(QtGui.QImage(resource_path(os.path.join('include', 'measures', 'smile_angle_focus.png'))))
        text_SA_title = 'Угол улыбки:'
        text_SA_content = 'Угол между горизонтальной плоскостью в точке соединения нижней губы и углом рта'
        self._help_SA.clicked.connect(lambda: self.push_help(pixmap_SA, text_SA_title, text_SA_content))
        self._help_SA.setIconSize(QtCore.QSize(20, 20))
        
        # Асимметрия стояния верхней губы
        self._help_UVH = QtWidgets.QPushButton('', self)
        self._help_UVH.setIcon(question_icon())
        pixmap_UVH = QtGui.QPixmap.fromImage(QtGui.QImage(resource_path(os.path.join('include', 'measures', 'upper_lip_height_deviation_focus.png'))))
        text_UVH_title = 'Асимметрия стояния верхней губы:'
        text_UVH_content = 'Вертикальное расстояние между горизонтальными плоскостями верхней губы на середине между средней линией и углом рта'
        self._help_UVH.clicked.connect(lambda: self.push_help(pixmap_UVH, text_UVH_title, text_UVH_content))
        self._help_UVH.setIconSize(QtCore.QSize(20, 20))
        
        # Высота обнажения зубов
        self._help_DS = QtWidgets.QPushButton('', self)
        self._help_DS.setIcon(question_icon())
        pixmap_DS = QtGui.QPixmap.fromImage(QtGui.QImage(resource_path(os.path.join('include', 'measures', 'dental_show_focus.png'))))
        text_DS_title = 'Высота обнажения зубов при улыбке:'
        text_DS_content = 'Вертикальное расстояние между слизистыми границами верхней и нижней губы на середине между средней линией и углом рта'
        self._help_DS.clicked.connect(lambda: self.push_help(pixmap_DS, text_DS_title, text_DS_content))
        self._help_DS.setIconSize(QtCore.QSize(20, 20))
        
        # Асимметрия стояния нижней губы
        self._help_LVH = QtWidgets.QPushButton('', self)
        self._help_LVH.setIcon(question_icon())
        pixmap_LVH = QtGui.QPixmap.fromImage(QtGui.QImage(resource_path(os.path.join('include', 'measures', 'lower_lip_height_deviation_focus.png'))))
        text_LVH_title = 'Асимметрия стояния нижней губы:'
        text_LVH_content = 'Вертикальное расстояние между горизонтальными плоскостями нижней губы на середине между средней линией и углом рта'
        self._help_LVH.clicked.connect(lambda: self.push_help(pixmap_LVH, text_LVH_title, text_LVH_content))
        self._help_LVH.setIconSize(QtCore.QSize(20, 20))
        
        # --- Разметка таблицы (сетка) ---
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self._label0a, 0, 2, 1, 1)
        layout.addWidget(spacerh, 0, 3)
        layout.addWidget(self._label0b, 0, 4, 1, 1)
        layout.addWidget(spacerh, 0, 5)
        layout.addWidget(self._label0c, 0, 6, 1, 1)
        layout.addWidget(spacerh, 0, 7)
        layout.addWidget(self._label0d, 0, 8, 1, 1)
        
        # Строка 1: Высота брови
        layout.addWidget(spacerv, 1, 0, 6, 1)
        layout.addWidget(self._BH, 2, 0, 1, 1)
        layout.addWidget(self._help_BH, 2, 1, 1, 1)
        layout.addWidget(self._BH_right, 2, 2, 1, 1)
        layout.addWidget(self._BH_left, 2, 4, 1, 1)
        layout.addWidget(self._BH_dev, 2, 6, 1, 1)
        layout.addWidget(self._BH_dev_p, 2, 8, 1, 1)
        
        # Строка 2: MRD1
        layout.addWidget(spacerv, 3, 0, 6, 1)
        layout.addWidget(self._MRD1, 4, 0, 1, 1)
        layout.addWidget(self._help_MRD1, 4, 1, 1, 1)
        layout.addWidget(self._MRD1_right, 4, 2, 1, 1)
        layout.addWidget(self._MRD1_left, 4, 4, 1, 1)
        layout.addWidget(self._MRD1_dev, 4, 6, 1, 1)
        layout.addWidget(self._MRD1_dev_p, 4, 8, 1, 1)
        
        # Строка 3: MRD2
        layout.addWidget(spacerv, 5, 0, 6, 1)
        layout.addWidget(self._MRD2, 6, 0, 1, 1)
        layout.addWidget(self._help_MRD2, 6, 1, 1, 1)
        layout.addWidget(self._MRD2_right, 6, 2, 1, 1)
        layout.addWidget(self._MRD2_left, 6, 4, 1, 1)
        layout.addWidget(self._MRD2_dev, 6, 6, 1, 1)
        layout.addWidget(self._MRD2_dev_p, 6, 8, 1, 1)
        
        # Строка 4: Высота глазной щели
        layout.addWidget(spacerv, 7, 0, 6, 1)
        layout.addWidget(self._PFH, 8, 0, 1, 1)
        layout.addWidget(self._help_PFH, 8, 1, 1, 1)
        layout.addWidget(self._PFH_right, 8, 2, 1, 1)
        layout.addWidget(self._PFH_left, 8, 4, 1, 1)
        layout.addWidget(self._PFH_dev, 8, 6, 1, 1)
        layout.addWidget(self._PFH_dev_p, 8, 8, 1, 1)
        
        # Строка 5: Расстояние от средней линии губы до угла рта
        layout.addWidget(spacerv, 9, 0, 6, 1)
        layout.addWidget(self._CE, 10, 0, 1, 1)
        layout.addWidget(self._help_CE, 10, 1, 1, 1)
        layout.addWidget(self._CE_right, 10, 2, 1, 1)
        layout.addWidget(self._CE_left, 10, 4, 1, 1)
        layout.addWidget(self._CE_dev, 10, 6, 1, 1)
        layout.addWidget(self._CE_dev_p, 10, 8, 1, 1)
        
        # Строка 6: Асимметрия стояния углов рта
        layout.addWidget(spacerv, 11, 0, 6, 1)
        layout.addWidget(self._CH, 12, 0, 1, 1)
        layout.addWidget(self._help_CH, 12, 1, 1, 1)
        layout.addWidget(self._CH_right, 12, 2, 1, 1)
        layout.addWidget(self._CH_left, 12, 4, 1, 1)
        layout.addWidget(self._CH_dev, 12, 6, 1, 1)
        layout.addWidget(self._CH_dev_p, 12, 8, 1, 1)
        
        # Строка 7: Угол улыбки
        layout.addWidget(spacerv, 13, 0, 6, 1)
        layout.addWidget(self._SA, 14, 0, 1, 1)
        layout.addWidget(self._help_SA, 14, 1, 1, 1)
        layout.addWidget(self._SA_right, 14, 2, 1, 1)
        layout.addWidget(self._SA_left, 14, 4, 1, 1)
        layout.addWidget(self._SA_dev, 14, 6, 1, 1)
        layout.addWidget(self._SA_dev_p, 14, 8, 1, 1)
        
        # Строка 8: Асимметрия стояния верхней губы
        layout.addWidget(spacerv, 15, 0, 6, 1)
        layout.addWidget(self._UVH, 16, 0, 1, 1)
        layout.addWidget(self._help_UVH, 16, 1, 1, 1)
        layout.addWidget(self._UVH_right, 16, 2, 1, 1)
        layout.addWidget(self._UVH_left, 16, 4, 1, 1)
        layout.addWidget(self._UVH_dev, 16, 6, 1, 1)
        layout.addWidget(self._UVH_dev_p, 16, 8, 1, 1)
        
        # Строка 9: Высота обнажения зубов
        layout.addWidget(spacerv, 17, 0, 6, 1)
        layout.addWidget(self._DS, 18, 0, 1, 1)
        layout.addWidget(self._help_DS, 18, 1, 1, 1)
        layout.addWidget(self._DS_right, 18, 2, 1, 1)
        layout.addWidget(self._DS_left, 18, 4, 1, 1)
        layout.addWidget(self._DS_dev, 18, 6, 1, 1)
        layout.addWidget(self._DS_dev_p, 18, 8, 1, 1)
        
        # Строка 10: Асимметрия стояния нижней губы
        layout.addWidget(spacerv, 19, 0, 6, 1)
        layout.addWidget(self._LVH, 20, 0, 1, 1)
        layout.addWidget(self._help_LVH, 20, 1, 1, 1)
        layout.addWidget(self._LVH_right, 20, 2, 1, 1)
        layout.addWidget(self._LVH_left, 20, 4, 1, 1)
        layout.addWidget(self._LVH_dev, 20, 6, 1, 1)
        layout.addWidget(self._LVH_dev_p, 20, 8, 1, 1)
        
        self.setLayout(layout)
    
    def push_help(self, pixmap, text_title='', text_content=''):
        self._Example_window = ShowExample()
        self._Example_window._view_photo.setPhoto(pixmap)
        self._Example_window.label_title.setText(text_title)
        self._Example_window.label_content.setText(text_content)
        self._Example_window.show()

class ShowResults(QtWidgets.QWidget):
    def __init__(self, tab1, tab2=None, tab3=None, parent=None):
        super(ShowResults, self).__init__(parent)
        
        self.setWindowTitle('Метрики')
        self.setWindowIcon(QtGui.QIcon(resource_path(os.path.join('include', 'icon_color', 'ruler_icon.ico'))))
        self._Example_window = None
        
        self.main_Widget = QtWidgets.QTabWidget(self)
        tab1.setAutoFillBackground(True)
        self.main_Widget.addTab(tab1, tab1._tab_name)
        
        if tab2 is not None:
            tab2.setAutoFillBackground(True)
            self.main_Widget.addTab(tab2, tab2._tab_name)
        
        if tab3 is not None:
            tab3.setAutoFillBackground(True)
            self.main_Widget.addTab(tab3, 'Разница')
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.main_Widget)
        self.setLayout(layout)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    GUI = ShowResults()
    GUI.show()
    app.exec_()
