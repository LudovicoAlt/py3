#!/usr/bin/env python

'''
Script to download continuous data from Fermi GBM FTP

Downloads CTIME/CSPEC/POSHIST Files 
'''

import argparse
import ftplib
from ftplib import FTP
import sys

def parseArgs():
    # define parent parser which contains common arguments
	parentParser = argparse.ArgumentParser(add_help = False)
	parentParser.add_argument('date',type = str,  
	                          help = 'Date to download - should be in YYMMDD format',
	                          action = 'store',)
	parentParser.add_argument('--ctime', help = 'Download CTIME data',
	                          action = 'store_true', default = False)
	parentParser.add_argument('--cspec', help = 'Download CSPEC data',
	                          action = 'store_true', default = False)
	parentParser.add_argument('--poshist', help = 'Download POSHIST data',
	                          action = 'store_true', default = False)
	parentParser.add_argument('--dets', help = "Detectors", type =str, nargs='*')

	args = parentParser.parse_args()
	return args

class Data_date:
	def __init__(self, date,):
		'''Define date & ftp'''
		yr = '20' + date[0:2]
		mt = date[2:4]
		dy = date[4:6]
		self.ftp_dir = 'fermi/data/gbm/daily/'+yr+'/'+mt+'/'+dy+'/' +'current'
	def download_data(self, dets, cspec=False, ctime=False, poshist=False):
		'''Login to FTP & Download Data'''
		if not (cspec | ctime | poshist):
			print("No arguments passed - returning ...")
			return
		print("Connecting ...")
		ftp = FTP('legacy.gsfc.nasa.gov')
		ftp.login()
		print("Connected")
		try:
			ftp.cwd(self.ftp_dir)
		except ftplib.error_perm:
			print("*** Cannot cd to folder! Date may be incorrect. Exiting ...")
			sys.exit()
		ctime_files = ftp.nlst('glg_*ctime*pha')
		cspec_files = ftp.nlst('glg_*cspec*pha')
		poshist_files = ftp.nlst('glg_*poshist*fit')
		if ctime:
			print("Downloading CTIME")
			for i in ctime_files:
				det = i.split("_")[2]
				if (dets == None) or det in (dets):
					print("\tDownloading %s" %i)
					ftp.retrbinary('RETR ' + i, open(i,'wb').write)
				# print "\tDownloading %s" %i
				# ftp.retrbinary('RETR ' + i, open(i,'wb').write)
		if cspec:
			print("Downloading CSPEC")
			for i in cspec_files:
				det = i.split("_")[2]
				if (dets == None) or det in (dets):
					print("\tDownloading %s" %i)
					ftp.retrbinary('RETR ' + i, open(i,'wb').write)
		if poshist:
			print("Downloading POSHIST")
			for i in poshist_files:
				print("\tDownloading %s" %i)
				ftp.retrbinary('RETR ' + i, open(i,'wb').write)
		ftp.quit()

def main(argv = []):
	if len(argv):
		sys.argv = [sys.argv[0]] + argv
	else:
		argv = sys.argv
	args = parseArgs()
	data=Data_date(args.date)
	data.download_data(args.dets, args.cspec, args.ctime, args.poshist)

if __name__ == '__main__':
    main()


