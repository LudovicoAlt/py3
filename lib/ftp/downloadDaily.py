#!/usr/bin/env python

'''
Script to download continuous data from Fermi GBM FTP

Downloads CTIME/CSPEC/POSHIST Files 
'''

import argparse
import ftplib
import sys
import os
from pathlib import Path
import concurrent
from concurrent.futures import ThreadPoolExecutor
import contextlib


def parse_args():
    """Parse command-line arguments with improved help messages"""
    parser = argparse.ArgumentParser(
        description='Download continuous data from Fermi GBM FTP server')
    
    parser.add_argument(
        'date', 
        type=str,
        help='Date to download in YYMMDD format (e.g., 220315 for March 15, 2022)'
    )
    parser.add_argument(
        '--ctime', 
        help='Download CTIME (count time) data',
        action='store_true'
    )
    parser.add_argument(
        '--cspec', 
        help='Download CSPEC (count spectrum) data',
        action='store_true'
    )
    parser.add_argument(
        '--poshist', 
        help='Download POSHIST (position history) data',
        action='store_true'
    )
    parser.add_argument(
        '--dets', 
        help="Detector list (e.g., n0 n1 b0)",
        type=str, 
        nargs='*',
        metavar='DETECTOR'
    )
    parser.add_argument(
        '--output-dir',
        help="Directory to save downloaded files (default: current directory)",
        type=Path,
        default=Path.cwd()
    )
    parser.add_argument(
        '--parallel',
        help="Number of parallel downloads (default: 4)",
        type=int,
        default=4
    )

    return parser.parse_args()


