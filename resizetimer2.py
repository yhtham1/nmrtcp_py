
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class MainWindow(QMainWindow):

	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		self.someWidget = QWidget()
		self.setCentralWidget(self.someWidget)

		self.layout = QVBoxLayout(self.someWidget)
		self.label = QLabel("Some Text")
		self.layout.addWidget(self.label, Qt.AlignCenter)

		self.delayer = DelayedUpdater(self.someWidget)


class DelayedUpdater(QObject):

	def __init__(self, target, parent=None):
		super(DelayedUpdater, self).__init__(parent)
		self.target = target
		target.installEventFilter(self)

		self.delayEnabled = True
		self.delayTimeout = 100

		self._resizeTimer = QTimer()
		self._resizeTimer.timeout.connect(self._delayedUpdate)

	def eventFilter(self, obj, event):
		if self.delayEnabled and obj is self.target:
			if event.type() == event.Resize:
				self._resizeTimer.start(self.delayTimeout)
				self.target.setUpdatesEnabled(False)

		return False

	def _delayedUpdate(self):
		print("Performing actual update")
		self._resizeTimer.stop()
		self.target.setUpdatesEnabled(True)
