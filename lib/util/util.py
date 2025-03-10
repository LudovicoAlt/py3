
import math
import os
import datetime

import numpy as np
import astropy.io.fits as pf

def calc_occ_steps(src_ra, src_dec, time, pos):
    '''    
    Calculate occulation step times for a input source location. This function 
    was converted to python from the IDL function calc_step_times2_glc, which
    is distributed with occ_fit. 
    
    Inputs are: 
        src_ra, src_dec: the source coordinates
        time: Time array from the relevant poshist file
        pos: n x 3 array containing the x, y, z, spacecraft coordinates from the
            relevant poshist file
    
    Outputs are:
        rise_times: Times corresponding to the source rising from occultation
        set_times: Times corresponding to the source setting into occultation
    
    Added: 06.12.11
    
    '''
    r_earth = 6378.136*1000     #radius of earth in m
    f = 1/298.257               #oblateness factor
    dtorad = 180./np.arccos(-1.)
    
    #Source position
    fra=src_ra/dtorad
    fdec=src_dec/dtorad
    src_pos=np.zeros((3),float)
    src_pos[0] = np.cos(fdec) * np.cos(fra)
    src_pos[1] = np.cos(fdec) * np.sin(fra)
    src_pos[2] = np.sin(fdec)
    
    nt=np.size(time)
    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]  

    hmin= (np.sqrt(x**2 + y**2 + z**2/ (1-f)**2 - 
                  (x*src_pos[0] + y*src_pos[1] + z*src_pos[2] / (1-f))**2 
                  /(src_pos[0]**2 + src_pos[1]**2 + src_pos[2]**2 / (1-f)**2)) 
                  - r_earth )
    smin = (-1.*(x*src_pos[0] + y*src_pos[1] + z*src_pos[2]/(1-f)**2)/
        (src_pos[0]**2 + src_pos[1]**2 + src_pos[2]**2/(1-f)**2) )

    wrises = np.where(((hmin[:-1] <= 70000.) & (smin[:-1] >= 0)) & 
                      ((hmin[1:] > 70000.) & (smin[1:] >= 0)))
    wsets = np.where(((hmin[1:] <= 70000.) & (smin[1:] >= 0)) &
                      ((hmin[:-1] > 70000.) & (smin[:-1] >= 0)))

    
    if wrises[0].size > 0:
         rise_times = ((70000. - hmin[wrises])/(hmin[wrises[0] + 1] 
                        - hmin[wrises]) * (time[wrises[0] + 1]-time[wrises])
                        +time[wrises])
    if wsets[0].size > 0:
        set_times=((70000. - hmin[wsets])/(hmin[wsets[0] + 1] - hmin[wsets])*
                        (time[wsets[0] + 1] - time[wsets]) + time[wsets])
    return rise_times, set_times

def make_gti(data, bool_list):
    '''
    Read in an array of data, and a boolean array where the True values 
    correspond to good data points, and generate good time interval arrays.
    
    Added: 11.11 
    '''
    record_data = False
    gti_i, gti_j = [], []
    for var, indexes in zip(data, bool_list):
        if (indexes == False) & (record_data == True):
                gti_j.extend([data[np.where(data == var)[0]][0] ])
                record_data = False
        elif (indexes == False) & (record_data == True) & (var == data[-1]):
            gti_j.extend([var])
        elif (indexes == True) & (record_data == True):
            continue
        elif (indexes == True) & (record_data == False):
            record_data = True
            gti_i.extend([var])
    if len(gti_i) > len(gti_j):
        gti_j.extend([data[np.where(data == var)[0]][0] + 1 ])
    gti = np.column_stack((np.asarray(gti_i), np.asarray(gti_j)))
    return gti_i, gti_j

def steppify(x, y, width):
    '''
    Take in an array x,y and return modified x1, y1 which can be used with
    fill between.
    
    Added: 25.11.11
    '''
    if np.size(width) == 1: width = width * np.ones(x.size)
    width = width / 2.
    x1=[]
    y1=[]
    for i, j, exp in zip(x, y, width):
        x1.extend([ i -exp, i + exp])
        y1.extend([j ,j])
    x1 = np.asarray(x1)
    y1 = np.asarray(y1)
    return x1, y1

