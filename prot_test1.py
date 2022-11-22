
import prot
import matplotlib.pyplot as plt

# 描画機能を用いるので matplotlibが必要です。
#  NMRTCP main.exeテストプログラム
# あらかじめ main.exeを起動しておくこと。
# 1.パルサー,ＡＤ,RFローレベルに接続する。
# 2.ADの準備を行う
# 3.パルスを1回打つ
# 4.ADを読み出し描画
#
def main():
	host_ip = 'localhost'
	print('start prot_test1.py')
	# パルサーを開く
	pul = prot.prot_pulser()
	pul.init(host_ip)
	s = pul.open()
	if None == s:
		print('prot.py:error connect pulser')
		return
	print('CONNECT [{}]'.format(s))

	# ADを開く
	adc = prot.prot_ad()
	adc.init(host_ip)
	s = adc.open()
	if None == s:
		print('prot.py:error connect ad')
		return
	print('CONNECT [{}]'.format(s))

	# RF制御部分を開く
	rfl = prot.prot_rf()
	rfl.init(host_ip)
	s = rfl.open()
	if None == s:
		print('prot.py:error connect RF low level')
		return
	print('CONNECT [{}]'.format(s))

	# パルス作成　1回のみ
	iteration = 1
	wavesize = 4096
	pul.send('stop')
	pul.wait()                 # パルサー停止まで待ち合わせ
	rfl.send('RFSWW1')

	adc.send('startad {}, {}, 1, 0'.format(wavesize, iteration))  # setup ADC

	pul.send('setmode 0')      # 0:standard pulse mode 1:extended pulse mode
	pul.send('loopmode')
	pul.send('usecomb 0')      # comb pulse not use
	pul.send('cpn 1')          # comb pulse not use
	pul.send('adtrg 1')        # 0:Spin echo position  1:Freedecay position
	pul.send('double')         # double pulse mode
	pul.send('adoff -100e-6')  # AD trigger offset
	pul.send('fpw 20e-6')      # 1st pulse width
	pul.send('t2  50e-6')
	pul.send('spw 40e-6')      # 2nd pulse width
	pul.send('fpq 0')          # 1st pulse +X QPSK1ST
	pul.send('spq 1')          # 2nd pulse +Y QPSK2ND
	pul.send('blank 1')
	pul.send('start {}'.format(iteration)) 	# パルス出力開始
	pul.wait()                              # パルサー停止の待ち合わせ

	adcos, adsin = adc.readadf(0, wavesize, iteration) # ＡＤは取り込みが終わっているはずなのでメモリー読みだし
	rfl.send('RFSWW0')

	rfl.close()
	adc.close()
	pul.close()

	# MATPLOTLIBを用いてadcos,adsinデータの表示
	a1 = plt.subplot()
	a1.set_ylim([-2, 2])  # voltage is -2.0..2.0V
	a1.plot(adcos)
	a2 = plt.subplot()
	a2.set_ylim([-2, 2])
	a2.plot(adsin)
	plt.show()

	return


# -------------------------------------------------------------------
# -------------------------------------------------------------------
if __name__ == "__main__":
	main()
	pass
