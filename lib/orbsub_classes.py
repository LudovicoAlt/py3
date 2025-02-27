
import  os
import  numpy   as np
from    glob    import glob
from    lib     import fitsUtil
import  lib.util.util as util

class Regions:
    '''
    Determine the time of selection regions
    '''
    def __init__(self, zero_met, tmin, tmax, offset, 
                 orbit_period = 5737.70910239):
        self.period = orbit_period 
        ranges = {}
        shifts = {}
        for i in offset:
            if i == 'src':
                tempShift = 0
            else:
                tempShift = orbit_period * float(i)
            shifts.update({i: tempShift})
            
        signs = {'pre': -1, 'pos': +1, 'src': 0}        
        for i in list(shifts.keys()):
            if i != 'src':
                loop = ['pre','pos']
            else:
                loop = ['src']
            for range in loop:
                if range == 'src':
                    index = range
                else:
                    index = range+i
                temp = np.array([zero_met + tmin + signs[range] * shifts[i], 
                      zero_met + tmax + signs[range] * shifts[i]])
                ranges.update({index: temp}) 
        self.ranges = ranges
        self.offset = offset
        
    def __str__(self):
        mes = "Offsets for selection Periods\n" 
#        mes = mes + "Zero offset: "\n"
#        mes = mes + "Negative offset (14 orbits): " + str(self.pre_14) + "\n"
#        mes = mes + "Positive offset (14 orbits): " + str(self.pos_14) + "\n"
#        mes = mes + "Negative offset (16 orbits): " + str(self.pre_16) + "\n"
#        mes = mes + "Positive offset (16 orbits): " + str(self.pos_16) + "\n"
#        mes = mes + "Negative offset (30 orbits): " + str(self.pre_30) + "\n"
#        mes = mes + "Positive offset (30 orbits): " + str(self.pos_30) + "\n"
        return mes

class Files:
    def __init__(self, zero_met, offsets, offset):
        ''' Returns a list of days '''
        #Find maximum offsets from tzero
        regions = []
        days = []
        self.pha_files = []
        self.pos_files = []
        self.days = []
        for i in offset:
            if i != 'src': 
                for j in ['pre','pos']:
                    regions.append(j + i)
            else:
                regions.append( i )
            
        for i in regions:
            for t in offsets.ranges[i]:
                grb_t = util.met_grb(t, day = True)
                days.append(grb_t)
        # remove duplicates
        days = list(set(days)) 
        days.sort()
        self.days = days
        self.errMes = ''
        self.error = False
        
        detDict = {}
        for i in self.days:
            detDict.update({i: []})
        self.missingFiles = {'pos': [], 'cspec': detDict, 'ctime':detDict}

    def find_poshist_files(self, data_dir):
        
        ''' Find a list a of POSHIST files corresponding to input dates '''
        for i in self.days:
            # pos_file = glob(str(data_dir) + slash + i + slash + 'glg_poshist_all_' + i + '*fit')
            pos_file = glob(os.path.join(data_dir,i,'glg_poshist_all_' + i + '*fit'))
            if i == self.days[0]:
                self.pos_files = pos_file
            else:
                self.pos_files = self.pos_files + pos_file
            if not len(pos_file):
                self.missingFiles['pos'] += [i]
        if self.pos_files == []:
            #No pos files found
            self.pos_files = None
            self.error = True
            self.errMes += "*** No poshist files found\n"
        elif len(self.days) != len(self.pos_files):
            #Missing days
            self.error = True
            self.errMes += "*** Unequal number of days and poshist files\n"
            self.errMes += "*** %s \n" %self.days
            self.errMes += "*** %s \n" %self.pos_files
    def find_pha_files(self, detectors, spec_type = 'ctime', data_dir = ''):
        '''
        Find a list a of PHA files corresponding to input dates & detectors
        Result is stored in a dictionary
        
        '''
        for j in detectors:
            for i in self.days:
                # pha_file_string = (str(data_dir) + slash + i + slash + 'glg_' + spec_type.lower() + '_' + j + '_' + i + '*pha')
                pha_file_string = os.path.join(data_dir, i,'glg_' + spec_type.lower() + '_' + j + '_' + i + '*pha')
                pha_file = glob(pha_file_string)
                if i == self.days[0]:
                    pha_file_list = pha_file
                else:
                    pha_file_list = pha_file_list + pha_file
                # pha file not found
                if not len(pha_file):
                    self.missingFiles[spec_type.lower()][i].append(j)
            if len(pha_file_list) != len (self.days):
                self.error = True
                self.errMes += "*** PHA Files missing for %s\n" %j
                self.errMes += "*** %s \n" %self.days
                self.errMes += "*** %s \n" %pha_file_list
            if j == detectors[0]:
                pha_files = {j:pha_file_list}
            else:
                pha_files[j] = pha_file_list
        self.pha_files = pha_files

    def __str__(self):
        message = '\n<Begin Files>\n'
        message = message + "Days:"+"\n"
        for i in self.days:
            message = message + "  " + i + "\n"
        message = message + "POSHIST Files:" + "\n"
        for i in self.pos_files:
            message = message + "  " + i + "\n"
        message = message + "PHA Files:" + "\n"
        for i in self.pha_files:
            message = message + "  " + i + ":\n"
            for j in self.pha_files[i]:
                message = message + "       " + j + "\n"
        message += '<End Files>\n\n'                
        return message

