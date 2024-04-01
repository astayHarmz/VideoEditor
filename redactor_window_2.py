from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QWidget, QFileDialog, QDialog
from PyQt5.QtWidgets import QMessageBox

import moviepy.editor as mpy
import os
import random
import string
import sqlite3


import main_window
import redactor_window_1
import redactor_window_3


class RedactorWindow2(QWidget):
    def __init__(self, previous_window):
        super().__init__()
        self.video_clip = None
        self.player = None
        self.redactor = None
        self.new_loaded_file = None
        self.file_number = 1
        self.file_change_number = previous_window.file_change_number
        self.video_file = previous_window.video_file
        self.current_file = previous_window.current_file
        self.switch_to_another_window = False
        self.file_changes = sqlite3.connect('file_changes.db')
        self.cur = self.file_changes.cursor()
        self.video_files = [self.current_file]
        uic.loadUi('ui-files/videoredactor2.ui', self)
        self.setWindowTitle('Видеоредактор')
        self.setWindowIcon(QtGui.QIcon('icon.ico'))

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_file)))
        self.media_player.positionChanged.connect(self.change_position)
        self.media_player.durationChanged.connect(self.change_duration)
        self.video_widget.show()

        self.files_list.addItem(f'{self.file_number}. {self.video_file.split("/")[-1]}')

        self.select_option.setCurrentText('Склеить несколько файлов в один')
        self.select_option.currentTextChanged.connect(self.change_option)

        self.playButton.clicked.connect(self.play)
        self.playButton.setStyleSheet('border-image: url(imgs/play_button.png)')
        self.playButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.media_player.pause()

        self.applyButton.clicked.connect(self.apply)
        self.applyButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.cancelButton.clicked.connect(self.cancel)
        self.cancelButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.loadFileButton.clicked.connect(self.load_file)
        self.loadFileButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.deleteFileButton.clicked.connect(self.delete_loaded_file)
        self.deleteFileButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.cancelButton.setStyleSheet('border-image: url(imgs/cancel_button.png)')
        self.saveButton.clicked.connect(self.save_file)
        self.saveButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.goToPlayer.clicked.connect(self.go_to_player)
        self.goToPlayer.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.timelineSlider.sliderMoved.connect(self.set_position)
        self.timelineSlider.setRange(0, 0)

    def play(self):
        if self.media_player.state() == self.media_player.PlayingState:
            self.media_player.pause()
            self.playButton.setStyleSheet('border-image: url(imgs/play_button.png)')
        else:
            self.playButton.setStyleSheet('border-image: url(imgs/play_button1.png)')
            self.media_player.play()

    def change_position(self, position):
        self.timelineSlider.setValue(position)
        self.timer.setText(
            f'{position // 600000}{position % 600000 // 60000}:{position % 60000 // 10000}{position % 10000 // 1000}')

    def change_duration(self, duration):
        self.timelineSlider.setRange(0, duration)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def apply(self):
        if self.file_number > 1:
            message = QDialog()
            message.resize(400, 20)
            message.show()
            message.setWindowTitle('Видео обрабатывается. Не закрывайте окно.')
            self.file_change_number += 1
            file_name = ''
            for i in range(4):
                file_name += random.choice(string.ascii_letters)
            new_file = 'temp_files/' + file_name + '.mp4'
            self.video_clip = mpy.concatenate_videoclips([mpy.VideoFileClip(file) for file in self.video_files])
            self.video_clip.write_videofile(new_file)
            self.current_file = new_file
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(new_file)))
            new_file_change = (self.file_change_number, self.current_file)
            self.cur.execute("""INSERT INTO last_changes(id, filepath)
                            VALUES(?, ?);""", new_file_change)
            self.file_changes.commit()
            message.close()

    def cancel(self):
        if self.cur.execute("""SELECT COUNT(*) FROM last_changes""").fetchone()[0] > 1:
            prev_file = self.cur.execute("""SELECT filepath FROM last_changes 
                ORDER BY id DESC LIMIT 2;""").fetchmany(2)
            self.current_file = prev_file[1][0]
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_file)))
            os.remove(prev_file[0][0])
            self.file_change_number -= 1
            self.video_clip = mpy.VideoFileClip(self.current_file)
            self.cur.execute("""DELETE from last_changes WHERE filepath = ?;""", prev_file[0])
            self.file_changes.commit()
            self.video_files[0] = self.current_file

    def change_option(self, text):
        if text == 'Вырезать фрагмент':
            self.switch_to_another_window = True
            self.close()
            self.redactor = redactor_window_1.RedactorWindow1(self)
            self.redactor.show()
        elif text == 'Вырезать аудиодорожку из файла':
            self.switch_to_another_window = True
            self.close()
            self.redactor = redactor_window_3.RedactorWindow3(self)
            self.redactor.show()

    def load_file(self):
        new_loaded_file = QFileDialog.getOpenFileName(
            self, 'Выбрать видеофайл', '', 'Видеофайл (*.mp4)')[0]
        if new_loaded_file != '':
            if mpy.VideoFileClip(new_loaded_file).size != mpy.VideoFileClip(self.video_files[-1]).size:
                message = QMessageBox.question(self, 'Warning',
                                               'При объединении видеофайлов разного разрешения могут возникнуть '
                                               'проблемы. Хотите продолжить?',
                                               QMessageBox.Ok | QMessageBox.Cancel)
                if message == QMessageBox.Ok:
                    self.video_files.append(new_loaded_file)
                    self.file_number += 1
                    self.files_list.addItem(f'{self.file_number}. {new_loaded_file.split("/")[-1]}')
            else:
                self.video_files.append(new_loaded_file)
                self.file_number += 1
                self.files_list.addItem(f'{self.file_number}. {new_loaded_file.split("/")[-1]}')

    def delete_loaded_file(self):
        if self.file_number > 1:
            self.files_list.takeItem(self.file_number - 1)
            self.file_number -= 1
            self.video_files.pop(self.file_number)

    def save_file(self):
        try:
            file_name, _ = QFileDialog.getSaveFileName(self, 'Сохранить файл',
                                                       '', '*.mp4')
            if file_name != '':
                message = QDialog()
                message.resize(400, 20)
                message.setWindowTitle('Файл сохраняется. Не закрывайте окно.')
                message.show()
                self.video_clip.write_videofile(file_name)
                self.video_file = file_name
                message.close()
        except Exception:
            error = QMessageBox()
            error.setWindowTitle('Ошибка')
            error.setText('')
            error.setStandardButtons(QMessageBox.Ok)
            error.exec()

    def go_to_player(self):
        self.close()
        self.player = main_window.PlayerWindow()
        self.player.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_Space:
            self.play()

    def closeEvent(self, event):
        if self.switch_to_another_window is False:
            exit_warning = QMessageBox.question(self, 'Warning',
                                                'Вы уверены, что хотите выйти? Все несохраненные данные будут удалены.',
                                                QMessageBox.Ok | QMessageBox.Save | QMessageBox.Cancel)
            if exit_warning == QMessageBox.Ok:
                self.media_player.setMedia(QMediaContent())
                self.cur.execute("""DROP table if exists last_changes""")
                event.accept()
            elif exit_warning == QMessageBox.Cancel:
                event.ignore()
            else:
                self.save_file()
                self.media_player.setMedia(QMediaContent())
                self.cur.execute("""DROP table if exists last_changes""")
                event.accept()
        else:
            self.media_player.setMedia(QMediaContent())
            event.accept()