def rebin_gen(x, y, exp, err = [], resolution = [], trange = []):
    '''
    Rebin general data. differs from rebin_gbm in that it can handle single 
    channel data.  Takes in x,y,exp, where x is the bin
    centre or bin edges, y is the counts array (bins), err is an array
    of errors (same shape as counts array) and exp is the exposure per bin.
    
    Returns x1, y1, exp1, err, the rebinned data. 
    
    If resolution is not passed then the coarsest resolution from the data is 
    selected. If x1 is a 2xnbins array (i.e. the bin edges) then the same shape 
    array will be returned. An optional parameter trange can also be passed - 
    this is a 2x1 list which contains the edges of the data to be binned.
    
    Errors: If no error is passed then the statistical error is assumed to arise
    from counting error and is given by N^1/2 where N is the number of counts in 
    a bin. If an array of errors is passed then the error on a bin is found by
    summing in quadrature the errors of each bin contributing to it. This will
    fail if the desired resolution is lower than the native resolution of the 
    input data -> but you probably shouldn't be trying to resample the data in
    this case anyway.
    
    '''
    if resolution == []:
        resolution = exp.max().round(3)
    
    #Is x the bin centres or bin edges?
    #Irregardless we need to have edges for error calculation 
    #if user passed an err array
    if len(x.shape)!=1:
        #we have bin edges - get bin centres
        x_edges = x
        bin_edge = True
        x=(x[:,1]-x[:,0])/2 +x[:,0]
    else:
        x_edges=np.column_stack((x-exp/2 ,x+exp/2 ))
        bin_edge = False
    if trange == []:
        x1=np.arange(x[0],x[-1],resolution)
        #x1=np.arange(x[0,0],x[-1,1],resolution)
    else:
        x1=np.arange(trange[0],trange[1],resolution)
    #Define new arrays to house rebinned data
    #    x1=np.arange(x[0],x[-1],resolution)
    nchan=1
    nbin=x1.size
    exp1=np.ones(nbin)*resolution
    y1=np.zeros(nbin)
    
    #interpolate y
    y1=np.interp(x1, x, y /exp)*exp1
    if err==[]:
        #Statistical error
        err1=np.sqrt(y1)
    else:
        err1=np.zeros((nbin,nchan))
        for i in range(0,nchan):
            err1[:,i]=np.interp(x1,x,err[:,i]/exp)*exp1
        
    if bin_edge:
        #If user passed bin edges return bin edges, otherwise return bin centres
        xi=x1 -(exp1/2)
        xj=x1 +(exp1/2)
        x1=np.column_stack((xi,xj))

    return x1,y1,exp1,err1

