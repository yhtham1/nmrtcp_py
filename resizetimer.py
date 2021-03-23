
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class DelayedUpdater(QWidget):
	def __init__(self):
		super(DelayedUpdater, self).__init__()
		# self.layout = QVBoxLayout(self)
		# self.label = QLabel("Some Text")
		# self.layout.addWidget(self.label, Qt.AlignCenter)

		self.delayEnabled = True
		self.delayTimeout = 10

		self._resizeTimer = QTimer(self)
		self._resizeTimer.timeout.connect(self._delayedUpdate)

	def resizeEvent(self, event):
		if self.delayEnabled:
			self._resizeTimer.start(self.delayTimeout)
			self.setUpdatesEnabled(False)
		super().resizeEvent(event)

	def _delayedUpdate(self):
		print("Performing actual update")
		self._resizeTimer.stop()
		self.setUpdatesEnabled(True)


if __name__ == "__main__":
	app = QApplication(sys.argv)
	win = QMainWindow()
	view = DelayedUpdater()
	win.setCentralWidget(view)
	win.show()
	
	view.delayEnabled = True
	sys.exit(app.exec_())
	
	
	