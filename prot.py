#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import socket
import etools as et
import matplotlib.pyplot as plt


IP = 'localhost'
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
		self.send(msg)
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

	def __init__(self):
		super().__init__()
		self.MAX_PULMEM = 3000
		self.internal_clock = 100e6  # 100MHz
		self.ip = 'localghost'
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

	def readmemoryb(self, st_add, num):
		self.send('readmemoryb {},{}'.format(st_add, num))
		ans = self.recv_utf8(16)
		data_bytes = int(ans[7:7 + 8], base=16)
		ans = self.recv_utf8_sized(data_bytes)
		vals = int((data_bytes - 2) / 16)
		for i in range(vals):
			self.mem[st_add + i].t = int(ans[i * 16:i * 16 + 8], base=16)
			self.mem[st_add + i].d = int(ans[i * 16 + 8:i * 16 + 16], base=16)
		return self.mem[st_add: st_add + num]

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
class prot_ad(tcp_client):
	"""
	使用できる関数一覧
	readadf()
	"""
	bitwidth = 16

	def __init__(self):
		super().__init__()
		self.ip = 'localhost'
		self.port = AD_PORT

	# -------------------------------------------------------------------
	def status(self):
		ans = int(self.query('readstatus'))
		return ans

	def getsamplefreq(self):
		ans = float(self.query('getsamplefreq'))
		return ans

	def readad_raw(self, address, samples):
		self.send('readmemoryb {},{}'.format(address, samples))
		ans = self.recv_utf8(16)
		data_bytes = int(ans[7:7 + 8], base=16)
		# print('samplesS:{}'.format(ans[7:7+8]))
		# print('samplesI:{}'.format(data_bytes))
		# samples = int('0x'+ ans[0])
		# print('size:{}'.format(data_bytes))
		ans = self.recv_utf8_sized(data_bytes)
		vals = int((data_bytes - 2) / 16)
		# print('vals:{}'.format(vals))
		# print('--------------', type(ans))
		# print('anslen:{}:{}'.format(len(ans),data_bytes))
		vcos = []
		vsin = []
		for i in range(vals):
			cosdat = int(ans[i * 16:i * 16 + 8], base=16)
			sindat = int(ans[i * 16 + 8:i * 16 + 16], base=16)
			# print(cosdat,sindat)
			vcos.append(cosdat)
			vsin.append(sindat)
		return vcos, vsin

	def readadf(self, address, samples, iteration):
		fcos = []
		fsin = []
		dcos, dsin = self.readad_raw(address, samples)
		if 16 == self.bitwidth:
			# ----------------------------- bit 16
			for i in dcos:
				v = float(i) / float(iteration)
				f = (v - 32768.0) / 13107.2  # 13107.2=(32768.0/2.5)	#±2.5にする。
				fcos.append(f)
			for i in dsin:
				v = float(i) / float(iteration)
				f = (v - 32768.0) / 13107.2  # 13107.2=(32768.0/2.5)	#±2.5にする。
				fsin.append(f)
		else:
			# ----------------------------- bit 14
			for i in dcos:
				v = float(i) / float(iteration)
				f = (v - 8192.0) / 3276.8  # 3276.8.2=(8192.0/2.5)	#±2.5にする。
				fcos.append(f)
			for i in dsin:
				v = float(i) / float(iteration)
				f = (v - 8192.0) / 3276.8  # 3276.8=(8192.0/2.5)	#±2.5にする。
				fsin.append(f)
		return fcos, fsin

	def init(self, ip='localhost', port = AD_PORT):
		self.ip = ip
		self.port = port

	def open(self):
		ans = self.connect(self.ip, self.port)
		if None == ans:
			print('ERROR {}.init()'.format(self.__class__.__name__))
			return None
		ans_idn = self.query('*IDN?')
		p = ans_idn.find(',BIT=')
		if 0 <= p:
			self.bitwidth = int(ans_idn[p + 5:p + 7])
			print('AD bit:{}'.format(self.bitwidth))
		else:
			print('AD BIT ERROR {}.init()'.format(self.__class__.__name__))
		return ans_idn


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
class prot_rf(tcp_client):
	"""
	使用できる関数一覧
	import prot
	rfl = prot.prot_rf()
	rfl.init(ip,port)	connect parameters 接続情報
	rfl.open()          接続に成功した場合　*IDNの文字列を返す
	rfl.send('rfsww0')	コマンド例
	rfl.query('*idn?')	コマンド例
	"""
	def __init__(self):
		super().__init__()
		self.ip = 'localhost'
		self.port = RF_PORT

	# -------------------------------------------------------------------
	def send(self, msg):
		super().send(msg)
		a = self.recv_utf8(100)
		return

	def query(self, msg):
		super().send(msg)
		a = self.recv_utf8(100)
		while 2 == len(a):
			a = self.recv_utf8(100)
		ans = a.strip()
		return ans

	def init(self, ip = 'localhost',port=RF_PORT):
		self.ip = ip
		self.port = port
		# print('{}-IP:{} PORT{}'.format(self.__class__.__name__, ip, port ))

	def open(self):
		ans = self.connect(self.ip, self.port)
		if None == ans:
			print('ERROR {}.init()'.format(self.__class__.__name__))
			return None
		ans_idn = self.query('*IDN?')
		return ans_idn


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