def rebin_gbm(x, y, exp, err = [], resolution = [], trange = []):
    '''
    Rebin GBM CSPEC or CTIME data. Takes in x,y,exp, where x is the bin
    centre or bin edges, y is the counts array (bins*chan), err is an array
    of errors (same shape as counts array) and exp is the exposure per bin.
    
    Returns x1, y1, exp1, err, the rebinned data. 
    
    If resolution is not passed then the coarsest resolution from the data is 
    selected. If x1 is a 2xnbins array (i.e. the bin edges) then the same shape 
    array will be returned. An optional parameter trange can also be passed - 
    this is a 2x1 list which contains the edges of the data to be binned.
    
    Errors: If no error is passed then the statistical error is assumed to arise
    from counting error and is given by N^1/2 where N is the number of counts in 
    a bin. If an array of errors is passed then the error on a bin is found by
    summing in quadrature the errors of each bin contributing to it. This will
    fail if the desired resolution is lower than the native resolution of the 
    input data -> but you probably shouldn't be trying to resample the data in
    this case anyway.
    
    '''
    if resolution == []:
        resolution = exp.max().round(3)
    
    #Is x the bin centres or bin edges?
    #Irregardless we need to have edges for error calculation 
    #if user passed an err array
    if len(x.shape)!=1:
        #we have bin edges - get bin centres
        x_edges = x
        bin_edge = True
        x=(x[:,1]-x[:,0])/2 +x[:,0]
    else:
        x_edges=np.column_stack((x-exp/2 ,x+exp/2 ))
        bin_edge = False
    
    if len(trange) == 0: #instead of checking [] check if empty
        x1=np.arange(x[0],x[-1],resolution)
        #x1=np.arange(x[0,0],x[-1,1],resolution)
    else:
        x1=np.arange(trange[0],trange[1],resolution)
    
    #Define new arrays to house rebinned data
    nchan=y[0,:].size
    nbin=x1.size
    y1=np.zeros((nbin,nchan))
    
    # first interpolate exposure
    if bin_edge:
        binWidth = x_edges[:,1] - x_edges[:,0]        
        binWidth1 = np.ones(nbin)*resolution
        exp1 = np.interp(x1,x,exp/binWidth)*binWidth1
    else:
        # no quite correct if there is deadtime, but the 
        # best that can be done without bin edges
        exp1 = np.ones(nbin)*resolution
    
    # import matplotlib.pyplot as plt
    # plt.cla() 
    # plt.plot(x,exp, marker = 's', ls = '-', color = 'g', label = 'native')
    # plt.plot(x1, binWidth1, marker = 'o', ls = '--', color = 'b', label = 'wrong')
    # plt.plot(x1, exp1, marker = 'x', ls = '-.', color = 'r', label = 'interp')
    # plt.legend()
    # plt.show()


    for i in range(0,nchan):
        y1[:,i]=np.interp(x1,x,y[:,i]/exp)*exp1
    if len(err)==0: #instead of checking [] check if empty
        #Statistical error
        err1=np.sqrt(y1)
    else:
        err1=np.zeros((nbin,nchan))
        for i in range(0,nchan):
            err1[:,i]=np.interp(x1,x,err[:,i]/exp)*exp1
        
    if bin_edge:
        #If user passed bin edges return bin edges, otherwise return bin centres
        xi=x1 - resolution/2. #(exp1/2)
        xj=x1 + resolution/2. # (exp1/2)
        x1=np.column_stack((xi,xj))

    return x1,y1,exp1,err1

def calcLogBins(minBin, maxBin, nBin):
    '''
    09.01.12
    Take in bin edges, number of bins and then calculate
    log bin edges
    '''
    inc = (np.log10(maxBin) - np.log10(minBin) )/nBin
    binEdges = 10** (np.log10(minBin) + np.arange(nBin + 1)*inc)
    binCentres = np.zeros(nBin)
    binLeftEdges = np.zeros(nBin)
    binRightEdges = np.zeros(nBin)
    for i in range(0, nBin): 
        binCentres[i] =  10**(np.log10(binEdges[i]) + (np.log10(binEdges[i+1]) - np.log10(binEdges[i]))/2)    
    for i in range(0, nBin):
        binLeftEdges[i] = binCentres[i] - binEdges[i]
        binRightEdges[i] = binEdges[i + 1] - binCentres[i]
    return binCentres, binLeftEdges, binRightEdges
                      
def counts_spec(counts,e_min,e_max,chan_range=[0,8]):
    '''
    Take in counts, channel edges, and return e_centres & spec data.
    The matplotlib step function does not plot the full extent of the first or
    last bin. This bit of code appends an extra value onto the start and end of
    the spec values and bin centeres to account for this. So an input counts
    array of 128xnbins will yield an output of 130.
    '''
    spec = np.sum(counts,0)
    e_centres = 10**(np.log10(e_min) + (np.log10(e_max) - np.log10(e_min))/2.) 
    # e_centres = np.concatenate((np.array(e_min[:1]),e_centres))
    # e_centres = np.concatenate((e_centres,np.array(e_max[-1:])))
    # spec = np.concatenate((np.array(spec[:1]),spec))
    # spec = np.concatenate((spec,np.array(spec[-1:]) ))
    spec_exp = e_max - e_min
    # spec_exp = np.concatenate((np.array(spec_exp[:1]),spec_exp))
    # spec_exp = np.concatenate((spec_exp,np.array(spec_exp[-1:])))
    #    print spec_exp
    return e_centres,spec,spec_exp

def mjd_met(t):
    ''' Convert from MJD to Fermi MET '''
    return (t - (51910+0.00074287037037)) * 86400.0

def met_mjd(t):
    """Converts from Fermi MET to MJD """
    return (t /86400.0)+51910+0.00074287037037

