#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import socket
import etools as et

IP = 'localhost'
PULSER_PORT = 5025  # PULSER
AD_PORT = 5026  	# AD
RF_PORT = 5027  	# RF LOWLEVEL


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
class tcp_client():
	dev_socket = []

	def close(self):
		self.dev_socket.close()

	def connect(self, ip, port, timeout=5):
		s = socket.socket()
		s.settimeout(timeout)
		try:
			# self.dev_socket = socket.create_connection((ip, port), timeout)
			s.connect((ip, port))
			self.dev_socket = s
			return self.dev_socket
		except ConnectionRefusedError:
			print('{}-IP:{} PORT:{}:connect error'.format(self.__class__.__name__, ip, port))
			return None

	# -------------------------------------------------------------------
	def send_utf8(self, msg):
		bstr = msg.encode('utf-8')
		# print( bstr )
		self.dev_socket.sendall(bstr)
		return

	# -------------------------------------------------------------------
	def recv_utf8(self, rxlen):  # 指定バイト数を読まなくても戻る
		bans = self.dev_socket.recv(rxlen)
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
			b1 = self.dev_socket.recv(block_size)
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
		cmdstr = msg + '\n'
		self.send(cmdstr)
		tans = self.recv_utf8(rxlen)
		ans = tans.strip()
		return ans
# -------------------------------------------------------------------


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
class prot_pulser(tcp_client):
	MAX_PULMEM = 3000
	"""
	使用できる関数一覧
	import prot
	pul = prot.prot_pulser()
	pul.init(ip,port)		*IDNの文字列を返す
	pul.send('start 0')
	"""

	class puldatc:
		def __init__(self, t1, d1):
			self.t = t1
			self.d = d1

	def __init__(self):
		self.internal_clock = 100e6  # 100MHz
		self.mem = []
		for i in range(self.MAX_PULMEM ):
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
			time.sleep(10e-3)

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

	def init(self, ip):
		port = PULSER_PORT
		ans = self.connect(ip, port)
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


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
class prot_ad(tcp_client):
	"""
	使用できる関数一覧
	import prot
	adc = prot.prot_ad()
	adc.init(ip,port)		*IDNの文字列を返す
	"""
	bitwidth = 16

	# -------------------------------------------------------------------
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
		for x in dcos:
			v = float(x) / float(iteration)
			f = (v - 32768.0) / 13107.2  # 13107.2=(32768.0/2.5)	#±2.5にする。
			fcos.append(f)
		for x in dsin:
			v = float(x) / float(iteration)
			f = (v - 32768.0) / 13107.2  # 13107.2=(32768.0/2.5)	#±2.5にする。
			fsin.append(f)
		return fcos, fsin

	def init(self, ip):
		port = AD_PORT
		ans = self.connect(ip, port)
		if None == ans:
			print('ERROR {}.init()'.format(self.__class__.__name__))
			return None
		ans_idn = self.query('*IDN?')
		p = ans_idn.find(',BIT=')
		if 0 <= p:
			self.bitwidth = int(ans_idn[p + 5:p + 7])
			# print('bit:{}'.format(self.bitwidth))
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
	rfl.init(ip,port)		*IDNの文字列を返す
	rfl.send('rfsww0')
	rfl.query('*idn?')
	"""

	# -------------------------------------------------------------------
	def query(self, msg):
		self.send(msg)
		a = self.recv_utf8(100)
		while 2 == len(a):
			a = self.recv_utf8(100)
		ans = a.strip()
		return ans

	def init(self, ip):
		port = RF_PORT
		# print('{}-IP:{} PORT{}'.format(self.__class__.__name__, ip, port ))
		ans = self.connect(ip, port)
		if None == ans:
			print('ERROR {}.init()'.format(self.__class__.__name__))
			return None
		ans_idn = self.query('*IDN?')
		return ans_idn


# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
def main():  # SELF TEST PROGRAM
	print('start self test program')

	pul = prot_pulser()
	s = pul.init(IP)
	if None == s:
		print('prot.py:error socket')
		return
	print('CONNECT [{}]'.format(s))

	adc = prot_ad()
	s = adc.init(IP)
	if None == s:
		print('prot.py:error socket')
		return
	print('CONNECT [{}]'.format(s))

	rfl = prot_rf()
	s = rfl.init(IP)
	if None == s:
		print('prot.py:error socket')
		return
	print('CONNECT [{}]'.format(s))

	iteration = 1
	wavesize = 4096
	pul.send('stop')
	pul.wait()
	adc.send('startad {}, {}, 1, 0'.format(wavesize, iteration))

	pul.send('setmode 0')
	pul.send('loopmode')
	pul.send('single')
	pul.send('adoff -100e-6')
	pul.send('fpw 100e-6')
	pul.send('blank 0.1')
	pul.send('start {}'.format(iteration))
	pul.wait()

	pul.readmemoryb(0, 10)
	a = pul.readmemoryb(2, 3)
	pul.dump(0, 10)
	print('----------')
	for b in a:
		print('{:08X}:{:08X}'.format(b.t, b.d))

	adcos, adsin = adc.readadf(0, wavesize, iteration)
	#	print(adcos)
	print(len(adcos))
	#	a1 = plt.subplot()
	#	a1.set_ylim([-2,2])
	#	a1.plot(adcos)
	#	a2 = plt.subplot()
	#	a2.set_ylim([-2,2])
	#	a2.plot(adsin)
	#	plt.show()
	#	a = adc.query('readmemoryb {},4'.format(wavesize))
	#	print(a)

	rfl.close()
	adc.close()
	pul.close()
	return

# -------------------------------------------------------------------
# -------------------------------------------------------------------
if __name__ == "__main__":
	main()
	pass
