# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 22:12:59 2017

@author: Diego L.Guarin -- diego_guarin at meei.harvard.edu
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 22:12:59 2017

@author: Diego L.Guarin -- diego_guarin at meei.harvard.edu
"""

import os
import numpy as np
import cv2
from scipy import linalg
import pandas as pd
import ctypes

from measurements import get_measurements_from_data

# ------------------ Функция для безопасного пути ------------------
def safe_path(path):
    """Преобразует путь в безопасную форму (короткий путь 8.3 на Windows)."""
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

# ---------- Unicode-совместимые функции чтения/записи изображений ----------
def imread_unicode(path):
    """Читает изображение из пути с любыми символами (Unicode)."""
    try:
        with open(path, 'rb') as f:
            data = f.read()
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            # попробуем прочитать как серое
            with open(path, 'rb') as f:
                data = f.read()
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
        return img
    except Exception:
        return None

def imwrite_unicode(path, img):
    """Сохраняет изображение в путь с любыми символами (Unicode)."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        encode_ext = '.jpg'
    else:
        encode_ext = '.png'
    success, encoded = cv2.imencode(encode_ext, img)
    if success:
        with open(path, 'wb') as f:
            f.write(encoded.tobytes())
        return True
    return False
# --------------------------------------------------------------------

def shape_to_np(shape, dtype="int"):
    coords = np.zeros((68, 2), dtype=dtype)
    for i in range(0, 68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords

def get_info_from_txt(file):
    # file может быть безопасным путём, но open сам обрабатывает Unicode,
    # однако для надёжности используем safe_path при вызове
    shape = np.zeros((68, 2), dtype=int)
    left_pupil = np.zeros((1, 3), dtype=int)
    right_pupil = np.zeros((1, 3), dtype=int)
    bounding_box = np.zeros((1, 4), dtype=int)
    
    cont_landmarks = 0
    get_landmarks = 0
    get_leftpupil = 0
    cont_leftpupil = 0
    get_rightpupil = 0
    cont_rightpupil = 0
    get_boundingbox = 0
    cont_boundingbox = 0 
    
    # Явно указываем кодировку UTF-8
    with open(file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):    
            if i == 4:    
                get_landmarks = 1
            if i == 72:
                get_landmarks = 0
            if get_landmarks == 1:
                temp = line.strip().split(',')
                shape[cont_landmarks, 0] = int(temp[0])
                shape[cont_landmarks, 1] = int(temp[1])
                cont_landmarks += 1
            if i == 74:
                get_leftpupil = 1
            if i == 77:
                get_leftpupil = 0
            if get_leftpupil == 1:
                left_pupil[0, cont_leftpupil] = int(line.strip())
                cont_leftpupil += 1
            if i == 79:
                get_rightpupil = 1
            if i == 82:
                get_rightpupil = 0
            if get_rightpupil == 1:            
                right_pupil[0, cont_rightpupil] = int(line.strip())
                cont_rightpupil += 1 
            if i == 84:
                get_boundingbox = 1
            if i == 88:
                get_boundingbox = 0
            if get_boundingbox == 1:
                bounding_box[0, cont_boundingbox] = int(line.strip())
                cont_boundingbox += 1
     
    lefteye = [left_pupil[0, 0], left_pupil[0, 1], left_pupil[0, 2]]
    righteye = [right_pupil[0, 0], right_pupil[0, 1], right_pupil[0, 2]]
    
    if cont_boundingbox > 0:
        boundingbox = [bounding_box[0, 0], bounding_box[0, 1], bounding_box[0, 2], bounding_box[0, 3]]    
    else:
        boundingbox = [0, 0, 0, 0]
    
    if lefteye[2] < 0 and righteye[2] > 0:
        lefteye[2] = righteye[2]           
        x_eye = shape[42:47, 0]
        y_eye = shape[42:47, 1]
        lefteye[0] = int(np.round(np.mean(x_eye), 0))
        lefteye[1] = int(np.round(np.mean(y_eye), 0))
         
    if righteye[2] < 0 and lefteye[2] > 0:
        righteye[2] = lefteye[2]
        x_eye = shape[36:41, 0]
        y_eye = shape[36:41, 1]
        righteye[0] = int(np.round(np.mean(x_eye), 0))
        righteye[1] = int(np.round(np.mean(y_eye), 0))
            
    if righteye[2] < 0 and lefteye[2] < 0:
        x_eye = shape[42:47, 0]
        y_eye = shape[42:47, 1]
        lefteye[0] = int(np.round(np.mean(x_eye), 0))
        lefteye[1] = int(np.round(np.mean(y_eye), 0))
        lefteye[2] = int(np.round((shape[45, 0] - lefteye[0]) / 2))
        
        x_eye = shape[36:41, 0]
        y_eye = shape[36:41, 1]
        righteye[0] = int(np.round(np.mean(x_eye), 0))
        righteye[1] = int(np.round(np.mean(y_eye), 0))
        righteye[2] = int(np.round((shape[39, 0] - righteye[0]) / 2))
           
    return shape, lefteye, righteye, boundingbox

def get_landmark_size(shape):
    if shape[36, 1] != -1 and shape[39, 1] != -1:
        size_landmarks = np.round(0.025 * np.sqrt((shape[39, 0] - shape[36, 0])**2 + (shape[39, 1] - shape[36, 1])**2), 0)
        size_landmarks = int(np.floor(size_landmarks))
    else:
        size_landmarks = np.round(0.025 * np.sqrt((shape[42, 0] - shape[45, 0])**2 + (shape[42, 1] - shape[45, 1])**2), 0)
        size_landmarks = int(np.floor(size_landmarks))  
    return size_landmarks

def mark_picture(image, shape, circle_left, circle_right, points=None, size_landmarks=None):
    h, w, _ = image.shape
    
    if points is not None:
        if h < 1000:
            cv2.line(image, points[0], points[1], (0, 255, 0), 2)        
            cv2.line(image, points[2], points[3], (0, 255, 0), 2)
            cv2.line(image, points[4], points[5], (0, 255, 0), 2)
        else:
            cv2.line(image, points[0], points[1], (0, 255, 0), 4)        
            cv2.line(image, points[2], points[3], (0, 255, 0), 4)
            cv2.line(image, points[4], points[5], (0, 255, 0), 4)
    
    aux = 1
    if size_landmarks is None:
        if shape[36, 1] != -1 and shape[39, 1] != -1:
            size_landmarks = np.round(0.025 * np.sqrt((shape[39, 0] - shape[36, 0])**2 + (shape[39, 1] - shape[36, 1])**2), 0)
            size_landmarks = int(np.floor(size_landmarks))
        else:
            size_landmarks = np.round(0.025 * np.sqrt((shape[42, 0] - shape[45, 0])**2 + (shape[42, 1] - shape[45, 1])**2), 0)
            size_landmarks = int(np.floor(size_landmarks))
    
    for (x, y) in shape:
        if x > 0:
            if aux == 62 or aux == 64 or aux == 38 or aux == 39 or aux == 44 or aux == 45:
                cv2.circle(image, (x, y), size_landmarks, (0, 255, 255), -1)
            elif aux == 63:
                cv2.circle(image, (x, y), size_landmarks + 1, (0, 255, 255), -1)
            elif aux == 67:
                cv2.circle(image, (x, y), size_landmarks + 1, (0, 0, 255), -1)
            else:
                cv2.circle(image, (x, y), size_landmarks, (0, 0, 255), -1)
            cv2.putText(image, str(aux), (x - 2, y - 2), cv2.FONT_HERSHEY_DUPLEX, 0.125 * size_landmarks, (0, 0, 0), 1)
        aux += 1
    
    if circle_left[2] > 0:
        if h < 1000:
            cv2.circle(image, (int(circle_left[0]), int(circle_left[1])), int(circle_left[2]), (0, 255, 0), 1)
        else:
            cv2.circle(image, (int(circle_left[0]), int(circle_left[1])), int(circle_left[2]), (0, 255, 0), 2)
        cv2.circle(image, (int(circle_left[0]), int(circle_left[1])), int(circle_left[2] // 4), (0, 255, 0), -1)
    
    if circle_right[2] > 0:
        if h < 1000:
            cv2.circle(image, (int(circle_right[0]), int(circle_right[1])), int(circle_right[2]), (0, 255, 0), 1)
        else:
            cv2.circle(image, (int(circle_right[0]), int(circle_right[1])), int(circle_right[2]), (0, 255, 0), 2)
        cv2.circle(image, (int(circle_right[0]), int(circle_right[1])), int(circle_right[2] // 4), (0, 255, 0), -1)
    
    return image

def estimate_lines(InputImage, circle_left, circle_right):
    h, w, _ = InputImage.shape
    x_1 = circle_right[0]
    y_1 = circle_right[1]
    x_2 = circle_left[0]
    y_2 = circle_left[1]
    
    x_m = ((x_2 - x_1) / 2) + x_1
    m = (y_2 - y_1) / (x_2 - x_1)
    y_m = y_1 + m * (x_m - x_1)
    x_m = int(round(x_m, 0))
    y_m = int(round(y_m, 0))
    angle = np.arctan(m) + np.pi / 2
    
    x_p1 = int(round(x_m + 0.5 * h * np.cos(angle)))
    y_p1 = int(round(y_m + 0.5 * h * np.sin(angle)))
    x_p2 = int(round(x_m - 0.25 * h * np.cos(angle)))
    y_p2 = int(round(y_m - 0.25 * h * np.sin(angle)))
    
    points = [(x_1, y_1), (x_2, y_2), (x_m, y_m), (x_p1, y_p1), (x_m, y_m), (x_p2, y_p2)]
    return points

def find_circle_from_points(x, y):
    x_m = np.mean(x)
    y_m = np.mean(y)
    u = x - x_m
    v = y - y_m
    Suv = sum(u * v)
    Suu = sum(u ** 2)
    Svv = sum(v ** 2)
    Suuv = sum(u ** 2 * v)
    Suvv = sum(u * v ** 2)
    Suuu = sum(u ** 3)
    Svvv = sum(v ** 3)
    
    A = np.array([[Suu, Suv], [Suv, Svv]])
    B = np.array([Suuu + Suvv, Svvv + Suuv]) / 2.0
    uc, vc = linalg.solve(A, B)
    xc_1 = x_m + uc
    yc_1 = y_m + vc
    Ri_1 = np.sqrt((x - xc_1) ** 2 + (y - yc_1) ** 2)
    R_1 = np.mean(Ri_1)
    circle = [int(xc_1), int(yc_1), int(R_1)]
    return circle

def save_snaptshot_to_file(image, name):
    # Используем универсальную функцию для записи с поддержкой Unicode
    imwrite_unicode(name, image)

def save_txt_file(file_name, shape, circle_left, circle_right, boundingbox):
    file_no_ext = file_name[0:-4]
    delimiter = os.path.sep
    temp = file_name.split(delimiter)
    photo_name = temp[-1]
    
    # Временные файлы
    np.savetxt(file_no_ext + '_temp_shape.txt', shape, delimiter=',', fmt='%i', newline='\r')
    np.savetxt(file_no_ext + '_temp_circle_left.txt', circle_left, delimiter=',', fmt='%i', newline='\r')
    np.savetxt(file_no_ext + '_temp_circle_right.txt', circle_right, delimiter=',', fmt='%i', newline='\r')
    np.savetxt(file_no_ext + '_temp_boundingbox.txt', boundingbox, delimiter=',', fmt='%i', newline='\r')
    
    if os.path.isfile(file_no_ext + '.txt'):
        os.remove(file_no_ext + '.txt')
    
    # Запись с кодировкой UTF-8
    with open(file_no_ext + '.txt', 'a', encoding='utf-8') as f:
        f.write('# Имя файла { \n')
        f.write(photo_name)
        f.write('\n# } \n')
        f.write('# 68 лицевых ориентиров [x,y] { \n')
        with open(file_no_ext + '_temp_shape.txt', 'r', encoding='utf-8') as temp_f:
            f.write(temp_f.read())
        f.write('# } \n')
        f.write('# Левая радужка [x,y,r] { \n')
        with open(file_no_ext + '_temp_circle_left.txt', 'r', encoding='utf-8') as temp_f:
            f.write(temp_f.read())
        f.write('# } \n')
        f.write('# Правая радужка [x,y,r] { \n')
        with open(file_no_ext + '_temp_circle_right.txt', 'r', encoding='utf-8') as temp_f:
            f.write(temp_f.read())
        f.write('# } \n')
        f.write('# Ограничивающая рамка лица [top(x), left(y), width, height] { \n')
        with open(file_no_ext + '_temp_boundingbox.txt', 'r', encoding='utf-8') as temp_f:
            f.write(temp_f.read())
        f.write('# }')
    
    os.remove(file_no_ext + '_temp_shape.txt')
    os.remove(file_no_ext + '_temp_circle_left.txt')
    os.remove(file_no_ext + '_temp_circle_right.txt')
    os.remove(file_no_ext + '_temp_boundingbox.txt')

def save_xls_file(file_name, MeasurementsLeft, MeasurementsRight, MeasurementsDeviation, MeasurementsPercentual):
    file_no_ext = file_name[0:-4]
    delimiter = os.path.sep
    temp = file_name.split(delimiter)
    photo_name = temp[-1]
    
    number_of_measurements = 9
    Columns = ['Правая сторона', 'Левая сторона', 'Разница (абс.)', 'Разница (%)']
    Columns = Columns * number_of_measurements
    
    temp_names = ['Высота брови', 'Рефлекс MRD1', 'Рефлекс MRD2', 
                  'Смещение комиссуры', 'Отклонение высоты комиссуры', 'Угол улыбки',
                  'Отклонение высоты верхней губы', 'Видимость зубов', 'Отклонение высоты нижней губы']
    number_of_repetitions = 4
    Header = [item for item in temp_names for i in range(number_of_repetitions)]
    
    elements = ['BH', 'MRD1', 'MRD2', 'CE', 'CH', 'SA', 'UVH', 'DS', 'LVH']
    BH = np.array([[MeasurementsRight.BrowHeight, MeasurementsLeft.BrowHeight, MeasurementsDeviation.BrowHeight, MeasurementsPercentual.BrowHeight]], dtype=object)
    MRD1 = np.array([[MeasurementsRight.MarginalReflexDistance1, MeasurementsLeft.MarginalReflexDistance1, MeasurementsDeviation.MarginalReflexDistance1, MeasurementsPercentual.MarginalReflexDistance1]], dtype=object)
    MRD2 = np.array([[MeasurementsRight.MarginalReflexDistance2, MeasurementsLeft.MarginalReflexDistance2, MeasurementsDeviation.MarginalReflexDistance2, MeasurementsPercentual.MarginalReflexDistance2]], dtype=object)
    CE = np.array([[MeasurementsRight.CommissureExcursion, MeasurementsLeft.CommissureExcursion, MeasurementsDeviation.CommissureExcursion, MeasurementsPercentual.CommissureExcursion]], dtype=object)
    CH = np.array([['', '', MeasurementsDeviation.CommisureHeightDeviation, '']], dtype=object)
    SA = np.array([[MeasurementsRight.SmileAngle, MeasurementsLeft.SmileAngle, MeasurementsDeviation.SmileAngle, MeasurementsPercentual.SmileAngle]], dtype=object)
    UVH = np.array([['', '', MeasurementsDeviation.UpperLipHeightDeviation, '']], dtype=object)
    DS = np.array([[MeasurementsRight.DentalShow, MeasurementsLeft.DentalShow, MeasurementsDeviation.DentalShow, MeasurementsPercentual.DentalShow]], dtype=object)
    LVH = np.array([['', '', MeasurementsDeviation.LowerLipHeightDeviation, '']], dtype=object)
    
    fill = BH
    for i in elements:
        if i != 'BH':
            fill = np.append(fill, eval(i), axis=1)
    
    Index = [photo_name]
    df = pd.DataFrame(fill, index=Index, columns=Columns)
    df.columns = pd.MultiIndex.from_tuples(list(zip(Header, df.columns)))
    df.to_excel(file_no_ext + '.xlsx', index=True)

def save_xls_file_patient(path, Patient, CalibrationType, CalibrationValue):
    number_of_measurements = 9
    Columns = ['Правая сторона', 'Левая сторона', 'Разница (абс.)', 'Разница (%)']
    Columns = Columns * number_of_measurements
    
    temp_names = ['Высота брови', 'Рефлекс MRD1', 'Рефлекс MRD2', 
                  'Смещение комиссуры', 'Отклонение высоты комиссуры', 'Угол улыбки',
                  'Отклонение высоты верхней губы', 'Видимость зубов', 'Отклонение высоты нижней губы']
    number_of_repetitions = 4
    Header = [item for item in temp_names for i in range(number_of_repetitions)]
    
    elements = ['BH', 'MRD1', 'MRD2', 'CE', 'CH', 'SA', 'UVH', 'DS', 'LVH']
    
    # Первое фото
    MeasurementsLeftFirst, MeasurementsRightFirst, MeasurementsDeviation, MeasurementsPercentual = get_measurements_from_data(
        Patient.FirstPhoto._shape, Patient.FirstPhoto._lefteye, Patient.FirstPhoto._righteye, CalibrationType, CalibrationValue)
    
    BH = np.array([[MeasurementsRightFirst.BrowHeight, MeasurementsLeftFirst.BrowHeight, MeasurementsDeviation.BrowHeight, MeasurementsPercentual.BrowHeight]], dtype=object)
    MRD1 = np.array([[MeasurementsRightFirst.MarginalReflexDistance1, MeasurementsLeftFirst.MarginalReflexDistance1, MeasurementsDeviation.MarginalReflexDistance1, MeasurementsPercentual.MarginalReflexDistance1]], dtype=object)
    MRD2 = np.array([[MeasurementsRightFirst.MarginalReflexDistance2, MeasurementsLeftFirst.MarginalReflexDistance2, MeasurementsDeviation.MarginalReflexDistance2, MeasurementsPercentual.MarginalReflexDistance2]], dtype=object)
    CE = np.array([[MeasurementsRightFirst.CommissureExcursion, MeasurementsLeftFirst.CommissureExcursion, MeasurementsDeviation.CommissureExcursion, MeasurementsPercentual.CommissureExcursion]], dtype=object)
    CH = np.array([['', '', MeasurementsDeviation.CommisureHeightDeviation, '']], dtype=object)
    SA = np.array([[MeasurementsRightFirst.SmileAngle, MeasurementsLeftFirst.SmileAngle, MeasurementsDeviation.SmileAngle, MeasurementsPercentual.SmileAngle]], dtype=object)
    UVH = np.array([['', '', MeasurementsDeviation.UpperLipHeightDeviation, '']], dtype=object)
    DS = np.array([[MeasurementsRightFirst.DentalShow, MeasurementsLeftFirst.DentalShow, MeasurementsDeviation.DentalShow, MeasurementsPercentual.DentalShow]], dtype=object)
    LVH = np.array([['', '', MeasurementsDeviation.LowerLipHeightDeviation, '']], dtype=object)
    
    fillFirst = BH
    for i in elements:
        if i != 'BH':
            fillFirst = np.append(fillFirst, eval(i), axis=1)
    
    # Второе фото
    MeasurementsLeftSecond, MeasurementsRightSecond, MeasurementsDeviation, MeasurementsPercentual = get_measurements_from_data(
        Patient.SecondPhoto._shape, Patient.SecondPhoto._lefteye, Patient.SecondPhoto._righteye, CalibrationType, CalibrationValue)
    
    BH = np.array([[MeasurementsRightSecond.BrowHeight, MeasurementsLeftSecond.BrowHeight, MeasurementsDeviation.BrowHeight, MeasurementsPercentual.BrowHeight]], dtype=object)
    MRD1 = np.array([[MeasurementsRightSecond.MarginalReflexDistance1, MeasurementsLeftSecond.MarginalReflexDistance1, MeasurementsDeviation.MarginalReflexDistance1, MeasurementsPercentual.MarginalReflexDistance1]], dtype=object)
    MRD2 = np.array([[MeasurementsRightSecond.MarginalReflexDistance2, MeasurementsLeftSecond.MarginalReflexDistance2, MeasurementsDeviation.MarginalReflexDistance2, MeasurementsPercentual.MarginalReflexDistance2]], dtype=object)
    CE = np.array([[MeasurementsRightSecond.CommissureExcursion, MeasurementsLeftSecond.CommissureExcursion, MeasurementsDeviation.CommissureExcursion, MeasurementsPercentual.CommissureExcursion]], dtype=object)
    CH = np.array([['', '', MeasurementsDeviation.CommisureHeightDeviation, '']], dtype=object)
    SA = np.array([[MeasurementsRightSecond.SmileAngle, MeasurementsLeftSecond.SmileAngle, MeasurementsDeviation.SmileAngle, MeasurementsPercentual.SmileAngle]], dtype=object)
    UVH = np.array([['', '', MeasurementsDeviation.UpperLipHeightDeviation, '']], dtype=object)
    DS = np.array([[MeasurementsRightSecond.DentalShow, MeasurementsLeftSecond.DentalShow, MeasurementsDeviation.DentalShow, MeasurementsPercentual.DentalShow]], dtype=object)
    LVH = np.array([['', '', MeasurementsDeviation.LowerLipHeightDeviation, '']], dtype=object)
    
    fillSecond = BH
    for i in elements:
        if i != 'BH':
            fillSecond = np.append(fillSecond, eval(i), axis=1)
    
    # Разница
    BH = np.array([[MeasurementsRightFirst.BrowHeight - MeasurementsRightSecond.BrowHeight, 
                    MeasurementsLeftFirst.BrowHeight - MeasurementsLeftSecond.BrowHeight, '', '']], dtype=object)
    MRD1 = np.array([[MeasurementsRightFirst.MarginalReflexDistance1 - MeasurementsRightSecond.MarginalReflexDistance1,
                      MeasurementsLeftFirst.MarginalReflexDistance1 - MeasurementsLeftSecond.MarginalReflexDistance1, '', '']], dtype=object)
    MRD2 = np.array([[MeasurementsRightFirst.MarginalReflexDistance2 - MeasurementsRightSecond.MarginalReflexDistance2,
                      MeasurementsLeftFirst.MarginalReflexDistance2 - MeasurementsLeftSecond.MarginalReflexDistance2, '', '']], dtype=object)
    CE = np.array([[MeasurementsRightFirst.CommissureExcursion - MeasurementsRightSecond.CommissureExcursion,
                    MeasurementsLeftFirst.CommissureExcursion - MeasurementsLeftSecond.CommissureExcursion, '', '']], dtype=object)
    CH = np.array([['', '', '', '']], dtype=object)
    SA = np.array([[MeasurementsRightFirst.SmileAngle - MeasurementsRightSecond.SmileAngle,
                    MeasurementsLeftFirst.SmileAngle - MeasurementsLeftSecond.SmileAngle, '', '']], dtype=object)
    UVH = np.array([['', '', '', '']], dtype=object)
    DS = np.array([[MeasurementsRightFirst.DentalShow - MeasurementsRightSecond.DentalShow,
                    MeasurementsLeftFirst.DentalShow - MeasurementsLeftSecond.DentalShow, '', '']], dtype=object)
    LVH = np.array([['', '', '', '']], dtype=object)
    
    fillDifference = BH
    for i in elements:
        if i != 'BH':
            fillDifference = np.append(fillDifference, eval(i), axis=1)
    
    Index = [Patient.FirstPhoto._ID, Patient.SecondPhoto._ID, 'Разница']
    df = pd.DataFrame(np.vstack((fillFirst, fillSecond, fillDifference)), index=Index, columns=Columns)
    df.columns = pd.MultiIndex.from_tuples(list(zip(Header, df.columns)))
    
    delimiter = os.path.sep
    temp = path.split(delimiter)
    path_dir = temp[:-1]
    path_dir = delimiter.join(path_dir)
    file_name = path_dir + delimiter + Patient.patient_ID + '.xlsx'
    df.to_excel(file_name, index=True)
