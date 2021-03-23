#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

def search_unit(ss):
	x = 0
	u = None
	s = ss.lower()

	x = s.find('n')
	if 0 < x:
		return x,1e-9
	x = s.find('u')
	if 0 < x:
		return x,1e-6
	x = ss.find('m')
	if 0 < x:
		return x,1e-3
	x = ss.find('M')
	if 0 < x:
		return x,1e6
	x = s.find('k')
	if 0 < x:
		return x,1e3
	return None,1

def str2time(ss):
	x, k = search_unit(ss)
	if None != x:
		v = float(ss[0:x]) * k
	else:
		v = float(ss)
	return v

def time2str(tt):
	t = abs(float(tt))
	ans = ''
	if 9990  < t:
		ans = '{:.0f}S'.format(float(tt))
	elif 999   < t:
		ans = '{:.0f}S'.format(float(tt))
	elif 99.9  < t:
		ans = '{:.1f}S'.format(float(tt))
	elif 9.99  < t:
		ans = '{:.2f}S'.format(float(tt))
	elif 0.999 < t:
		ans = '{:.3f}S'.format(float(tt))
	elif 99.9e-3  < t:
		ans = '{:.0f}mS'.format(float(tt)*1e3)
	elif 9.99e-3  < t:
		ans = '{:.1f}mS'.format(float(tt)*1e3)
	elif 0.999e-3 < t:
		ans = '{:.2f}mS'.format(float(tt)*1e3)
	elif 99.9e-6  < t:
		ans = '{:.3f}mS'.format(float(tt)*1e3)
	elif 9.99e-6  < t:
		ans = '{:.1f}uS'.format(float(tt)*1e6)
	else:
		ans = '{:.2f}uS'.format(float(tt)*1e6)
	return ans

def str2freq(ss):
	x, k = search_unit(ss)
	if None != x:
		v = float(ss[0:x]) * k
	else:
		v = float(ss)
	return v

def freq2str(tt):
	t = abs(float(tt))
	ans = ''
	if  10e9  <= t:
		ans = '{:.2f}GHz'.format(float(tt)*1e-9)
	elif 1e9  <= t:
		ans = '{:.3f}GHz'.format(float(tt)*1e-9)
	elif 100e6 <= t:
		ans = '{:.1f}MHz'.format(float(tt)*1e-6)
	elif 10e6  <= t:
		ans = '{:.2f}MHz'.format(float(tt)*1e-6)
	elif 1e6   <= t:
		ans = '{:.3f}MHz'.format(float(tt)*1e-6)
	elif 100e3 <= t:
		ans = '{:.1f}kHz'.format(float(tt)*1e-3)
	elif 10e3  <= t:
		ans = '{:.2f}kHz'.format(float(tt)*1e-3)
	elif 1e3   <= t:
		ans = '{:.3f}kHz'.format(float(tt)*1e-3)
	else:
		ans = '{:.1f}Hz'.format(float(tt))
	return ans




def main():
	a = -1e-3
	print(time2str(a))


#-------------------------------------------------------------------
#-------------------------------------------------------------------
if __name__ == "__main__":
	main()
	pass





