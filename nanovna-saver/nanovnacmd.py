
#  nanovnacmd - a python module meant to be used as a command line (or notebook) tool
#		which uses NanoVNASaver (https://github.com/NanoVNA-Saver/nanovna-saver)
#		to perform time and frequency domain measurements. 
#
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
#
# To use:
# 1. Download, install, and test NanoVNA-Saver.
# 2. Place this script in the top level directory of the program (same folder as nanovna-saver.py)
#
#
#  Examples:

# ### setup ###
# import nanovnacmd as nv
# import numpy as np
# import matplotlib.pyplot as plt
# #connect to the nanovna
# vna = nv.connect()

# ### calibration ###
# #calculate the frequency range for the tdr lab
# #use a frequency range with 101 steps (102 when including the extrapolated DC value)
# fwithDC = np.linspace(0,1.01e9,102)

# #set the frequencies
# vna.setSweep(fwithDC[1],fwithDC[-1])

# #1 port calibration - short, open, load
# calibration = nv.calibrate1port(vna)
# # #2 port calibration - short, open, load, through, isolation (cap the two lines w/ 50 ohms)
# # calibration = nv.calibrate2port(vna)

# ### frequency domain measurement #### 
# #take a measurement using the calibration object
# f,s11,s21 = nv.measure(vna,calibration)

# #take a measurement without calibration
# # f,s11,s21 = nv.measure(vna,nv.Calibration())

# #plot the measurement
# plt.plot(f/1e9,20*np.log10(np.abs(s11)),label='S11')
# plt.plot(f/1e9,20*np.log10(np.abs(s21)),label='S21')
# plt.xlabel('Frequency (GHz)')
# plt.ylabel('S parameter (dB)')
# plt.ylim(-80,5)
# plt.show()

# plt.plot(f/1e9,np.angle(s11),label='S11')
# plt.plot(f/1e9,np.angle(s21),label='S21')
# plt.xlabel('Frequency (GHz)')
# plt.ylabel('Phase (rad)')
# plt.ylim(-np.pi,np.pi)
# plt.show()

# ### time domain measurement ###
# # #take the measurement
# # f,s11,s21 = nv.measure(vna,calibration)
# # #calculate the time domain response
# # t,tdstep = nv.calculateTDR(f,s11)

# #measure the frequency domain response
# #and calculate the time domain response
# t,tdstep = nv.measureTDR(vna,calibration)

# #plot the real and imaginary parts 
# #(the imaginary part should be zero unless we made a mistake)
# plt.plot(t*1e9,np.real(tdstep))
# plt.plot(t*1e9,np.imag(tdstep))

# #restrict the time range
# plt.ylim([-1.1,1.1]);
# plt.xlim([0,np.max(t)/2*1e9]);
# plt.xlabel("time (s)")
# plt.ylabel("magnitude")


import numpy as np
import scipy
import logging
import sys
import threading
from collections import OrderedDict
from time import sleep, strftime, localtime
from typing import List
from typing import Iterator, List, NamedTuple, Tuple

from NanoVNASaver.Formatting import format_frequency, format_vswr, format_gain
from NanoVNASaver.Hardware.Hardware import Interface, get_interfaces, get_VNA
from NanoVNASaver.Hardware.VNA import VNA
from NanoVNASaver.RFTools import Datapoint, corr_att_data
from NanoVNASaver.Calibration import Calibration
from NanoVNASaver.Touchstone import Touchstone
from NanoVNASaver.About import VERSION
from NanoVNASaver.RFTools import Datapoint


def updateData(calibration,frequencies, values11, values21):
	'''Turn the lists of strings into calibrated output data.
	If you dont want a calibration to be applied. Pass an
	empty calibration object'''
	v11 = values11[:]
	v21 = values21[:]
	raw_data11 = []
	raw_data21 = []

	for freq in frequencies:
		real11, imag11 = v11.pop(0).split(" ")
		real21, imag21 = v21.pop(0).split(" ")
		raw_data11.append(Datapoint(freq, float(real11), float(imag11)))
		raw_data21.append(Datapoint(freq, float(real21), float(imag21)))

	data11, data21 = applyCalibration(calibration, raw_data11, raw_data21)

	return data11, data21

