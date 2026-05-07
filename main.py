import sys

from PySide6 import QtWidgets
#from widget import Widget
from gui.main_window import MainWindow


app = QtWidgets.QApplication(sys.argv)
window = MainWindow( )
window.show()
app.exec()