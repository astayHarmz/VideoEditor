import os
import sqlite3

from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QWidget

import open_file_dialog
import redactor_window_1


class PlayerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.redactor = None
        self.current_file = None
        self.file_changes = sqlite3.connect('file_changes.db')
        self.cur = self.file_changes.cursor()
        self.file_change_number = 1
        self.video_file = ''
        self.cur.execute("""CREATE TABLE IF NOT EXISTS last_changes(
            id INTEGER PRIMARY KEY,
            filepath TEXT);""")
        self.cur.execute("""INSERT INTO last_changes(id, filepath)
                            VALUES(?, ?);""", (self.file_change_number, self.video_file))
        self.file_changes.commit()
        uic.loadUi('ui-files/videoplayer.ui', self)
        self.setWindowTitle('Видеоплеер')
        self.setWindowIcon(QtGui.QIcon('icon.ico'))

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.change_position)
        self.media_player.durationChanged.connect(self.change_duration)
        self.video_widget.show()

        self.openButton.clicked.connect(self.open)

        self.playButton.setEnabled(False)
        self.playButton.clicked.connect(self.play)
        self.playButton.setStyleSheet('border-image: url(imgs/play_button.png)')
        self.playButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.rewindButton.setEnabled(False)
        self.rewindButton.clicked.connect(self.rewind)
        self.rewindButton.setStyleSheet('border-image: url(imgs/rewind_button.png)')
        self.rewindButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.ffButton.setEnabled(False)
        self.ffButton.clicked.connect(self.ff)
        self.ffButton.setStyleSheet('border-image: url(imgs/ff_button.png)')
        self.ffButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.soundButton.setEnabled(False)
        self.soundButton.clicked.connect(self.sound)
        self.soundButton.setStyleSheet('border-image: url(imgs/sound_button1.png)')
        self.soundButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.timelineSlider.sliderMoved.connect(self.set_position)
        self.timelineSlider.setRange(0, 0)
        self.volumeSlider.sliderMoved.connect(self.set_volume)
        self.volumeSlider.setRange(0, 0)
        self.goToRedactor.setEnabled(False)
        self.goToRedactor.clicked.connect(self.go_to_redactor)
        self.goToRedactor.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

    def play(self):
        if self.media_player.state() == self.media_player.PlayingState:
            self.media_player.pause()
            self.playButton.setStyleSheet('border-image: url(imgs/play_button.png)')
        else:
            self.playButton.setStyleSheet('border-image: url(imgs/play_button1.png)')
            self.media_player.play()

    def open(self):
        open_new_file = open_file_dialog.OpenFileDialog()
        open_new_file.exec()
        if open_new_file.video_file != '':
            if os.path.exists(open_new_file.video_file):
                self.video_file = open_new_file.video_file
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_file)))
                self.cur.execute("""UPDATE last_changes
                                    SET filepath=? WHERE id=1;""", (self.video_file,))
                self.file_changes.commit()
                self.playButton.setEnabled(True)
                self.media_player.play()
                self.rewindButton.setEnabled(True)
                self.ffButton.setEnabled(True)
                self.soundButton.setEnabled(True)
                self.goToRedactor.setEnabled(True)
                self.volumeSlider.setRange(1, 100)
                self.volumeSlider.setSliderPosition(50)
                self.media_player.setVolume(50)
                self.current_file = self.video_file
                self.playButton.setStyleSheet('border-image: url(imgs/play_button1.png)')
            else:
                error = QMessageBox()
                error.setWindowTitle('Ошибка')
                error.setText('Упс! Что-то пошло не так. Не удается загрузить файл.')
                error.setStandardButtons(QMessageBox.Ok)
                error.exec()

    def rewind(self):
        if self.media_player.position() - 10000 >= 0:
            self.timelineSlider.setValue(self.media_player.position() - 10000)
            self.media_player.setPosition(self.media_player.position() - 10000)
        else:
            self.media_player.setPosition(0)
            self.timelineSlider.setValue(0)

    def ff(self):
        if self.media_player.position() + 10000 <= self.media_player.duration():
            self.timelineSlider.setValue(self.media_player.position() + 10000)
            self.media_player.setPosition(self.media_player.position() + 10000)
        else:
            self.media_player.setPosition(self.media_player.duration())
            self.timelineSlider.setValue(self.media_player.duration())

    def sound(self):
        if self.media_player.volume() == 0:
            if self.volumeSlider.value() <= 3:
                self.media_player.setVolume(0)
            else:
                self.media_player.setVolume(self.volumeSlider.value())

            if 60 <= self.media_player.volume() <= 100:
                self.soundButton.setStyleSheet('border-image: url(imgs/sound_button.png)')
            elif 25 <= self.media_player.volume() < 60:
                self.soundButton.setStyleSheet('border-image: url(imgs/sound_button1.png)')
            elif self.media_player.volume() == 0:
                self.soundButton.setStyleSheet('border-image: url(imgs/sound_button3.png)')
            else:
                self.soundButton.setStyleSheet('border-image: url(imgs/sound_button2.png)')
        else:
            self.media_player.setVolume(0)
            self.soundButton.setStyleSheet('border-image: url(imgs/sound_button3.png)')

    def change_position(self, position):
        self.timelineSlider.setValue(position)
        if self.timelineSlider.value() == self.media_player.duration():
            self.playButton.setStyleSheet('border-image: url(imgs/play_button.png)')
        self.timer.setText(
            f'{position // 600000}{position % 600000 // 60000}:{position % 60000 // 10000}{position % 10000 // 1000}')

    def change_duration(self, duration):
        self.timelineSlider.setRange(0, duration)
        self.duration.setText(
            f'{duration // 600000}{duration % 600000 // 60000}:{duration % 60000 // 10000}{duration % 10000 // 1000}')

    def set_position(self, position):
        self.media_player.setPosition(position)

    def set_volume(self):
        if self.volumeSlider.value() <= 3:
            self.media_player.setVolume(0)
        else:
            self.media_player.setVolume(self.volumeSlider.value())

        if 60 <= self.media_player.volume() <= 100:
            self.soundButton.setStyleSheet('border-image: url(imgs/sound_button.png)')
        elif 25 <= self.media_player.volume() < 60:
            self.soundButton.setStyleSheet('border-image: url(imgs/sound_button1.png)')
        elif self.media_player.volume() == 0:
            self.soundButton.setStyleSheet('border-image: url(imgs/sound_button3.png)')
        else:
            self.soundButton.setStyleSheet('border-image: url(imgs/sound_button2.png)')

    def go_to_redactor(self):
        self.media_player.stop()
        self.redactor = redactor_window_1.RedactorWindow1(self)
        self.redactor.show()
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