def find_nearest(array,value):
    idx=(np.abs(array-value)).argmin()
    return array[idx]

def good_gbm_met(met):
    '''Ensure that a GBM MET does not extend pre launch or to the Future'''
    good_time = True
    #Triggering enable 14 June 08, put min date at this plus 2 days for offset
    then = datetime.datetime(2008, 6, 16)
    now = datetime.datetime.now()
    dif = now - then
    min_met = 235300000 #2008, 6, 16th, 09:07:44
    max_met = min_met + dif.total_seconds()
    if min_met > met or met > max_met:
        good_time = False
    return good_time

def mjd_greg(mjd):
    """Converts an input date from MJD to Gregorian"""
    jd=mjd+2400000.5+.5
    Z=int(jd)
    F=jd-Z
    if Z < 2299161:
            A=Z
    elif Z >= 2299161:
            alpha = int((Z-1867216.25)/36524.25)
            A = Z + 1 + alpha - int(alpha/4)
    B = A + 1524
    C = int( (B-122.1)/365.25)
    D = int( 365.25*C )
    E = int( (B-D)/30.6001 )

    dd = B - D - int(30.6001*E) + F 
    
    if E < 13.5:
            mm = E - 1
    elif E > 13.5:
            mm = E - 13

    if mm>2.5:
            yyyy = C - 4716
    elif mm<2.5:
            yyyy = C - 4715

    months=["January", "February", "March", "April", "May", "June", "July", "August", 
            "September", "October", "November", "December"]
    daylist=[31,28,31,30,31,30,31,31,30,31,30,31]
    daylist2=[31,29,31,30,31,30,31,31,30,31,30,31]

    h=int((dd-int(dd))*24)
    min=int((((dd-int(dd))*24)-h)*60)
    sec=86400*(dd-int(dd))-h*3600-min*60

    # Now calculate the fractional year. Do we have a leap year?
    if (yyyy%4 != 0):
            days=daylist2
    elif (yyyy%400 == 0):
            days=daylist2
    elif (yyyy%100 == 0):
            days=daylist
    else:
            days=daylist2              
    greg=[yyyy,mm,int(math.floor(dd)),h,min,sec]   
    return greg

def date_interpolate(start,end):
    """Interpolate between two input dates 

    Input Values are in list format as follows: [yyyy, mm, dd]
    Return values are in GRB date format (YYDDMM).
    
    Note: 06.12.11 This could be implemented using datetime module. Would have
    saved me some work and would probably be better. This code does not handle
    leap years at all, this will be an issue in the future.
    """
    days=np.array([31,28,31,30,31,30,31,31,30,31,30,31])
    months=np.arange(1,13)
    years=np.arange(8,12)

    over='no'
    dd=start[2]
    mm=start[1]
    yy=start[0]

    if len(str(int(dd))) ==1:
            day='0'+str(int(dd))
    else:
            day=str(int(dd))
    if len(str(int(mm))) ==1:
            month='0'+str(int(mm))
    else:
            month=str(int(mm))
    year=str(yy)[2:4]
    date=year+month+day

    #Check that days are not the same:
    if end[0:3] == start[0:3]:
        return [date]

    day_count=0
    day_range=[date]
    while over == 'no':
            if (dd < days[mm-1]):
                    dd_1=dd+1
                    mm_1=mm
                    yy_1=yy
            else:
                    dd_1=1
                    if mm ==12:
                            mm_1=1
                            yy_1=int(yy+1)
                    else:
                            mm_1=mm+1
                            yy_1=yy
            dd=dd_1
            mm=mm_1
            yy=yy_1

            if (yy==end[0] and mm==end[1] and dd==end[2]):
                    over='yes'
                    
            if len(str(int(dd))) ==1:
                    day='0'+str(int(dd))
            else:
                    day=str(int(dd))
            if len(str(int(mm))) ==1:
                    month='0'+str(int(mm))
            else:
                    month=str(int(mm))
            year=str(yy)[2:4]

            date=year+month+day
            day_range[len(day_range):] = [date]

    return day_range

