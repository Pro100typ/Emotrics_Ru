from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
import ctypes
import os

from utilities import find_circle_from_points

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

class ProcessEye(QtWidgets.QDialog):
    def __init__(self, image=None):
        super(ProcessEye, self).__init__()
        self.setWindowTitle('Выделение глаза')
        self._circle = None
        self._image = image
        self.label_title = QtWidgets.QLabel()
        self.label_title.setText('Пожалуйста, отметьте четыре точки вокруг радужки')
        self.label_title.setMaximumWidth(500)
        self.view = View(self)
        if self._image is not None:
            self.view._image = self._image
            self.view.set_picture()
        self.buttonReset = QtWidgets.QPushButton('Очистить', self)
        self.buttonReset.clicked.connect(self.view.handleClearView)
        self.buttonDone = QtWidgets.QPushButton('Готово', self)
        self.buttonDone.clicked.connect(self.handleReturn)
        
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.label_title, 0, 0, 1, 2)
        layout.addWidget(self.view, 1, 0, 1, 2)
        layout.addWidget(self.buttonDone, 2, 0, 1, 1)
        layout.addWidget(self.buttonReset, 2, 1, 1, 1)
    
    def handleReturn(self):
        if self.view._counter == 4:
            self._circle = self.view._circle
        self.close()

class View(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(View, self).__init__(parent)
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setSceneRect(QtCore.QRectF(self.viewport().rect()))
        self._counter = 0
        self._circle = None
        self._mouse_pos = np.array([]).reshape(0, 2)
        self._image = None
    
    def process_circle(self):
        x = np.array([self._mouse_pos[0, 0], self._mouse_pos[1, 0], self._mouse_pos[2, 0], self._mouse_pos[3, 0]])
        y = np.array([self._mouse_pos[0, 1], self._mouse_pos[1, 1], self._mouse_pos[2, 1], self._mouse_pos[3, 1]])
        circle = find_circle_from_points(x, y)
        self._circle = [int(circle[0]), int(circle[1]), int(circle[2])]
        
        Ellipse = QtWidgets.QGraphicsEllipseItem(0, 0, self._circle[2] * 2, self._circle[2] * 2)
        pen = QtGui.QPen(QtCore.Qt.green)
        Ellipse.setPen(pen)
        Ellipse.setPos(circle[0] - self._circle[2], circle[1] - self._circle[2])
        Ellipse.setTransform(QtGui.QTransform())
        self._scene.addItem(Ellipse)
    
    def mousePressEvent(self, event):
        if self._counter < 4:
            scenePos = self.mapToScene(event.pos())
            x = scenePos.x()
            y = scenePos.y()
            self._mouse_pos = np.concatenate((self._mouse_pos, [[float(x), float(y)]]), axis=0)
            pen = QtGui.QPen(QtCore.Qt.red)
            brush = QtGui.QBrush(QtCore.Qt.red)
            size = int(self._scene.width() * (1 / 100) + 1)
            Rec = QtCore.QRectF(x, y, size, size)
            self._scene.addEllipse(Rec, pen, brush)
        QtWidgets.QGraphicsView.mousePressEvent(self, event)
    
    def mouseReleaseEvent(self, event):
        self._counter += 1
        if self._counter == 4:
            self.process_circle()
        QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)
    
    def set_picture(self):
        image = self._image.copy()
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        img_Qt = QtGui.QImage(image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        img_show = QtGui.QPixmap.fromImage(img_Qt)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._photo.setPixmap(img_show)
        self._scene.addItem(self._photo)
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        self.fitInView(rect)
        self.setSceneRect(rect)
    
    def resizeEvent(self, event):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        self.fitInView(rect)
        self.setSceneRect(rect)
    
    def handleClearView(self):
        self._scene.clear()
        self.set_picture()
        self._circle = None
        self._counter = 0
        self._mouse_pos = np.array([]).reshape(0, 2)

if __name__ == '__main__':
    import sys
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    GUI = ProcessEye()
    GUI.show()
    sys.exit(app.exec_())
