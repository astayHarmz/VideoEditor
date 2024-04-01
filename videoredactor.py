import os
import sqlite3
import sys

from PyQt5.QtWidgets import QApplication

import main_window


def delete_temp_files():
    file_changes = sqlite3.connect('file_changes.db')
    cur = file_changes.cursor()
    cur.execute("""DROP table if exists last_changes""")
    file_changes.commit()
    folder = 'temp_files'
    for file in os.scandir(folder):
        os.remove(file.path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    delete_temp_files()
    m = main_window.PlayerWindow()
    m.show()
    sys.exit(app.exec())