def read_poshist(pos_file, verbose = True):
    '''
    Extract Quaternions, Position, Time & Geo Coordinates from file.
    Poshist files for days prior to March 2009 either have the spacecraft lat &
    lon set to zero or the fields are missing altogheter. This should be caught
    by the try except block in place.
    '''
    dtorad=180./math.acos(-1.)
    data=pf.getdata(pos_file,ext=1)
    nt=np.size(data)
    sc_time=data.SCLK_UTC
    sc_quat=np.zeros((nt,4),float)
    sc_pos=np.zeros((nt,3),float) # Fermi GBM tools makes this redundant but manually is always fine
    sc_coords=np.zeros((nt,2),float)
    try:
        sc_coords[:,0]=data.SC_LON
        sc_coords[:,1]=data.SC_LAT
    except:
        if verbose:
            mes = ''
            mes += '*** No geographical coordinates available '
            mes += 'for this file: %s' %pos_file
            print(mes)
            
    sc_quat[:,0]=data.QSJ_1
    sc_quat[:,1]=data.QSJ_2
    sc_quat[:,2]=data.QSJ_3
    sc_quat[:,3]=data.QSJ_4
    sc_pos[:,0]=data.POS_X
    sc_pos[:,1]=data.POS_Y
    sc_pos[:,2]=data.POS_Z
    return sc_time,sc_pos,sc_quat,sc_coords

def pha_rebin(bin_range, t_start, t_end, data, new_binsize = 10): 
    '''
    Rebin a pha object to a certain resolution 
    
    Note: 06.12.11 This method is not longer used, the gbm_rebin should be used
    instead.
    '''
    bin_start=math.ceil(bin_range[0])
    bin_end=math.ceil(bin_range[1])
    bins=np.arange(bin_start,bin_end,new_binsize)
    N=np.size(bins)-1
    #    print "Number of bins: ", N
    binned_r=np.zeros(N)
    bin_centres=np.zeros(N) 
    binned_counts=np.zeros((N,data.shape[1]))
    for i in range(0,N):
        ind=np.where((t_start > bins[i]) & (t_end<bins[i]+new_binsize))
        #temp_data=data[np.where(
        temp_counts=np.sum(data[ind[0],:],0)
        binned_counts[i,:]=temp_counts
    time=bins[0:N]
    endtime=bins[1:N+1]
    exposure=np.ones((N))*new_binsize
    stat_err=np.sqrt(binned_counts)
    return binned_counts, exposure, time, endtime, stat_err

def read_pha(pha_file, gti = False, qualMask = True, tOffset = True,):
    """
    Extract Counts & Time From a GBM Pha File
    If gti is true then only data corresponding to gti is returned
    if qualMask is true then apply quality mask
    if tOffset is true then add tzero to time arrays
    
    13.01.10: Fixed a bug where gtis where calculated between time rather
    than time & endtime.
    """
    data = pf.open(pha_file)
    gtis = np.array((data[3].data.START,data[3].data.STOP)) 
    qual = data[2].data['QUALITY']
    if qualMask:
        qual = (qual == 0)
    else:
        qual = (qual != 99)
    time = data[2].data.TIME [qual]
    endtime = data[2].data.ENDTIME [qual]
    if gti:
        #User wants gtis
        if gtis.size:
            #gtis are valid
            for i in range(0,len(gtis[0])):
                temp_index=np.where((time >= gtis[0,i]) &(endtime <= gtis[1,i]))
                if i == 0: 
                    gti_index = temp_index[0]
                else: 
                    gti_index = np.concatenate((gti_index,temp_index[0]))
            gti_index = (gti_index,)
        else:       
            #gtis are not valid
            gti_index = (np.empty(0),)#np.where(time == -1)
    else:       
        #user does not want gtis, return all data
        gti_index = np.where(time != -1)
    #Temporal offset (Tzero4) may not exist - check
    tzero = 0
    if tOffset:
        if data[2].header.__contains__('TZERO4'):
            tzero = data[2].header['TZERO4']
    
    # print("Here is tzero4: ", tzero)
    # print("Here is tstart without this tzero factor :", data[2].data.TIME[qual])
    # TODO write tests to double check this util functions
    # TODO double check what this TZERO4 stands for, it offsets way too much
    tzero = 0
    #print(tzero)
    pha_counts = data[2].data['COUNTS'][qual]
    t_start    = data[2].data.TIME[qual]  + tzero
    t_end      = data[2].data.ENDTIME[qual] + tzero
    t_exposure = data[2].data.EXPOSURE[qual]
    eMin = data[1].data.E_MIN
    eMax = data[1].data.E_MAX
    data.close()
    if gti:
        return t_start, t_end, t_exposure, pha_counts, gti_index, eMin, eMax
    else:
        return  t_start, t_end, t_exposure, pha_counts,  eMin, eMax

