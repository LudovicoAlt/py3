
import os
import sys
import argparse

import lib.util.util as util
import lib.dep_ver_checker as setup

def cmdLineOptions():
    cfg = setup.getConfig()
    booleanArg = {'action': 'store_true', 'default': False}
    parser = argparse.ArgumentParser(description = 'Estimate the background for\
                                        Fermi GBM using the orbital\
                                        subtraction technique. ',
                                        epilog = ' ',)
    parser.add_argument('tZero', help = 'Time to centre data on, by default it \
                        should be in mission elapsed time (MET) format, however\
                        it can be passed as Universal Time (UT) or Modified\
                        Julian Day (MJD) provided the appropriate flag is\
                        passed (--UT, --MJD).', action = 'store', type = float)
    parser.add_argument('--offsets', help = 'The number of orbits offset from\
                        tZero which will be used to estimate the background.\
                        Can be a single value or a range of values.\
                        [default: %s]' %(cfg['offset']), nargs ='*', 
                        type = str, default = cfg['offset'])
    parser.add_argument('--tRange', help = 'Time range over which to estimate\
                        the background. Should be given in seconds relative to\
                        tZero; e.g. for a range of 300 s, symmetric around\
                        tZero, --tRange -150 150. [default: ] %s' %cfg['tRange'], 
                        nargs = 2, type = float,
                        default = cfg['tRange'],)
    parser.add_argument('--name', help = 'String to use in naming any output\
                        files. If not passed the standard 10 digit UT date\
                        string will be calculated from tZero, i.e. YYMMDDTTT\
                        where YY is the year, MM is the month, DD is the day \
                        and TTT is the decimal fraction of day.',
                        default = False, type = str)
    parser.add_argument('--dets', help = 'Detectors to process: Should be\
                        passed as integers in the range 0-13 where 0-11\
                        are NaI and 12-13 are BGO.', nargs = '*', type = int)
    parser.add_argument('--CSPEC', help = 'Use CSPEC data. If both CSPEC &\
                        CTIME flags are passed, %s will be used.' %(cfg['specType']), 
                        **booleanArg)
    parser.add_argument('--CTIME', help = 'Use CTIME data. If both CSPEC &\
                        CTIME flags are passed, %s will be used.' %(cfg['specType']), 
                         **booleanArg)
    parser.add_argument('--coords', help = 'Source coordinates (RA, Dec)',
                        type = float, default = False, nargs = 2)                        

    
    args = parser.parse_args()
    # We now need to convert these arguments to 
    # that required by orbsub. 
    osvArgs = OSV_Args()
    osvArgs.mapArgs(args)

    return osvArgs


