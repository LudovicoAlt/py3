#!/usr/bin/env python

from .orbsub_classes import *

__version__='1.3'
class OrbSub():
    """
    Orbital Subtraction handler class
    Manages the process of orbital background subtraction for GBM data
    """
    # Default Fermi orbit period in seconds
    DEFAULT_PERIOD = 5737.70910239
    
    def __init__(self, opts):
        self.opts = opts
        self.files = None
        self.regions = None
        self.data = {}
        self.pos = None
        
        # Status attributes
        self.period = self.DEFAULT_PERIOD
        self.autoscale = True  # Add this attribute to fix GUI issue
        
        # Message containers
        self.perMes = ""
        self.perErrMes = ""
        self.gtiMes = ""
        self.gtiErrMes = ""
        self.occMes = ""
        self.occErrMes = ""
        self.orbMes = ""
        self.orbErrMes = ""
    
    def find_files(self):
        """
        Find all relevant files needed for background subtraction
        Returns True if files found successfully, False otherwise
        """
        # Validate options
        self.opts.check()
        
        # Create temporal regions based on input parameters
        self.regions = Regions(
            self.opts.tzero, 
            self.opts.tRange[0], 
            self.opts.tRange[1], 
            self.opts.offset,
            orbit_period=self.period
        )
        
        # Find relevant data files
        self.files = Files(self.opts.tzero, self.regions, self.opts.offset)
        
        # Find PHA files for each detector
        self.files.find_pha_files(
            self.opts.dets, 
            spec_type=self.opts.spec_type,
            data_dir=self.opts.data_dir
        )
        
        # Find position history files
        self.files.find_poshist_files(self.opts.data_dir)
        
        return self.files.error
    
    def calc_period(self):
        """
        Calculate the orbit period of Fermi using position history files
        Updates the period if it differs from the current value by more than tolerance
        """
        tolerance = 0.1
        self.perMes = '<Begin Recalculating Period>\n'
        
        # Check if files are available
        if not self.files:
            self.perErrMes = '<Begin error: Period>\n'
            self.perErrMes += '*** Unable to recalculate period - No poshist files.\n'
            self.perErrMes += f'Defaulting to: {self.period}s\n'
            self.perErrMes += '<End error: Period>\n\n'
            return False
        
        # Initialize position data if not already done
        if not self.pos:
            self.pos = Poshist_data(self.files.pos_files)
        
        # Calculate period
        self.pos.calc_period()
        
        # Check if period has changed significantly
        if abs(self.pos.period - self.period) > tolerance:
            self.perMes += f'Difference b/w new & old period is > {tolerance}\n'
            self.perMes += f'Old Period: {self.period}s, New Period: {self.pos.period}s\n'
            self.perMes += 'Recalculating temporal regions & finding files\n'
            
            # Update period and recalculate
            self.period = self.pos.period
            self.find_files()
        else:
            self.perMes += f"New and old periods are consistent within tolerance ({tolerance})\n"
        
        self.perMes += '<End Recalculating Period>\n\n'
        return True
    
    def _check_coords(self, operation):
        """
        Helper method to check if source coordinates are set
        Returns True if coordinates are valid, False otherwise
        """
        if not self.opts.coords[0] or not self.opts.coords[1]:
            error_msg = f'<Begin error: {operation}>\n'
            error_msg += f"No coordinates set: cannot calculate {operation}\n"
            error_msg += f'<End error: {operation}>\n\n'
            
            # Set the appropriate error message based on operation
            if operation == "Occultation Steps":
                self.occErrMes = error_msg
            elif operation == "G.T.I.":
                self.gtiErrMes = error_msg
                
            return False
        return True
    
    def _init_position_data(self):
        """
        Initialize position data if not already done
        Returns True if position data is available, False otherwise
        """
        if not self.files:
            return False
            
        if not self.pos:
            self.pos = Poshist_data(self.files.pos_files)
        return True
    
    def get_steps(self):
        """
        Calculate occultation step times for all available data
        """
        self.occMes = '<Begin Calculating Occultation Steps>\n'
        self.occErrMes = ''
        
        # Check coordinates
        if not self._check_coords("Occultation Steps"):
            return False
            
        # Initialize position data
        if not self._init_position_data():
            self.occErrMes = '<Begin error: Occultation Steps>\n'
            self.occErrMes += "No position history files available\n"
            self.occErrMes += '<End error: Occultation Steps>\n\n'
            return False
        
        # Calculate occultation steps
        self.pos.get_steps(self.opts.coords[0], self.opts.coords[1])
        self.occMes += 'Occultation Steps successfully found\n'
        self.occMes += '<End Calculating Occultation Steps>\n\n'
        return True
    
    def get_gti(self):
        """
        Calculate Good Time Intervals for each detector
        Based on source angles (<60° for NaI, <90° for BGO)
        """
        self.gtiMes = '<Begin Calculating G.T.I.>\n'
        self.gtiErrMes = ''
        
        # Check coordinates
        if not self._check_coords("G.T.I."):
            return False
            
        # Initialize position data
        if not self._init_position_data():
            self.gtiErrMes = '<Begin error: G.T.I.>\n'
            self.gtiErrMes += "No position history files available\n"
            self.gtiErrMes += '<End error: G.T.I.>\n\n'
            return False
        
        # Calculate angles and GTIs
        self.pos.calculate_angles(
            self.regions, 
            self.opts.coords[0],
            self.opts.coords[1]
        )
        self.pos.get_gti()
        
        self.gtiMes += 'G.T.I.s successfully found\n'
        self.gtiMes += '<End Calculating G.T.I.>\n\n'
        return True

    def do_orbsub(self):
        """
        Perform orbital subtraction for each detector
        Processes data files and calculates background for each detector
        """
        self.orbMes = ''
        self.orbErrMes = ''
        isValid = True
        
        # Process each detector in parallel
        for det in self.opts.dets:
            self.orbMes += f' Processing {det}:\n'
            
            # Create detector data object
            det_data = Pha_data(self.files.pha_files[det])
            
            # Bin PHA data and calculate background
            det_data.bin_pha(self.regions, self.opts.offset, self.opts)
            
            # Check for errors
            if det_data.binDataError:
                self.orbErrMes += det_data.binDataErrMes
                isValid = False
                
            # Calculate background
            det_data.calc_background(self.opts.offset)
            
            # Store result
            self.data[det] = det_data
            
        return isValid