def test2(d):
	ct = 0
	for i in range(100):
		d.send('RFSWW0')
		d.send('RFSWW1')
		time.sleep(0.1)
	return


def test3(d):
	ct = 0
	a = 0
	for i in range(90):
		t1 = time.perf_counter()
		ans = d.query('GAINW{}'.format(a))
		ct += 1
		t2 = time.perf_counter()
		print('ct:{} Time:{:f} ans:{}'.format(ct, t2 - t1, ans))


# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
def main():  # SELF TEST PROGRAM
	print('start self test program')

	pul = prot_pulser()
	pul.init(IP)
	s = pul.open()
	if None == s:
		print('prot.py:error socket')
		return
	print('CONNECT [{}]'.format(s))

	adc = prot_ad()
	adc.init(IP)
	s = adc.open()
	if None == s:
		print('prot.py:error socket')
		return
	print('CONNECT [{}]'.format(s))

	rfl = prot_rf()
	rfl.init(IP)
	s = rfl.open()
	if None == s:
		print('prot.py:error socket')
		return
	print('CONNECT [{}]'.format(s))

	# test1(pul)
	# test2(rfl)
	# test3(rfl)

	iteration = 1
	wavesize = 4096
	pul.send('stop')
	pul.wait()

	adc.send('startad {}, {}, 1, 0'.format(wavesize, iteration))  # setup ADC
	pul.send('setmode 0')			# 0:standard pulse mode 1:extended pulse mode
	pul.send('loopmode')
	pul.send('usecomb 0')			# comb pulse not use
	pul.send('cpn 1')				# comb pulse not use
	pul.send('adtrg 1')				# 0:Spin echo position  1:Freedecay position
	pul.send('double')				# double pulse mode
	pul.send('adoff -100e-6')		# AD trigger offset
	pul.send('fpw 20e-6')       	# 1st pulse width
	pul.send('t2  50e-6')
	pul.send('spw 40e-6')			# 2nd pulse width
	pul.send('fpq 0')				# 1st pulse +X QPSK1ST
	pul.send('spq 1')				# 2nd pulse +Y QPSK2ND
	pul.send('blank 0.1')
	pul.send('start {}'.format(iteration))
	pul.wait()

	allpulmem = pul.readmemoryb(0, 3000)

	a = pul.readmemoryb(2, 3)
	pul.dump(0, 10)
	print('----------')
	for b in a:
		print('{:08X}:{:08X}'.format(b.t, b.d))

	adcos, adsin = adc.readadf(0, wavesize, iteration)
	# a = adc.query('readmemoryb {},4'.format(wavesize))
	# print(a)

	rfl.close()
	adc.close()
	pul.close()


	# print('adcos len=',len(adcos))
	#	print(adcos)
	# print(len(adcos))
	a1 = plt.subplot()
	a1.set_ylim([-2,2])	# voltage is -2.0..2.0V
	a1.plot(adcos)
	a2 = plt.subplot()
	a2.set_ylim([-2,2])
	a2.plot(adsin)
	plt.show()

	return


# -------------------------------------------------------------------
# -------------------------------------------------------------------
if __name__ == "__main__":
	main()
	pass
