from ftplib import FTP
import os
from pathlib import Path
import urllib.request, urllib.error, urllib.parse

def chdir(directory):
	''' cd to dir, creating it if it does not exist '''
	if not os.path.isdir(directory):
		os.makedirs(directory)
	os.chdir(directory)

class Downloader:
	def __init__(self, files, spec_type):
		'''
		input files is a dictionary indexed by pos, ctime & cspec. 
		files[pos] is a list of days in GRB format (e.g. 101206)
		files[ctime/cspec] is a dictionary indexed by day in grb format, 
		the contents of which are a list of detectors.
		'''
		self.download_pos = False
		self.download_ctime = False
		self.download_cspec = False
		self.spec_type = spec_type

		if spec_type == 'CSPEC':
			self.download_cspec = True
		else:
			self.download_ctime = True
		
		self.download_pos = True
		self.pos = False
		if len (files['pos']):
			self.pos = True
		if len (files['ctime']):
			self.ctime = True
		if len (files['cspec']):
			self.cspec = True
		self.files = files
		self.originalDirectory = os.getcwd()

	def createDownloadScript(self, dataDirectory):
		'''
		Creates a script which can be used to download gbm data
		'''
		curPath = os.path.realpath(__file__)
		topPath = Path(curPath).parents[2] # Should look two levels up to find osv.py, 0 is ftp, 1 is lib, 2 is package folder
		osvPath = topPath / "osv.py" #using Path from Python >3.4 replaces os.path.join(topPath, "osv.py")

		lines = ''
		lines += 'cd %s\n' % dataDirectory
		
		days = []
		if self.pos:
			days.extend(self.files['pos'])
		if self.ctime:
			days.extend(list(self.files['ctime'].keys()))
		if self.cspec:
			days.extend(list(self.files['cspec'].keys()))

		days = list(set(days))
		for i in days:
			# check to make sure we need files on these days
			if self.download_ctime:
				existing_files = self.files['ctime'][i]
			else:
				existing_files = self.files['cspec'][i]

			if not len(self.files['ctime'][i] + self.files['cspec'][i]) and not (i in self.files['pos']):
				continue

			lines += 'if [ ! -d "%s" ]; then\n' %(i)
			lines += '\tmkdir %s\n' %i
			lines += 'fi\n'
			lines += 'cd %s\n' %i
			data = ''
			dets = ''
			if self.download_pos:
				if i in self.files['pos']:
					data += ' --poshist '
			if self.download_ctime:
				if i in list(self.files['ctime'].keys()):
					data += ' --ctime '
					for j in self.files['ctime'][i]:
						dets += "%s "%j
			if self.download_cspec:
				if i in list(self.files['cspec'].keys()):
					data += ' --cspec '
					for j in self.files['cspec'][i]:
						dets += "%s "%j
			
			lines += 'python %s getData %s %s'%(osvPath, i,data)
			if len(dets):
				lines += ' --dets %s ' %dets	
			lines += '\n'
			lines += 'cd ../\n\n'
		lines += 'cd %s \n' %self.originalDirectory
		# so the file works with bash, windows uses backwards slashes for paths, 
		# python uses that when writing the file making it unusable in bash that 
		# looks for forward slashes
		self.lines = lines.replace('\\', '/') 

	def save(self):
		''' Save download script to file'''
		fo = Path( 'osv_dl_script.sh' )
		fo.write_text(self.lines)

	def download(self, dataDirectoryx):
		''' take in a directory, cd to it and download missing files via ftp
		'''
		if (self.cspec | self.ctime | self.pos):
			ftp = FTP('legacy.gsfc.nasa.gov')
			ftp.login()
		else: 
			return

		chdir(dataDirectoryx)

		if self.pos:
			posFiles = []
			for i in self.files['pos']:
				ftpDir='fermi/data/gbm/daily/20'+i[:2]+'/'+i[2:4]+'/'+i[4:6]+'/' +'current'				
				ftp.cwd('../../../../../../../../' +ftpDir)
				posFiles = ftp.nlst('glg_*poshist*fit')	
				chdir(i)
				for posFile in posFiles:
					fo = open(posFile,'wb')
					ftp.retrbinary('RETR ' + posFile, fo.write)
					fo.close()
				chdir('..')

		if self.ctime:
			spec = 'ctime'
			for i in self.files[spec]:
				ftpDir='fermi/data/gbm/daily/20'+i[:2]+'/'+i[2:4]+'/'+i[4:6]+'/' +'current'				
				ftp.cwd('../../../../../../../../' +ftpDir)			
				print(ftpDir)	
				ctimeFiles = []
				for j in self.files[spec][i]:
					print('glg_' + spec + '_' + j + '_' + i +'*pha')
					ctimeFiles.extend(ftp.nlst('glg_' + spec + '_' + j + '_' + i +'*pha')	)
				chdir(i)
				for ctimeFile in ctimeFiles:
					print(ctimeFile)
					ftp.retrbinary('RETR ' + ctimeFile, open(ctimeFile,'wb').write)
				chdir('..')

		if self.cspec:
			spec = 'cspec'
			for i in self.files[spec]:
				ftpDir='fermi/data/gbm/daily/20'+i[:2]+'/'+i[2:4]+'/'+i[4:6]+'/' +'current'				
				ftp.cwd('../../../../../../../../' +ftpDir)				
				cspecFiles = []
				for j in self.files[spec][i]:
					cspecFiles.extend(ftp.nlst('glg_' + spec + '_' + j + '_' + i +'*pha')	)
				chdir(i)
				for cspecFile in cspecFiles:
					print(cspecFile)
					ftp.retrbinary('RETR ' + cspecFile, open(cspecFile,'wb').write)
				chdir('..')

		os.chdir(self.originalDirectory)
		ftp.quit()
