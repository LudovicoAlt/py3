#!/usr/bin/env python

from .orbsub_classes import *

__version__='1.3'

class OrbSub():
    def __init__(self,opts):
        self.opts = opts
        self.files = ''
        self.data = {}
        self.gti = None
        self.period = 5737.70910239
        self.pos = None
        self.data_err = False
        self.perErr = False
        self.perMes = ''
        self.perErrMes = ''
    def find_files(self):
        '''Find all relevant files needed for bkg subtraction'''
        opts = self.opts
        opts.check()
        #Regions is a class which contains the time ranges
        regions = Regions(opts.tzero, opts.tRange[0], opts.tRange[1], opts.offset,
                          orbit_period = self.period)
        #Files is a class which is used to first calculate what days are needed,
        #the corresponding files are then found
        files = Files(opts.tzero, regions, opts.offset)
        files.find_pha_files(opts.dets, spec_type = opts.spec_type,
                             data_dir = opts.data_dir)
        files.find_poshist_files(opts.data_dir)
        self.regions = regions
        self.files = files
        return self.files.error
    def calc_period(self):
        ''' 
        Calculate period of fermi using relevant poshist files, then do 
        a comparison with the period used to pick those files. If they are 
        sufficiently different then redo region calculation and file selection.
        '''
        tolerance = 0.1
        self.perMes = ''
        self.perMes += '<Begin Recalculating Period>\n'
        if not self.files:
            #No poshist files
            self.perErrMes += '<Begin error: Period>\n'
            self.perErrMes += '*** Unable to recalculate period - No poshist files.\n'
            self.perErrMes += 'Defaulting to: %fs\n' %self.period
            self.perErrMes += '<End error: Period>\n\n'
            return False
        elif not self.pos:
            pos = Poshist_data(self.files.pos_files)
        pos.calc_period()
        if abs(pos.period - self.period) > 0.1:
            self.perMes += 'Difference b/w new & old period is > %f\n' %tolerance
            self.perMes += 'Old Period: %fs, New Period: %fs\n' %(self.period, pos.period)
            self.perMes += 'Recalculating temporal regions & finding files\n'
            #print "*** "Recalculating temporal regions "
            #print "*** Old period: %f" % self.period
            #print "*** New period: %f" % pos.period
            self.period = pos.period
            self.find_files()
        else:
            self.perMes += "New and old periods are consistent within tolerance (%f)\n" %tolerance
        self.perMes += '<End Recalculating Period>\n\n'
        return True
    def get_steps(self):
        '''
        Get times of occultation steps. This is done for all the available data.
        It would be quicker to just find the steps in each region of interest,
        however the current implemtation is the easiest and provided it is not 
        too slow it will be kept. 
        Each temporal region of interest is then checked to see if a step 
        occurs within it. The times when the is occulted are flagged as dubious,
        quality = 2. Based on standard 
        @ heasarc.nasa.gov/docs/ofwg/docs/spectra/ogip_92_007
    
        Added: 06.12.11
        '''
        self.occErrMes = ''
        self.occMes = ''
        self.occMes += '<Begin Calculating Occultation Steps>\n'
        if self.opts.coords[0] == '' or self.opts.coords[1] == '':
            # Coordinates not set
            self.occErrMes += '<Begin error: Occultation Steps>\n'
            self.occErrMes += "No coordinates set:cannot calculate Occultation Steps\n"
            self.occErrMes += '<End error: Occultation Steps.>\n\n'
            return False
        if not self.pos:
            self.pos = Poshist_data(self.files.pos_files)
        self.pos.get_steps(self.opts.coords[0], self.opts.coords[1])
        self.occMes += 'Occultation Steps successfully found\n'
        self.occMes += '<End Calculating Occultation Steps>\n\n'
        return True        
        #        self.occTI = self.pos.occTI
        #        occI = self.pos.occTI[0]
        #        occJ = self.pos.occTI[1]
        #        offset = 5e4 # seconds        
        #        tRange = self.regions.ranges['dur']
        #        occI = occI[(occI > (tRange[0] - offset)) & 
        #                    (occI < (tRange[1] + offset))]
        #        occJ = occJ[(occJ > (tRange[0] - offset)) & 
        #                    (occJ < (tRange[1] + offset))]
             
    def get_gti(self):
        '''
        Create Good Time Intervals for each detector. This is found by 
        calculating the source angles for each detector and extracting the times
        at which they are <60,<90 for the NaI & BGO
        '''
        self.gtiErrMes = ''
        self.gtiMes = ''
        self.gtiMes += '<Begin Calculating G.T.I.>\n'
        if self.opts.coords[0] == '' or self.opts.coords[1] == '':
            # Coordinates not set
            self.gtiErrMes += '<Begin error: G.T.I.>\n'
            self.gtiErrMes += "No coordinates set:cannot calculate GTI\n"
            self.gtiErrMes += '<End error: G.T.I.>\n\n'
            return False
        if not self.pos:
            self.pos = Poshist_data(self.files.pos_files)
        self.pos.calculate_angles(self.regions, self.opts.coords[0],
                                    self.opts.coords[1])
        self.pos.get_gti()
        #self.gti = self.pos.gti
        self.gtiMes += 'G.T.I.s successfully found\n'
        self.gtiMes += '<End Calculating G.T.I.>\n\n'
        return True

    def do_orbsub(self):
        ''' perform orbital subtraction for each detector '''
        # data is a dictionary that will be used to store the data for each det
        data={}
        self.orbErrMes = ''
        self.orbMes = ''
        isValid = True
        # Loop over each detector, extract data from relevant temporal regions,
        # then average them to find the bkg.
        for det in self.opts.dets:
            self.orbMes += ' Processing %s:\n' %det
            #print det            
            #Read in data from each day & concatenate it into several arrays
            det_data = Pha_data(self.files.pha_files[det])
            det_data.bin_pha(self.regions, self.opts.offset, 
                                            self.opts)
            if det_data.binDataError:
                self.orbErrMes += det_data.binDataErrMes
                isValid = False
            det_data.calc_background(self.opts.offset)
            det_dic = {det:det_data}
            data.update(det_dic)
        self.data = data
        return isValid    