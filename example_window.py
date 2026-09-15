# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 10:03:21 2017

@author: Diego L.Guarin -- diego_guarin at meei.harvard.edu
"""

import os
import sys
import ctypes
from PyQt5 import QtWidgets
from PyQt5 import QtGui

from ImageViewerandProcess import ImageViewer

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ------------------ Функция для безопасного пути ------------------
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
# ----------------------------------------------------------------

class ShowExample(QtWidgets.QMainWindow):
    def __init__(self):
        super(ShowExample, self).__init__()
        
        self.setWindowTitle('Пример')
        
        if os.name == 'posix':
            scriptDir = os.path.dirname(sys.argv[0])
        else:
            scriptDir = os.getcwd()
        
        # Загружаем изображение через safe_path
        img_Qt = QtGui.QImage(safe_path(scriptDir + os.path.sep + 'include' + os.path.sep + 'icons' + os.path.sep + 'Facial-Nerve-Center.jpg'))
        pixmap = QtGui.QPixmap.fromImage(img_Qt)
        self._view_photo = ImageViewer()
        self._view_photo.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(230, 230, 230)))
        self._view_photo.setPhoto(pixmap)
        
        self.label_title = QtWidgets.QLabel()
        self.label_title.setText('Пример текста')
        self.label_title.setWordWrap(True)
        self.label_title.setFont(QtGui.QFont("Times", weight=QtGui.QFont.Bold))
        
        self.label_content = QtWidgets.QLabel()
        self.label_content.setText('Пример текста')
        self.label_content.setWordWrap(True)
        
        self.main_Widget = QtWidgets.QWidget(self)
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label_title)
        layout.addWidget(self.label_content)
        layout.addWidget(self._view_photo)
        
        self.main_Widget.setLayout(layout)
        self.setCentralWidget(self.main_Widget)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    GUI = ShowExample()
    GUI.show()
    app.exec_()
