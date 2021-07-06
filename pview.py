#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import math
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import json
import time
import struct
import prot
import etools as et
import pickle
import resizetimer



IP = 'localhost'

bit_name = [  		# bit
	'TX1',  		# 0
	'TX2',  		# 1
	'AUX',  		# 2
	'QPSK1',  		# 3
	'QPSK2',  		# 4
	'AUX2',  		# 5
	'TRG.OUT',  	# 6
	'METER',  		# 7
	'AUX9',  		# 8
	'AD.TRG',  		# 9
	'AUX3',  		# 10
	'COMB/DA.TRG',  # 11
	"1'st/AUX6",  	# 12
	"2'nd/AUX7",  	# 13
	'AUX4',  		# 14
	'AUX10',  		# 15
]


class PUL_P: # 設定の保存用
	cpw      = 0.1e-6
	cpi      = 0.1e-6
	cpn      = 0
	cpq      = 0
	tj       = 1e-3
	fpw      = 0.1e-6
	fpq      = 0
	t2       = 1e-3
	spw      = 0.1e-6
	blank    = 1
	adoff    = 1e-6
	waitmode = False
	usecomb  = False
	double   = False
	waitmode = False

# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
class Canvas(QWidget):
	resize1 = pyqtSignal()
	click1 = pyqtSignal()

	def __init__(self, parent=None):
		super(Canvas, self).__init__(parent)
		self.myPenWidth = 1
		self.myPenColor = Qt.black
		self.image = QImage()
		self.check = False

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.click1.emit()

	def mouseMoveEvent(self, event):
		if event.buttons() and Qt.LeftButton and self.check:
			pass

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.LeftButton and self.check:
			pass

	def drawLine(self, x1, y1, x2, y2):
		painter = QPainter(self.image)
		painter.setPen(
			QPen(self.myPenColor, self.myPenWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
		)
		painter.drawLine(x1, y1, x2, y2)
		self.update()

	def drawText(self, x1, y1, msg, angle=0.0):
		rad = (angle * math.pi) / 180
		x2 = int(x1 * math.cos(rad) + (-1 * math.sin(rad)) * y1)
		y2 = int(x1 * math.sin(rad) + (1 * math.cos(rad)) * y1)

		painter = QPainter(self.image)
		painter.setPen(
			QPen(self.myPenColor, self.myPenWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
		)
		painter.rotate(0 - angle)
		painter.drawText(x2, y2, msg)
		painter.rotate(angle)
		self.update()

	def paintEvent(self, event):
		painter = QPainter(self)
		rect = event.rect()
		painter.drawImage(rect, self.image, rect)

	def resizeEvent(self,event):
		if self.image.width() < self.width() or self.image.height() < self.height():
			changeWidth = max(self.width(), self.image.width())
			changeHeight = max(self.height(), self.image.height())
			self.image = self.resizeImage(self.image, QSize(changeWidth, changeHeight))
			self.update()
			self.resize1.emit()

	def resizeImage(self, image, newSize):
		changeImage = QImage(newSize, QImage.Format_RGB32)
		changeImage.fill(qRgb(255, 255, 255))
		painter = QPainter(changeImage)
		painter.drawImage(QPoint(0, 0), image)
		return changeImage

	def saveImage(self, filename):
		if self.image.save(filename):
			return True
		else:
			return False

	def loadImage(self, filename):
		image = QImage()
		if not image.load(filename):
			return False

		self.image = image
		self.update()
		return True

	def penColor(self):
		return self.myPenColor

	def penWidth(self):
		return self.myPenWidth

	def setPenColor(self, newColor):
		self.myPenColor = newColor

	def setPenWidth(self, newWidth):
		self.myPenWidth = newWidth

	def resetImage(self):
		self.image.fill(qRgb(255, 255, 255))
		self.update()


# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------
class MainWindow(QMainWindow):
	ok = 0
	mem = []
	rot = 0

	def __init__(self):
		super(MainWindow, self).__init__()
		# print('enter {}.__init__()'.format(self.__class__.__name__))
		self.mem = []
		self.cv = Canvas()
		# check
		self.statusBar().showMessage('Ready')

		qcore = QWidget(self)
		c1 = QVBoxLayout(qcore)
		c1.addWidget(self.cv)
		b = QScrollBar(self)
		b.setOrientation(Qt.Horizontal)
		c1.addWidget(b)



		# check1
		self.setCentralWidget(qcore)

		self.pul = prot.prot_pulser()
		s = self.pul.init(IP)
		self.pulpara = self.query_all_pulser()
		self.mem = self.pul.readmemoryb(0, 30)

		self.InitUI()
		self.ct = 0
		# for m1 in self.mem:
		# 	print('{:08X}:{:08X}'.format(m1.t,m1.d))
		# 	print(type(self.mem))
		self.ok = 1
		self.cv.click1.connect(self.draw_mem)
		self.cv.resize1.connect(self.resizeA)

		self.delayTimeout = 1000
		self._resizeTimer = QTimer(self)
		self._resizeTimer.timeout.connect(self._delayedUpdate)


	ct1=0
	def resizeA(self):
		print('resizeA({})'.format(self.ct1))
		self.ct1 += 1
		self._resizeTimer.start(self.delayTimeout)

	def _delayedUpdate(self):
		print("Performing actual update")
		self._resizeTimer.stop()
		self.draw_mem()
		# self.setUpdatesEnabled(True)



	def query_all_pulser(self): # HW -> python
		p = self.pul
		p1 = PUL_P()
		p1.usecomb  = True if int(p.query('usecomb?')) == 1 else False
		p1.double   = True if int(p.query('double?')) == 1 else False
		p1.cpw      = et.str2time(p.query('cpw?'))
		p1.cpi      = et.str2time(p.query('cpi?'))
		p1.cpn      = int(p.query('cpn?'))
		p1.cpq      = int(p.query('cpq?'))
		p1.tj       = et.str2time(p.query('tj?'))
		p1.fpw      = et.str2time(p.query('fpw?'))
		p1.fpq      = int(p.query('fpq?'))
		p1.t2       = et.str2time(p.query('t2?'))
		p1.spw      = et.str2time(p.query('spw?'))
		p1.spq      = int(p.query('spq?'))
		p1.blank    = et.str2time(p.query('blank?'))
		p1.adoff    = et.str2time(p.query('adoff?'))
		p1.waitmode = True if int(p.query('waitmode?')) == 1 else False
		return p1

	def setWidget(self,p):
		pass

	def send_all_pulser(self): # python -> HW
		p = self.pul
		d = self.pulpara
		p.send('usecomb '+'1' if d.usecomb == True else '0')
		p.send( 'double '+'1' if d.double  == True else '0')
		p.send('cpw {}'.format( d.cpw))
		p.send('cpi {}'.format( d.cpi))
		p.send('cpn {}'.format( d.cpn))
		p.send('cpq {}'.format( d.cpq))
		p.send('tj {}'.format( d.tj))
		p.send('fpw {}'.format( d.fpw))
		p.send('fpq {}'.format( d.fpq))
		p.send('t2 {}'.format( d.t2))
		p.send('spw {}'.format( d.spw))
		p.send('spq {}'.format( d.spq))
		p.send('blank {}'.format( d.blank))
		p.send('adoff {}'.format( d.adoff))
		p.send( 'waitmode' if d.waitmode == True else 'loopmode')

	def sendpul(self, a):
		print('setcpw({} = {})'.format(a.lb.text(), a.tb.text()))
		sendok = 1
		if 0 < sendok:
			self.pul.send('stop')
			msg = a.lb.text() + ' ' + a.tb.text()
			print(msg)
			self.pul.send(msg)

	def setUsecomb(self):
		a = self.chkUseComb.isChecked()
		print('comb',a)
		if True == a:
			self.pul.send('usecomb 1')
		else:
			self.pul.send('usecomb 0')

	def setDouble(self):
		a = self.chkDouble.isChecked()
		print('double',a)
		if True == a:
			self.pul.send('double')
		else:
			self.pul.send('single')

	def setCPQ(self):
		a = self.cmbCPQ.currentIndex()
		print('setCPQ',a)
		self.pul.send('cpq {}'.format(a))

	def setFPQ(self):
		a = self.cmbFPQ.currentIndex()
		print('setFPQ',a)
		self.pul.send('fpq {}'.format(a))

	def setSPQ(self):
		a = self.cmbSPQ.currentIndex()
		print('setSPQ',a)
		self.pul.send('spq {}'.format(a))

	def makeLineEdit(self, label, text):
		lb = QLabel(label)
		le = QLineEdit(text)
		b = QHBoxLayout()
		b.addWidget(lb)
		b.addWidget(le)
		b.lb = lb
		b.tb = le
		le.editingFinished.connect(lambda: self.sendpul(b))
		return b, le

	def start(self):
		self.pul.send('start 0')

	def stop(self):
		self.pul.send('stop')

	def setLoop(self):
		print('send loop mode')
		self.pul.send('loopmode')

	def setWait(self):
		print('send wait mode')
		self.pul.send('waitmode')

	def Var2Panel(self,k):
		self.pulpara = k
		# self.send_all_pulser()
		self.chkUseComb.setChecked(k.usecomb)
		self.chkDouble.setChecked(k.double)
		self.txtFPW.setText(et.time2str(k.fpw))
		self.txtSPW.setText(et.time2str(k.spw))
		self.txtBLANK.setText(et.time2str(k.blank))
		self.txtADOFF.setText(et.time2str(k.adoff))
		self.txtT2.setText(et.time2str(k.t2))
		self.txtCPW.setText(et.time2str(k.cpw))
		self.txtCPI.setText(et.time2str(k.cpi))
		self.txtCPN.setText('{}'.format(k.cpn))
		self.txtTJ.setText(et.time2str(k.tj))
		self.cmbCPQ.setCurrentIndex(k.cpq)
		self.cmbFPQ.setCurrentIndex(k.fpq)
		self.cmbSPQ.setCurrentIndex(k.spq)
		self.btnWait.setChecked(k.waitmode)


	def Panel2Var(self):
		p = PUL_P()
		p.usecomb = self.chkUseComb.isChecked()
		p.double  = self.chkDouble.isChecked()
		p.fpw = et.str2time(self.txtFPW.text())
		p.spw = et.str2time(self.txtSPW.text())
		p.blank = et.str2time(self.txtBLANK.text())
		p.adoff = et.str2time(self.txtADOFF.text())
		p.t2 = et.str2time(self.txtT2.text())
		p.tj = et.str2time(self.txtTJ.text())
		p.cpw = et.str2time(self.txtCPW.text())
		p.cpi = et.str2time(self.txtCPI.text())
		p.cpn = int(self.txtCPN.text())
		p.cpq = self.cmbCPQ.currentIndex()
		p.fpq = self.cmbFPQ.currentIndex()
		p.spq = self.cmbSPQ.currentIndex()
		p.waitmode = self.btnWait.isChecked()
		return p


	def save(self):
		fn = 'settings.bin'
		p = self.Panel2Var()
		# p = self.query_all_pulser()
		print('pickle start ', p.fpw )
		with open(fn,'wb') as fd:
			pickle.dump(p, fd)
		print('pickle end')

	def load(self):
		print('load from settings.bin')
		fn = 'settings.bin'
#		k = self.query_all_pulser()
		with open(fn,'rb') as fd:
			k = pickle.load(fd)
		self.Var2Panel(k)

	def set_to_ui(self):
		self.cmbCPQ.setCurrentIndex(0)


	def InitUI(self):
		dockWidget = QDockWidget('control', self)
		dockWidget2 = QDockWidget('pulses', self)

		self.btn2 = QPushButton('START 0')
		self.btn2.clicked.connect(self.start)
		self.btn3 = QPushButton('STOP')
		self.btn3.clicked.connect(self.stop)
		self.btnDraw = QPushButton('DRAW')
		self.btnDraw.clicked.connect(self.draw_mem)

		dockWidget.setWidget(self.btnDraw)

		tool_center = QWidget(self)
		tool_left = QVBoxLayout(self)
		tool_right = QVBoxLayout(self)

		qv = QHBoxLayout(tool_center)
		qv.addLayout(tool_left)
		# qv.addLayout(tool_right)

		qv = tool_left
		a, le = self.makeLineEdit('cpw', et.time2str(self.pulpara.cpw))
		self.txtCPW = le
		# -------------------------------
		h = QHBoxLayout(self)
		h.addLayout(a)
		self.chkUseComb = QCheckBox('use')
		self.chkUseComb.setChecked(self.pulpara.usecomb)
		self.chkUseComb.stateChanged.connect( self.setUsecomb)
		h.addWidget(self.chkUseComb)
		qv.addLayout(h)
		# -------------------------------
		a,le = self.makeLineEdit('cpi', et.time2str(self.pulpara.cpi))
		self.txtCPI = le
		# -------------------------------
		h = QHBoxLayout(self)
		h.addLayout(a)
		c = QComboBox()
		c.addItems(['0','90','180','270'])
		c.setCurrentIndex(self.pulpara.cpq)
		c.activated.connect(self.setCPQ)
		self.cmbCPQ = c
		h.addWidget(self.cmbCPQ)
		qv.addLayout(h)
		# -------------------------------
		a,le = self.makeLineEdit('cpn', '{}'.format(self.pulpara.cpn))
		self.txtCPN = le
		qv.addLayout(a)
		a, le = self.makeLineEdit('tj', et.time2str(self.pulpara.tj))
		self.txtTJ = le
		qv.addLayout(a)
		a, le = self.makeLineEdit('fpw', et.time2str(self.pulpara.fpw))
		self.txtFPW = le
		# -------------------------------
		h = QHBoxLayout(self)
		h.addLayout(a)
		c = QComboBox()
		c.addItems(['0','90','180','270'])
		c.setCurrentIndex(self.pulpara.fpq)
		c.activated.connect(self.setFPQ)
		self.cmbFPQ = c
		h.addWidget(self.cmbFPQ)
		qv.addLayout(h)
		# -------------------------------
		a, le = self.makeLineEdit('t2', et.time2str(self.pulpara.t2))
		self.txtT2 = le
		# -------------------------------
		h = QHBoxLayout(self)
		h.addLayout(a)
		self.chkDouble = QCheckBox('use')
		self.chkDouble.setChecked(self.pulpara.double)
		self.chkDouble.stateChanged.connect( self.setDouble)
		h.addWidget(self.chkDouble)
		qv.addLayout(h)
		# -------------------------------
		a, le = self.makeLineEdit('spw', et.time2str(self.pulpara.spw))
		self.txtSPW = le
		# -------------------------------
		h = QHBoxLayout(self)
		h.addLayout(a)
		c = QComboBox()
		c.addItems(['0','90','180','270'])
		c.setCurrentIndex(self.pulpara.spq)
		c.activated.connect(self.setSPQ)
		self.cmbSPQ = c
		h.addWidget(self.cmbSPQ)
		qv.addLayout(h)
		# -------------------------------
		a, le = self.makeLineEdit('blank', et.time2str(self.pulpara.blank))
		self.txtBLANK = le
		qv.addLayout(a)
		a, le = self.makeLineEdit('adoff', et.time2str(self.pulpara.adoff))
		self.txtADOFF = le
		qv.addLayout(a)
		qv.addWidget(self.btn2)
		qv.addWidget(self.btn3)

		qh = QHBoxLayout()
		a = QRadioButton('loop')
		if True == self.pulpara.waitmode:
			a.setChecked(False)
		else:
			a.setChecked(True)
		a.clicked.connect(self.setLoop)
		qh.addWidget(a)
		self.btnLoop = a

		a = QRadioButton('wait')
		if True == self.pulpara.waitmode:
			a.setChecked(True)
		else:
			a.setChecked(False)
		a.clicked.connect(self.setWait)
		qh.addWidget(a)
		self.btnWait = a
		qv.addLayout(qh)

		b = QPushButton('save')
		b.clicked.connect(self.save)
		qv.addWidget(b)
		b = QPushButton('load')
		b.clicked.connect(self.load)
		qv.addWidget(b)

		qv.addStretch()
		# check2
		dockWidget2.setWidget(tool_center)

		dockWidget.setFloating(False)
		dockWidget2.setFloating(False)
		self.addDockWidget(Qt.RightDockWidgetArea, dockWidget)
		self.addDockWidget(Qt.RightDockWidgetArea, dockWidget2)

		# アイコン付加、ラベルはExitのアクションオブジェクト作成
		exitAction = QAction(QIcon('imoyokan.jpg'), '&Exit', self)
		# ショートカットできるようにする
		exitAction.setShortcut('Ctrl+Q')
		# カーソルを乗せるとステータスバーへ表示
		exitAction.setStatusTip('Exit application')
		# Exitボタンを押すと表示終了
		exitAction.triggered.connect(qApp.quit)

		# メニューバー作成
		menubar = self.menuBar()
		fileMenu = menubar.addMenu('&File')
		# exitActionを紐づける
		fileMenu.addAction(exitAction)
		self.setGeometry(300, 300, 800, 600)
		self.setWindowTitle('PVIEW for nmrtcp')
		self.show()

	def draw_mem(self):
		lineHeight = 15
		self.pul.send('update')  # メモリーのアップデート
		self.mem = self.pul.readmemoryb(0, 30)
		# for i in self.mem:
		# 	print( '{:08X} -- {:08X}'.format(i.t, i.d))
		self.cv.resetImage()
		add = 0
		x = self.cv.height()
		y = self.cv.width()
		print('size:{},{}'.format(x,y))


		for i in range(16):  # BIT TITLE
			y = i * lineHeight + 100 + 5
			self.cv.setPenColor(Qt.black)
			self.cv.drawText(10, y, '{} {}'.format(i, bit_name[i]), 0)
			self.cv.setPenColor(Qt.gray)
			self.cv.drawLine(0, y, 300, y)

		for k in self.mem:
			add += 1
			x = add * 20 + 80
			self.cv.setPenColor(Qt.gray)
			self.cv.drawLine(x, 0, x, 400)
			self.cv.setPenColor(Qt.blue)
			lp = [0] * 16
			dt = (1 / self.pul.internal_clock) * k.t
			self.cv.setPenColor(Qt.blue)
			if 0xff000000 == (0xff000000 & k.t):
				if 0xffffffff == k.t:
					self.cv.drawText(x + 13, 80, 'EOF', 90)
				elif 0xff200000 == k.t:
					self.cv.drawText(x + 13, 80, 'GOTO', 90)
				elif 0xff400000 == k.t:
					self.cv.drawText(x + 13, 80, 'STOP', 90)
				elif 0xff800000 == k.t:
					self.cv.drawText(x + 13, 80, 'TRG', 90)
				else:
					self.cv.drawText(x + 13, 80, '{:08X}'.format(k.t), 90)
			else:
				self.cv.drawText(x + 13, 80, '{}'.format(et.time2str(dt)), 90)

			self.cv.setPenColor(Qt.blue)
			for i in range(16):
				y = i * lineHeight + 100
				lp[i] = k.d & (1 << i)
				if lp[i]:
					self.cv.setPenWidth(2)
					self.cv.drawLine(x, y, x + 20, y)
					pass
				else:
					self.cv.setPenWidth(1)
					self.cv.drawLine(x, y + 5, x + 20, y + 5)
					pass


def main2():
	app = QApplication(sys.argv)
	w = MainWindow()
	sys.exit(app.exec_())

# -------------------------------------------------------------------
# -------------------------------------------------------------------
if __name__ == "__main__":
	main2()

### EOF ###
