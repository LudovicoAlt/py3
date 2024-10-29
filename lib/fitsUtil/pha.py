'''
pha.py

Create a PHA file.

PHA files consist of 4 extensions (0-3). 
 #0 Primary: contains no data 
 #1 EBounds: Contains rates per channel in discrete time bins
 #2 SPECTRUM: Contains channel and corresponding count value with stat error
 #3 GTI: Contains good time intervals


Dependencies: 
numpy
astropy.io.fits

'''

import os
import datetime

import astropy.io.fits as pf
import numpy as np

__version__ = 1.0

class PHA:
    ''' Class for the creation of PHA files'''
    def __init__(self, t, exp, pha, det,trigTime, fileStem, hdrComment, edges,
                    ra, dec, radErr, nchan, gti = (), qual = np.empty((0)), 
                    err = None, statErr = False):
        '''Read in time and pha arrays, detector and set up file.'''
        # define detDic - this maps from detector name needed for header to 
        # detector name needed for filename
        detDic = {'NAI_00': 'n0', 'NAI_01': 'n1', 'NAI_02': 'n2', 
                  'NAI_03': 'n3', 'NAI_04': 'n4', 'NAI_05': 'n5', 
                  'NAI_06': 'n6', 'NAI_07': 'n7', 'NAI_08': 'n8', 
                  'NAI_09': 'n9', 'NAI_10': 'na', 'NAI_11': 'nb', 
                  'BGO_00': 'b0', 'BGO_01': 'b1'}
        
        detDic_inverted = {v: k for k, v in detDic.items()}

        self.det = detDic_inverted[det]

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
        self.tMin = self.ti[0] 
        self.tMax = self.tj[-1]
        self.date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        # Observation start & end in UT
        self.obsStart = (datetime.datetime(2001, 0o1, 0o1, 0, 0, 0) + datetime.timedelta(0, (float(self.tMin)) ) ).strftime("%Y-%m-%dT%H:%M:%S")
        self.obsEnd =   (datetime.datetime(2001, 0o1, 0o1, 0, 0, 0) + datetime.timedelta(0, (float(self.tMax)) ) ).strftime("%Y-%m-%dT%H:%M:%S")

        # Observatoin start & end in MET
        self.tStart = self.trig - self.tMin
        self.tStop = self.trig + self.tMax
        # filename is the output filename and may be a full path. We also
        # need just the filename - this is for the keyword FILENAME in 
        # extensions 0 & 1
        self.filename = fileStem
        self.hdrFileName = str(os.path.split(self.filename)[-1]) # astropy.io.fits will not write the file without the extra str()
        
        # Energy Edges (EBOUNDS)
        self.eMin = edges[0]
        self.eMax = edges[1]            
        if nchan == 8:
            self.spec = 'CTIME'
        else:
            self.spec = 'CSPEC'
        self.nchan = nchan
        # SPECTRUM
        self.exp = exp.sum()
        self.rate = pha.sum(0)/self.exp
        
        if err is None:
            #Poisson error divided by exposure
            self.rateErr = np.sqrt(pha.sum(0))/self.exp
        else:
            self.rateErr = np.sqrt((err**2).sum(0))/self.exp
        
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
        hdr.set('Creator', 'osv.py V' + str(__version__), 'Software and version creating file')
        hdr.set('FILETYPE', 'SPECTRUM'              , 'Name for this type of FITS File')
        hdr.set('FILE-VER', '1.0.0'              , 'Version of the format for this filetype')
        hdr.set('TELESCOP', 'GLAST'              , 'Name of mission/Satellite')
        hdr.set('INSTRUME', 'GBM'                , 'Specific Instrument used for observation')
        hdr.set('DETNAM',   self.det             , 'Individual detector name')
        hdr.set('OBSERVER','MEEGAN'              , 'GLAST Burst Monitor P.I.')
        hdr.set('ORIGIN'  ,'UCD SSAMR'           , 'Name of Organisation making file' )
        hdr.set('DATE'    , self.date            , 'File creation date (YYYY-MM-DDThh:mm:ss UT)')
        hdr.set('DATE-OBS', self.obsStart        , 'Date of start of observation') 
        hdr.set('DATE-END', self.obsEnd          , 'Date of end of observation')                
        hdr.set('TIMESYS ', 'TT'                 , 'Time system used in time keywords')
        hdr.set('TIMEUNIT', 's'                  , 'Time since MJDREF, used in TSTART and TSTOP')
        hdr.set('MJDREFI' , 51910                , 'MJD of GLAST reference epoch, integer part')  
        hdr.set('MJDREFF' , 7.428703703703703e-4 , 'MJD of GLAST reference epoch, fractional part')  
        hdr.set('TSTART'  , self.tMin            , '[GLAST MET] Observation start time')
        hdr.set('TSTOP'   , self.tMax            , '[GLAST MET] Observation stop time')           
        hdr.set('FILENAME', self.hdrFileName     , 'Name of this file')
        hdr.set('DATATYPE', self.spec            , 'GBM datatype for this file')
        hdr.set('TRIGTIME', self.trig            , 'Trigger time relative to MJDREF, double precisi')
        hdr.set('OBJECT'  , ''                   , 'Object')  
        hdr.set('RADECSYS', 'FK5'                , 'Stellar reference frame')     
        hdr.set('EQUINOX' , 2000.0               , 'Equinox for RA and Dec')                      
        hdr.set('RA_OBJ'  , self.ra              , 'Calculated RA of burst')                       
        hdr.set('DEC_OBJ' , self.dec             , 'Calculated Dec of burst')                       
        hdr.set('ERR_RAD' , self.radErr          , 'Calculated Location Error Radius')
        hdr.set('INFILE01', ''                   , 'Level 1 input lookup table file')     
        hdr.set('INFILE02', ''                   , 'Level 0 input data file')                      
        hdr.set('INFILE03', ''                   , 'Level 0 input data file')                    
        
        if self.hdrComment:
            hdr.add_comment(self.hdrComment)
        hdu = pf.PrimaryHDU(data = None, header = hdr)
        self.primExt = hdu
    def doEbounds(self):
        '''
        Create EBounds Extension.
        '''
        # First we define header
        hdr = pf.Header()
        hdr.set('EXTNAME', 'EBOUNDS'            , 'Name of extension')    
        hdr.set('TELESCOP', 'GLAST'              , 'Name of mission/Satellite')
        hdr.set('INSTRUME', 'GBM'                , 'Specific Instrument used for observation')
        hdr.set('DETNAM', self.det               , 'Individual detector name')
        hdr.set('OBSERVER', 'MEEGAN'             , 'GLAST Burst Monitor P.I.')
        hdr.set('ORIGIN', 'UCD SSAMR'            , 'Name of Organisation making file' )
        hdr.set('DATE', self.date                , 'File creation date (YYYY-MM-DDThh:mm:ss UT)')
        hdr.set('DATE-OBS', self.obsStart        , 'Date of start of observation') 
        hdr.set('DATE-END', self.obsEnd          , 'Date of end of observation')                
        hdr.set('TIMESYS ', 'TT'                 , 'Time system used in time keywords')
        hdr.set('TIMEUNIT', 's'                  , 'Time since MJDREF, used in TSTART and TSTOP')
        hdr.set('MJDREFI' , 51910                , 'MJD of GLAST reference epoch, integer part')  
        hdr.set('MJDREFF' , 7.428703703703703e-4 , 'MJD of GLAST reference epoch, fractional part')  
        hdr.set('TSTART'  , self.tMin          , '[GLAST MET] Observation start time')
        hdr.set('TSTOP'   , self.tMax           , '[GLAST MET] Observation stop time')           
        hdr.set('FILENAME', self.hdrFileName     , 'Name of this file')
        # hdr.set('DATATYPE', 'TTE'                , 'GBM datatype for this file')
        hdr.set('TRIGTIME', self.trig            , 'Trigger time relative to MJDREF, double precisi')
        hdr.set('OBJECT'  , 'SimData'            , 'Object')  
        hdr.set('RADECSYS', 'FK5'                , 'Stellar reference frame')     
        hdr.set('EQUINOX' , 2000.0               , 'Equinox for RA and Dec')                      
        hdr.set('RA_OBJ'  , self.ra              , 'Calculated RA of burst')                       
        hdr.set('DEC_OBJ' , self.dec             , 'Calculated Dec of burst')                       
        hdr.set('ERR_RAD' , self.radErr          , 'Calculated Location Error Radius')
        hdr.set('HDUCLASS', 'OGIP'               , 'Confirms to OGIP standard indicated in HDUCLAS1')     
        hdr.set('HDUCLAS1', 'RESPONSE'           , 'These are typically found in RMF files')                      
        hdr.set('HDUCLAS2', 'EBOUNDS'            , 'From CAL/GEN/92-002')   
        hdr.set('HDUVERS' , '1.2.0'              , 'Version of HDUCLAS1 format in use')
        hdr.set('CHANTYPE', 'PHA'                , 'No corrections have been applied')
        hdr.set('FILTER'  , 'NONE'               , 'The instrument filter in use (if any)')
        hdr.set('DETCHANS', self.nchan           , 'Total number of channels in each rate')
        hdr.set('EXTVER'  , 1                    , 'Version of this extension format')
        hdr.set('CH2E_VER', 'SPLINE 2.0'         , 'Channel to energy conversion scheme used')
        hdr.set('GAIN_COR', 1.0                  , 'Gain correction factor applied to energy edges')
        #Now we define data table
        channels = np.arange(0, self.nchan)
        
        channelsCols = pf.Column(name='Channels', format='1I', array = channels, 
                              unit = 'none', bscale = 1, bzero = 0)
        eMinCols = pf.Column(name='E_MIN', format='1E', array = self.eMin, 
                              unit = 'kev', bscale = 1, bzero = 0)
        eMaxCols = pf.Column(name='E_MAX', format='1E', array = self.eMax, 
                              unit = 'kev', bscale = 1, bzero = 0)
        eBoundsCols = pf.ColDefs([channelsCols, eMinCols, eMaxCols])
        eBoundsHdu = pf.BinTableHDU.from_columns(eBoundsCols, hdr)
        self.eBoundsExt = eBoundsHdu
        
    def doGTI(self):
        ''' Create GTI extension. Interval is taken as the entire data set. '''
        # First we define header
        hdr = pf.Header()
        hdr.set('EXTNAME', 'GTI'                 , 'Name of extension')    
        hdr.set('TELESCOP', 'GLAST'              , 'Name of mission/Satellite')
        hdr.set('INSTRUME', 'GBM'                , 'Specific Instrument used for observation')
        hdr.set('DETNAM', self.det               , 'Individual detector name')
        hdr.set('OBSERVER', 'MEEGAN'             , 'GLAST Burst Monitor P.I.')
        hdr.set('ORIGIN', 'UCD SSAMR'            , 'Name of Organisation making file' )
        hdr.set('DATE', self.date                , 'File creation date (YYYY-MM-DDThh:mm:ss UT)')
        hdr.set('DATE-OBS', self.obsStart        , 'Date of start of observation') 
        hdr.set('DATE-END', self.obsEnd          , 'Date of end of observation')                
        hdr.set('TIMESYS ', 'TT'                 , 'Time system used in time keywords')
        hdr.set('TIMEUNIT', 's'                  , 'Time since MJDREF, used in TSTART and TSTOP')
        hdr.set('MJDREFI' , 51910                , 'MJD of GLAST reference epoch, integer part')  
        hdr.set('MJDREFF' , 7.428703703703703e-4 , 'MJD of GLAST reference epoch, fractional part')  
        hdr.set('TSTART'  , self.tMin          , '[GLAST MET] Observation start time')
        hdr.set('TSTOP'   , self.tMax           , '[GLAST MET] Observation stop time')           
        hdr.set('HDUCLASS', 'OGIP'               , 'Confirms to OGIP standard indicated in HDUCLAS1')     
        hdr.set('HDUCLAS1', 'GTI'                , 'Indicates good time intervals')                      
        hdr.set('HDUCLAS2', 'EBOUNDS'            , 'From CAL/GEN/92-002')   
        hdr.set('HDUVERS' , '1.2.0'              , 'Version of HDUCLAS1 format in use')
        hdr.set('EXTVER'  , 1                    , 'Version of this extension format')
        hdr.set('TRIGTIME', self.trig            , 'Trigger time relative to MJDREF, double precisi')        
        hdr.set('OBJECT'  , 'SimData'            , 'Object')  
        hdr.set('RADECSYS', 'FK5'                , 'Stellar reference frame')     
        hdr.set('EQUINOX' , 2000.0               , 'Equinox for RA and Dec')                      
        hdr.set('RA_OBJ'  , self.ra              , 'Calculated RA of burst')                       
        hdr.set('DEC_OBJ' , self.dec             , 'Calculated Dec of burst')                       
        hdr.set('ERR_RAD' , self.radErr          , 'Calculated Location Error Radius')
        #Now we define data table
        gti_start = pf.Column(name='START', format='1D',
                                array = self.gti_i, 
                                unit = 's', bscale = 1, bzero = self.tzero)
        gti_end  = pf.Column(name='STOP', format='1D',
                                array= self.gti_j, 
                                unit = 's', bscale = 1, bzero  = self.tzero)
        gtiCols = pf.ColDefs([gti_start, gti_end])
        gtiHdu = pf.BinTableHDU.from_columns(gtiCols, hdr)
        self.gtiExt = gtiHdu
    def doEvents(self):
        ''' Create Events extension '''
        # First we define header
        hdr = pf.Header()
        hdr.set('EXTNAME', 'SPECTRUM'            , 'Name of extension')    
        hdr.set('TELESCOP', 'GLAST'              , 'Name of mission/Satellite')
        hdr.set('INSTRUME', 'GBM'                , 'Specific Instrument used for observation')
        hdr.set('DETNAM', self.det               , 'Individual detector name')
        hdr.set('OBSERVER', 'MEEGAN'             , 'GLAST Burst Monitor P.I.')
        hdr.set('ORIGIN', 'UCD SSAMR'            , 'Name of Organisation making file' )
        hdr.set('DATE', self.date                , 'File creation date (YYYY-MM-DDThh:mm:ss UT)')
        hdr.set('DATE-OBS', self.obsStart        , 'Date of start of observation') 
        hdr.set('DATE-END', self.obsEnd          , 'Date of end of observation')                
        hdr.set('TIMESYS ', 'TT'                 , 'Time system used in time keywords')
        hdr.set('TIMEUNIT', 's'                  , 'Time since MJDREF, used in TSTART and TSTOP')
        hdr.set('MJDREFI' , 51910                , 'MJD of GLAST reference epoch, integer part')  
        hdr.set('MJDREFF' , 7.428703703703703e-4 , 'MJD of GLAST reference epoch, fractional part')  
        hdr.set('TSTART'  , self.tMin          , '[GLAST MET] Observation start time')
        hdr.set('TSTOP'   , self.tMax           , '[GLAST MET] Observation stop time')           
        hdr.set('TRIGTIME', self.trig            , 'Trigger time relative to MJDREF, double precisi')        
        hdr.set('OBJECT'  , 'SimData'            , 'Object')
        hdr.set('RADECSYS', 'FK5'                , 'Stellar reference frame')
        hdr.set('EXPOSURE', self.exp             , 'exposure time (in seconds)')
        hdr.set('QUALITY', 0, '')
        hdr.set('EQUINOX' , 2000.0               , 'Equinox for RA and Dec')
        hdr.set('RA_OBJ'  , self.ra              , 'Calculated RA of burst')
        hdr.set('DEC_OBJ' , self.dec             , 'Calculated Dec of burst')
        hdr.set('ERR_RAD' , self.radErr          , 'Calculated Location Error Radius')
        hdr.set('FILTER'  , 'none'               , 'Instrument Filter in use (if any)')
        hdr.set('AREASCAL', 1.                   , '')
        hdr.set('BACKFILE', 'none'               , '')
        hdr.set('BACKSCAL', 1.                   , '')
        hdr.set('RESPFILE', 'none'               , '')
        hdr.set('ANCRFILE', 'none'               , '')
        #hdr.set('SYS_ERR',  0.                   , '')
        hdr.set('POISSERR',  True                  , '')
        
        hdr.set('GROUPING', 0                    , '')
        hdr.set("CORRFILE", 'none', 'associated correction filename')
        hdr.set("CORRSCAL", 1.0, 'correction file scaling factor')

        hdr.set("HDUVERS", '1.2.0   ',           "Format version number")
        hdr.set("HDUVERS1", '1.1.0   ',           "Version of format (OGIP memo OGIP-92-007a)")


        hdr.set('CHANTYPE' , 'PHA'                , '')
        hdr.set('DETCHANS', self.nchan           , 'Total number of channels in each rate')
        hdr.set('HDUCLASS', 'OGIP'               , 'Format conforms to OGIP/GSFC conventions')
        hdr.set('HDUCLAS1', 'SPECTRUM'           , 'PHA dataset (OGIP memo OGIP-92-007)')
        hdr.set('HDUCLAS2', 'TOTAL'              , 'Indicates data type (source or background)')
        hdr.set('HDUCLAS3', 'RATE'              , '')
        hdr.set('HDUCLAS4', 'TYPEI'             , '')
        hdr.set('EXTVER'  , 1                    , 'Version of this extension format')
        
        #if self.statErr:
            #hdr['POISSERR'] = False

        #Now we define data table
        channels = np.arange(self.nchan).reshape(1, 128)
        qual_in = (np.ones(self.nchan) * self.qual).reshape(1, 128)
        rate_in = self.rate.reshape(1, 128)
        group_in = np.ones(self.nchan).reshape(1, 128)

        channelsCols = pf.Column(name='CHANNEL', format=f'{self.nchan}I', array = channels) # bscale = 1, bzero = 0)
        #rateCols = pf.Column(name='RATE', format='1E', array = self.rate, unit = 'count/s',)# bscale = 1, bzero = 32768)
        rateCols = pf.Column(name='RATE', format=f'{self.nchan}D', array = rate_in, unit='Count/s')


        time_col        = pf.Column(name='TSTART'   , format='D', array = [min(self.ti)], unit = 's')
        telapse_col     = pf.Column(name='TELAPSE'  , format='D', array = [max(self.ti)-min(self.ti)], unit = 's')
        specnum_col     = pf.Column(name='SPEC_NUM' , format='I', array = [1])

        quality_col     = pf.Column(name='QUALITY'  , format=f'{self.nchan}I', array = qual_in)
        groupin_col     = pf.Column(name='GROUPING' , format=f'{self.nchan}I', array = group_in)
        exposure_col    = pf.Column(name='EXPOSURE' , format='D', array = [self.exp], unit = 's')
        backfile_col    = pf.Column(name='BACKFILE' , format='6A', array = np.array(['none']))
        respfile_col    = pf.Column(name='RESPFILE' , format='6A', array = np.array(['none']))
        ancrfile_col    = pf.Column(name='ANCRFILE' , format='6A', array = np.array(['none']))
       # rateErrCols = pf.Column(name='STAT_ERR', format='1E', array = self.rateErr, 
       #                       unit = 'count/s', )#bscale = 1, bzero = 32768)
        # TODO - add error column if there are issues

        #eventsCols = pf.ColDefs([channelsCols, rateCols, rateErrCols])
        # eventsCols = pf.ColDefs([channelsCols, 
        #                          rateCols])

        eventsCols = pf.ColDefs([time_col, 
                         telapse_col, 
                         specnum_col, 
                         channelsCols, 
                         rateCols, 
                         quality_col, 
                         groupin_col, 
                         exposure_col,
                         backfile_col,
                         respfile_col,
                         ancrfile_col
                         ])


        eventsHdu = pf.BinTableHDU.from_columns(eventsCols, hdr)
        
        self.eventsExt = eventsHdu
    def write(self):
        ''' 
        Write the HDU list to the file
        '''
        hdulist = pf.HDUList([self.primExt, self.eBoundsExt, self.eventsExt, 
                              self.gtiExt]) 
        hdulist.writeto(self.filename, overwrite = self.clobber)
        hdulist.close()

        

def createPHA(t, exp, pha, det, trigTime, fileStem = '', hdrComment = '', edges = (),
                ra = 0, dec = 0, errRad = 0, qual = (), err = None, statErr = False,
                bkg = False):
    ''' 
    Takes 5 inputs: t, pha, det, trigTime, fileStem & hdrComment. t is the time 
    of events and must be a numpy array. Pha is the channel of the events and 
    must be a numpy array. det is the detector, and should take the format 
    BGO_00 or BGO_01.  trigTime is the zeroTime of the file. 
    fileStem is the string which will identify the file and will 
    replace the usual yymmddfff. hdrComment is a string that will be written
    to the header of the primary extension.   
    '''
    nChan = pha.shape[1] #!they use phaii variable adjust for clarity?
    phaii = PHA( t, exp, pha, det, trigTime, fileStem, hdrComment, edges,
                    ra, dec, errRad, nChan, err = err, statErr = statErr)
    phaii.doPrimary()
    phaii.doEbounds()
    phaii.doGTI()
    phaii.doEvents()
    if bkg:
        phaii.eventsExt.header["HDUCLAS2"] = "BKG"
    phaii.write()