def applyCalibration(calibration, raw_data11: List[Datapoint],
					raw_data21: List[Datapoint]
					) -> Tuple[List[Datapoint], List[Datapoint]]:
	'''Apply the calibration object to the raw data. 
	The calibration is only applied if the calibration
	is valid.'''

	if not calibration.isCalculated:
		return raw_data11, raw_data21

	data11: List[Datapoint] = []
	data21: List[Datapoint] = []

	if calibration.isValid1Port():
		for dp in raw_data11:
			data11.append(calibration.correct11(dp))
	else:
		data11 = raw_data11

	if calibration.isValid2Port():
		for dp in raw_data21:
			data21.append(calibration.correct21(dp))
	else:
		data21 = raw_data21
	return data11, data21


def connect():
	'''Connect to the first available Nanovna'''
	iface = get_interfaces()[0]
	VNA(iface).connect()
	vna = get_VNA(iface)
	#set the sweep to the maximum range
	# vna.setSweep(10e3,4e9)

	return vna

def calibrate1port(vna):
	'''Performs a full single port calibration.
	Place the requested terminations on the end of the
	first port and press enter.'''

	calibration = Calibration()

	#short
	name = input("Short")
	frequencies = vna.readFrequencies()
	values11 = vna.readValues('data 0')
	values21 = vna.readValues('data 1')
	data = updateData(calibration,frequencies, values11, values21)
	calibration.insert("short",data[0])

	#open
	name = input("Open")
	frequencies = vna.readFrequencies()
	values11 = vna.readValues('data 0')
	values21 = vna.readValues('data 1')
	data = updateData(calibration,frequencies, values11, values21)
	calibration.insert("open",data[0])

	#load
	name = input("Load")
	frequencies = vna.readFrequencies()
	values11 = vna.readValues('data 0')
	values21 = vna.readValues('data 1')
	data = updateData(calibration,frequencies, values11, values21)
	calibration.insert("load",data[0])

	#calculate the corrections
	calibration.calc_corrections()

	print("Done")


	return calibration

def calibrate2port(vna):
	'''Performs a complete 2 port calibration. Isolation
	requires capping both ports with a 50 ohm load.'''

	calibration = Calibration()

	#short
	name = input("Short")
	frequencies = vna.readFrequencies()
	values11 = vna.readValues('data 0')
	values21 = vna.readValues('data 1')
	data = updateData(calibration,frequencies, values11, values21)
	calibration.insert("short",data[0])

	#open
	name = input("Open")
	frequencies = vna.readFrequencies()
	values11 = vna.readValues('data 0')
	values21 = vna.readValues('data 1')
	data = updateData(calibration,frequencies, values11, values21)
	calibration.insert("open",data[0])

	#load
	name = input("Load")
	frequencies = vna.readFrequencies()
	values11 = vna.readValues('data 0')
	values21 = vna.readValues('data 1')
	data = updateData(calibration,frequencies, values11, values21)
	calibration.insert("load",data[0])

	#through
	name = input("Through")
	frequencies = vna.readFrequencies()
	values11 = vna.readValues('data 0')
	values21 = vna.readValues('data 1')
	data = updateData(calibration,frequencies, values11, values21)
	calibration.insert("through",data[1])

	#isolation
	name = input("Isolation")
	frequencies = vna.readFrequencies()
	values11 = vna.readValues('data 0')
	values21 = vna.readValues('data 1')
	data = updateData(calibration,frequencies, values11, values21)
	calibration.insert("isolation",data[1])

	print("Done")

	#calculate the corrections
	calibration.calc_corrections()

	return calibration


