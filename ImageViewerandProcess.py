# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 10:53:19 2017

@author: Diego L.Guarin -- diego_guarin at meei.harvard.edu
"""

import cv2
import numpy as np
from scipy.spatial.distance import cdist
import ctypes
import os

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from utilities import mark_picture
from process_eye import get_iris_manual

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

class ImageViewer(QtWidgets.QGraphicsView):
    def __init__(self):
        super(ImageViewer, self).__init__()
        self._zoom = 0
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(100, 100, 100)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setMouseTracking(True)
        
        self._shape = None
        self._lefteye = None
        self._righteye = None
        self._opencvimage = None
        self._boundingbox = None
        self._PointToModify = None
        self._points = None
        self._landmark_size = None
        
        self._IsPointLifted = False
        self._IsDragEyes = False
        self._IsDragLeft = False
        self._IsDragRight = False
        self._BothEyesTogether = False
        
    def setPhoto(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
            self._photo.setPixmap(pixmap)
            self.fitInView()
        else:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
    
    def fitInView(self):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
            self.scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.viewport().rect()
            scenerect = self.transform().mapRect(rect)
            factor = min(viewrect.width() / scenerect.width(),
                         viewrect.height() / scenerect.height())
            self.scale(factor, factor)
            self.centerOn(rect.center())
            self._zoom = 0
    
    def zoomFactor(self):
        return self._zoom
    
    def wheelEvent(self, event):
        if not self._photo.pixmap().isNull():
            move = event.angleDelta().y() / 120
            if move > 0:
                factor = 1.2
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom <= 0:
                self._zoom = 0
                self.fitInView()
    
    def mousePressEvent(self, event):
        if not self._photo.pixmap().isNull():
            scenePos = self.mapToScene(event.pos())
            if event.button() == QtCore.Qt.RightButton:
                if self._IsPointLifted == False:
                    if self._shape is not None and not self._BothEyesTogether:
                        x_mousePos = scenePos.toPoint().x()
                        y_mousePos = scenePos.toPoint().y()
                        mousePos = np.array([(x_mousePos, y_mousePos)])
                        points_all = np.append(self._shape,
                                               [[self._righteye[0], self._righteye[1]],
                                                [self._lefteye[0], self._lefteye[1]]], axis=0)
                        distance = cdist(points_all, mousePos)
                        distance = distance[:, 0]
                        if self._scene.height() < 1000:
                            PointToModify = [i for i, j in enumerate(distance) if j <= 3]
                        else:
                            PointToModify = [i for i, j in enumerate(distance) if j <= 6]
                        if PointToModify:
                            self._PointToModify = PointToModify[0]
                            if self._PointToModify >= 68:
                                if self._PointToModify == 69:
                                    position = 'left'
                                    temp = get_iris_manual(self._opencvimage, self._shape, position)
                                    if temp is not None:
                                        self._lefteye = temp
                                elif self._PointToModify == 68:
                                    position = 'right'
                                    temp = get_iris_manual(self._opencvimage, self._shape, position)
                                    if temp is not None:
                                        self._righteye = temp
                            else:
                                self._shape[self._PointToModify] = [-1, -1]
                                self._IsPointLifted = True
                            self.set_update_photo()
                    elif self._BothEyesTogether:
                        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                        self._IsDragEyes = False
                        self._IsDragLeft = False
                        self._IsDragRight = False
                        self._BothEyesTogether = False
                        self.set_update_photo()
            elif event.button() == QtCore.Qt.LeftButton:
                if self._IsPointLifted:
                    x_mousePos = scenePos.toPoint().x()
                    y_mousePos = scenePos.toPoint().y()
                    self._shape[self._PointToModify] = [x_mousePos, y_mousePos]
                    self._IsPointLifted = False
                    self._PointToModify = None
                elif self._BothEyesTogether:
                    self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    self._IsDragEyes = False
                    self._IsDragLeft = False
                    self._IsDragRight = False
                    self._BothEyesTogether = False
                    self.set_update_photo()
                else:
                    self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
                    if self._shape is not None:
                        x_mousePos = scenePos.toPoint().x()
                        y_mousePos = scenePos.toPoint().y()
                        mousePos = np.array([(x_mousePos, y_mousePos)])
                        distance = cdist([[self._righteye[0], self._righteye[1]],
                                          [self._lefteye[0], self._lefteye[1]]], mousePos)
                        distance = distance[:, 0]
                        if self._scene.height() < 1000:
                            PointToModify = [i for i, j in enumerate(distance) if j <= 3]
                        else:
                            PointToModify = [i for i, j in enumerate(distance) if j <= 6]
                        if PointToModify:
                            self._PointToModify = PointToModify[0]
                            if self._PointToModify == 0:
                                self._IsDragEyes = True
                                self._IsDragLeft = False
                                self._IsDragRight = True
                                self._BothEyesTogether = False
                            elif self._PointToModify == 1:
                                self._IsDragEyes = True
                                self._IsDragRight = False
                                self._IsDragLeft = True
                                self._BothEyesTogether = False
                            self.set_update_photo()
                            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
                            self.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
                            self.draw_circle(self._righteye)
                            self.draw_circle(self._lefteye)
            QtWidgets.QGraphicsView.mousePressEvent(self, event)
    
    def mouseReleaseEvent(self, event):
        if not self._BothEyesTogether:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
            self._IsDragEyes = False
            self._IsDragLeft = False
            self._IsDragRight = False
            self._BothEyesTogether = False
            self.set_update_photo()
        elif self._BothEyesTogether:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            event.accept()
            if self._shape is not None:
                scenePos = self.mapToScene(event.pos())
                x_mousePos = scenePos.toPoint().x()
                y_mousePos = scenePos.toPoint().y()
                mousePos = np.array([(x_mousePos, y_mousePos)])
                distance = cdist([[self._righteye[0], self._righteye[1]],
                                  [self._lefteye[0], self._lefteye[1]]], mousePos)
                distance = distance[:, 0]
                if self._scene.height() < 1000:
                    PointToModify = [i for i, j in enumerate(distance) if j <= 3]
                else:
                    PointToModify = [i for i, j in enumerate(distance) if j <= 6]
                if PointToModify:
                    self._PointToModify = PointToModify[0]
                    if self._PointToModify == 0:
                        self._IsDragEyes = True
                        self._IsDragRight = True
                        self._IsDragLeft = False
                        self._BothEyesTogether = True
                    elif self._PointToModify == 1:
                        self._IsDragEyes = True
                        self._IsDragRight = False
                        self._IsDragLeft = True
                        self._BothEyesTogether = True
                    self.set_update_photo()
                    self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
                    self.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        else:
            event.ignore()
        self.draw_circle(self._righteye)
        self.draw_circle(self._lefteye)
        QtWidgets.QGraphicsView.mouseDoubleClickEvent(self, event)
    
    def mouseMoveEvent(self, event):
        if self._IsDragEyes and not self._BothEyesTogether:
            event.accept()
            for item in self._scene.items():
                if isinstance(item, QtWidgets.QGraphicsEllipseItem):
                    self._scene.removeItem(item)
            scenePos = self.mapToScene(event.pos())
            x_mousePos = scenePos.toPoint().x()
            y_mousePos = scenePos.toPoint().y()
            if self._IsDragLeft:
                self._lefteye = [x_mousePos, y_mousePos, self._lefteye[2]]
                self.draw_circle(self._lefteye)
            elif self._IsDragRight:
                self._righteye = [x_mousePos, y_mousePos, self._righteye[2]]
                self.draw_circle(self._righteye)
        elif self._IsDragEyes and self._BothEyesTogether:
            event.accept()
            for item in self._scene.items():
                if isinstance(item, QtWidgets.QGraphicsEllipseItem):
                    self._scene.removeItem(item)
            scenePos = self.mapToScene(event.pos())
            x_mousePos = scenePos.toPoint().x()
            y_mousePos = scenePos.toPoint().y()
            if self._IsDragLeft:
                delta_x = x_mousePos - self._lefteye[0]
                delta_y = y_mousePos - self._lefteye[1]
                self._lefteye = [x_mousePos, y_mousePos, self._lefteye[2]]
                self._righteye = [self._righteye[0] + delta_x, self._righteye[1] + delta_y, self._righteye[2]]
                self.draw_circle(self._lefteye)
                self.draw_circle(self._righteye)
            if self._IsDragRight:
                delta_x = x_mousePos - self._righteye[0]
                delta_y = y_mousePos - self._righteye[1]
                self._righteye = [x_mousePos, y_mousePos, self._righteye[2]]
                self._lefteye = [self._lefteye[0] + delta_x, self._lefteye[1] + delta_y, self._lefteye[2]]
                self.draw_circle(self._righteye)
                self.draw_circle(self._lefteye)
        else:
            event.ignore()
        QtWidgets.QGraphicsView.mouseMoveEvent(self, event)
    
    def draw_circle(self, CircleInformation):
        Ellipse = QtWidgets.QGraphicsEllipseItem(0, 0, CircleInformation[2] * 2, CircleInformation[2] * 2)
        pen = QtGui.QPen(QtCore.Qt.green)
        if self._scene.height() < 1000:
            pen.setWidth(1)
        else:
            pen.setWidth(3)
        Ellipse.setPen(pen)
        Ellipse.setPos(CircleInformation[0] - CircleInformation[2], CircleInformation[1] - CircleInformation[2])
        Ellipse.setTransform(QtGui.QTransform())
        self._scene.addItem(Ellipse)
    
    def set_update_photo(self, toggle=True):
        if self._opencvimage is not None:
            self._scene.removeItem(self._photo)
            temp_image = self._opencvimage.copy()
            if toggle:
                if self._shape is not None:
                    if self._IsDragEyes:
                        if self._IsDragRight and not self._BothEyesTogether:
                            temp_image = mark_picture(temp_image, self._shape, self._lefteye, [0, 0, -1], self._points, self._landmark_size)
                        elif self._IsDragLeft and not self._BothEyesTogether:
                            temp_image = mark_picture(temp_image, self._shape, [0, 0, -1], self._righteye, self._points, self._landmark_size)
                        elif self._BothEyesTogether:
                            temp_image = mark_picture(temp_image, self._shape, [0, 0, -1], [0, 0, -1], self._points, self._landmark_size)
                    else:
                        temp_image = mark_picture(temp_image, self._shape, self._lefteye, self._righteye, self._points, self._landmark_size)
            image = cv2.cvtColor(temp_image, cv2.COLOR_BGR2RGB)
            height, width, channel = image.shape
            bytesPerLine = 3 * width
            img_Qt = QtGui.QImage(image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            img_show = QtGui.QPixmap.fromImage(img_Qt)
            self._photo.setPixmap(img_show)
            self._scene.addItem(self._photo)
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
    
    def show_entire_image(self):
        self.fitInView()
    
    def resizeEvent(self, event):
        self.fitInView()
    
    def update_view(self):
        if self._opencvimage is not None:
            temp_image = self._opencvimage.copy()
            if self._shape is not None:
                temp_image = mark_picture(temp_image, self._shape, self._lefteye, self._righteye, self._points, self._landmark_size)
            image = cv2.cvtColor(temp_image, cv2.COLOR_BGR2RGB)
            height, width, channel = image.shape
            bytesPerLine = 3 * width
            img_Qt = QtGui.QImage(image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            img_show = QtGui.QPixmap.fromImage(img_Qt)
            self.setPhoto(img_show)
