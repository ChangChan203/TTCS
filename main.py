import sys
from PySide6 import QtWidgets

from Controllers.MyApplication import MyApplication

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    my_app = MyApplication()

    with open("style.qss", "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    app.exec()