def get_pha_rate(t, counts, exposure, data_type = 'ctime', channel_range = [], binsize = 10):
    '''Read in t,counts,exposure and return binned up rate in a channel range'''
    if channel_range == []:
        if data_type == 'ctime':
            channel_range = [1,7]
        else:
            channel_range = [10,120]
    t_centre = t+exposure/2
    rate = np.sum(counts[:,channel_range[0]:channel_range[1]],1)/exposure
    return t,rate,exposure
    
def get_binned_rate(t,rate,exposure,new_binsize=10):
    '''Read in t, rate, old binsize: then Bin up to new bin size'''
    #    bin_res=0.256
    #    binsize=int(new_binsize/bin_res)*bin_res
    bins=np.arange(min(t),max(t)+new_binsize,new_binsize)
    N=np.size(bins)-1
    binned_r=np.zeros(N)
    bin_centres=np.zeros(N) 
    for i in range(0,N):
        ind=np.where((t>bins[i])& (t<bins[i+1]))
        r_temp=np.average(rate[ind])
        binned_r[i]=r_temp
        bin_centres[i]=(bins[i+1]-bins[i])/2. + bins[i]
    return bin_centres,binned_r

def calc_angles(sc_time,sc_pos,sc_quat,src_ra,src_dec):
    """
    Calculate GBM source angles & pointing
    
    Modified 28.11.11 to also calculate the angles for BGO
    
    Note: 06.12.11 I think the loop where the angles are calculated may be 
    superfluous. It this is the case, then getting rid of this loop should
    speed up this function significantly.
    """
    dtorad=180./math.acos(-1.)
    nt=np.size(sc_time)
    #Calculate Direction Cosines
    scx=np.zeros((nt,3),float)
    scx[:,0]=(sc_quat[:,0]**2-sc_quat[:,1]**2-sc_quat[:,2]**2+sc_quat[:,3]**2)
    scx[:,1]=2.*(sc_quat[:,0]*sc_quat[:,1] + sc_quat[:,3]*sc_quat[:,2])
    scx[:,2]=2.*(sc_quat[:,0]*sc_quat[:,2] - sc_quat[:,3]*sc_quat[:,1])
    scy=np.zeros((nt,3),float)
    scy[:,0]=2.*(sc_quat[:,0]*sc_quat[:,1] - sc_quat[:,3]*sc_quat[:,2])
    scy[:,1]=(-sc_quat[:,0]**2+sc_quat[:,1]**2-sc_quat[:,2]**2+sc_quat[:,3]**2)
    scy[:,2]=2.*(sc_quat[:,1]*sc_quat[:,2] + sc_quat[:,3]*sc_quat[:,0])
    scz=np.zeros((nt,3),float)
    scz[:,0]=2.*(sc_quat[:,0]*sc_quat[:,2] + sc_quat[:,3]*sc_quat[:,1])
    scz[:,1]=2.*(sc_quat[:,1]*sc_quat[:,2] - sc_quat[:,3]*sc_quat[:,0])
    scz[:,2]=(-sc_quat[:,0]**2-sc_quat[:,1]**2+sc_quat[:,2]**2+sc_quat[:,3]**2)

    #Calculate Source coordinates
    source_pos=np.zeros((3),float)

    fra=src_ra/dtorad
    fdec=src_dec/dtorad
    source_pos[0]=math.cos(fdec)*math.cos(fra)
    source_pos[1]=math.cos(fdec)*math.sin(fra)
    source_pos[2]=math.sin(fdec)
    sdotprod=source_pos / math.sqrt(source_pos[0]*source_pos[0]+source_pos[1]*source_pos[1]+source_pos[2]*source_pos[2])
    sc_source_pos=np.zeros((nt,3),float)
    sc_source_pos[:,0]=scx[:,0]*source_pos[0]+scx[:,1]*source_pos[1]+scx[:,2]*source_pos[2]
    sc_source_pos[:,1]=scy[:,0]*source_pos[0]+scy[:,1]*source_pos[1]+scy[:,2]*source_pos[2]
    sc_source_pos[:,2]=scz[:,0]*source_pos[0]+scz[:,1]*source_pos[1]+scz[:,2]*source_pos[2]

    #Define Fermi/GBM detector Geometries
    #The following coordinates are taken from Meegan et al., 2009
    det_zen=[20.58, 45.31, 90.21, 45.24, 90.27, 89.79, 20.43, 
             46.18, 89.97, 45.55, 90.42, 90.32, 90, 90]
    det_az=[45.89, 45.11, 58.44, 314.87, 303.15,  3.35, 224.93,
             224.62, 236.61, 135.19, 123.73, 183.74, 0, 180]
    dets=np.array(['n0','n1','n2','n3','n4','n5','n6','n7','n8','n9','na','nb','b0','b1'])
    ndet = 14 #take the length of the array if anything
    det_index = np.arange(0,ndet)
    dtorad_arr = np.ones((ndet))*dtorad
    det_zen = det_zen / dtorad_arr
    det_az = det_az / dtorad_arr
    
    #Calculate Detector unit vectors
    det_unit = np.zeros((ndet,3),float)
    det_unit[:,0] = np.sin(det_zen[:])*np.cos(det_az[:])
    det_unit[:,1] = np.sin(det_zen[:])*np.sin(det_az[:])
    det_unit[:,2] = np.cos(det_zen[:])
    
    distfromz = np.zeros((nt),float)
    distfromgeo = np.zeros((nt),float) #! you can set this to ones and then multiply by the singular values
    distfromdet = np.zeros((nt,ndet),float)

    #! numpy can handle this without for loop
    for i in range(0, nt):
        dotprod = np.zeros((3),float)
        dotprod[0] = -sc_pos[i,0]/ math.sqrt(sc_pos[i,0]*sc_pos[i,0]+sc_pos[i,1]*sc_pos[i,1]+sc_pos[i,2]*sc_pos[i,2])
        dotprod[1] = -sc_pos[i,1]/ math.sqrt(sc_pos[i,0]*sc_pos[i,0]+sc_pos[i,1]*sc_pos[i,1]+sc_pos[i,2]*sc_pos[i,2])   
        dotprod[2] = -sc_pos[i,2]/ math.sqrt(sc_pos[i,0]*sc_pos[i,0]+sc_pos[i,1]*sc_pos[i,1]+sc_pos[i,2]*sc_pos[i,2])

        zdotprod = np.zeros((3),float)
        zdotprod[0] = scz[i,0]/ math.sqrt(scz[i,0]*scz[i,0]+scz[i,1]*scz[i,1]+scz[i,2]*scz[i,2])
        zdotprod[1] = scz[i,1]/ math.sqrt(scz[i,0]*scz[i,0]+scz[i,1]*scz[i,1]+scz[i,2]*scz[i,2])
        zdotprod[2] = scz[i,2]/ math.sqrt(scz[i,0]*scz[i,0]+scz[i,1]*scz[i,1]+scz[i,2]*scz[i,2])
        # you can multiply dtorad at the end, maybe saves time
        distfromgeo[i]= dtorad* math.acos(dotprod[0]*sdotprod[0]+dotprod[1]*sdotprod[1]+dotprod[2]*sdotprod[2]) #could use sum of prod for starters
        distfromz[i] =  dtorad* math.acos(sdotprod[0]*zdotprod[0]+sdotprod[1]*zdotprod[1]+sdotprod[2]*zdotprod[2])      
        distfromdet[i,:] = dtorad*np.arccos(det_unit[:,0]*sc_source_pos[i,0]+det_unit[:,1]*sc_source_pos[i,1]+det_unit[:,2]*sc_source_pos[i,2])        

    return distfromz, distfromgeo, distfromdet

