#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ctypes
import time
import socket
import etools as et
import matplotlib.pyplot as plt

IP = '192.168.0.224'
PULSER_PORT = 5025  # PULSER
AD_PORT = 5026  # AD
RF_PORT = 5027  # RF LOWLEVEL


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
class tcp_client():
	my_socket = None

	def __init__(self):
		self.my_socket = None

	def close(self):
		self.my_socket.close()
		self.my_socket = None

	def connect(self, ip, port, timeout=5):
		s = socket.socket()
		s.settimeout(timeout)
		try:
			# self.dev_socket = socket.create_connection((ip, port), timeout)
			s.connect((ip, port))
			self.my_socket = s
			return self.my_socket
		except ConnectionRefusedError:
			print('{}-IP:{} PORT:{}:connect error'.format(self.__class__.__name__, ip, port))
			return None

	# -------------------------------------------------------------------
	def send_utf8(self, msg):
		bstr = msg.encode('utf-8')
		# print( 'chk---------------------------',bstr )
		self.my_socket.sendall(bstr)
		return

	# -------------------------------------------------------------------
	def recv_utf8(self, rxlen):  # 指定バイト数を読まなくても戻る
		bans = self.my_socket.recv(rxlen)
		if None == bans:
			return ''
		ans = bans.decode('utf-8')
		return ans

	def recv_utf8_sized(self, rxlen):  # 指定バイト数読み込むまで戻らない。
		block_size = 4096
		if rxlen < block_size:
			block_size = rxlen
		remain = rxlen
		ans = ''
		while 0 < remain:
			b1 = self.my_socket.recv(block_size)
			if None == b1:
				return ''
			# print('recv_utf8:-2:{} -1:{}'.format(bans[-2], bans[-1] ))
			ans += b1.decode('utf-8')
			remain -= len(b1)
		return ans

	# -------------------------------------------------------------------
	def send(self, msg):
		cmdstr = msg + '\n'  # CTRL+J
		self.send_utf8(cmdstr)

	def query(self, msg, rxlen=1024):
		if None == self.my_socket:
			print('error not open')
		self.send(msg+'\r\n')
		tans = self.recv_utf8(rxlen)
		ans = tans.strip()
		return ans


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
class prot_pulser(tcp_client):
	"""
	使用できる関数一覧
	import prot
	pul = prot.prot_pulser()	インスタンス生成
	pul.init(ip,port)			接続情報の設定
	pul.open()					*IDNの文字列を返す
	pul.send('start 0')			コマンド実行
	"""

	class puldatc:
		def __init__(self, t1, d1):
			self.t = t1
			self.d = d1

	def __init__(self, ip='localhost'):
		super().__init__()
		self.MAX_PULMEM = 6000
		self.internal_clock = 100e6  # 100MHz
		self.ip = ip
		self.port = PULSER_PORT
		self.mem = []
		for i in range(self.MAX_PULMEM):
			p = self.puldatc(0xfeffffff, 0)
			self.mem.append(p)
		p = self.puldatc(0xffffffff, 0)
		self.mem.append(p)

	def dump(self, st, num):
		for i in range(num):
			t = self.mem[st + i].t
			d = self.mem[st + i].d
			dt = t / self.internal_clock
			print('{:08X}:{:08X} --- {}'.format(t, d, et.time2str(dt)))

	# -------------------------------------------------------------------
	def wait(self):
		while 'RUN' == self.query('isrun?'):
			time.sleep(1e-3)

	def startpulser(self, num):
		self.send('start {}'.format(num))

	def isrun(self):
		a = self.query('isrun?')
		return a



	def init(self, ip='localhost', port=PULSER_PORT):
		self.ip = ip
		self.port = port

	def open(self):
		ans = self.connect(self.ip, self.port)
		if None == ans:
			print('ERROR {}.init()'.format(self.__class__.__name__))
			return None
		self.send('setmode 0')
		ans_idn = self.query('*IDN?')
		p1 = ans_idn.find(',CLK=')
		if 0 <= p1:
			p1 += 5
			p2 = ans_idn.find(',', p1)
			if 0 <= p2:
				s1 = ans_idn[p1:p2]
				clk = et.str2freq(s1)
				self.internal_clock = clk
		# print('clk:{}'.format(self.internal_clock))
		else:
			print(' BIT ERROR {}.init()'.format(self.__class__.__name__))
		return ans_idn

	def close(self):
		super().close()


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

def test1(pul):
	print('Start------------ {} '.format(pul.query('*idn?')))
	pul.send('setmode 0')
	pul.send('loopmode')
	pul.send('single')
	pul.send('adoff 0')
	pul.send('fpw 100e-6')
	pul.send('blank 0.001')
	ct = 0
	for i in range(5000):
		t1 = time.perf_counter()
		pul.send('start 1')
		pul.wait()
		t2 = time.perf_counter()
		print('ct:{} t:{:f}'.format(ct, t2 - t1))
		ct += 1



# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
def main():  # SELF TEST PROGRAM
	print('start self test program')
	# パルサーを開く
	pul = prot_pulser()
	pul.init(IP)
	s = pul.open()
	if None == s:
		print('prot.py:error socket')
		return
	print('CONNECT [{}]'.format(s))
	pul.send('memclr')
	for i in range(1000):
		a = pul.query(('peek {}'.format(i+50)))
		if 0 > a.find(':FEFF'):
			print(a)
	return













	# パルス作成　1回のみ
	iteration = 100
	wavesize = 4096
	pul.send('stop')
	pul.wait()

	pul.send('setmode 0')      # 0:standard pulse mode 1:extended pulse mode
	pul.send('loopmode')
	pul.send('usecomb 0')      # comb pulse not use
	pul.send('cpn 1')          # comb pulse not use
	pul.send('adtrg 1')        # 0:Spin echo position  1:Freedecay position
	pul.send('double')         # double pulse mode
	pul.send('adoff -100e-6')  # AD trigger offset
	pul.send('fpw 200e-6')      # 1st pulse width
	pul.send('t2  50e-6')
	pul.send('spw 40e-6')      # 2nd pulse width
	pul.send('fpq 0')          # 1st pulse +X QPSK1ST
	pul.send('spq 1')          # 2nd pulse +Y QPSK2ND
	pul.send('blank 0.1')
	pul.send('start {}'.format(iteration)) 	# パルス出力開始
	pul.wait()                              # パルス出力の待ち合わせ
	print('wait ok')
	pul.close()
	return


# -------------------------------------------------------------------
# -------------------------------------------------------------------
if __name__ == "__main__":
	# a  = ADC_Flags()
	# a.asbyte = 0x0c
	# print(a.b.BUSY)
	# print(a.b.END)


	main()
	pass