class OSV_Args:
    def __init__(self):
        '''Set Options to Default Values'''
        cfg = setup.getConfig()

        self.data_dir = cfg['dataDir']
        self.spec_type = cfg['specType']
        self.tRange  = cfg['tRange']
        self.offset = cfg['offset']
        self.doGTI = cfg['doGTI']    
        self.warnAll = cfg['gui']['warnAll']
        self.autoLoadLU = cfg['gui']['autoLoadLU']
        self.save_dir = './'
        self.back = 'pos-neg'
        self.name = ''
        self.tzero = ''
        self.dets = []
        self.warning = False
        self.error = False
        self.DetLbls={'n0':'NaI 0','n1':'NaI 1','n2':'NaI 2','n3':'NaI 3',
                      'n4':'NaI 4','n5':'NaI 5','n6':'NaI 6','n7':'NaI 7',
                      'n8':'NaI 8','n9':'NaI 9','na':'NaI A','nb':'NaI B',
                      'b0':'BGO 0','b1':'BGO 1'}
        self.DetInd = ['n0', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8', 
                       'n9', 'na', 'nb', 'b0', 'b1']
        self.LblsDet={'NaI 0':'n0','NaI 1':'n1','NaI 2':'n2','NaI 3':'n3',
                      'NaI 4':'n4','NaI 5':'n5','NaI 6':'n6','NaI 7':'n7',
                      'NaI 8':'n8','NaI 9':'n9','NaI A':'na','NaI B':'nb',
                      'BGO 0':'b0','BGO 1':'b1'}
        self.DetLblsInd={'NaI 0':0,'NaI 1':1,'NaI 2':2,'NaI 3':3,
                      'NaI 4':4,'NaI 5':5,'NaI 6':6,'NaI 7':7,
                      'NaI 8':8,'NaI 9':9,'NaI A':10,'NaI B':11,
                      'BGO 0':12,'BGO 1':13}
        # GTI/Occultation Flag 
        self.doGeom = False
        self.coords = ['', '']
        self.reCalcOrbit = True
        self.autoLU = False
        # error/warning errors
        self.error = False
        self.warning = False
        self.warning_mes = ''
        self.err_mes = ''        
    def mapArgs(self, args):
        '''
        Take in a command line argument object (argparse.parse_args()) and fill
        the options.
        '''
        self.tzero = args.tZero
        self.tRange = args.tRange
        self.offset = args.offsets
        if not args.name:
            self.name = ''
        else:
            self.name = args.name
        # self.autoLU = args.autoLU
        if not args.dets:
            self.dets = self.DetInd[:]
        else:
            for i in args.dets:
                self.dets.extend([self.DetInd[i]])
        if args.CSPEC:
            self.spec_type = 'CSPEC'
        else:
            self.spec_type = 'CTIME'
        if args.coords:
            self.doGeom = True
            self.coords = args.coords
            self.doGTI = True
        # self.reCalcOrbit = args.reCalcOrbit
    def check(self):
        '''
        Are passed options sensible? Lets check em.
        Should be called after options are received from gui.
        '''
        self.tRange = [float(self.tRange[0]), float(self.tRange[1])]
        self.tzero = float(self.tzero)
        if self.spec_type != 'CTIME':
            self.resolution = 4.096
        else:
            self.resolution = 1.024
        # We want a bin edge at zero. To get this we take shift the leftmost edge (tmin)
        # to ensure that there area an integer multiple of the resolution between it and
        # zero. We then shift the right edge for the same reason.
        self.tRange[0] = int(self.tRange[0]/self.resolution) * self.resolution + self.resolution/2.
        self.tRange[1] = int(self.tRange[1]/self.resolution) * self.resolution        
        
        if not util.good_gbm_met(self.tzero):
            self.error = True
            self.err_mes += '*** tZero does not fall \n'
            self.err_mes += '    within the lifetime of Fermi\n'''
            #self.err_mes += '*** tZero does not fall within lifetime of Fermi\n'''
            #self.err_mes += '*** tZero does not fall within lifetime of Fermi\n'''

        if self.dets == []:
            self.warning = True
            self.warning_mes += '** No detectors specified - defaulting to all\n'
            self.dets = ['n0', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 
                        'n7', 'n8', 'n9', 'na', 'nb', 'b0', 'b1']
            
        if( self.spec_type != 'CTIME') and (self.spec_type != 'CSPEC'):
            self.err_mes += 'Spec Type is not CTIME or CSPEC\n'
            self.err_mes += 'Defaulting to CSPEC\n'
            self.spec_type = 'CSPEC'

        if 'src' not in self.offset:
            self.offset.append('src')
        if self.doGeom:
            if( self.coords[0] == '' ) | (self.coords[1] == ''):
                self.warning = True
                self.warning_mes += '** GTI/Occultation Flag set but no RA/Dec entered\n'
            else:
                self.coords[0] = float(self.coords[0])
                self.coords[1] = float(self.coords[1])
        elif (self.coords[0] != '' ) | (self.coords[1] != ''):
            self.doGeom = True
            self.coords[0] = float(self.coords[0])
            self.coords[1] = float(self.coords[1])
        if len(self.name) < 1:
            self.name = util.met_grb(self.tzero)

    def __str__(self):
        mes = '\n'
        mes += '< Begin Options> \n'
        mes += "Name: %s\n" %str(self.name)
        mes += "tZero: %s\n" % str(self.tzero)
        mes += "tRange: %s %s\n" %(self.tRange[0], self.tRange[1],)
        mes += "offset: %s\n" %(self.offset)
        mes += "Spec Type: %s\n" %str(self.spec_type)
        mes += "Dets: "   +  '\n'
        mes += ' ' +str(self.dets)+'\n'
        mes += "Data Dir: "+'\n'
        mes += ' '  + str(self.data_dir) + '\n'
        mes += 'Coords: %s, %s\n' %(self.coords[0], self.coords[1])
        mes += 'doGeom: %s\n' %(self.doGeom)
        mes += 'doGTI: %s\n' %(self.doGTI)
        mes += '\nWarning Messages:\n'
        mes += self.warning_mes
        mes += '\nError Messages:\n'
        mes += self.err_mes        
        mes += '< End Options> \n'
        return mes
