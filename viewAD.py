#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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
		MyMplCanvas.__init__(self, *args, **kwargs)

	def compute_initial_figure(self):
		self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

	def update_figure(self, t, cosdata, sindata):
		# Build a list of 4 random integers between 0 and 10 (both inclusive)
		self.axes.cla()
		self.axes.set_ylabel('電圧')
		self.axes.set_ylim(-2.5, 2.5)
		self.axes.plot(t, cosdata, sindata, 'r')
		self.draw()


class MyStaticMplCanvas(MyMplCanvas):
	"""Simple canvas with a sine plot."""

	def compute_initial_figure(self):
		t = arange(0.0, 3.0, 0.01)
		s = sin(2 * pi * t)
		self.axes.plot(t, s)


class MyDynamicMplCanvas(MyMplCanvas):
	"""A canvas that updates itself every second with a new plot."""

	def __init__(self, *args, **kwargs):
		MyMplCanvas.__init__(self, *args, **kwargs)
		timer = QTimer(self)
		timer.timeout.connect(self.update_figure)
		timer.start(1000)

	def compute_initial_figure(self):
		self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

	def update_figure(self):
		# Build a list of 4 random integers between 0 and 10 (both inclusive)
		l = [random.randint(0, 10) for i in range(4)]
		self.axes.cla()
		self.axes.plot([0, 1, 2, 3], l, 'r')
		self.draw()


class myAD(QMainWindow):
	def __init__(self):
		QMainWindow.__init__(self)
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
		self.tools_widget = QWidget(self)

		self.timer = QTimer()
		self.timer.timeout.connect(self.showTime)
		self.timer.start(100)

		all = QHBoxLayout(self.main_widget)
		v = QVBoxLayout(self.tools_widget)
		l = QVBoxLayout(self.main_widget)
		all.addLayout(l)
		all.addLayout(v)

		self.osc = OscilloCanvas(self.main_widget, width=5, height=4, dpi=100)

		dk1 = QDockWidget('controls', self)
		dk1.setWidget(self.tools_widget)
		dk1.setFloating(False)
		self.addDockWidget(Qt.RightDockWidgetArea, dk1)

		l.addWidget(self.osc)

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

		self.main_widget.setFocus()
		self.setCentralWidget(self.main_widget)
		self.statusBar().showMessage("All hail matplotlib!", 2000)

	def showTime(self):
		k = self.children()
		# print('enter showTime {}'.format(len(k)))
		e = self.findChild(QLineEdit, 'counter')
		if None != e:
			e.setText('')
		adcst = (0x07 & adc.status())
		if 6 == adcst:
			x = []
			for i in range(4096):
				x.append(i)
			adcos, adsin = adc.readadf(0, 4096, 1)
			self.osc.update_figure(x, adcos, adsin)
			adc.send('startad {}, {}, 1, 0'.format(4096, 1))  # setup ADC
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
	a = adc.status()
	return a


def onepulse():
	iteration = 0  # forever
	wavesize = 4096
	pul.send('stop')
	pul.wait()

	adc.send('startad {}, {}, 1, 0'.format(4096, 1))  # setup ADC
	# adc.send('startad {}, {}, 1, 0'.format(wavesize, iteration))  # setup ADC
	pul.send('setmode 0')  # 0:standard pulse mode 1:extended pulse mode
	pul.send('loopmode')
	pul.send('usecomb 0')  # comb pulse not use
	pul.send('cpn 1')  # comb pulse not use
	pul.send('adtrg 1')  # 0:Spin echo position  1:Freedecay position
	pul.send('double')  # double pulse mode
	pul.send('adoff -100e-6')  # AD trigger offset
	pul.send('fpw 20e-6')  # 1st pulse width
	pul.send('t2  50e-6')
	pul.send('spw 40e-6')  # 2nd pulse width
	pul.send('fpq 0')  # 1st pulse +X QPSK1ST
	pul.send('spq 1')  # 2nd pulse +Y QPSK2ND
	pul.send('blank 1.0')
	# print('ad0:{:02X}'.format(0x07 & int(adc.query('readstatus'))))
	pul.send('start {}'.format(iteration))
	# pul.wait()
	# print('ad1:{:02X}'.format(0x07 & int(adc.query('readstatus'))))
	# adcos, adsin = adc.readadf(0, wavesize, iteration)
	# a = adc.query('readmemoryb {},4'.format(wavesize))
	# print(a)
	pass


adc = prot_ad()
pul = prot_pulser()


def main():
	adc.init('localhost')
	s = adc.open()
	if None == s:
		print('prot.py:error socket')
		return
	print('CONNECT [{}]'.format(s))
	pul.init('localhost')
	s = pul.open()
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
	adc.close()
	pul.close()
	pass


if __name__ == "__main__":
	main()
