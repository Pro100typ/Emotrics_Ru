import os
import sys
import shutil
import re
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QGridLayout, QFileDialog, QDialog, QComboBox, QGroupBox, QCheckBox, QScrollArea
import ctypes
from PIL import Image
from PIL.ExifTags import TAGS
import cv2

from utilities import save_txt_file, mark_picture, get_landmark_size, imread_unicode, imwrite_unicode
from measurements import get_measurements_from_data

# ------------------ safe_path ------------------
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

def get_date_from_image(image_path):
    try:
        img = Image.open(image_path)
        exif = img.getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    date_str = value.split()[0]
                    year, month, day = date_str.split(':')
                    return QtCore.QDate(int(year), int(month), int(day))
    except Exception:
        pass
    return QtCore.QDate.currentDate()

def sanitize_filename(name):
    """Очищает строку для использования в имени файла (удаляет недопустимые символы, заменяет пробелы на _)."""
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    name = re.sub(r'[\s]+', '_', name)
    name = name.strip('_')
    return name

# ----------------------------------------------------------------------
# Класс для сохранения одной фотографии
# ----------------------------------------------------------------------
class SaveWindow(QDialog):
    def __init__(self, parent=None, file_name=None, 
                 MeasurementsLeft=None, MeasurementsRight=None,
                 MeasurementsDeviation=None, MeasurementsPercentual=None,
                 image_path=None, shape=None, left_eye=None, right_eye=None, boundingbox=None,
                 points=None, landmark_size=None):
        super(SaveWindow, self).__init__(parent)
        
        self._original_image_path = image_path
        self._shape = shape
        self._left_eye = left_eye
        self._right_eye = right_eye
        self._boundingbox = boundingbox
        self._points = points
        self._landmark_size = landmark_size
        
        if image_path:
            self._selected_folder = os.path.dirname(image_path)
        else:
            self._selected_folder = os.getcwd()
        
        self._MeasurementsLeft = MeasurementsLeft
        self._MeasurementsRight = MeasurementsRight
        self._MeasurementsDeviation = MeasurementsDeviation
        self._MeasurementsPercentual = MeasurementsPercentual
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Сохранить результаты')
        self.setWindowIcon(QtGui.QIcon(safe_path(os.path.join('include', 'icon_color', 'save_icon.ico'))))
        
        # --- Выбор папки ---
        folder_label = QLabel('Папка для сохранения:')
        self.folder_edit = QLineEdit(self)
        self.folder_edit.setText(self._selected_folder)
        self.folder_edit.setReadOnly(True)
        self.folder_button = QPushButton('Выбрать папку', self)
        self.folder_button.clicked.connect(self.select_target_folder)
        
        folder_layout = QGridLayout()
        folder_layout.addWidget(folder_label, 0, 0)
        folder_layout.addWidget(self.folder_edit, 0, 1)
        folder_layout.addWidget(self.folder_button, 0, 2)
        folder_box = QGroupBox('Целевая папка')
        folder_box.setLayout(folder_layout)
        
        # --- Информация о пациенте ---
        patient_box = QGroupBox('Информация о пациенте')
        patient_layout = QGridLayout()
              
        self.fullname_edit = QLineEdit(self)
        patient_layout.addWidget(QLabel('ФИО пациента:'), 1, 0)
        patient_layout.addWidget(self.fullname_edit, 1, 1)
        
        self.birthdate_edit = QtWidgets.QDateEdit(self)
        self.birthdate_edit.setCalendarPopup(True)
        self.birthdate_edit.setDisplayFormat('dd.MM.yyyy')
        self.birthdate_edit.setDate(QtCore.QDate())
        self.birthdate_edit.setSpecialValueText(" ")
        patient_layout.addWidget(QLabel('Дата рождения:'), 2, 0)
        patient_layout.addWidget(self.birthdate_edit, 2, 1)
        
        self.shooting_date_edit = QtWidgets.QDateEdit(self)
        self.shooting_date_edit.setCalendarPopup(True)
        self.shooting_date_edit.setDisplayFormat('dd.MM.yyyy')
        if self._original_image_path and os.path.exists(self._original_image_path):
            exif_date = get_date_from_image(self._original_image_path)
            self.shooting_date_edit.setDate(exif_date)
        else:
            self.shooting_date_edit.setDate(QtCore.QDate.currentDate())
        patient_layout.addWidget(QLabel('Дата съёмки:'), 3, 0)
        patient_layout.addWidget(self.shooting_date_edit, 3, 1)
        
        self.diagnosis_edit = QLineEdit(self)
        patient_layout.addWidget(QLabel('Диагноз:'), 4, 0)
        patient_layout.addWidget(self.diagnosis_edit, 4, 1)
        
        self.consent_file_edit = QLineEdit(self)
        self.consent_file_edit.setReadOnly(True)
        consent_button = QPushButton('Выбрать файл согласия', self)
        consent_button.clicked.connect(self.load_consent_file)
        patient_layout.addWidget(QLabel('Скан согласия:'), 5, 0)
        patient_layout.addWidget(consent_button, 5, 1)
        patient_layout.addWidget(self.consent_file_edit, 6, 0, 1, 2)
        
        patient_box.setLayout(patient_layout)
        
        # --- Клиническая информация ---
        clinical_box = QGroupBox('Клиническая информация')
        clinical_layout = QGridLayout()
        
        self.pre_post_combo = QComboBox()
        self.pre_post_combo.addItems(['', 'До процедуры', 'После процедуры'])
        clinical_layout.addWidget(QLabel('До/после процедуры:'), 0, 0)
        clinical_layout.addWidget(self.pre_post_combo, 0, 1)
        
        self.surgery_edit = QLineEdit(self)
        clinical_layout.addWidget(QLabel('Процедура:'), 1, 0)
        clinical_layout.addWidget(self.surgery_edit, 1, 1)
        
        self.expression_edit = QLineEdit(self)
        clinical_layout.addWidget(QLabel('Выражение лица:'), 2, 0)
        clinical_layout.addWidget(self.expression_edit, 2, 1)
        
        self.comments_edit = QLineEdit(self)
        clinical_layout.addWidget(QLabel('Доп. комментарии:'), 3, 0)
        clinical_layout.addWidget(self.comments_edit, 3, 1)
        
        clinical_box.setLayout(clinical_layout)
        
        # --- Чекбоксы для выбора сохраняемых файлов ---
        self.save_original_checkbox = QCheckBox('Сохранить исходное фото')
        self.save_original_checkbox.setChecked(False)
        self.save_marked_checkbox = QCheckBox('Сохранить размеченное фото')
        self.save_marked_checkbox.setChecked(False)
        self.export_txt_checkbox = QCheckBox('Экспортировать координаты разметки лица')
        self.export_txt_checkbox.setChecked(False)
        
        # --- Кнопки ---
        save_btn = QPushButton('Сохранить всё', self)
        save_btn.clicked.connect(self.save_all)
        cancel_btn = QPushButton('Отмена', self)
        cancel_btn.clicked.connect(self.close)
        
        btn_layout = QGridLayout()
        btn_layout.addWidget(save_btn, 0, 0, QtCore.Qt.AlignCenter)
        btn_layout.addWidget(cancel_btn, 0, 1, QtCore.Qt.AlignCenter)
        
        # --- Общий layout ---
        main_layout = QGridLayout()
        main_layout.addWidget(folder_box, 0, 0)
        main_layout.addWidget(patient_box, 1, 0)
        main_layout.addWidget(clinical_box, 2, 0)
        main_layout.addWidget(self.save_original_checkbox, 3, 0)
        main_layout.addWidget(self.save_marked_checkbox, 4, 0)
        main_layout.addWidget(self.export_txt_checkbox, 5, 0)
        main_layout.addLayout(btn_layout, 6, 0)
        self.setLayout(main_layout)
        self.resize(600, 650)
    
    def select_target_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Выберите папку для сохранения')
        if folder:
            self.folder_edit.setText(os.path.normpath(folder))
    
    def load_consent_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Выберите файл согласия', '',
            'Все поддерживаемые файлы (*.png *.jpg *.jpeg *.tif *.tiff *.pdf)'
        )
        if file_path:
            self.consent_file_edit.setText(file_path)
    
    def copy_file(self, src, dst):
        try:
            shutil.copy2(safe_path(src), safe_path(dst))
            return True
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', f'Не удалось скопировать файл:\n{e}')
            return False
    
    def check_overwrite(self, files_list):
        existing = [f for f in files_list if os.path.exists(f['path'])]
        if not existing:
            return True
        msg = "Следующие файлы уже существуют:\n"
        for f in existing:
            msg += f"- {f['description']}: {os.path.basename(f['path'])}\n"
        msg += "\nПерезаписать их?"
        reply = QtWidgets.QMessageBox.question(
            self, 'Файлы существуют', msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        return reply == QtWidgets.QMessageBox.Yes
    
    def save_all(self):
        target_folder = self.folder_edit.text()
        if not target_folder or not os.path.exists(target_folder):
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Укажите существующую папку для сохранения')
            return
        
        fullname = self.fullname_edit.text().strip()
        if not fullname:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Введите ФИО пациента перед сохранением')
            return
        
        safe_name = sanitize_filename(fullname)
        
        # Собираем список всех файлов, которые будут созданы
        files_to_check = []
        
        # Исходное фото
        original_photo_path = ''
        if self.save_original_checkbox.isChecked() and self._original_image_path and os.path.exists(self._original_image_path):
            photo_ext = os.path.splitext(self._original_image_path)[1]
            photo_dest_name = safe_name + photo_ext
            original_photo_path = os.path.join(target_folder, photo_dest_name)
            files_to_check.append({'path': original_photo_path, 'description': 'исходное фото'})
        
        # Размеченное фото
        marked_photo_path = ''
        if self.save_marked_checkbox.isChecked() and self._shape is not None and self._original_image_path:
            marked_ext = os.path.splitext(self._original_image_path)[1]
            marked_dest_name = safe_name + '_размеченное' + marked_ext
            marked_photo_path = os.path.join(target_folder, marked_dest_name)
            files_to_check.append({'path': marked_photo_path, 'description': 'размеченное фото'})
        
        # TXT-файл
        if self.export_txt_checkbox.isChecked() and self._shape is not None:
            txt_path = os.path.join(target_folder, safe_name + '.txt')
            files_to_check.append({'path': txt_path, 'description': 'файл координат (.txt)'})
        
        # Файл согласия
        consent_src = self.consent_file_edit.text()
        consent_dest_fullpath = ''
        if consent_src and os.path.exists(consent_src):
            consent_ext = os.path.splitext(consent_src)[1]
            consent_dest_name = safe_name + '_согласие' + consent_ext
            consent_dest_fullpath = os.path.join(target_folder, consent_dest_name)
            files_to_check.append({'path': consent_dest_fullpath, 'description': 'скан согласия'})
        
        # Excel-файл
        excel_path = os.path.join(target_folder, safe_name + '_метрики.xlsx')
        files_to_check.append({'path': excel_path, 'description': 'Excel-отчёт'})
        
        # Проверяем существование и запрашиваем перезапись
        if not self.check_overwrite(files_to_check):
            return
        
        # --- Сохранение ---
        error_occurred = False
        
        # 1. Исходное фото
        if self.save_original_checkbox.isChecked() and self._original_image_path and os.path.exists(self._original_image_path):
            if not self.copy_file(self._original_image_path, original_photo_path):
                error_occurred = True
        
        # 2. Размеченное фото
        if self.save_marked_checkbox.isChecked() and self._shape is not None and self._original_image_path:
            temp_image = imread_unicode(self._original_image_path)
            if temp_image is not None:
                if self._landmark_size is None:
                    self._landmark_size = get_landmark_size(self._shape)
                marked_img = mark_picture(temp_image, self._shape, self._left_eye, self._right_eye,
                                          self._points, self._landmark_size)
                marked_ext = os.path.splitext(self._original_image_path)[1]
                success, encoded = cv2.imencode(marked_ext, marked_img)
                if success:
                    with open(safe_path(marked_photo_path), 'wb') as f:
                        f.write(encoded.tobytes())
                else:
                    QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Не удалось сохранить размеченное фото')
                    error_occurred = True
            else:
                QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Не удалось прочитать исходное изображение для создания размеченной копии')
                error_occurred = True
        
        # 3. TXT-файл
        if self.export_txt_checkbox.isChecked() and self._shape is not None:
            txt_path = os.path.join(target_folder, safe_name + '.txt')
            try:
                save_txt_file(txt_path, self._shape, self._left_eye, self._right_eye, self._boundingbox)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, 'Ошибка', f'Не удалось сохранить TXT-файл:\n{e}')
                error_occurred = True
        
        # 4. Копируем файл согласия
        if consent_src and os.path.exists(consent_src):
            if not self.copy_file(consent_src, consent_dest_fullpath):
                error_occurred = True
        
        # 5. Excel
        if not self.save_excel(excel_path, original_photo_path, marked_photo_path, consent_dest_fullpath, safe_name):
            error_occurred = True
        
        if error_occurred:
            return  # не показываем успех, окно остаётся открытым
        
        QtWidgets.QMessageBox.information(self, 'Успех', f'Все выбранные файлы сохранены в папку:\n{target_folder}')
        self.accept()
    
    def save_excel(self, excel_path, original_photo_path, marked_photo_path, consent_path, safe_name):
        try:
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                ML = self._MeasurementsLeft
                MR = self._MeasurementsRight
                MD = self._MeasurementsDeviation
                MP = self._MeasurementsPercentual
                
                metrics = [
                    ('Высота брови', MR.BrowHeight, ML.BrowHeight, MD.BrowHeight, MP.BrowHeight),
                    ('Расстояние от зрачка до верхнего века', MR.MarginalReflexDistance1, ML.MarginalReflexDistance1, MD.MarginalReflexDistance1, MP.MarginalReflexDistance1),
                    ('Расстояние от зрачка до нижнего века', MR.MarginalReflexDistance2, ML.MarginalReflexDistance2, MD.MarginalReflexDistance2, MP.MarginalReflexDistance2),
                    ('Высота глазной щели', MR.PalpebralFissureHeight, ML.PalpebralFissureHeight, MD.PalpebralFissureHeight, MP.PalpebralFissureHeight),
                    ('Расстояние от средней линии губы до угла рта', MR.CommissureExcursion, ML.CommissureExcursion, MD.CommissureExcursion, MP.CommissureExcursion),
                    ('Асимметрия стояния углов рта', '', '', MD.CommisureHeightDeviation, ''),
                    ('Угол улыбки', MR.SmileAngle, ML.SmileAngle, MD.SmileAngle, MP.SmileAngle),
                    ('Асимметрия стояния верхней губы', '', '', MD.UpperLipHeightDeviation, ''),
                    ('Высота обнажения зубов при улыбке', MR.DentalShow, ML.DentalShow, MD.DentalShow, MP.DentalShow),
                    ('Асимметрия стояния нижней губы', '', '', MD.LowerLipHeightDeviation, '')
                ]
                
                rows = []
                for name, right_val, left_val, abs_diff, perc_diff in metrics:
                    rows.append([name, right_val, left_val, abs_diff, perc_diff])
                
                df_metrics = pd.DataFrame(rows, columns=['Метрика', 'Правая сторона', 'Левая сторона', 'Разница (абс.)', 'Разница (%)'])
                
                info_data = {
                    'Параметр': [
                        'ФИО пациента', 'Дата рождения', 'Дата съёмки', 'Диагноз',
                        'До/после процедуры', 'Процедура', 'Выражение лица', 'Доп. комментарии',
                        'Путь к исходному фото', 'Путь к размеченному фото', 'Путь к согласию'
                    ],
                    'Значение': [
                        self.fullname_edit.text(),
                        self.birthdate_edit.date().toString('dd.MM.yyyy'),
                        self.shooting_date_edit.date().toString('dd.MM.yyyy'),
                        self.diagnosis_edit.text(),
                        self.pre_post_combo.currentText(),
                        self.surgery_edit.text(),
                        self.expression_edit.text(),
                        self.comments_edit.text(),
                        original_photo_path,
                        marked_photo_path,
                        consent_path
                    ]
                }
                df_info = pd.DataFrame(info_data)
                
                df_metrics.to_excel(writer, sheet_name='Метрики', index=False)
                df_info.to_excel(writer, sheet_name='Информация', index=False)
                
                worksheet_metrics = writer.sheets['Метрики']
                worksheet_metrics.set_column(0, 0, 40)
                worksheet_metrics.set_column(1, 1, 14)
                worksheet_metrics.set_column(2, 5, 13)
                
                worksheet_info = writer.sheets['Информация']
                worksheet_info.set_column(0, 0, 30)
                worksheet_info.set_column(1, 1, 60)
                
            return True
        except PermissionError:
            QtWidgets.QMessageBox.warning(
                self, 'Ошибка',
                f'Не удалось сохранить Excel-файл.\nВозможно, файл уже открыт в другой программе.\n'
                f'Закройте файл и повторите попытку.\nПуть: {excel_path}'
            )
            return False
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', f'Не удалось сохранить Excel-файл:\n{e}')
            return False