def calc_period(sc_pos):
    '''
    Calculate orbital period of Fermi using the position of the spacecraft and
    assuming circular motion.   
    '''
    G = 6.67428e-11    # m^3 kg^-1 s^-2
    M = 5.9722e24      # kg Mass Earth  
    r = (np.sum(sc_pos**2.,1))**(1/2.)
    r_avg = np.average(r)
    r_cubed = (r_avg)**3.
    factor = r_cubed/(G*M)
    period = 2. * np.pi * np.sqrt(factor)
    return period

def write_aux(test,pointing,filename="aux_file.fits"):
    '''
    Routine to generate fits file containing auxillary data

    Write SC location in geo coords and pointing in 5 regions:
    +-16/14 orbits and region of interest
    
    Needs work: currently doesnt include any useful header information
    '''
    col1=pf.Column(name='Neg_Point',format='1E',array=pointing[0] ,unit='degree' )
    col2=pf.Column(name='Point',format='1E',array=pointing[1] ,unit='degree')
    col3=pf.Column(name='Pos_Point',format='1E',array=pointing[2] ,unit='degree')
    LAT_pre_14=test[0][0][:,0]
    LON_pre_14=test[0][0][:,1]
    LAT=test[0][1][:,0]
    LON=test[0][1][:,1]
    LAT_pos_14=test[0][2][:,0]
    LON_pos_14=test[0][2][:,1]
    col4=pf.Column(name='LAT_pre_14',format='1E',array=LAT_pre_14 ,unit='degree')
    col5=pf.Column(name='LON_pre_14',format='1E',array=LON_pre_14 ,unit='degree')
    col6=pf.Column(name='LAT_pos_14',format='1E',array=LAT_pos_14 ,unit='degree')
    col7=pf.Column(name='LON_pos_14',format='1E',array=LON_pos_14 ,unit='degree')
    columns=pf.ColDefs([col1,col2,col3,col4,col5,col6,col7])
    aux=pf.new_table(columns)
    aux.header.update('EXTNAME','Aux')
    aux.writeto(filename,clobber=True)

