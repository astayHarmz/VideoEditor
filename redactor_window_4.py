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
import redactor_window_2
import redactor_window_1
import redactor_window_3


class RedactorWindow4(QWidget):
    def __init__(self, previous_window):
        super().__init__()
        self.audio_file = None
        self.redactor = None
        self.player = None
        self.file_change_number = previous_window.file_change_number
        self.video_file = previous_window.video_file
        self.current_file = previous_window.current_file
        self.switch_to_another_window = False
        self.file_changes = sqlite3.connect('file_changes.db')
        self.cur = self.file_changes.cursor()
        self.video_clip = mpy.VideoFileClip(self.current_file)
        uic.loadUi('ui-files/videoredactor4.ui', self)
        self.setWindowTitle('Видеоредактор')
        self.setWindowIcon(QtGui.QIcon('icon.ico'))

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_file)))
        self.media_player.positionChanged.connect(self.change_position)
        self.media_player.durationChanged.connect(self.change_duration)
        self.video_widget.show()

        self.audio_player = QMediaPlayer()

        self.playButton.clicked.connect(self.play)
        self.playButton.setStyleSheet('border-image: url(imgs/play_button.png)')
        self.playButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.media_player.pause()

        self.audioPlayButton.clicked.connect(self.play)
        self.audioPlayButton.setStyleSheet('border-image: url(imgs/play_button.png)')
        self.audioPlayButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.audio_player.pause()

        self.select_option.setCurrentText('Вставить аудиодорожку')
        self.select_option.currentTextChanged.connect(self.change_option)

        self.loadAudio.clicked.connect(self.load_audio)
        self.loadAudio.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.insertAudio.clicked.connect(self.insert_audio)
        self.insertAudio.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.cancelButton.clicked.connect(self.cancel)
        self.cancelButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.cancelButton.setStyleSheet('border-image: url(imgs/cancel_button.png)')
        self.saveButton.clicked.connect(self.save_file)
        self.saveButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.goToPlayer.clicked.connect(self.go_to_player)
        self.goToPlayer.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.timelineSlider.sliderMoved.connect(self.set_position)
        self.timelineSlider.setRange(0, 0)
        self.audioTimelineSlider.sliderMoved.connect(self.audio_set_position)
        self.audioTimelineSlider.setRange(0, 0)

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

    def load_audio(self):
        self.audio_file = QFileDialog.getOpenFileName(self, 'Выбрать аудиофайл', '', 'Аудиофайл (*.mp3)')[0]
        if self.audio_file != '':
            if os.path.exists(self.audio_file):
                self.audio_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.audio_file)))
                self.audio_player.positionChanged.connect(self.audio_change_position)
                self.audio_player.durationChanged.connect(self.audio_change_duration)
            else:
                error = QMessageBox()
                error.setWindowTitle('Ошибка')
                error.setText('Упс! Что-то пошло не так. Не удается загрузить файл.')
                error.setStandardButtons(QMessageBox.Ok)
                error.exec()

    def audio_play(self):
        if self.audio_player.state() == self.audio_player.PlayingState:
            self.audio_player.pause()
            self.audioPlayButton.setStyleSheet('border-image: url(imgs/play_button.png)')
        else:
            self.audioPlayButton.setStyleSheet('border-image: url(imgs/play_button1.png)')
            self.audio_player.play()

    def audio_change_position(self, position):
        self.audioTimelineSlider.setValue(position)
        self.audioTimer.setText(
            f'{position // 600000}{position % 600000 // 60000}:{position % 60000 // 10000}{position % 10000 // 1000}')

    def audio_change_duration(self, duration):
        self.audioTimelineSlider.setRange(0, duration)

    def audio_set_position(self, position):
        self.audio_player.setPosition(position)

    def insert_audio(self):
        pass

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

    def change_option(self, text):
        if text == 'Вырезать фрагмент':
            self.switch_to_another_window = True
            self.close()
            self.redactor = redactor_window_1.RedactorWindow1(self)
            self.redactor.show()
        elif text == 'Склеить несколько файлов в один':
            self.switch_to_another_window = True
            self.close()
            self.redactor = redactor_window_2.RedactorWindow2(self)
            self.redactor.show()
        elif text == 'Вырезать/извлечь аудиодорожку из файла':
            self.switch_to_another_window = True
            self.close()
            self.redactor = redactor_window_3.RedactorWindow3(self)
            self.redactor.show()

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