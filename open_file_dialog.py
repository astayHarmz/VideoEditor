import sqlite3
from datetime import date

from PyQt5 import uic
from PyQt5.QtWidgets import QFileDialog, QDialog


class OpenFileDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui-files/open_file_dialog.ui', self)
        self.setWindowTitle('Открыть файл')
        self.video_file = ''
        self.file_changes = sqlite3.connect('file_changes.db')
        self.cur = self.file_changes.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS last_opened_files(
                    id INTEGER PRIMARY KEY,
                    filepath TEXT,
                    date TEXT);""")
        self.file_changes.commit()
        if self.cur.execute("""SELECT COUNT(*) FROM last_opened_files""").fetchone()[0] != 0:
            self.n = self.cur.execute("""SELECT id FROM last_opened_files ORDER BY id DESC;""").fetchone()[0] + 1
        else:
            self.n = 1
        self.openNewFileButton.clicked.connect(self.open_file)
        self.cancelButton.clicked.connect(self.return_to_main_window)

        if self.cur.execute("""SELECT COUNT(*) FROM last_opened_files""").fetchone()[0] >= 5:
            prev_files = self.cur.execute("""SELECT * FROM last_opened_files
                            ORDER BY id DESC;""").fetchmany(5)
            for i in range(5):
                self.last_files.addItem(f'{i + 1}. {prev_files[i][2]}   {prev_files[i][1].split("/")[-1]}')
        else:
            prev_files = self.cur.execute("""SELECT * FROM last_opened_files
                                            ORDER BY id DESC;""").fetchall()
            for i in range(len(prev_files)):
                self.last_files.addItem(f'{i + 1}. {prev_files[i][2]}   {prev_files[i][1].split("/")[-1]}')
        self.last_files.itemClicked.connect(self.open_from_last_files)

    def open_file(self):
        self.video_file = QFileDialog.getOpenFileName(
            self, 'Выбрать видеофайл', '', 'Видеофайл (*.mp4)')[0]
        if self.video_file != '':
            if self.cur.execute("""SELECT filepath FROM last_opened_files 
                                WHERE filepath=?""", (self.video_file,)).fetchall() is not None:
                self.cur.execute("""DELETE from last_opened_files WHERE filepath = ?""", (self.video_file,))
            self.cur.execute("""INSERT INTO last_opened_files(id, filepath, date)
                                VALUES(?, ?, ?)""", (self.n, self.video_file, date.today()))
            self.file_changes.commit()
            self.n += 1
            self.close()

    def open_from_last_files(self, item):
        if self.cur.execute("""SELECT COUNT(*) FROM last_opened_files""").fetchone()[0] >= 5:
            prev_files = self.cur.execute("""SELECT filepath FROM last_opened_files
                            ORDER BY id DESC;""").fetchmany(5)
        else:
            prev_files = self.cur.execute("""SELECT filepath FROM last_opened_files
                                            ORDER BY id DESC;""").fetchall()
        self.video_file = prev_files[int(item.text().split()[0][0]) - 1][0]

        if self.cur.execute("""SELECT filepath FROM last_opened_files 
                            WHERE filepath=?""", (self.video_file,)).fetchall() is not None:
            self.cur.execute("""DELETE from last_opened_files WHERE filepath = ?""", (self.video_file,))
        self.cur.execute("""INSERT INTO last_opened_files(id, filepath, date)
                            VALUES(?, ?, ?)""", (self.n, self.video_file, date.today()))
        self.file_changes.commit()
        self.n += 1
        self.close()

    def return_to_main_window(self):
        self.close()