class Poshist_data:
    def __init__(self,pos_files):
        '''
        Read in data for a list of POSHIST Files 
        '''
        
        for i in pos_files:
            poshist_data = util.read_poshist(i, verbose = False)
            if i == pos_files[0]:
                self.sc_time = poshist_data[0]
                self.sc_pos = poshist_data[1]
                self.sc_quat = poshist_data[2]
                self.sc_coords = poshist_data[3]
            else:
                self.sc_time = np.concatenate((self.sc_time, poshist_data[0]))
                self.sc_pos = np.concatenate((self.sc_pos, poshist_data[1]))
                self.sc_quat = np.concatenate((self.sc_quat, poshist_data[2]))
                self.sc_coords = np.concatenate((self.sc_coords,
                                                 poshist_data[3]))
        self.period = None
        self.rises = None
        self.sets = None
        self.occTI = None
        
    def calculate_angles(self, regions, ra, dec):
        '''
        Calculate detector angles for region of interest. Result is stored in 
        a dictionary, the keys of which are the detectors
        '''
        ranges = regions.ranges
        offset = regions.offset
        # First calculate angles during ROI
        dur_indices = ((self.sc_time >ranges['src'][0]) & 
            (self.sc_time < ranges['src'][1]))
        self.dur_pointing, pointingGeo, distfromdet = util.calc_angles(
                                    self.sc_time[dur_indices],
                                    self.sc_pos[dur_indices],
                                    self.sc_quat[dur_indices],
                                    ra, dec)
        self.dur_t = self.sc_time[dur_indices]
        pointing = { 'src': self.dur_pointing}
        times = {'src': self.dur_t}
        for i in offset:
            if i == 'src':
                continue
            for j in ['pre', 'pos']:
                tRange = ranges[j + i]
                boolIndex = ((self.sc_time > tRange[0]) &
                              (self.sc_time < tRange[1]))
                t = self.sc_time[boolIndex]
                pointTemp,pointingGeo, detAngles = util.calc_angles(self.sc_time[boolIndex],
                                                        self.sc_pos[boolIndex],
                                                        self.sc_quat[boolIndex],
                                                        ra, dec)
                times.update({j + i: t})
                pointing.update({j + i: pointTemp})
        self.pointing = pointing
        self.times = times
        dets = np.array(['n0','n1','n2','n3','n4','n5','n6','n7','n8',
                         'n9','na','nb','b0','b1'])
        det_angles = {}
        for ang, det in zip(distfromdet.transpose(), dets):
            det_angles.update({det: ang})
        self.det_angles = det_angles
    def calc_period(self):
        '''
        Calculate orbital period of Fermi. Assumes circular motion, not quite
        correct.
        '''
        G = 6.67428e-11    # m^3 kg^-1 s^-2
        M = 5.9722e24      # kg Mass Earth  
        r = (np.sum(self.sc_pos**2., 1))**(1/2.)
        r_avg = np.average(r)
        r_cubed = (r_avg)**3.
        factor = r_cubed/(G*M)
        period = 2. * np.pi * np.sqrt(factor)
        self.period = period

    def get_gti(self):
        '''
        Determine what NaI, BGO detectors have angles <60, <90 respectively.
        '''
        gtis = {}
        for det in self.det_angles:
            ang = self.det_angles[det]
            #BGO & NaI have different criteria for good detector selecitons
            if det =='b0' or det == 'b1':
                good_ang = 90
            else:
                good_ang = 60
            bool_list = ang < good_ang
            gti = util.make_gti(self.dur_t, bool_list)
            if gti == ([],[]):
                gti = None
            gtis.update({det: gti})
        self.gti = gtis
    def get_steps(self, ra, dec):
        ''' 
        Get Occultation Step Times and determine corresponding time intervals
        '''
        rises, sets = util.calc_occ_steps(ra, dec, self.sc_time, self.sc_pos)
        self.rises, self.sets = rises, sets
        
        # Now lets make the time intervals (TIs) corresponding to the times when 
        # the source is occulted. There are several possibilities
        # 1) There are an equal number of rises and sets
        # 2) There are more sets than rises
        # 3) There are more rises than sets
        # If we have 1), and the first step occurs before the first rise then
        # we can simply fill the TIs with the sets & rises. If however, the
        # first rise occurs before the first step, we have to stick the earliest
        # possible time onto the start of the set array.
        # If we have 2), then the first set should be less than the first rise,
        # and we can simply add the last possible time to the rise list
        # If we have 3), then the first rise should be less than the first set,
        # and we can simply add the first possible time to the set list.

        if rises.size == sets.size:
            if sets[0] < rises[0]:
                occI = list(sets)
                occJ = list(rises)
            else:
                occI = [self.sc_time[0]]
                occI.extend(list(sets))
                occJ = list(rises)
                occJ.extend([self.sc_time[-1]])
        elif sets.size > rises.size:
            if sets[0] < rises[0]:
                occI = list(sets)[:-1]
                occJ = list(rises)                
            else:
                mes = '*** More sets than rises, yet first rise occurs before \
                    first set - shouldn\'t be possible. Likely to crash soon!'
                print(mes)
        elif sets.size < rises.size:
            if rises[0] < sets[0]:
                occI = list(sets)
                # Ignore the first rise
                occJ = list(rises)[1:]
            else:
                mes = '*** More rises than sets, yet first set occurs before \
                    first rise - shouldn\'t be possible. Likely to crash soon!'
                print(mes)

        self.occTI = occI, occJ