def measure(vna,calibration):
	'''Measure the complex s parameters, requires the vna
	object and the calibration object as arguments'''

	##TODO: i want this to handle electrical delay properly.

	frequencies = vna.readFrequencies()
	values11 = vna.readValues('data 0')
	values21 = vna.readValues('data 1')
	data = updateData(calibration,frequencies, values11, values21)


	s11 = np.array([d.z for d in data[0]])
	s21 = np.array([d.z for d in data[1]])
	f = np.array([d.freq for d in data[0]])

	return f, s11, s21


def extrapolatetodc(f,s):
	'''Extrapolate s parameters to DC. Assumes the frequency difference between
	DC and the first point is equal to the frequency difference between adjacent points '''
	fwithDC = np.insert(f,0,0)
	swithDC = np.insert(s,0,0)

	phase = scipy.interpolate.interp1d(f, np.unwrap(np.angle(s)), axis=0, fill_value='extrapolate')(0)
	magnitude = scipy.interpolate.interp1d(f, np.abs(s), axis=0, fill_value='extrapolate')(0)
	#is the sign here correct?
	swithDC[0] = np.real(magnitude*np.exp(-1j*phase))
	return fwithDC,swithDC


def calculateTDR(f,s,mode='lowpass_step',window='normal',electrical_delay=0.0):
	'''Calculate the time domain step response from the frequency domain data.
	Uses the same window as the NanoVNA v2 firmware which can be found at
	https://github.com/nanovna-v2/NanoVNA-V2-firmware in the file main2.cpp 
	in the function transform_domain() with option TD_FUNC_LOWPASS_STEP'''


	points = len(s)

	#the window is symmetric about the middle of the array
	#if mode is lowpass, made window twice and wide and apply only
	#the right half of the window to the data. 
	if mode == 'lowpass_step' or mode == 'lowpass_impulse':
		window_size = 2*points
	else:
		window_size = points


	#apply a window to reduce high frequency noise and aliasing
	#use a kaiser window for consistency with NanoVNA firmware
	#beta = 6 for TD_WINDOW_NORMAL, 0 for TD_WINDOW_MINIMUM, and 13 for TD_WINDOW_MAXIMUM
	if window == 'minimum':
		beta = 0 #rectangular window in the frequency domain
	elif window == 'normal':
		beta = 6
	elif window == 'maximum':
		beta = 13
	else:
		raise Exception("Allowed window sizes are minimum, normal, or maximum")
	window = np.kaiser(window_size,beta)

	#if we are using one of the lowpass modes, apply only the right half
	#of the window to the data. otherwise apply the full window. 
	if mode == 'lowpass_step' or mode == 'lowpass_impulse':
		snoDC = s*window[points:]
	else:
		snoDC = s*window


	#extrapolate the s parameters to DC
	fwithDC, swithDC = extrapolatetodc(f,snoDC)

	#we expect a real signal but we are only measuring positive frequencies.
	#append the complex conjugate (without the dc component to preserve conjugate symmetry)
	swithconj = np.concatenate((swithDC,np.conj(np.flip(snoDC))))

	## same as above but zero padding
	# pad_width=1024-(2*points+1)
	# swithconj = np.concatenate((np.pad(swithDC,(0,pad_width)),np.pad(np.conj(np.flip(snoDC)),(pad_width,0))))

	#inverse fourier transform to get back into the time domain
	td = np.fft.ifft(swithconj)

	#take the cumulative sum to simulate the step response (rather than the impulse response)
	if mode == 'lowpass_step':
		td = np.cumsum(td)

	#calculate the time axis
	tmax = 1 / (f[1] - f[0])
	t = np.linspace(0, tmax, len(td))

	return t,td

def measureTDR(vna,calibration,mode='lowpass_step',window='normal',electrical_delay=0.0):

	f,s11,s21 = measure(vna,calibration)


	return calculateTDR(f,s11,mode,window,electrical_delay)


# def apply_electrical_delay(s,electrical_delay):
# 	'''apply an electrical delay'''
# 	return s*np.exp(1j*electrical_delay)