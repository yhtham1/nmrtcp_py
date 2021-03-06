#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 引用元
# https://matplotlib.org/2.0.2/examples/user_interfaces/embedding_in_qt5.html
import sys
import os
import random
import matplotlib
import japanize_matplotlib
from prot import prot_ad, prot_rf, prot_pulser

# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

progname = os.path.basename(sys.argv[0])


# progversion = "0.1"


class MyMplCanvas(FigureCanvas):
	"""Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

	def __init__(self, parent=None, width=5, height=4, dpi=200):
		fig = Figure(figsize=(width, height), dpi=dpi)
		self.axes = fig.add_subplot(111)

		self.compute_initial_figure()

		FigureCanvas.__init__(self, fig)
		self.setParent(parent)

		FigureCanvas.setSizePolicy(self,
								   QSizePolicy.Expanding,
								   QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

	def compute_initial_figure(self):
		pass


class OscilloCanvas(MyMplCanvas):
	def __init__(self, *args, **kwargs):
		# super().__init__()
		MyMplCanvas.__init__(self, *args, **kwargs)
		self.y1 = -1.0
		self.y2 = 1.0

	def compute_initial_figure(self):
		self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

	def update_figure(self, t, cosdata, sindata):
		# Build a list of 4 random integers between 0 and 10 (both inclusive)
		self.axes.cla()
		self.axes.set_ylabel('電圧')
		self.axes.set_ylim(self.y1, self.y2)
		self.axes.plot(t, cosdata, sindata, 'r')
		self.draw()


class Oscillo(QWidget):
	def pbBtn1(self):
		self.osc.y1 += -0.1
		self.osc.y2 += 0.1
	def pbBtn2(self):
		self.osc.y1 -= -0.1
		self.osc.y2 -= 0.1

	def __init__(self, parent=None):
		super(Oscillo, self).__init__(parent)
		qcore = QWidget(self)
		h = QHBoxLayout(qcore)
		v = QVBoxLayout(qcore)
		self.btn1 = QPushButton('+')
		v.addWidget(self.btn1)
		self.btn2 = QPushButton('-')
		v.addWidget(self.btn2)
		b = QPushButton('update')
		v.addWidget(b)

		self.btn1.clicked.connect(self.pbBtn1)
		self.btn2.clicked.connect(self.pbBtn2)



		self.osc = OscilloCanvas(qcore, width=5, height=4, dpi=96)
		h.addWidget(self.osc)
		h.addLayout(v)

		self.setLayout(h)


class myAD(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setWindowTitle("application main window")

		self.file_menu = QMenu('&File', self)
		self.file_menu.addAction('&Quit', self.fileQuit,
								 Qt.CTRL + Qt.Key_Q)
		self.menuBar().addMenu(self.file_menu)

		self.help_menu = QMenu('&Help', self)
		self.menuBar().addSeparator()
		self.menuBar().addMenu(self.help_menu)

		self.help_menu.addAction('&About', self.about)

		self.main_widget = QWidget(self)
		self.control_widget = QWidget(self)
		self.device_widget = QWidget(self)

		self.timer = QTimer()
		self.timer.timeout.connect(self.showTime)
		self.timer.start(100)

		all = QHBoxLayout(self.main_widget)
		v = QVBoxLayout(self.control_widget)
		v1 = QVBoxLayout(self.device_widget)
		l = QVBoxLayout(self.main_widget)
		l.setObjectName('main_frame')
		all.addLayout(l)
		all.addLayout(v)
		all.addLayout(v1)

		osc = Oscillo(self.main_widget)
		osc.setObjectName('frame0')
		l.addWidget(osc)
		osc = Oscillo(self.main_widget)
		osc.setObjectName('frame1')
		l.addWidget(osc)

		osc = Oscillo(self.main_widget)
		osc.setObjectName('frame2')
		l.addWidget(osc)



		dk1 = QDockWidget('controls', self)
		dk1.setObjectName('controls')
		dk1.setWidget(self.control_widget)
		dk1.setFloating(False)
		self.addDockWidget(Qt.RightDockWidgetArea, dk1)

		dk2 = QDockWidget('device', self)
		dk2.setObjectName('device')
		dk2.setWidget(self.device_widget)
		dk2.setFloating(False)
		self.addDockWidget(Qt.RightDockWidgetArea, dk2)


		pn1 = QLineEdit()
		pn1.setObjectName('counter')
		pn2 = QPushButton('Quit')
		pn2.clicked.connect(self.fileQuit)
		h1 = QHBoxLayout()
		n1 = QLabel('SAMPLES')
		self.txtSamples = QLineEdit()
		h1.addWidget(n1)
		h1.addWidget(self.txtSamples)
		v.addWidget(pn1)
		v.addWidget(pn2)
		v.addLayout(h1)
		v.addStretch()

		pn1 = QLineEdit()
		pn1.setObjectName('frames')
		h1 = QHBoxLayout()
		n1 = QLabel('FRAMES')
		self.txtFrames = QLineEdit()
		h1.addWidget(n1)
		h1.addWidget(self.txtFrames)
		v1.addWidget(pn1)
		v1.addLayout(h1)
		v1.addStretch()

		self.main_widget.setFocus()
		self.setCentralWidget(self.main_widget)
		self.statusBar().showMessage("All hail matplotlib!", 2000)

	def showTime(self):
		k = self.children()
		# print('enter showTime {}'.format(len(k)))
		e = self.findChild(QLineEdit, 'counter')
		if None != e:
			e.setText('')
		ADC.status()  # update status
		if 0 == ADC.flag.b.BUSY:
			ADC.send('startad {}, {}, 1, 0'.format(4096, 1))  # setup ADC
		if 1 == ADC.flag.b.END:
			x = []
			for i in range(4096):
				x.append(i)
			for it in self.main_widget.findChildren(Oscillo):
				nm = it.objectName()
				f = int(nm[5:])
				# print(nm, f)
				adcos, adsin = ADC.readadf(f*4096, 4096, 1)
				it.osc.update_figure(x, adcos, adsin)
			#  startad wavelength, HW-iteration, colums, flip_onoff
			ADC.send('startad {}, {}, 1, 0'.format(4096, 1))  # setup ADC
			# onepulse()
			pass
		else:
			# print(adcst)
			pass

	def fileQuit(self):
		self.close()

	def closeEvent(self, ce):
		self.fileQuit()

	def about(self):
		QMessageBox.about(self, "About",
						  """embedding_in_qt5.py example