class Pha_data:
    '''
    Class for GBM PHA data
    '''
    def __init__(self, pha_files):
        '''
        Concatenate the data from several days into single arrays
        '''
        self.detector = 'null'
        # the double slash vs forward slash makes it work on windows 
        # does nothing if there are no double slashes
        self.detector =  pha_files[0].replace('\\', '/').split('/')[-1][10:12]
        
        for i in pha_files:
            
            t_start, t_end, t_exposure, counts,  eMin, eMax = util.read_pha(i)
            
            # TODO clean up, quality is handled in read pha no ?
            #print("This is the file: ", i, "\n")
            #print(" with t_start ", t_start)
            #print(" with t_end ", t_end)
            #print(" with t_exposure ", t_exposure)

            #self.pha_data=pha_data[4]
            #qual = pha_data[2].data['QUALITY']
            #qual = (qual!=11)
            
            if i == pha_files[0]:
                
                self.t_start = t_start
                self.t_end = t_end
                self.t_exposure = t_exposure
                self.counts = counts
                self.eEdgeMin = eMin
                self.eEdgeMax = eMax

            else:
                self.t_start = np.concatenate((self.t_start, t_start))
                self.t_end = np.concatenate((self.t_end, t_end))
                self.t_exposure = np.concatenate((self.t_exposure, t_exposure))
                self.counts = np.concatenate((self.counts, counts))
            
    def bin_pha(self, regions, offset, opts):
        '''
        Bin up pha counts to desired binsize -> also keep original data
        '''
        nchan = self.eEdgeMin.size
        
        if nchan == 128:
            resolution = 4.096 # seconds
        elif nchan == 8:
            resolution = 1.024 # 0.256
        # deltaT = -opts.tRange[0] + opts.tRange[1] never referenced?

        # Loop over orbit offsets & extract data in each region.
        # The offsets are strings which are used to index the dictionary 
        # _ region.ranges which contains the time ranges associated with each 
        # offset in MET. For the source interval the index is 'src'.
        # The data for each orbit offset is stored in dictionary data which 
        # is indexed by the same offset string as region.ranges

        data = {}
        self.binDataMes = ''
        self.binDataErrMes = ''
        self.binDataError = False

        for i in offset:
            if i != 'src':
                loop = ['pre' + i, 'pos' + i]
            else:
                loop = ['src']
            for index in loop:
                # Here we extract the indices for the region of interest (index)
                # We can potentially have an issue were no data falls in this 
                # range, e.g. if our region is coincident with a SAA passage.
                # We could force the user to input a minimum range - but this
                # will still fail if the detectors are turned off for more
                # than this time - has happened in the past. 
                # The best thing to do is to simply check if there is data in 
                # the range - if so, carry on as normal. If not - update the 
                # data dictionary with False and also create a warning message
                # than can be passed back up to the user interface. 
                
                #print "<> %s <>" %index
                region = regions.ranges[index]
                
                mask = np.where((self.t_start >= region[0] ) & 
                                (self.t_end <= region[1]))

                if not mask[0].size:
                    self.binDataErrMes += "*** Detector: %s, No data found: times: %.3f-%.3f, index: %s\n" %(self.detector, region[0], region[1], index)
                    data.update({index: False})
                    self.binDataError = True
                    continue

                x,y,exp,err = util.rebin_gbm(
                        np.column_stack((self.t_start[mask], self.t_end[mask])),
                                        self.counts[mask],
                                        self.t_exposure[mask],
                                        resolution = resolution,
                                        trange = region)
                data.update({index: [x,y,exp,err]})
        self.data = data
        
        return
    
    def calc_background(self, offset):
        '''
        Take average of offset regions to determine the background.
        
        29.11.11 Fixed the error with the zeromask. The boolean logic was wrong
        in the initial determination of zeromask - it was ignoring ~half of the
        background regions. In addition the zeromask of the counts in the
        region of interest was not calculated.
        
        '''
        data = self.data
        background = {}
        #Loop over pre & pos, then over the orbit offset (e.g. 14,16, etc..)
        #For pre/pos we increment the background & error each time,
        #then at the end we combine the result from each to make the 
        #total background and error. The results are stored in a dictionary
        
        # We only want to look at the background regions -> define new offset
        # variable
        
        bak_offset = list( set(offset) - set(['src']))
        zeromask = None
        # For pre & pos regions, we first sum the counts and error, then 
        # get the average
        
        for j in ['pre','pos']:

            n = 0
            for i in bak_offset:
                
                index = j + i              
                if not data[index]:
                    continue                    
                if n == 0:
                    zeromask = (np.average(data[index][1],1)==0)
                    bkg = data[index][1]
                    bkgErr = data[index][3]**2 #! TODO dble check Should the error not be sqrt?
                else:
                    zeromask = (zeromask == True) | (np.average(data[index][1],1)==0)
                    bkg += data[index][1]
                    bkgErr += data[index][3]**2
                n += 1
            
            # We have summed the counts and background (in quadrature)
            # Now we divide by the contributing to get the average 
            bkg = bkg/(1.0*n)
            
            bkgErr = (1.0/n) * np.sqrt(bkgErr)
            background.update({j:bkg})
            background.update({j+'err':bkgErr})                       
        background.update({'all': np.average((background['pre'],background['pos'],),0)})
        
        allerr=0.5 * np.sqrt(background['preerr']**2 +background['poserr']**2)
        background.update({'allerr': allerr})

        #Now find which indices for values of non-zero counts common to all 
        #bkg regions. Use this to set counts to zero & for quality flag
        zeromask = (zeromask == True) | (np.average(data['src'][1],1) == 0)
        for i in range(1, zeromask.size-1):
            if zeromask[i] == True:
                if zeromask[i-1] != True:
                #This seemed to be removing too much data - edited 16.12.11
                    zeromask[i-1:i] = True
        
        #Set any bin which has one or more saa contributers to zero
        for i in ['all','pre','pos','preerr','poserr','allerr']:
            background[i][zeromask] = 0

        data['src'][1][zeromask] = 0 # 1 -> counts
        data['src'][3][zeromask] = 0 # 3 -> errors

        # Any SAA bin is flagged as bad (1)
        # Bins beside SAA shoule be flagged as dubious (2) - come back to later
        quality = np.zeros(background['all'].shape[0])
        quality[zeromask] = 1
        for i in range(1, quality.size -1):
                if quality[i] == 1:
                    if quality[i-1] != 1:
                        quality[i-10:i] = 1

        self.quality = quality
        self.background = background


        # The exposure is stored separately for each background region. We also want to calculate the total average,
        # and the average for the pre/pos regions
        bkgExp = np.zeros(data["src"][2].size)
        bkgExpPre = np.zeros(data["src"][2].size)
        bkgExpPos = np.zeros(data["src"][2].size)
        nPre, nPos, n = 0, 0, 0
        for i in list(data.keys()):
            if i    == "src":
                continue
            if "pre" in i:
                bkgExpPre += data[i][2]
                nPre +=1
            elif "pos" in i:
                bkgExpPos += data[i][2]
                nPos +=1
            bkgExp += data[i][2]
            n +=1

        bkgExp = bkgExp / n
        bkgExpPre = bkgExpPre / nPre
        bkgExpPos = bkgExpPos / nPos
        self.bkgExp = {"all":bkgExp, "pre": bkgExpPre, "pos": bkgExpPos}

        self.data = data
        
    def getNearestBinEdges(self, vals, dataType = False, offset = 0):
        '''
        Take in a list of data values and a type (either lc or spec)
        and return a list of nearest bin edges.
        Offset is optional - if there is a difference between the
        vals and the data (say a trigger time - then pass an offset 
            equal to this value.)
        '''
        if not dataType:
            return False
        if dataType == 'lc':
            t = self.data['src'][0] - offset 
            lEdges = t[:,0]
            rEdges = t[:,1]
        elif dataType == 'spec':
            lEdges =  self.eEdgeMin
            rEdges = self.eEdgeMax
        else:
            return False
        edges = []
        # Loop over the vals - we loop over two at a time
        for i in range(0, len(vals) ,2):
            # x will store our value & y will store the nearest edges
            x = vals[i:i+2]
            y = []
            # if necessary - reverse sub list x
            if x[0] > x[1]:
                x = x[::-1]
            # print x
            # print lEdges
            # print rEdges
            # print util.find_nearest(lEdges, x[0]), util.find_nearest(lEdges, x[1])
            y.append(util.find_nearest(lEdges, x[0]))
            y.append(util.find_nearest(rEdges, x[1]))
            # print ('%.5f-%.5f, %.5f-%.5f')%(x[0], y[0], x[1], y[1])
            edges.extend(y)
        # for i,j in zip(vals, edges):
        #     print i,j 
        # print '\n'
        return edges
    def write_phaii(self, opts, data_class = 'TOTAL', new_file = [], data = [], dir = './', gti = [], names = [],):
        '''
        Write a set of PHAII files.
        '''

        # Primary
        ra = opts.coords[0]
        dec = opts.coords[1]
        radErr = 0.
        tzero = opts.tzero
        fileStem = "glg_osv_%s_%s.XX" %(opts.name, self.detector)
        # Spectrum
        t = self.data['src'][0]
        ti = t[:,0] 
        tj = t[:,1]
        t = (ti,tj)
        
        src = self.data['src'][1]
        srcErr = self.data['src'][3]
        
        srcExp = self.data['src'][2]
        qual = self.quality        
        
        bkg = self.background['all']
        bkgErr = self.background['allerr']

        bkgExp = self.bkgExp['all']

        # Edges
        edges = (self.eEdgeMin, self.eEdgeMax)
        # GTI
        gti = ()
        if not len(names):
            names.append(fileStem.replace('.XX', '.PHA'))
            names.append(fileStem.replace('.XX', '.BAK'))
        fitsUtil.createPHAII(t, srcExp, src, self.detector, tzero, names[0], 
                            edges = edges, ra = ra, dec = dec, errRad = radErr, qual = qual, bkg = False)
        fitsUtil.createPHAII(t, bkgExp, bkg, self.detector, tzero, names[1], 
                            edges = edges, ra = ra, dec = dec, errRad = radErr, qual = qual,
                            statErr = bkgErr, bkg = True)
    def write_pha(self, opts, data_class = 'TOTAL', new_file = [], data = [], dir = './', gti = [], names = [],
                    lcMask = np.empty((0)), specMask = np.empty((0))):
        '''
        Write a set of PHA files.
        '''
        
        # Primary
        ra = opts.coords[0]
        dec = opts.coords[1]
        radErr = 0.
        tzero = opts.tzero
        fileStem = "glg_osv_%s_%s.XX" %(opts.name, self.detector)
        # Spectrum
        t = self.data['src'][0]
        ti = t[:,0] 
        tj = t[:,1]
        t = (ti,tj)
        src = self.data['src'][1]
        srcErr = self.data['src'][3]    
        
        bkg = self.background['all']
        bkgErr = self.background['allerr']

        exp = self.data['src'][2]
        qual = self.quality

        if not lcMask.size:
            lcMask = ti != -99999999
        if not specMask.size:
            specMask = self.eEdgeMin != -99999999

        # Edges
        edges = (self.eEdgeMin[specMask], self.eEdgeMax[specMask])
        # GTI
        gti = ()

        if not len(names):
            names.append(fileStem.replace('.XX', '.PHA1'))
            names.append(fileStem.replace('.XX', '.BAK1'))

        # Apply both masks seperately to avoid ValueError exception
        src = src[:,specMask]
        src = src[lcMask,:]
        srcErr = srcErr[:,specMask]
        srcErr = srcErr[lcMask,:]
        
        bkg = bkg[:,specMask]
        bkg = bkg[lcMask,:]
        bkgErr = bkgErr[:,specMask]
        bkgErr = bkgErr[lcMask,:]        

        srcExp = exp[lcMask]
        bkgExp = self.bkgExp['all'][lcMask]
        t = (ti[lcMask], tj[lcMask])

        fitsUtil.createPHA(t, srcExp, src, self.detector, tzero, names[0], 
                            edges = edges, ra = ra, dec = dec, errRad = radErr, qual = qual,
                            err = srcErr, bkg = False)
        fitsUtil.createPHA(t, bkgExp, bkg, self.detector, tzero, names[1], 
                            edges = edges, ra = ra, dec = dec, errRad = radErr, qual = qual,
                            err = bkgErr, statErr = True, bkg = True)
    def write_ascii(self, opts, data_class = 'TOTAL', new_file = [], data = [], dir = './', gti = [], names = [],
                    lcMask = np.empty((0)), specMask = np.empty((0))):
        '''
        Write a set of PHA files.
        '''
        if data == []:        
            if data_class == 'TOTAL':
                data = self.data['src'][1]
                err = self.data['src'][3]
            elif data_class == 'NET':
                data = self.data['src'][1] - self.background['all']
                # The following error is not correct, this should be ok as I
                # am not creating the NET PHA files now (Dec 11)
                err = self.data['src'][3]
            elif data_class == 'BKG':
                data = self.background['all']
                err = self.background['allerr']
        
        # Primary
        ra = opts.coords[0]
        dec = opts.coords[1]
        radErr = 0.
        tzero = opts.tzero
        fileStem = "glg_osv_%s_%s.XX" %(opts.name, self.detector)
        # Spectrum
        t = self.data['src'][0]
        ti = t[:,0] 
        tj = t[:,1]
        t = (ti,tj)
        src = self.data['src'][1]
        bkg = self.background['all']
        srcExp = self.data['src'][2]
        bkgExp = self.bkgExp['all']
        qual = self.quality        

        if not lcMask.size:
            lcMask = ti != -99999999
        if not specMask.size:
            specMask = self.eEdgeMin != -99999999

        # Edges
        edges = (self.eEdgeMin[specMask], self.eEdgeMax[specMask])
        # GTI
        gti = ()
        # fitsUtil.createPHA(t, exp, src, self.detector, tzero, fileStem.replace('.XX', '.PHA1'), 
        #                     edges = edges, ra = ra, dec = dec, errRad = radErr, qual = qual)
        # fitsUtil.createPHA(t, exp, bkg, self.detector, tzero, fileStem.replace('.XX', '.BAK1'), 
        #                     edges = edges, ra = ra, dec = dec, errRad = radErr, qual = qual)
        if not len(names):
            names.append(fileStem.replace('.XX', '.PHA1'))
            names.append(fileStem.replace('.XX', '.BAK1'))

        # Apply both masks separately to avoid ValueError exception
        src = src[:,specMask]
        src = src[lcMask,:]
        bkg = bkg[:,specMask]
        bkg = bkg[lcMask,:]
        srcExp = srcExp[lcMask]
        bkgExp = bkgExp[lcMask]
        t = (ti[lcMask], tj[lcMask])
        fitsUtil.createASCII(t, srcExp, src, self.detector, tzero, names[0], )
        fitsUtil.createASCII(t, bkgExp, bkg, self.detector, tzero, names[1], )