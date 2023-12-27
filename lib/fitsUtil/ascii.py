'''
ascii.py

V 0.1

Create an ascii output file

'''

import os

import numpy as np

def createASCII(t, exp, counts, detector, tzero, name, delim = ','):
	'''     '''
	r = counts.sum(1)/exp

	rErr = np.sqrt(counts.sum(1))/exp
	fo = open(name, 'w')
	fo.write("%s%s %s%s %s%s %s%s\n"%('T_i',delim, 'T_j',delim, 'Rate (Counts/s)',delim, 'Rate Err (Counts/s)',delim,))
	for i in range(r.size):
		fo.write("%s%s %s%s %s%s %s%s\n" %(t[0][i],delim,  t[1][i],delim, r[i],delim, rErr[i],delim))
	fo.close()