# ----------------------------------------------------------------------
# Класс для сохранения пациента (две фотографии)
# ----------------------------------------------------------------------
class SavePatientWindow(QDialog):
    def __init__(self, parent=None, patient=None, calibration_type='Iris', calibration_value=11.77,
                 first_image_path=None, second_image_path=None):
        super(SavePatientWindow, self).__init__(parent)
        
        self._patient = patient
        self._calibration_type = calibration_type
        self._calibration_value = calibration_value
        self._first_image_path = first_image_path
        self._second_image_path = second_image_path
        
        if first_image_path:
            self._selected_folder = os.path.dirname(first_image_path)
        else:
            self._selected_folder = os.getcwd()
        
        self._compute_metrics()
        self.initUI()
    
    def _compute_metrics(self):
        if self._patient is None:
            return
        first = self._patient.FirstPhoto
        second = self._patient.SecondPhoto
        if first._shape is not None and second._shape is not None:
            left1, right1, dev1, perc1 = get_measurements_from_data(
                first._shape, first._lefteye, first._righteye,
                self._calibration_type, self._calibration_value)
            left2, right2, dev2, perc2 = get_measurements_from_data(
                second._shape, second._lefteye, second._righteye,
                self._calibration_type, self._calibration_value)
            self._metrics_first = (left1, right1, dev1, perc1)
            self._metrics_second = (left2, right2, dev2, perc2)
        else:
            self._metrics_first = None
            self._metrics_second = None
    
    def initUI(self):
        self.setWindowTitle('Сохранить данные пациента')
        self.setWindowIcon(QtGui.QIcon(safe_path(os.path.join('include', 'icon_color', 'save_icon.ico'))))
        
        # --- Выбор папки ---
        folder_label = QLabel('Папка для сохранения:')
        self.folder_edit = QLineEdit(self)
        self.folder_edit.setText(self._selected_folder)
        self.folder_edit.setReadOnly(True)
        self.folder_button = QPushButton('Выбрать папку', self)
        self.folder_button.clicked.connect(self.select_target_folder)
        
        folder_layout = QGridLayout()
        folder_layout.addWidget(folder_label, 0, 0)
        folder_layout.addWidget(self.folder_edit, 0, 1)
        folder_layout.addWidget(self.folder_button, 0, 2)
        folder_box = QGroupBox('Целевая папка')
        folder_box.setLayout(folder_layout)
        
        # --- Общая информация ---
        common_box = QGroupBox('Общая информация о пациенте')
        common_layout = QGridLayout()
        
        self.fullname_edit = QLineEdit(self)
        common_layout.addWidget(QLabel('ФИО пациента:'), 0, 0)
        common_layout.addWidget(self.fullname_edit, 0, 1)
        
        self.birthdate_edit = QtWidgets.QDateEdit(self)
        self.birthdate_edit.setCalendarPopup(True)
        self.birthdate_edit.setDisplayFormat('dd.MM.yyyy')
        self.birthdate_edit.setDate(QtCore.QDate())
        self.birthdate_edit.setSpecialValueText(" ")
        common_layout.addWidget(QLabel('Дата рождения:'), 1, 0)
        common_layout.addWidget(self.birthdate_edit, 1, 1)
        
        self.diagnosis_edit = QLineEdit(self)
        common_layout.addWidget(QLabel('Диагноз:'), 2, 0)
        common_layout.addWidget(self.diagnosis_edit, 2, 1)
        
        self.surgery_edit = QLineEdit(self)
        common_layout.addWidget(QLabel('Процедура:'), 3, 0)
        common_layout.addWidget(self.surgery_edit, 3, 1)
        
        self.consent_file_edit = QLineEdit(self)
        self.consent_file_edit.setReadOnly(True)
        consent_button = QPushButton('Выбрать файл согласия', self)
        consent_button.clicked.connect(self.load_consent_file)
        common_layout.addWidget(QLabel('Скан согласия:'), 4, 0)
        common_layout.addWidget(consent_button, 4, 1)
        common_layout.addWidget(self.consent_file_edit, 5, 0, 1, 2)
        
        common_box.setLayout(common_layout)
        
        # --- Фото ДО ---
        before_box = QGroupBox('Фото ДО процедуры')
        before_layout = QGridLayout()
        
        self.before_date_edit = QtWidgets.QDateEdit(self)
        self.before_date_edit.setCalendarPopup(True)
        self.before_date_edit.setDisplayFormat('dd.MM.yyyy')
        if self._first_image_path and os.path.exists(self._first_image_path):
            exif_date = get_date_from_image(self._first_image_path)
            self.before_date_edit.setDate(exif_date)
        else:
            self.before_date_edit.setDate(QtCore.QDate.currentDate())
        before_layout.addWidget(QLabel('Дата съёмки:'), 0, 0)
        before_layout.addWidget(self.before_date_edit, 0, 1)
        
        self.before_expression_edit = QLineEdit(self)
        before_layout.addWidget(QLabel('Выражение лица:'), 1, 0)
        before_layout.addWidget(self.before_expression_edit, 1, 1)
        
        self.before_comments_edit = QLineEdit(self)
        before_layout.addWidget(QLabel('Комментарий:'), 2, 0)
        before_layout.addWidget(self.before_comments_edit, 2, 1)
        
        before_box.setLayout(before_layout)
        
        # --- Фото ПОСЛЕ ---
        after_box = QGroupBox('Фото ПОСЛЕ процедуры')
        after_layout = QGridLayout()
        
        self.after_date_edit = QtWidgets.QDateEdit(self)
        self.after_date_edit.setCalendarPopup(True)
        self.after_date_edit.setDisplayFormat('dd.MM.yyyy')
        if self._second_image_path and os.path.exists(self._second_image_path):
            exif_date = get_date_from_image(self._second_image_path)
            self.after_date_edit.setDate(exif_date)
        else:
            self.after_date_edit.setDate(QtCore.QDate.currentDate())
        after_layout.addWidget(QLabel('Дата съёмки:'), 0, 0)
        after_layout.addWidget(self.after_date_edit, 0, 1)
        
        self.after_expression_edit = QLineEdit(self)
        after_layout.addWidget(QLabel('Выражение лица:'), 1, 0)
        after_layout.addWidget(self.after_expression_edit, 1, 1)
        
        self.after_comments_edit = QLineEdit(self)
        after_layout.addWidget(QLabel('Комментарий:'), 2, 0)
        after_layout.addWidget(self.after_comments_edit, 2, 1)
        
        after_box.setLayout(after_layout)
        
        # --- Чекбоксы для выбора сохраняемых файлов ---
        self.save_original_checkbox = QCheckBox('Сохранить исходные фото (ДО и ПОСЛЕ)')
        self.save_original_checkbox.setChecked(False)
        self.save_marked_checkbox = QCheckBox('Сохранить размеченные фото (ДО и ПОСЛЕ)')
        self.save_marked_checkbox.setChecked(False)
        self.export_txt_checkbox = QCheckBox('Экспортировать координаты разметки лица (для обоих фото)')
        self.export_txt_checkbox.setChecked(False)
        
        # --- Кнопки ---
        save_btn = QPushButton('Сохранить всё', self)
        save_btn.clicked.connect(self.save_all)
        cancel_btn = QPushButton('Отмена', self)
        cancel_btn.clicked.connect(self.close)
        
        btn_layout = QGridLayout()
        btn_layout.addWidget(save_btn, 0, 0, QtCore.Qt.AlignCenter)
        btn_layout.addWidget(cancel_btn, 0, 1, QtCore.Qt.AlignCenter)
        
        # --- Общий layout с прокруткой ---
        main_widget = QtWidgets.QWidget()
        main_layout = QGridLayout(main_widget)
        main_layout.addWidget(folder_box, 0, 0)
        main_layout.addWidget(common_box, 1, 0)
        main_layout.addWidget(before_box, 2, 0)
        main_layout.addWidget(after_box, 3, 0)
        main_layout.addWidget(self.save_original_checkbox, 4, 0)
        main_layout.addWidget(self.save_marked_checkbox, 5, 0)
        main_layout.addWidget(self.export_txt_checkbox, 6, 0)
        main_layout.addLayout(btn_layout, 7, 0)
        
        scroll = QScrollArea()
        scroll.setWidget(main_widget)
        scroll.setWidgetResizable(True)
        
        container = QGridLayout(self)
        container.addWidget(scroll)
        self.resize(700, 750)
    
    def select_target_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Выберите папку для сохранения')
        if folder:
            self.folder_edit.setText(os.path.normpath(folder))
    
    def load_consent_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Выберите файл согласия', '',
            'Все поддерживаемые файлы (*.png *.jpg *.jpeg *.tif *.tiff *.pdf)'
        )
        if file_path:
            self.consent_file_edit.setText(file_path)
    
    def copy_file(self, src, dst):
        try:
            shutil.copy2(safe_path(src), safe_path(dst))
            return True
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', f'Не удалось скопировать файл:\n{e}')
            return False
    
    def save_marked_image(self, img_path, shape, left_eye, right_eye, points, landmark_size, dest_path):
        img = imread_unicode(img_path)
        if img is None:
            return False
        if landmark_size is None:
            landmark_size = get_landmark_size(shape)
        marked = mark_picture(img, shape, left_eye, right_eye, points, landmark_size)
        ext = os.path.splitext(dest_path)[1]
        success, encoded = cv2.imencode(ext, marked)
        if success:
            with open(safe_path(dest_path), 'wb') as f:
                f.write(encoded.tobytes())
            return True
        else:
            return False
    
    def check_overwrite(self, files_list):
        existing = [f for f in files_list if os.path.exists(f['path'])]
        if not existing:
            return True
        msg = "Следующие файлы уже существуют:\n"
        for f in existing:
            msg += f"- {f['description']}: {os.path.basename(f['path'])}\n"
        msg += "\nПерезаписать их?"
        reply = QtWidgets.QMessageBox.question(
            self, 'Файлы существуют', msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        return reply == QtWidgets.QMessageBox.Yes
    
    def save_all(self):
        target_folder = self.folder_edit.text()
        if not target_folder or not os.path.exists(target_folder):
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Укажите существующую папку для сохранения')
            return
        
        fullname = self.fullname_edit.text().strip()
        if not fullname:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Введите ФИО пациента перед сохранением')
            return
        
        safe_name = sanitize_filename(fullname)
        
        # Формируем список всех файлов, которые будут созданы
        files_to_check = []
        
        original_first_path = ''
        original_second_path = ''
        marked_first_path = ''
        marked_second_path = ''
        consent_dest = ''
        txt_path1 = ''
        txt_path2 = ''
        
        # Исходные фото
        if self.save_original_checkbox.isChecked():
            if self._first_image_path:
                ext1 = os.path.splitext(self._first_image_path)[1]
                dest_name1 = safe_name + '_до' + ext1
                original_first_path = os.path.join(target_folder, dest_name1)
                files_to_check.append({'path': original_first_path, 'description': 'исходное фото ДО'})
            if self._second_image_path:
                ext2 = os.path.splitext(self._second_image_path)[1]
                dest_name2 = safe_name + '_после' + ext2
                original_second_path = os.path.join(target_folder, dest_name2)
                files_to_check.append({'path': original_second_path, 'description': 'исходное фото ПОСЛЕ'})
        
        # Размеченные фото
        if self.save_marked_checkbox.isChecked() and self._patient is not None:
            if self._first_image_path:
                ext1 = os.path.splitext(self._first_image_path)[1]
                dest_name1 = safe_name + '_до_размеченное' + ext1
                marked_first_path = os.path.join(target_folder, dest_name1)
                files_to_check.append({'path': marked_first_path, 'description': 'размеченное фото ДО'})
            if self._second_image_path:
                ext2 = os.path.splitext(self._second_image_path)[1]
                dest_name2 = safe_name + '_после_размеченное' + ext2
                marked_second_path = os.path.join(target_folder, dest_name2)
                files_to_check.append({'path': marked_second_path, 'description': 'размеченное фото ПОСЛЕ'})
        
        # TXT-файлы
        if self.export_txt_checkbox.isChecked() and self._patient is not None:
            if self._patient.FirstPhoto._shape is not None:
                txt_path1 = os.path.join(target_folder, safe_name + '_до.txt')
                files_to_check.append({'path': txt_path1, 'description': 'файл разметки ДО'})
            if self._patient.SecondPhoto._shape is not None:
                txt_path2 = os.path.join(target_folder, safe_name + '_после.txt')
                files_to_check.append({'path': txt_path2, 'description': 'файл разметки ПОСЛЕ'})
        
        # Файл согласия
        consent_src = self.consent_file_edit.text()
        if consent_src and os.path.exists(consent_src):
            consent_ext = os.path.splitext(consent_src)[1]
            consent_name = safe_name + '_согласие' + consent_ext
            consent_dest = os.path.join(target_folder, consent_name)
            files_to_check.append({'path': consent_dest, 'description': 'скан согласия'})
        
        # Excel-файл
        excel_path = os.path.join(target_folder, safe_name + '_метрики.xlsx')
        files_to_check.append({'path': excel_path, 'description': 'Excel-отчёт'})
        
        # Проверяем существование и запрашиваем перезапись
        if not self.check_overwrite(files_to_check):
            return
        
        # --- Сохранение ---
        error_occurred = False
        
        # 1. Исходные фото
        if self.save_original_checkbox.isChecked():
            if self._first_image_path and os.path.exists(self._first_image_path):
                if not self.copy_file(self._first_image_path, original_first_path):
                    error_occurred = True
            if self._second_image_path and os.path.exists(self._second_image_path):
                if not self.copy_file(self._second_image_path, original_second_path):
                    error_occurred = True
        
        # 2. Размеченные фото
        if self.save_marked_checkbox.isChecked() and self._patient is not None:
            first = self._patient.FirstPhoto
            second = self._patient.SecondPhoto
            if first._shape is not None and self._first_image_path:
                if not self.save_marked_image(self._first_image_path, first._shape, first._lefteye, first._righteye,
                                              first._points, first._landmark_size, marked_first_path):
                    error_occurred = True
            if second._shape is not None and self._second_image_path:
                if not self.save_marked_image(self._second_image_path, second._shape, second._lefteye, second._righteye,
                                              second._points, second._landmark_size, marked_second_path):
                    error_occurred = True
        
        # 3. TXT-файлы
        if self.export_txt_checkbox.isChecked() and self._patient is not None:
            first = self._patient.FirstPhoto
            second = self._patient.SecondPhoto
            if first._shape is not None:
                try:
                    save_txt_file(txt_path1, first._shape, first._lefteye, first._righteye, first._boundingbox)
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, 'Ошибка', f'Не удалось сохранить TXT-файл (ДО):\n{e}')
                    error_occurred = True
            if second._shape is not None:
                try:
                    save_txt_file(txt_path2, second._shape, second._lefteye, second._righteye, second._boundingbox)
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, 'Ошибка', f'Не удалось сохранить TXT-файл (ПОСЛЕ):\n{e}')
                    error_occurred = True
        
        # 4. Согласие
        if consent_src and os.path.exists(consent_src):
            if not self.copy_file(consent_src, consent_dest):
                error_occurred = True
        
        # 5. Excel
        if not self.save_excel(excel_path, original_first_path, original_second_path,
                               marked_first_path, marked_second_path, consent_dest, safe_name):
            error_occurred = True
        
        if error_occurred:
            return  # не показываем успех, окно остаётся открытым
        
        QtWidgets.QMessageBox.information(self, 'Успех', f'Все выбранные файлы сохранены в папку:\n{target_folder}')
        self.accept()
    
    def save_excel(self, excel_path, orig_first, orig_second, marked_first, marked_second, consent_path, safe_name):
        if self._metrics_first is None or self._metrics_second is None:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Не удалось вычислить метрики')
            return False
        
        left1, right1, dev1, perc1 = self._metrics_first
        left2, right2, dev2, perc2 = self._metrics_second
        
        # ----- Подготовка данных для диаграмм -----
        metric_names = [
            'Высота брови',
            'Расстояние от зрачка до верхнего века',
            'Расстояние от зрачка до нижнего века',
            'Высота глазной щели',
            'Расстояние от средней линии губы до угла рта',
            'Угол улыбки',
            'Высота обнажения зубов при улыбке',
            'Асимметрия стояния углов рта',
            'Асимметрия стояния верхней губы',
            'Асимметрия стояния нижней губы'
        ]
        
        radar_before = []
        radar_after = []
        
        radar_before.append(abs(right1.BrowHeight - left1.BrowHeight))
        radar_after.append(abs(right2.BrowHeight - left2.BrowHeight))
        radar_before.append(abs(right1.MarginalReflexDistance1 - left1.MarginalReflexDistance1))
        radar_after.append(abs(right2.MarginalReflexDistance1 - left2.MarginalReflexDistance1))
        radar_before.append(abs(right1.MarginalReflexDistance2 - left1.MarginalReflexDistance2))
        radar_after.append(abs(right2.MarginalReflexDistance2 - left2.MarginalReflexDistance2))
        radar_before.append(abs(right1.PalpebralFissureHeight - left1.PalpebralFissureHeight))
        radar_after.append(abs(right2.PalpebralFissureHeight - left2.PalpebralFissureHeight))
        radar_before.append(abs(right1.CommissureExcursion - left1.CommissureExcursion))
        radar_after.append(abs(right2.CommissureExcursion - left2.CommissureExcursion))
        radar_before.append(abs(right1.SmileAngle - left1.SmileAngle))
        radar_after.append(abs(right2.SmileAngle - left2.SmileAngle))
        radar_before.append(abs(right1.DentalShow - left1.DentalShow))
        radar_after.append(abs(right2.DentalShow - left2.DentalShow))
        radar_before.append(dev1.CommisureHeightDeviation)
        radar_after.append(dev2.CommisureHeightDeviation)
        radar_before.append(dev1.UpperLipHeightDeviation)
        radar_after.append(dev2.UpperLipHeightDeviation)
        radar_before.append(dev1.LowerLipHeightDeviation)
        radar_after.append(dev2.LowerLipHeightDeviation)
        
        # ----- Формирование основной таблицы -----
        rows = []
        def add_metric(name, right_before, left_before, right_after, left_after):
            diff_before = abs(right_before - left_before)
            diff_after = abs(right_after - left_after)
            improvement = (diff_before - diff_after) / diff_before * 100 if diff_before != 0 else 0
            rows.append([name, 'Правая', right_before, right_after, right_after - right_before, ''])
            rows.append([name, 'Левая', left_before, left_after, left_after - left_before, ''])
            rows.append([name, 'Разница сторон', diff_before, diff_after, diff_after - diff_before, f"{improvement:.1f}%"])
        
        add_metric('Высота брови', right1.BrowHeight, left1.BrowHeight, right2.BrowHeight, left2.BrowHeight)
        add_metric('Расстояние от зрачка до верхнего века', right1.MarginalReflexDistance1, left1.MarginalReflexDistance1, right2.MarginalReflexDistance1, left2.MarginalReflexDistance1)
        add_metric('Расстояние от зрачка до нижнего века', right1.MarginalReflexDistance2, left1.MarginalReflexDistance2, right2.MarginalReflexDistance2, left2.MarginalReflexDistance2)
        add_metric('Высота глазной щели', right1.PalpebralFissureHeight, left1.PalpebralFissureHeight, right2.PalpebralFissureHeight, left2.PalpebralFissureHeight)
        add_metric('Расстояние от средней линии губы до угла рта', right1.CommissureExcursion, left1.CommissureExcursion, right2.CommissureExcursion, left2.CommissureExcursion)
        add_metric('Угол улыбки', right1.SmileAngle, left1.SmileAngle, right2.SmileAngle, left2.SmileAngle)
        add_metric('Высота обнажения зубов при улыбке', right1.DentalShow, left1.DentalShow, right2.DentalShow, left2.DentalShow)
        
        def add_deviation_metric(name, before_diff, after_diff):
            improvement = (before_diff - after_diff) / before_diff * 100 if before_diff != 0 else 0
            rows.append([name, 'Разница сторон', before_diff, after_diff, after_diff - before_diff, f"{improvement:.1f}%"])
        
        add_deviation_metric('Асимметрия стояния углов рта', dev1.CommisureHeightDeviation, dev2.CommisureHeightDeviation)
        add_deviation_metric('Асимметрия стояния верхней губы', dev1.UpperLipHeightDeviation, dev2.UpperLipHeightDeviation)
        add_deviation_metric('Асимметрия стояния нижней губы', dev1.LowerLipHeightDeviation, dev2.LowerLipHeightDeviation)
        
        df_metrics = pd.DataFrame(rows, columns=[
            'Метрика', 'Сторона', 'Фото ДО', 'Фото ПОСЛЕ', 'Разница (ДО→ПОСЛЕ)', 'Улучшение, %'
        ])
        
        info_data = {
            'Параметр': [
                'ФИО пациента', 'Дата рождения', 'Диагноз', 'Процедура',
                'Дата съёмки (ДО)', 'Выражение лица (ДО)', 'Комментарий (ДО)',
                'Дата съёмки (ПОСЛЕ)', 'Выражение лица (ПОСЛЕ)', 'Комментарий (ПОСЛЕ)',
                'Путь к исходному фото ДО', 'Путь к исходному фото ПОСЛЕ',
                'Путь к размеченному фото ДО', 'Путь к размеченному фото ПОСЛЕ',
                'Путь к согласию'
            ],
            'Значение': [
                self.fullname_edit.text(),
                self.birthdate_edit.date().toString('dd.MM.yyyy'),
                self.diagnosis_edit.text(),
                self.surgery_edit.text(),
                self.before_date_edit.date().toString('dd.MM.yyyy'),
                self.before_expression_edit.text(),
                self.before_comments_edit.text(),
                self.after_date_edit.date().toString('dd.MM.yyyy'),
                self.after_expression_edit.text(),
                self.after_comments_edit.text(),
                orig_first, orig_second,
                marked_first, marked_second,
                consent_path
            ]
        }
        df_info = pd.DataFrame(info_data)
        
        try:
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                df_metrics.to_excel(writer, sheet_name='Метрики', index=False)
                df_info.to_excel(writer, sheet_name='Информация', index=False)
                
                workbook = writer.book
                worksheet_metrics = writer.sheets['Метрики']
                worksheet_info = writer.sheets['Информация']
                
                # ----- Лист "Радарная диаграмма" -----
                worksheet_radar = workbook.add_worksheet('Радарная диаграмма')
                worksheet_radar.write(0, 0, 'Метрика')
                worksheet_radar.write(0, 1, 'ДО (асимметрия)')
                worksheet_radar.write(0, 2, 'ПОСЛЕ (асимметрия)')
                for i, (name, val_before, val_after) in enumerate(zip(metric_names, radar_before, radar_after)):
                    worksheet_radar.write(i+1, 0, name)
                    worksheet_radar.write(i+1, 1, val_before)
                    worksheet_radar.write(i+1, 2, val_after)
                
                radar_chart = workbook.add_chart({'type': 'radar'})
                radar_chart.add_series({
                    'name': 'ДО (асимметрия)',
                    'categories': ['Радарная диаграмма', 1, 0, len(metric_names), 0],
                    'values': ['Радарная диаграмма', 1, 1, len(metric_names), 1],
                    'line': {'color': 'red', 'width': 2},
                    'fill': {'color': 'red', 'transparency': 70}
                })
                radar_chart.add_series({
                    'name': 'ПОСЛЕ (асимметрия)',
                    'categories': ['Радарная диаграмма', 1, 0, len(metric_names), 0],
                    'values': ['Радарная диаграмма', 1, 2, len(metric_names), 2],
                    'line': {'color': 'green', 'width': 2},
                    'fill': {'color': 'green', 'transparency': 70}
                })
                radar_chart.set_title({'name': 'Динамика асимметрии лица'})
                radar_chart.set_legend({'position': 'right'})
                worksheet_radar.insert_chart('E2', radar_chart)
                
                # ----- Лист "Столбчатая диаграмма" -----
                worksheet_bar = workbook.add_worksheet('Столбчатая диаграмма')
                bar_metrics = metric_names[:7]
                worksheet_bar.write(0, 0, 'Метрика')
                worksheet_bar.write(0, 1, 'Правая ДО')
                worksheet_bar.write(0, 2, 'Левая ДО')
                worksheet_bar.write(0, 3, 'Правая ПОСЛЕ')
                worksheet_bar.write(0, 4, 'Левая ПОСЛЕ')
                
                bar_data = [
                    [right1.BrowHeight, left1.BrowHeight, right2.BrowHeight, left2.BrowHeight],
                    [right1.MarginalReflexDistance1, left1.MarginalReflexDistance1, right2.MarginalReflexDistance1, left2.MarginalReflexDistance1],
                    [right1.MarginalReflexDistance2, left1.MarginalReflexDistance2, right2.MarginalReflexDistance2, left2.MarginalReflexDistance2],
                    [right1.PalpebralFissureHeight, left1.PalpebralFissureHeight, right2.PalpebralFissureHeight, left2.PalpebralFissureHeight],
                    [right1.CommissureExcursion, left1.CommissureExcursion, right2.CommissureExcursion, left2.CommissureExcursion],
                    [right1.SmileAngle, left1.SmileAngle, right2.SmileAngle, left2.SmileAngle],
                    [right1.DentalShow, left1.DentalShow, right2.DentalShow, left2.DentalShow]
                ]
                
                for i, name in enumerate(bar_metrics):
                    worksheet_bar.write(i+1, 0, name)
                    for j in range(4):
                        worksheet_bar.write(i+1, j+1, bar_data[i][j])
                
                bar_chart = workbook.add_chart({'type': 'column'})
                bar_chart.add_series({
                    'name': 'Правая ДО',
                    'categories': ['Столбчатая диаграмма', 1, 0, len(bar_metrics), 0],
                    'values': ['Столбчатая диаграмма', 1, 1, len(bar_metrics), 1],
                    'fill': {'color': '#FF9999'}
                })
                bar_chart.add_series({
                    'name': 'Левая ДО',
                    'categories': ['Столбчатая диаграмма', 1, 0, len(bar_metrics), 0],
                    'values': ['Столбчатая диаграмма', 1, 2, len(bar_metrics), 2],
                    'fill': {'color': '#FFCC99'}
                })
                bar_chart.add_series({
                    'name': 'Правая ПОСЛЕ',
                    'categories': ['Столбчатая диаграмма', 1, 0, len(bar_metrics), 0],
                    'values': ['Столбчатая диаграмма', 1, 3, len(bar_metrics), 3],
                    'fill': {'color': '#99CC99'}
                })
                bar_chart.add_series({
                    'name': 'Левая ПОСЛЕ',
                    'categories': ['Столбчатая диаграмма', 1, 0, len(bar_metrics), 0],
                    'values': ['Столбчатая диаграмма', 1, 4, len(bar_metrics), 4],
                    'fill': {'color': '#66B2FF'}
                })
                bar_chart.set_title({'name': 'Сравнение сторон ДО и ПОСЛЕ'})
                bar_chart.set_x_axis({'name': 'Метрика'})
                bar_chart.set_y_axis({'name': 'Значение'})
                bar_chart.set_legend({'position': 'bottom'})
                worksheet_bar.insert_chart('F2', bar_chart)
                
                # Форматирование ширины
                worksheet_metrics.set_column(0, 0, 40)
                worksheet_metrics.set_column(1, 1, 14)
                worksheet_metrics.set_column(2, 3, 12)
                worksheet_metrics.set_column(4, 4, 19)
                worksheet_metrics.set_column(5, 5, 12)
                worksheet_info.set_column(0, 0, 30)
                worksheet_info.set_column(1, 1, 70)
                worksheet_radar.set_column(0, 0, 40)
                worksheet_radar.set_column(1, 2, 10)
                worksheet_bar.set_column(0, 0, 40)
                worksheet_bar.set_column(1, 4, 13)
                
            return True
        except PermissionError:
            QtWidgets.QMessageBox.warning(
                self, 'Ошибка',
                f'Не удалось сохранить Excel-файл.\nВозможно, файл уже открыт в другой программе.\n'
                f'Закройте файл и повторите попытку.\nПуть: {excel_path}'
            )
            return False
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', f'Не удалось сохранить Excel-файл:\n{e}')
            return False


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = SaveWindow()
    w.show()
    app.exec_()