Copyright 2005 Florent Rougon, 2006 Darren Dale, 2015 Jens H Nielsen

This program is a simple example of a Qt5 application embedding matplotlib
canvases.

It may be used and modified with no restriction; raw copies as well as
modified versions may be distributed without limitation.

This is modified from the embedding in qt4 example to show the difference
between qt4 and qt5"""
						  )


def is_adc():
	a = ADC.status()
	return a


def onepulse():
	iteration = 0  # forever
	wavesize = 4096
	PUL.send('stop')
	PUL.wait()

	# ADC.send('startad {}, {}, 1, 0'.format(4096, 1))  # setup ADC
	# adc.send('startad {}, {}, 1, 0'.format(wavesize, iteration))  # setup ADC
	PUL.send('setmode 0')  # 0:standard pulse mode 1:extended pulse mode
	PUL.send('loopmode')
	PUL.send('usecomb 0')  # comb pulse not use
	PUL.send('cpn 1')  # comb pulse not use
	PUL.send('adtrg 1')  # 0:Spin echo position  1:Freedecay position
	PUL.send('double')  # double pulse mode
	PUL.send('adoff -100e-6')  # AD trigger offset
	PUL.send('fpw 20e-6')  # 1st pulse width
	PUL.send('t2  50e-6')
	PUL.send('spw 40e-6')  # 2nd pulse width
	PUL.send('fpq 0')  # 1st pulse +X QPSK1ST
	PUL.send('spq 1')  # 2nd pulse +Y QPSK2ND
	PUL.send('blank 1.0')
	# print('ad0:{:02X}'.format(0x07 & int(adc.query('readstatus'))))
	PUL.send('start {}'.format(iteration))
	# pul.wait()
	pass


ADC = prot_ad()
PUL = prot_pulser()


def main():
	ADC.init('localhost')
	s = ADC.open()
	if None == s:
		print('prot.py:error socket')
		return
	print('CONNECT [{}]'.format(s))
	PUL.init('localhost')
	s = PUL.open()
	if None == s:
		print('prot.py:error socket')
		return
	print('CONNECT [{}]'.format(s))

	onepulse()

	qApp = QApplication(sys.argv)
	aw = myAD()
	aw.setWindowTitle("%s" % progname)
	aw.show()
	sys.exit(qApp.exec_())
	ADC.close()
	PUL.close()
	pass


if __name__ == "__main__":
	main()
