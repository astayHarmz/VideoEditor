import gc

from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QWidget, QFileDialog, QDialog
from PyQt5.QtWidgets import QMessageBox

import moviepy.editor as mpy
from moviepy.video.tools.subtitles import SubtitlesClip
import pvleopard
import os
import random
import string
import sqlite3

from typing_extensions import Optional, Sequence
from inspect import currentframe, getframeinfo

import main_window
import redactor_window_2
import redactor_window_1
import redactor_window_3
import redactor_window_4
#и это потом тоже не забыть удалить
leopard = pvleopard.create(access_key='cG9IZQDv4TBvRCk9ZhmkdEyfYM5Ot4yjpbxNeP9LxITGljSSayHcKg==')


class RedactorWindow5(QWidget):
    def __init__(self, previous_window):
        super().__init__()
        self.go_back = None
        self.redactor = None
        self.player = None
        self.file_change_number = previous_window.file_change_number
        self.video_file = previous_window.video_file
        self.current_file = previous_window.current_file
        self.switch_to_another_window = False
        self.file_changes = sqlite3.connect('file_changes.db')
        self.cur = self.file_changes.cursor()
        self.video_clip = mpy.VideoFileClip(self.current_file)
        uic.loadUi('ui-files/videoredactor5.ui', self)
        self.setWindowTitle('Видеоредактор')
        self.setWindowIcon(QtGui.QIcon('icon.ico'))

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_file)))
        self.media_player.positionChanged.connect(self.change_position)
        self.media_player.durationChanged.connect(self.change_duration)
        self.video_widget.show()

        self.playButton.clicked.connect(self.play)
        self.playButton.setStyleSheet('border-image: url(imgs/play_button.png)')
        self.playButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.media_player.pause()

        self.select_option.setCurrentText('Субтитры')
        self.select_option.currentTextChanged.connect(self.change_option)

        self.subtitlesButton.clicked.connect(self.generate)
        self.cancelButton.clicked.connect(self.cancel)
        self.cancelButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
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

    #временный код, потом перепишу на другую библиотеку
    def generate(self):
        global leopard
        message = QDialog()
        try:
            if self.video_clip.audio:
                message.resize(400, 20)
                message.show()
                message.setWindowTitle('Видео обрабатывается. Не закрывайте окно.')
                self.file_change_number += 1
                file_name = ''
                for i in range(4):
                    file_name += random.choice(string.ascii_letters)
                new_file = 'temp_files/' + file_name + '.mp4'
                print("OK1")
                self.video_clip.audio.set_duration(self.video_clip.duration).write_audiofile("temp_files/temp.mp3", bitrate='500k',
                                                                                             ffmpeg_params=[
                                                                                                 '-shortest'])
                transcript, words = leopard.process_file("temp_files/temp.mp3")
                with open("temp_files/subtitles.srt", 'w') as f:
                    f.write(self.to_srt(words))
                generator = lambda txt: mpy.TextClip(txt, font='Arial', fontsize=30, color='white', bg_color='black')
                subtitles = SubtitlesClip("temp_files/subtitles.srt", generator)
                self.video_clip = mpy.CompositeVideoClip([self.video_clip, subtitles.set_position(('center', 'bottom'))])
                self.video_clip.write_videofile(new_file)
                self.current_file = new_file
                self.video_clip = mpy.VideoFileClip(self.current_file)
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_file)))
                new_file_change = (self.file_change_number, self.current_file)
                self.cur.execute("""INSERT INTO last_changes(id, filepath)
                                                                    VALUES(?, ?);""", new_file_change)
                self.file_changes.commit()
                os.remove("temp_files/subtitles.srt")
                os.remove("temp_files/temp.mp3")
                message.close()
            else:
                message.close()
                error = QMessageBox()
                error.setWindowTitle('Ошибка')
                error.setText('Аудиодорожка отсутствует.')
                error.setStandardButtons(QMessageBox.Ok)
                error.exec()
        except Exception as e:
            message.close()
            error = QMessageBox()
            error.setWindowTitle('Ошибка')
            error.setText('Упс! Ошибка. Что-то пошло не так, процесс прерван.')
            error.setStandardButtons(QMessageBox.Ok)
            error.exec()
    #см.предыдущий комментарий
    def second_to_timecode(self, x: float) -> str:
        hour, x = divmod(x, 3600)
        minute, x = divmod(x, 60)
        second, x = divmod(x, 1)
        millisecond = int(x * 1000.)

        return '%.2d:%.2d:%.2d,%.3d' % (hour, minute, second, millisecond)

    def to_srt(self,
               words: Sequence[pvleopard.Leopard.Word],
               endpoint_sec: float = 1.,
               length_limit: Optional[int] = 16) -> str:

        def _helper(end: int) -> None:
            lines.append("%d" % section)
            lines.append(
                "%s --> %s" %
                (
                    self.second_to_timecode(words[start].start_sec),
                    self.second_to_timecode(words[end].end_sec)
                )
            )
            lines.append(' '.join(x.word for x in words[start:(end + 1)]))
            lines.append('')

        lines = list()
        section = 0
        start = 0
        for k in range(1, len(words)):
            if ((words[k].start_sec - words[k - 1].end_sec) >= endpoint_sec) or \
                    (length_limit is not None and (k - start) >= length_limit):
                _helper(k - 1)
                start = k
                section += 1
        _helper(len(words) - 1)

        return '\n'.join(lines)

    def cancel(self):
        if self.cur.execute("""SELECT COUNT(*) FROM last_changes""").fetchone()[0] > 1:
            prev_file = self.cur.execute("""SELECT filepath FROM last_changes 
                ORDER BY id DESC LIMIT 2;""").fetchmany(2)
            self.current_file = prev_file[1][0]
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_file)))
            self.file_change_number -= 1
            self.video_clip.close()
            self.video_clip = mpy.VideoFileClip(self.current_file)
            #os.remove(prev_file[0][0])
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
        elif text == 'Вставить аудиодорожку':
            self.switch_to_another_window = True
            self.close()
            self.redactor = redactor_window_4.RedactorWindow4(self)
            self.redactor.show()

    def go_to_player(self):
        self.close()
        self.cur.execute("""DROP table if exists last_changes""")
        self.file_changes.commit()
        if self.go_back:
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
                self.go_back = True
                self.media_player.setMedia(QMediaContent())
                event.accept()
            elif exit_warning == QMessageBox.Cancel:
                event.ignore()
                self.go_back = False
            else:
                self.go_back = True
                self.save_file()
                self.media_player.setMedia(QMediaContent())
                event.accept()
        else:
            self.media_player.setMedia(QMediaContent())
            event.accept()