def get_username():
    '''Return Username'''
    return os.environ.get('USERNAME')
    
def get_plot_limits(x1,y1,x2,y2):
    '''
    Get Ymax, Ymin, Xmax, Xmin for a multiplot
    '''
    ymax=max(y1.max(),y2.max())
    ymax=ymax*0.1 +ymax
    ymin=min(y1[y1!=0].min(),y2[y2!=0].min())
    ymin=ymin - ymin*0.1 
    xmin=min(x1.min(),x2.min())
    xmax=max(x1.max(),x2.max())

    return xmin,xmax,ymin,ymax

def met_grb(tzero, day = False):
    '''
    Take in a time in GBM MET and return name in GRB format
    
    Added 12.12.11 from orsub.py, also added day keyword, this will cause only
    day part of string to be returned.
    '''
    greg = mjd_greg(met_mjd(tzero))
    yr = str(greg[0])[2:]
    if len(str(greg[1])) == 1:
        mt = '0' + str(greg[1])
    else:
        mt = str(greg[1])
    if len(str(greg[2])) == 1:
        dd = '0' + str(greg[2])
    else:
        dd = str(greg[2])
    ttt = str((greg[3]*3600+greg[4]*60+greg[5])/86400)[2:5]
    if day:
        name = yr + mt + dd    
    else:
        name = yr + mt + dd + ttt
    return name

def date_to_met(date):
    '''
    Convert a date to Fermi MET
    
    Accepted formats:
    - YYYY-MM-DD
    - YYYY-MM-DD hh:mm
    - YYYY-MM-DD hh:mm:ss
    - YYYY-MM-DD hh:mm:ss.f
    
    Missing time components default to 0
    '''
    data_start = "2001:01:01 00:00:00"  # start of MET
    data_end = date
    
    date_start = datetime.datetime.strptime(data_start, '%Y:%m:%d %H:%M:%S')
    
    # Try different formats based on the input
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f'
    ]
    
    for fmt in formats:
        try:
            date_end = datetime.datetime.strptime(data_end, fmt)
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"Date '{date}' doesn't match any of the accepted formats: YYYY-MM-DD, YYYY-MM-DD hh:mm, YYYY-MM-DD hh:mm:ss, YYYY-MM-DD hh:mm:ss.f")
    
    # Calculate the difference in seconds
    delta = date_end - date_start
    
    return delta.total_seconds()
