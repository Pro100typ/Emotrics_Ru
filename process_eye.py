# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 16:59:44 2017

@author: Diego L.Guarin -- diego_guarin at meei.harvard.edu
"""

import cv2
from eye_window import ProcessEye

def get_iris_manual(Image, shape, position):
    """
    Функция для ручного выделения радужки.
    Открывает окно, где пользователь выбирает 4 точки вокруг радужки.
    Возвращает координаты центра и радиус.
    """
    if position == 'left':
        # Левый глаз
        x_left = shape[42, 0]
        w_left = (shape[45, 0] - x_left)
        y_left = min(shape[43, 1], shape[44, 1])
        h_left = (max(shape[46, 1], shape[47, 1]) - y_left)
        Eye = Image.copy()
        Eye = Eye[(y_left - 5):(y_left + h_left + 5), (x_left - 5):(x_left + w_left + 5)]
    elif position == 'right':
        # Правый глаз
        x_right = shape[36, 0]
        w_right = (shape[39, 0] - x_right)
        y_right = min(shape[37, 1], shape[38, 1])
        h_right = (max(shape[41, 1], shape[40, 1]) - y_right)
        Eye = Image.copy()
        Eye = Eye[(y_right - 5):(y_right + h_right + 5), (x_right - 5):(x_right + w_right + 5)]
    
    # Преобразуем BGR (OpenCV) в RGB для отображения в PyQt
    temp_image = Eye.copy()
    temp_image = cv2.cvtColor(temp_image, cv2.COLOR_BGR2RGB)
    
    # Открываем окно для выбора радужки
    EyeWindow = ProcessEye(temp_image)
    EyeWindow.exec_()
    
    circle = EyeWindow._circle
    if circle is not None:
        if position == 'left':
            circle[0] = circle[0] + x_left - 5
            circle[1] = circle[1] + y_left - 5
        elif position == 'right':
            circle[0] = circle[0] + x_right - 5
            circle[1] = circle[1] + y_right - 5
        return circle
    else:
        return None
