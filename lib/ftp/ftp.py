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
        self.download_pos   = False
        self.download_ctime = False
        self.download_cspec = False
        self.spec_type      = spec_type

        if spec_type == 'CSPEC':
            self.download_cspec = True
        else:
            self.download_ctime = True
        
        self.download_pos   = True
        self.pos            = False
        if len (files['pos']):
            self.pos = True
        if len (files['ctime']):
            self.ctime = True
        if len (files['cspec']):
            self.cspec = True
        self.files = files
        self.originalDirectory = os.getcwd()
        
    def createPythonDownloadScript(self, dataDirectory):
        '''
        Creates a Python script (download.py) which can be used to download GBM data
        '''
        curPath = os.path.realpath(__file__)
        topPath = Path(curPath).parents[2]  # Should look two levels up to find osv.py
        osvPath = topPath / "osv.py"  # using Path from Python >3.4

        # Start building the Python script content
        script_lines = [
            "#!/usr/bin/env python",
            "import os",
            "import sys",
            "import subprocess",
            "from pathlib import Path",
            "",
            "def main():",
            "    # Get the script directory",
            "    script_dir = Path(__file__).resolve().parent",
            "",
            f"    # Data directory (can be absolute or relative to script)",
            f"    data_dir = Path(r'{dataDirectory}')",
            "    if not data_dir.is_absolute():",
            "        data_dir = script_dir / data_dir",
            "    data_dir.mkdir(parents=True, exist_ok=True)",
            "",
            f"    # Path to osv.py",
            f"    osv_path = Path(r'{osvPath}')",
            "    if not osv_path.exists():",
            "        print(f'Warning: {osv_path} not found, will try relative to script location')",
            "        osv_path = script_dir / 'osv.py'",
            "        if not osv_path.exists():",
            "            print(f'Error: Could not find osv.py')",
            "            sys.exit(1)",
            "",
            "    # Keep track of current directory to restore at end",
            "    original_dir = os.getcwd()",
            ""
        ]

        # Get list of days
        days = []
        if self.pos:
            days.extend(self.files['pos'])
        if self.ctime:
            days.extend(list(self.files['ctime'].keys()))
        if self.cspec:
            days.extend(list(self.files['cspec'].keys()))
        days = sorted(list(set(days)))  # Sort unique days

        # Process each day
        for day in days:
            # Skip if no files needed
            if self.download_ctime:
                day_files = self.files['ctime'].get(day, [])
            else:
                day_files = self.files['cspec'].get(day, [])
                
            if not (day_files or (day in self.files.get('pos', []))):
                continue
                
            # Add code to create and change to directory
            script_lines.append(f"    # Process day {day}")
            script_lines.append(f"    day_dir = data_dir / '{day}'")
            script_lines.append("    day_dir.mkdir(exist_ok=True)")
            script_lines.append("    os.chdir(day_dir)")
            
            # Build the command
            cmd_parts = [f"sys.executable, str(osv_path), 'getData', '{day}'"]
            flags = []
            dets = []
            
            if self.download_pos and day in self.files.get('pos', []):
                flags.append("'--poshist'")
                
            if self.download_ctime and day in self.files.get('ctime', {}):
                flags.append("'--ctime'")
                for det in self.files['ctime'][day]:
                    dets.append(f"'{det}'")
                    
            if self.download_cspec and day in self.files.get('cspec', {}):
                flags.append("'--cspec'")
                for det in self.files['cspec'][day]:
                    dets.append(f"'{det}'")
            
            # Add flags to command
            if flags:
                cmd_parts.extend(flags)
                
            # Add detectors to command if any
            if dets:
                cmd_parts.append("'--dets'")
                cmd_parts.extend(dets)
                
            # Build the final command line
            cmd_line = f"    cmd = [{', '.join(cmd_parts)}]"
            script_lines.append(cmd_line)
            script_lines.append("    print(f'Running: {\" \".join(cmd)}')")
            script_lines.append("    subprocess.run(cmd, check=True)")
            script_lines.append("")
            
        # Return to original directory
        script_lines.append("    # Return to original directory")
        script_lines.append("    os.chdir(original_dir)")
        script_lines.append("    print('Download script completed successfully')")
        script_lines.append("")
        script_lines.append("if __name__ == '__main__':")
        script_lines.append("    main()")

        # Write the Python script to file
        script_content = "\n".join(script_lines)
        script_path = Path("download.py")
        script_path.write_text(script_content)
        print(f"Created Python download script: {script_path.resolve()}")