class DataDownloader:
	"""Handle FTP connection and data downloads for a specific date"""

	FTP_HOST = 'heasarc.gsfc.nasa.gov'

	def __init__(self, date, output_dir=None):
		"""
		Initialize the downloader with a date in YYMMDD format
		
		Args:
			date (str): Date in YYMMDD format
			output_dir (Path, optional): Directory to save files
		"""
		# Validate date format
		if not (len(date) == 6 and date.isdigit()):
			raise ValueError(f"Invalid date format: {date}. Must be YYMMDD (e.g., 220315)")
		
		yr = '20' + date[0:2]
		mt = date[2:4]
		dy = date[4:6]
		self.date = date
		self.ftp_dir = f'fermi/data/gbm/daily/{yr}/{mt}/{dy}/current'
		
		# Create output directory if provided
		self.output_dir = Path(output_dir) if output_dir else Path.cwd()
		self.output_dir.mkdir(exist_ok=True)

	def connect(self):
		"""Establish FTP connection and navigate to the data directory"""
		ftp = ftplib.FTP_TLS(self.FTP_HOST)
		ftp.login()
		ftp.prot_p()  # Set secure data connection
		
		try:
			ftp.cwd(self.ftp_dir)
		except ftplib.error_perm as e:
			raise ValueError(f"Cannot access directory {self.ftp_dir}: {e}")
		
		return ftp

	def download_file(self, filename):
		"""Download a single file with connection retry mechanism"""
		output_path = self.output_dir / filename
		temp_path = output_path.with_suffix(output_path.suffix + '.tmp')
		
		# Try up to 3 times to download the file
		max_retries = 3
		for attempt in range(max_retries):
			try:
				# Create a new FTP connection for each file to avoid timeout issues
				with ftplib.FTP_TLS(self.FTP_HOST) as ftp:
					ftp.login()
					ftp.prot_p()
					ftp.cwd(self.ftp_dir)
					
					# Download the file
					with open(temp_path, 'wb') as f:
						ftp.retrbinary(f'RETR {filename}', f.write)
					
					# Rename to final filename after successful download
					temp_path.rename(output_path)
					print(f"Successfully downloaded {filename}")
					return True
					
			except ftplib.error_temp as e:
				# Temporary FTP error, might be worth retrying
				if attempt < max_retries - 1:
					retry_delay = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
					print(f"Temporary error downloading {filename} (attempt {attempt+1}/{max_retries}): {e}")
					print(f"Retrying in {retry_delay} seconds...")
					import time
					time.sleep(retry_delay)
				else:
					print(f"Failed to download {filename} after {max_retries} attempts: {e}")
					# Clean up temp file
					with contextlib.suppress(FileNotFoundError):
						temp_path.unlink()
					return False
					
			except Exception as e:
				print(f"Error downloading {filename}: {e}")
				# Clean up temporary file if download failed
				with contextlib.suppress(FileNotFoundError):
					temp_path.unlink()
				return False

	def download_files(self, file_types=None, detectors=None, max_workers=4):
		"""
		Download files of specified types and for specified detectors
		
		Args:
			file_types (list): List of file types to download ('ctime', 'cspec', 'poshist')
			detectors (list): List of detector names or None for all detectors
			max_workers (int): Maximum number of parallel downloads
		"""
		if not file_types:
			print("No file types specified. Please use --ctime, --cspec, or --poshist")
			return
			
		print(f"Connecting to {self.FTP_HOST}...")
		try:
			# Use a temporary connection just to list files
			with ftplib.FTP_TLS(self.FTP_HOST) as ftp:
				ftp.login()
				ftp.prot_p()
				
				try:
					ftp.cwd(self.ftp_dir)
				except ftplib.error_perm as e:
					raise ValueError(f"Cannot access directory {self.ftp_dir}: {e}")
				
				# Get file listings for each type
				file_listings = {}
				for file_type in file_types:
					if file_type == 'ctime':
						file_listings['ctime'] = ftp.nlst('glg_*ctime*pha')
					elif file_type == 'cspec':
						file_listings['cspec'] = ftp.nlst('glg_*cspec*pha')
					elif file_type == 'poshist':
						file_listings['poshist'] = ftp.nlst('glg_*poshist*fit')
		except Exception as e:
			print(f"Connection failed: {e}")
			return
			
		print(f"Connected. Accessed {self.ftp_dir}")
		
		# Create a filter function to match detectors
		def matches_detector(filename, file_type):
			if file_type == 'poshist' or detectors is None:
				return True
			
			# Extract detector name from filename (format: glg_TYPE_DETECTOR_DATE_...)
			try:
				detector = filename.split('_')[2]
				return detector in detectors
			except IndexError:
				return False
		
		# Build list of files to download
		downloads = []
		for file_type, files in file_listings.items():
			matching_files = [f for f in files if matches_detector(f, file_type)]
			if not matching_files:
				print(f"No matching {file_type.upper()} files found")
				continue
				
			print(f"Found {len(matching_files)} {file_type.upper()} files to download")
			downloads.extend(matching_files)
		
		if not downloads:
			print("No files to download")
			return
			
		# Use a smaller number of workers to avoid connection limits
		actual_workers = min(max_workers, 3)  # Cap at 3 parallel downloads by default
		print(f"Starting downloads using {actual_workers} parallel connections")
		
		# Show progress
		total_files = len(downloads)
		completed = 0
		failed = 0
		
		# Download files in parallel
		with ThreadPoolExecutor(max_workers=actual_workers) as executor:
			# Submit all download tasks
			future_to_file = {executor.submit(self.download_file, filename): filename 
							for filename in downloads}
			
			# Process results as they complete
			for future in concurrent.futures.as_completed(future_to_file):
				filename = future_to_file[future]
				try:
					success = future.result()
					if success:
						completed += 1
					else:
						failed += 1
				except Exception as e:
					print(f"Download error for {filename}: {e}")
					failed += 1
					
				# Show progress
				print(f"Progress: {completed + failed}/{total_files} ({completed} succeeded, {failed} failed)")
		
		print(f"Download complete. {completed}/{total_files} files saved to {self.output_dir}")
		if failed:
			print(f"Failed to download {failed} files. You may want to retry.")


def main(argv=None):
    """Main entry point for the script"""
    # Handle passed arguments or use sys.argv
    if argv:
        # Save original args and replace with passed args
        original_argv = sys.argv.copy()
        sys.argv = [sys.argv[0]] + argv
        args = parse_args()
        # Restore original args
        sys.argv = original_argv
    else:
        args = parse_args()
    
    # Determine which file types to download
    file_types = []
    if args.ctime:
        file_types.append('ctime')
    if args.cspec:
        file_types.append('cspec')
    if args.poshist:
        file_types.append('poshist')
    
    # Set up and run the downloader
    try:
        downloader = DataDownloader(args.date, args.output_dir)
        downloader.download_files(
            file_types=file_types,
            detectors=args.dets,
            max_workers=args.parallel
        )
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())