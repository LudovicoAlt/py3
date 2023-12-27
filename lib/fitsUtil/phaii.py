'''
phaii.py

Create a PHAII file.

PHAII files consist of 4 extensions (0-3). 
 #0 Primary: contains no data 
 #1 EBounds: Contains rates per channel in discrete time bins
 #2 Events: Contains event times and corresponding energy channels
 #3 GTI: Contains good time intervals


Dependencies: 
numpy
astropy.io.fits

Gerard Fitzpatrick
gerard.fitzpatrick@ucdconnect.ie
          
'''

import os
import datetime

import astropy.io.fits as pf
import numpy as np

__version__ = 1.0


class PHAII:
    ''' Class for the creation of PHAII files'''
    def __init__(self, t, exp, pha, det,trigTime, fileStem, hdrComment, edges,
                    ra, dec, radErr, nchan, gti = (), qual = np.empty((0)),
                    statErr = None):
        '''Read in time and pha arrays, detector and set up file.'''
        # define detDic - this maps from detector name needed for header to 
        # detector name needed for filename
        detDic = {'NAI_00': 'n0', 'NAI_01': 'n1', 'NAI_02': 'n2', 
                  'NAI_03': 'n3', 'NAI_04': 'n4', 'NAI_05': 'n5', 
                  'NAI_06': 'n6', 'NAI_07': 'n7', 'NAI_08': 'n8', 
                  'NAI_09': 'n9', 'NAI_10': 'na', 'NAI_11': 'nb', 
                  'BGO_00': 'b0', 'BGO_01': 'b1'}
        self.det = det
        # Overwrite existing files
        self.clobber = True
        # coord stuff
        self.ra = ra
        self.dec = dec
        self.radErr = radErr
        # time array stuff
        self.trig = trigTime
        self.tzero = self.trig        
        self.ti = t[0]
        self.tj = t[1]

        # for i,j in zip(self.ti[1:] , self.tj[:-1]):
        #     print i,j
        # exit()

        self.tMin = self.ti[0] 
        self.tMax = self.tj[-1]
        self.date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        # Observation start & end in UT
        self.obsStart = (datetime.datetime(2001, 0o1, 0o1, 0, 0, 0) + datetime.timedelta(0, (float(self.tMin))) ).strftime("%Y-%m-%dT%H:%M:%S")
        self.obsEnd =   (datetime.datetime(2001, 0o1, 0o1, 0, 0, 0) + datetime.timedelta(0, (float(self.tMax)) ) ).strftime("%Y-%m-%dT%H:%M:%S")
        # Observatoin start & end in MET
        self.tStart = self.trig - self.tMin
        self.tStop = self.trig + self.tMax
        # filename is the output filename and may be a full path. We also
        # need just the filename - this is for the keyword FILENAME in 
        # extensions 0 & 1
        self.filename = fileStem
        self.hdrFileName = str(os.path.split(self.filename)[-1]) # pyfits will not write the file without the extra str()
        # Energy Edges (EBOUNDS)
        self.eMin = edges[0]
        self.eMax = edges[1]            
        if nchan == 8:
            self.spec = 'CTIME'
        else:
            self.spec = 'CSPEC'
        self.nchan = nchan
        # SPECTRUM
        self.pha = pha
        self.exp = exp
        if qual.size:
            self.qual = qual
        else:
            self.qual = np.zeros(self.exp.size)

        # Good Time Intervals (GTI)
        if len(gti) > 1:
            self.gti_i = gti[0]
            self.gti_j = gti[1]
        else:
            self.gti_i = np.asarray([self.tMin])
            self.gti_j = np.asarray([self.tMax])                  

        # Check if header comment was passed
        if len(hdrComment) > 0:
            self.hdrComment = hdrComment
        else:
            self.hdrComment = None

        self.statErr = statErr

    def doPrimary(self):
        ''' Create Primary Extension.'''
        hdr = pf.Header()
        hdr.update('Creator', 'TTE_creator.py V' + str(__version__), 'Software and version creating file')
        hdr.update('FILETYPE', 'PHAII'              , 'Name for this type of FITS File')
        hdr.update('FILE-VER', '1.0.0'              , 'Version of the format for this filetype')
        hdr.update('TELESCOP', 'GLAST'              , 'Name of mission/Satellite')
        hdr.update('INSTRUME', 'GBM'                , 'Specific Instrument used for observation')
        hdr.update('DETNAM',   self.det             , 'Individual detector name')
        hdr.update('OBSERVER','MEEGAN'              , 'GLAST Burst Monitor P.I.')
        hdr.update('ORIGIN'  ,'UCD SSAMR'           , 'Name of Organisation making file' )
        hdr.update('DATE'    , self.date            , 'File creation date (YYYY-MM-DDThh:mm:ss UT)')
        hdr.update('DATE-OBS', self.obsStart        , 'Date of start of observation') 
        hdr.update('DATE-END', self.obsEnd          , 'Date of end of observation')                
        hdr.update('TIMESYS ', 'TT'                 , 'Time system used in time keywords')
        hdr.update('TIMEUNIT', 's'                  , 'Time since MJDREF, used in TSTART and TSTOP')
        hdr.update('MJDREFI' , 51910                , 'MJD of GLAST reference epoch, integer part')  
        hdr.update('MJDREFF' , 7.428703703703703e-4 , 'MJD of GLAST reference epoch, fractional part')  
        hdr.update('TSTART'  , self.tMin            , '[GLAST MET] Observation start time')
        hdr.update('TSTOP'   , self.tMax            , '[GLAST MET] Observation stop time')           
        hdr.update('FILENAME', self.hdrFileName     , 'Name of this file')
        hdr.update('DATATYPE', self.spec            , 'GBM datatype for this file')
        hdr.update('TRIGTIME', self.trig            , 'Trigger time relative to MJDREF, double precisi')
        hdr.update('OBJECT'  , 'SimData'            , 'Object')  
        hdr.update('RADECSYS', 'FK5'                , 'Stellar reference frame')     
        hdr.update('EQUINOX' , 2000.0               , 'Equinox for RA and Dec')                      
        hdr.update('RA_OBJ'  , self.ra              , 'Calculated RA of burst')                       
        hdr.update('DEC_OBJ' , self.dec             , 'Calculated Dec of burst')                       
        hdr.update('ERR_RAD' , self.radErr          , 'Calculated Location Error Radius')
        hdr.update('INFILE01', ''                   , 'Level 1 input lookup table file')     
        hdr.update('INFILE02', ''                   , 'Level 0 input data file')                      
        hdr.update('INFILE03', ''                   , 'Level 0 input data file')

        if self.hdrComment:
            hdr.add_comment(self.hdrComment)
        hdu = pf.PrimaryHDU(data = None, header = hdr)
        self.primExt = hdu
    def doEbounds(self):
        '''
        Create EBounds Extension. Currently the same edges are used for both
        BGOs and for all 12 NaIs.
        '''
        # First we define header
        hdr = pf.Header()
        hdr.update('EXTNAME', 'EBOUNDS'            , 'Name of extension')    
        hdr.update('TELESCOP', 'GLAST'              , 'Name of mission/Satellite')
        hdr.update('INSTRUME', 'GBM'                , 'Specific Instrument used for observation')
        hdr.update('DETNAM', self.det               , 'Individual detector name')
        hdr.update('OBSERVER', 'MEEGAN'             , 'GLAST Burst Monitor P.I.')
        hdr.update('ORIGIN', 'UCD SSAMR'            , 'Name of Organisation making file' )
        hdr.update('DATE', self.date                , 'File creation date (YYYY-MM-DDThh:mm:ss UT)')
        hdr.update('DATE-OBS', self.obsStart        , 'Date of start of observation') 
        hdr.update('DATE-END', self.obsEnd          , 'Date of end of observation')                
        hdr.update('TIMESYS ', 'TT'                 , 'Time system used in time keywords')
        hdr.update('TIMEUNIT', 's'                  , 'Time since MJDREF, used in TSTART and TSTOP')
        hdr.update('MJDREFI' , 51910                , 'MJD of GLAST reference epoch, integer part')  
        hdr.update('MJDREFF' , 7.428703703703703e-4 , 'MJD of GLAST reference epoch, fractional part')  
        hdr.update('TSTART'  , self.tMin          , '[GLAST MET] Observation start time')
        hdr.update('TSTOP'   , self.tMax           , '[GLAST MET] Observation stop time')           
        hdr.update('FILENAME', self.hdrFileName     , 'Name of this file')
        # hdr.update('DATATYPE', 'TTE'                , 'GBM datatype for this file')
        hdr.update('TRIGTIME', self.trig            , 'Trigger time relative to MJDREF, double precisi')
        hdr.update('OBJECT'  , 'SimData'            , 'Object')  
        hdr.update('RADECSYS', 'FK5'                , 'Stellar reference frame')     
        hdr.update('EQUINOX' , 2000.0               , 'Equinox for RA and Dec')                      
        hdr.update('RA_OBJ'  , self.ra              , 'Calculated RA of burst')                       
        hdr.update('DEC_OBJ' , self.dec             , 'Calculated Dec of burst')                       
        hdr.update('ERR_RAD' , self.radErr          , 'Calculated Location Error Radius')
        hdr.update('HDUCLASS', 'OGIP'               , 'Confirms to OGIP standard indicated in HDUCLAS1')     
        hdr.update('HDUCLAS1', 'RESPONSE'           , 'These are typically found in RMF files')                      
        hdr.update('HDUCLAS2', 'EBOUNDS'            , 'From CAL/GEN/92-002')   
        hdr.update('HDUVERS' , '1.2.0'              , 'Version of HDUCLAS1 format in use')
        hdr.update('CHANTYPE', 'PHA'                , 'No corrections have been applied')
        hdr.update('FILTER'  , 'NONE'               , 'The instrument filter in use (if any)')
        hdr.update('DETCHANS', self.nchan           , 'Total number of channels in each rate')
        hdr.update('EXTVER'  , 1                    , 'Version of this extension format')
        hdr.update('CH2E_VER', 'SPLINE 2.0'         , 'Channel to energy conversion scheme used')
        hdr.update('GAIN_COR', 1.0                  , 'Gain correction factor applied to energy edges')
        #Now we define data table
        channels = np.arange(0, self.nchan)
        
        channelsCols = pf.Column(name='Channels', format='1I', array = channels, 
                              unit = 'none', bscale = 1, bzero = 0)
        eMinCols = pf.Column(name='E_MIN', format='1E', array = self.eMin, 
                              unit = 'kev', bscale = 1, bzero = 0)
        eMaxCols = pf.Column(name='E_MAX', format='1E', array = self.eMax, 
                              unit = 'kev', bscale = 1, bzero = 0)
        eBoundsCols = pf.ColDefs([channelsCols, eMinCols, eMaxCols])
        eBoundsHdu = pf.new_table(eBoundsCols, header = hdr)
        self.eBoundsExt = eBoundsHdu
        
    def doGTI(self):
        ''' Create GTI extension. Interval is taken as the entire data set. '''
        # First we define header
        hdr = pf.Header()
        hdr.update('EXTNAME', 'GTI'                 , 'Name of extension')    
        hdr.update('TELESCOP', 'GLAST'              , 'Name of mission/Satellite')
        hdr.update('INSTRUME', 'GBM'                , 'Specific Instrument used for observation')
        hdr.update('DETNAM', self.det               , 'Individual detector name')
        hdr.update('OBSERVER', 'MEEGAN'             , 'GLAST Burst Monitor P.I.')
        hdr.update('ORIGIN', 'UCD SSAMR'            , 'Name of Organisation making file' )
        hdr.update('DATE', self.date                , 'File creation date (YYYY-MM-DDThh:mm:ss UT)')
        hdr.update('DATE-OBS', self.obsStart        , 'Date of start of observation') 
        hdr.update('DATE-END', self.obsEnd          , 'Date of end of observation')                
        hdr.update('TIMESYS ', 'TT'                 , 'Time system used in time keywords')
        hdr.update('TIMEUNIT', 's'                  , 'Time since MJDREF, used in TSTART and TSTOP')
        hdr.update('MJDREFI' , 51910                , 'MJD of GLAST reference epoch, integer part')  
        hdr.update('MJDREFF' , 7.428703703703703e-4 , 'MJD of GLAST reference epoch, fractional part')  
        hdr.update('TSTART'  , self.tMin          , '[GLAST MET] Observation start time')
        hdr.update('TSTOP'   , self.tMax           , '[GLAST MET] Observation stop time')           
        hdr.update('HDUCLASS', 'OGIP'               , 'Confirms to OGIP standard indicated in HDUCLAS1')     
        hdr.update('HDUCLAS1', 'GTI'                , 'Indicates good time intervals')                      
        hdr.update('HDUCLAS2', 'EBOUNDS'            , 'From CAL/GEN/92-002')   
        hdr.update('HDUVERS' , '1.2.0'              , 'Version of HDUCLAS1 format in use')
        hdr.update('EXTVER'  , 1                    , 'Version of this extension format')
        hdr.update('TRIGTIME', self.trig            , 'Trigger time relative to MJDREF, double precisi')        
        hdr.update('OBJECT'  , 'SimData'            , 'Object')  
        hdr.update('RADECSYS', 'FK5'                , 'Stellar reference frame')     
        hdr.update('EQUINOX' , 2000.0               , 'Equinox for RA and Dec')                      
        hdr.update('RA_OBJ'  , self.ra              , 'Calculated RA of burst')                       
        hdr.update('DEC_OBJ' , self.dec             , 'Calculated Dec of burst')                       
        hdr.update('ERR_RAD' , self.radErr          , 'Calculated Location Error Radius')
        #Now we define data table
        gti_start = pf.Column(name='START', format='1D',
                                array = self.gti_i, 
                                unit = 's', bscale = 1, bzero = self.tzero)
        gti_end  = pf.Column(name='STOP', format='1D',
                                array= self.gti_j, 
                                unit = 's', bscale = 1, bzero  = self.tzero)
        gtiCols = pf.ColDefs([gti_start, gti_end])
        gtiHdu = pf.new_table(gtiCols, header = hdr)
        self.gtiExt = gtiHdu
    def doEvents(self):
        ''' Create Events extension '''
        # First we define header
        hdr = pf.Header()
        hdr.update('EXTNAME', 'SPECTRUM'              , 'Name of extension')    
        hdr.update('TELESCOP', 'GLAST'              , 'Name of mission/Satellite')
        hdr.update('INSTRUME', 'GBM'                , 'Specific Instrument used for observation')
        hdr.update('DETNAM', self.det               , 'Individual detector name')
        hdr.update('OBSERVER', 'MEEGAN'             , 'GLAST Burst Monitor P.I.')
        hdr.update('ORIGIN', 'UCD SSAMR'            , 'Name of Organisation making file' )
        hdr.update('DATE', self.date                , 'File creation date (YYYY-MM-DDThh:mm:ss UT)')
        hdr.update('DATE-OBS', self.obsStart        , 'Date of start of observation') 
        hdr.update('DATE-END', self.obsEnd          , 'Date of end of observation')                
        hdr.update('TIMESYS ', 'TT'                 , 'Time system used in time keywords')
        hdr.update('TIMEUNIT', 's'                  , 'Time since MJDREF, used in TSTART and TSTOP')
        hdr.update('MJDREFI' , 51910                , 'MJD of GLAST reference epoch, integer part')  
        hdr.update('MJDREFF' , 7.428703703703703e-4 , 'MJD of GLAST reference epoch, fractional part')  
        hdr.update('TSTART'  , self.tMin          , '[GLAST MET] Observation start time')
        hdr.update('TSTOP'   , self.tMax           , '[GLAST MET] Observation stop time')           
        hdr.update('TRIGTIME', self.trig            , 'Trigger time relative to MJDREF, double precisi')        
        hdr.update('OBJECT'  , 'SimData'            , 'Object')
        hdr.update('RADECSYS', 'FK5'                , 'Stellar reference frame')
        hdr.update('EQUINOX' , 2000.0               , 'Equinox for RA and Dec')
        hdr.update('RA_OBJ'  , self.ra              , 'Calculated RA of burst')
        hdr.update('DEC_OBJ' , self.dec             , 'Calculated Dec of burst')
        hdr.update('ERR_RAD' , self.radErr          , 'Calculated Location Error Radius')
        hdr.update('FILTER'  , 'none'               , 'Instrument Filter in use (if any)')
        hdr.update('AREASCAL', 1.                   , '')
        hdr.update('BACKFILE', 'none'               , '')
        hdr.update('BACKSCAL', 1.                   , '')
        hdr.update('RESPFILE', 'none'               , '')
        hdr.update('ANCRFILE', 'none'               , '')
        hdr.update('SYS_ERR',  0.                   , '')
        hdr.update('POISSERR',  True                    , '')
        hdr.update('GROUPING', 0                    , '')
        hdr.update('CHANTYPE' , 'PHA'                , '')
        hdr.update("CORRFILE", 'none', 'associated correction filename')
        hdr.update("CORRSCAL", 1.0, 'correction file scaling factor')        
        hdr.update('DETCHANS', self.nchan           , 'Total number of channels in each rate')
        hdr.update('HDUCLASS', 'OGIP'               , 'Format conforms to OGIP/GSFC conventions')
        hdr.update('HDUCLAS1', 'SPECTRUM'           , 'PHA dataset (OGIP memo OGIP-92-007)')
        hdr.update('HDUCLAS2', 'TOTAL'              , 'Indicates data type (source or background)')
        hdr.update('HDUCLAS3', 'COUNT'              , '')
        hdr.update('HDUCLAS4', 'TYPEII'             , '')
        hdr.update('HDUVERS', '1.2.1   '            , 'Version of HDUCLAS1 format in use')
        hdr.update('EXTVER'  , 1                    , 'Version of this extension format')
        
        if self.nchan == 128:
            phaFormat = '128J'
            errFormat = '128D'
        else:
            phaFormat = '8J'
            errFormat = '8D'
        
        #Now we define data table
        pha = np.array(self.pha, dtype=np.int32)
        countsCols = pf.Column(name = 'COUNTS', format = phaFormat, array = pha, 
                              unit = 'count', bscale = 1, bzero = int(32768),)

        expCols =  pf.Column(name = 'EXPOSURE', format = '1E', array = self.exp, unit = 's')
        qualCols = pf.Column(name = 'QUALITY', format = '1I', array = self.qual)

        time = pf.Column(name='TIME', format='1D', array = self.ti, 
                              unit = 's', bscale = 1, bzero = self.trig)
        endTime = pf.Column(name='ENDTIME', format='1D', array = self.tj, 
                              unit = 's', bscale = 1, bzero = self.trig)
        if self.statErr is not None:
            hdr['POISSERR'] = False
            statErr = pf.Column(name='STAT_ERR', format = errFormat, array=self.statErr,
                                unit = "count", bscale = 1, bzero = 0.)
            eventsCols = pf.ColDefs([countsCols, statErr, expCols, qualCols,time,endTime])
        else:
            eventsCols = pf.ColDefs([countsCols, expCols, qualCols,time,endTime])
        eventsHdu = pf.new_table(eventsCols, header = hdr)
        self.eventsExt = eventsHdu
    def write(self):
        ''' '''
        hdulist = pf.HDUList([self.primExt, self.eBoundsExt, self.eventsExt, 
                              self.gtiExt])
        hdulist.writeto(self.filename, clobber = self.clobber)

        

def createPHAII(t, exp, pha, det, trigTime, fileStem = '', hdrComment = '', edges = (),
                ra = 0, dec = 0, errRad = 0, qual = (), statErr = None, bkg = False):

    ''' 
    Takes 5 inputs: t, pha, det, trigTime, fileStem & hdrComment. t is the time 
    of events and must be a numpy array. Pha is the channel of the events and 
    must be a numpy array. det is the detector, and should take the format 
    BGO_00 or BGO_01.  trigTime is the zeroTime of the file. 
    fileStem is the string which will identify the file and will 
    replace the usual yymmddfff. hdrComment is a string that will be written
    to the header of the primary extension.
    '''
    nChan = pha.shape[1]
    phaii = PHAII( t, exp, pha, det, trigTime, fileStem, hdrComment, edges,
                    ra, dec, errRad, nChan, statErr = statErr )
    phaii.doPrimary()
    phaii.doEbounds()
    phaii.doGTI()
    phaii.doEvents()
    if bkg:
        phaii.eventsExt.header["HDUCLAS2"] = "BKG"    
    phaii.write()