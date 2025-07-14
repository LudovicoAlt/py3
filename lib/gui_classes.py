import os
import sys
import time
import platform
import pickle
from collections import defaultdict
from functools import lru_cache

import wx
from wx.adv import AboutDialogInfo, AboutBox
import matplotlib
#matplotlib.use('WXAgg')
matplotlib.rcParams['backend'] = 'WXAgg' #!from use to manual, safer
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg
import wx.lib.agw.flatmenu as FM
import numpy as np

from . import osv_classes
import lib.util.util as util
from .orbsub import __version__ as orbSubVersion
from lib.config.plotConfig import getPltCfg
from lib.config.lookupConfig import getLUCfg

from . import OrbsubExtras as extras


class Logger:
    '''
    This class acts as a logger of the orbsub code. As the code runs, 
    messages are passed to it by the individual functions. This is all
    done in the background. If there is an issue or if the user wants 
    to view it, it can be displayed in a gui. This gui has the option 
    to save the text to a text file.
    '''
    def __init__(self, progVer = False):
        ''' Set up logging system on first call '''
        self.mes = ''
        self.gui = False
        # Add programme info, time, python info, and platform info
        if not progVer:
            progVer = 'unknown'
        self.mes += 'Programme: %s\n' %progVer
        curTime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        self.mes += 'Log started at: %s\n' %curTime
        platInfo = platform.platform()
        self.mes += 'Platform: %s\n' %platInfo
        pyInfo = sys.version
        self.mes += 'Python: %s\n' %pyInfo
    def update(self, mes):
        ''' append input string to log '''
        self.mes += mes
        if self.gui:
            self.gui.update(logText = mes)
    def show(self, parent):
        '''
        Create GUI instance for viewing of log. We check if the GUI 
        has already been called - don't want to overload the user with
        multiple identical windows. If it does exist, focus attention
        on it.
        '''
        if self.gui:
            # Gui 
            self.gui.Show()
            self.gui.Raise() 
            self.gui.Iconize(False)            
            return
        else:
            self.gui = GUI_txtFrame(parent, title = 'LOG', size = (750, 750))
            self.gui.update(logText = self.mes)
    def save(self, filePath):
        ''' save log to a text file'''
        fop = open(filePath,'w')
        fop.write(self.mes)
        fop.close()
    def __str__(self):
        return self.mes
        
class GUI_txtFrame(wx.Frame):
    '''
    Frame which consits of a text box with option to save contents to file.
    Consits of a single textCtrl object and two buttons.
    Shortcuts are: Ctrl - d: close instance
                   Ctrl - s: save log 
    '''
    def __init__(self, *args, **kwargs):
        super(GUI_txtFrame, self).__init__(*args, **kwargs)
        self.InitUI()
        self.InitBindings()
        self.Centre() 
        self.Show()
    def InitUI(self):
        ''' setup user interface '''
        self.logBox = wx.TextCtrl(self, style = wx.TE_MULTILINE
                              | wx.HSCROLL|wx.TE_READONLY, size = (500,600))
        colour = wx.Colour(222, 222, 222)
        self.logBox.SetBackgroundColour(colour)
        self.lgBtn = wx.Button(self, label = 'Save Log')
        self.dsBtn = wx.Button(self, label = 'Dismiss')
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnBox = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.logBox, 5, wx.ALL| wx.EXPAND, 5)
        btnBox.Add(self.lgBtn, 5, wx.ALL| wx.EXPAND, 5)
        btnBox.Add(self.dsBtn, 5, wx.ALL| wx.EXPAND, 5)
        sizer.Add(btnBox, 0, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(sizer)
        self.SetInitialSize()            
    def InitBindings(self):
        ''' 
        Setup bindings b/w events and methods. Must be called after InitUI()
        '''
        dismissId = wx.NewId()
        saveId = wx.NewId()
        
        self.Bind(wx.EVT_MENU, self.dismiss, id = dismissId)
        self.Bind(wx.EVT_MENU, self.save, id = saveId)
        
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL,  ord('d'), 
                                          dismissId ),
                                         (wx.ACCEL_CTRL,  ord('s'), saveId ), ])
        self.SetAcceleratorTable(accel_tbl)
        self.Bind(wx.EVT_BUTTON, self.save, self.lgBtn)     
        self.Bind(wx.EVT_BUTTON, self.dismiss, self.dsBtn)     
    def save(self, event):
        '''
        Save Log To File. The default name is the current time + _log.txt
        '''
        curTime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        fileName = curTime.replace(' ', '_') + '_log.txt'
        dlg = wx.FileDialog(self, 'Choose a file', os.getcwd(), fileName, 
                            '*.*', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
                fop=open(dlg.GetPath(),'w')
                fop.write(self.logBox.GetValue())
                fop.close()
        dlg.Destroy()
    def update(self, logText = ''):
        ''' Append Text to log '''
        if len(logText) <1:
            return
        else:
            self.logBox.AppendText(logText)
    def dismiss(self, event):
        ''' close instance '''
        self.Close()

class GUI_showConfig(wx.Frame):

    '''
    Frame which display the contents of a wx.cfg file
    Consists of a single textCtrl object and three buttons.
    Shortcuts are: Ctrl - d: close instance
                   Ctrl - s: save config file 
    '''       
    def __init__(self, *args, **kwargs):
        super(GUI_showConfig, self).__init__(*args, **kwargs)
        self.InitVar()
        self.InitUI()
        self.InitBindings()
        self.Centre() 
        self.Show()   
    def InitVar(self):
        self.cfg = wx.Config('myconfig')
        dft_vals = {'warnAll': True}
        for i in dft_vals:
            if self.cfg.Exists(i):
                dft_vals[i] = self.cfg.ReadBool(i)
            else:
                self.cfg.WriteFloat(i, dft_vals[i])

    def InitUI(self):
        ''' setup user interface '''
        self.logBox = wx.TextCtrl(self, style = wx.TE_MULTILINE
                              | wx.HSCROLL|wx.TE_READONLY, size = (500,600))
        colour = wx.Colour(222, 222, 222)
        colour = 'pink'
        self.logBox.SetBackgroundColour(colour)
        self.savBtn = wx.Button(self, label = 'Save Config file')
        self.dmsBtn = wx.Button(self, label = 'Dismiss')
        
        
        btnBox = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.logBox, 5, wx.ALL| wx.EXPAND, 5)
        btnBox.Add(self.savBtn, 5, wx.ALL| wx.EXPAND, 5)
        btnBox.Add(self.dmsBtn, 5, wx.ALL| wx.EXPAND, 5)
        sizer.Add(btnBox, 0, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(sizer)
        self.SetInitialSize()

    def InitBindings(self):
        ''' 
        Setup bindings b/w events and methods. Must be called after InitUI()
        '''
        dismissId = wx.NewId()
        saveId = wx.NewId()
        
        self.Bind(wx.EVT_MENU, self.dismiss, id = dismissId)
        self.Bind(wx.EVT_MENU, self.save, id = saveId)
        
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL,  ord('d'), 
                                          dismissId ),
                                         (wx.ACCEL_CTRL,  ord('s'), saveId ), ])
        self.SetAcceleratorTable(accel_tbl)
        self.Bind(wx.EVT_BUTTON, self.dismiss, self.dmsBtn) 
        self.Bind(wx.EVT_BUTTON, self.save, self.savBtn) 
    def dismiss(self, event):
        ''' close instance '''
        self.Close()    
    def save(self, event):
        ''' save config '''
        print("saving config ")

class OrbsubGUI(wx.Frame):
    '''
    Main frame for an individual osv instance
    '''
    def __init__(self, *args, **kwargs):
        # pop plotDimensions from kwargs if present
        self.plotDimensions = kwargs.pop('plotDimensions', [(1, 1)])
        super(OrbsubGUI, self).__init__(*args, **kwargs)
        self.InitVar()
        self.InitUI()
        self.InitBindings()
        self.Centre() 
        self.Show()
    
    def InitVar(self):
        ''' setup variables '''
        # Start logger
        self.log = Logger(progVer = orbSubVersion)  
        self.cfgGUI = False      
        self.orbsub = False   
        self.curDet = False

        # pltLines - this variable is used to store the data that is plotted - this
        # means we can delete from the plot when change detectors. For convenience
        # it can be accessed by lines, vlines, patches, occ and gti

        self.pltLines = {
            'lines'     : defaultdict(list),
            'patches'   : defaultdict(list),
            'vLines'    : defaultdict(list),
            'occ'       : defaultdict(list),
            'gti'       : defaultdict(list)
        }
        
        self.pltCfg = getPltCfg()
        self.selectId = False
        self._pltSelections = {}
        self._pltSelections.update({0:[]})
        self._pltSelections.update({1:[]})
        #
        self.anglesPlot = False
        self.pointingPlot = False    
        self.plotAllBackgrounds = False
        self.bkgSubLC = False
        self.plotResiduals = False

        self.common_args = {
            "fontname": self.pltCfg['font'],
            "fontsize": self.pltCfg['fontsize']}

    def InitUI(self):
        ''' setup user interface '''

        # Figure & canvas
        self.figure = Figure((8.0, 6.0), dpi = 100)
        self.canvas = FigureCanvas(self, -1, self.figure)
        nAxes = self.plotDimensions[0] * self.plotDimensions[1]
        self.axes = []
        for i in range(nAxes):
            axis = self.figure.add_subplot(self.plotDimensions[0], 
                                            self.plotDimensions[1], i + 1,)
            self.axes.append(axis)
        # Give axes instances a label for identifying them
        self._axesIds = ['lc', 'spec']
        self.axes[0]._lblId = 'lc'
        self.axes[1]._lblId = 'spec'
        self._axesLbltoInd = {'lc': 0, 'spec': 1}
        #Set initial axis conditions
        self.axes[1].set_xscale('log')
        self.axes[1].set_yscale('log')
        # Do labels
        self.axes[0].set_xlabel('Time (s)', **self.common_args)
        self.axes[0].set_ylabel('Counts/s', **self.common_args)
        self.axes[1].set_xlabel('Energy (keV)', **self.common_args)
        self.axes[1].set_ylabel('Counts/s/keV', **self.common_args)
        # Do legends
        self.doLegends()

        #ToolBar
        self.toolbar    = NavigationToolbar2WxAgg(self.canvas, True)
        self.toolbar.Realize()
        self.toolbar.Update()
        self.xposId     = wx.NewId()
        self.yposId     = wx.NewId()
        xposTxt         = wx.StaticText(self, label = "X:")
        yposTxt         = wx.StaticText(self, label = "y:")
        self.xposTxt    = wx.TextCtrl(self, self.xposId, '', style = wx.TE_READONLY)
        self.yposTxt    = wx.TextCtrl(self, self.yposId, '', style = wx.TE_READONLY)
        self.statusBar = wx.StatusBar(self, -1)
        self.statusBar.SetFieldsCount(1)
        self.SetStatusBar(self.statusBar)        

        # Sizers: btnBox is a vertical sizer which is used to hold buttons
        #         pltBox is a vertical sizer which holds toolbar & the canvas
        #         guiBox is a horizontal sizer which holds the two sizers
        self.btnBox     = wx.BoxSizer(wx.VERTICAL)
        self.pltBox     = wx.BoxSizer(wx.VERTICAL)
        self.guiBox     = wx.BoxSizer(wx.HORIZONTAL)
        self.toolbarBox = wx.BoxSizer(wx.HORIZONTAL)
        
        # Button definitions
        button_specs = [
            ('detBtn', 'Detectors'), ('selBtn', 'Select'), ('pltBtn', 'Plot'),
            ('rbnBtn', 'Rebin'), ('expBtn', 'Export'), ('mscBtn', 'Misc.')
        ]
        
        self.btns = {}
        self.menus = {}
        
        # Create buttons and menus
        for attr_name, label in button_specs:
            button = wx.Button(self, label=label)
            setattr(self, attr_name, button) # the menus and buttons are called by attr, so for backward compatibility we just do this
            menu = FM.FlatMenu(self)
            setattr(self, attr_name.replace('Btn', 'Menu'), menu)
            self.btns[attr_name] = button
            self.btnBox.Add(button, 0, wx.RIGHT, 5)
            self.menus[attr_name] = menu

        # Menus continued: defining the individual components of each menu
        self.detM_sel = self.detMenu.Append(-1, "Select", "Text")
        self.detM_for = self.detMenu.Append(-1, "Forward", "Text")
        self.detM_bak = self.detMenu.Append(-1, "Backward", "Text")
        
        # Detector menu items
        self.selM_sel = self.selMenu.Append(-1, "Select", "Text")
        self.selM_clr = self.selMenu.Append(-1, "Clear", "Text")
        self.selM_svs = self.selMenu.Append(-1, "Save selections", "Text")
        self.selM_lds = self.selMenu.Append(-1, "Load selections", "Text")

        self.pltM_ang   = self.pltMenu.Append(-1, "Plot Detector Angles", "Text")
        self.pltM_ptg   = self.pltMenu.Append(-1, "Plot S/C Pointing", "Text")
        self.pltM_bkg   = self.pltMenu.Append(-1, "Plot backgrounds separately", "Text")
        self.pltM_lc    = self.pltMenu.Append(-1, "Plot background subtracted LC", "Text") 
        self.pltM_res   = self.pltMenu.Append(-1, "Plot Residuals of signal - background", "Test")

        self.rebM_inv       = self.rbnMenu.Append(-1, "Temporal", "Text")
        self.rebM_counts    = self.rbnMenu.Append(-1, "Log Counts", "Text")

        self.expM_pii = self.expMenu.Append(-1, "PHAII", "Text")
        self.expM_pha = self.expMenu.Append(-1, "PHA", "Text")
        self.expM_alc = self.expMenu.Append(-1, "ASCII LC", "Text")
        
        self.expM_occ = self.expMenu.Append(-1, "Occultation Times", "Text")
        
        self.mscM_log = self.mscMenu.Append(-1, "Show Log", "Text")
        self.mscM_abt = self.mscMenu.Append(-1, "About", "Text")
        
        # Add toolbar & position controls to toolbarBox
        self.toolbarBox.Add(self.toolbar)
        self.toolbarBox.Add(xposTxt, 0, wx.RIGHT, 5)
        self.toolbarBox.Add(self.xposTxt, 0, wx.RIGHT, 5)
        self.toolbarBox.Add(yposTxt, 0, wx.RIGHT, 5)
        self.toolbarBox.Add(self.yposTxt, 0, wx.RIGHT, 5)
        self.toolbarBox.Add(self.statusBar, 5, wx.ALL, 5)

        # Add toolbar & canvas to pltBox
        self.pltBox.Add(self.toolbarBox, 0, wx.LEFT | wx.EXPAND)
        self.pltBox.Add(self.canvas, 1 ,wx.EXPAND | wx.ALL, 5)
        
        # Add pltBox and btnBox into guiBox
        self.guiBox.Add(self.btnBox, 0, wx.EXPAND, 5)
        self.guiBox.Add(self.pltBox, 5, wx.ALL| wx.EXPAND, 5)

        self.SetSizer(self.guiBox)
        self.SetInitialSize() 
    
    def ToggleButtons(self, state):
        '''
        Enable or disable all buttons depending on logical value of state
        '''
        #for i in self.btns:
        #    i.Enable(state)
        for btn in self.btns.values():
            btn.Enable(state)
        self.toolbar.Enable(state)

    def InitBindings(self):
        ''' 
        Setup bindings b/w events and methods. Must be called after InitUI()
        '''
        # Bind keyboard shortcuts
        dismissId = wx.NewId()
        self.Bind(wx.EVT_MENU, self.dismiss, id = dismissId)
        
        self.Bind(wx.EVT_MENU, self.OnChangeDet, id = self.detM_for.GetId())
        self.Bind(wx.EVT_MENU, self.OnChangeDet, id = self.detM_bak.GetId())

        saveLUId = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnSaveLU, id = saveLUId)
        loadLUId = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnLoadLU, id = loadLUId)   
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL,  ord('d'), dismissId ),
                                            (wx.ACCEL_CTRL,  ord('s'), saveLUId ),
                                            (wx.ACCEL_CTRL,  ord('a'), loadLUId ),
                                            (wx.ACCEL_CTRL, ord('z'), self.detM_bak.GetId()),
                                            (wx.ACCEL_CTRL, ord('x'), self.detM_for.GetId()), 
                                            (wx.ACCEL_CTRL, ord('v'), self.selM_sel.GetId()), 
                                            (wx.ACCEL_CTRL, ord('q'), self.pltM_ang.GetId()),
                                            (wx.ACCEL_CTRL, ord('l'), self.mscM_log.GetId()),
                                            (wx.ACCEL_CTRL, ord('w'), self.pltM_ptg.GetId()),
                                                                                ])
                                                  
        self.SetAcceleratorTable(accel_tbl)
        # Bind menus to buttons
        for btn in self.btns.values():
            self.Bind(wx.EVT_BUTTON, self.popUpMenu, btn)
        
        # Bind methods to menus
        self.Bind(wx.EVT_MENU, self.OnShowLog, self.mscM_log)
        self.Bind(wx.EVT_MENU, self.OnAbout, self.mscM_abt)
        # self.Bind(wx.EVT_MENU, self.OnConfig, self.mscM_cfg)

        # Bind detector methods
        self.Bind(wx.EVT_MENU, self.OnChangeDet, self.detM_for)
        self.Bind(wx.EVT_MENU, self.OnChangeDet, self.detM_bak)
        self.Bind(wx.EVT_MENU, self.OnChangeDet, self.detM_sel)
        # Bind selection methods
        self.Bind(wx.EVT_MENU, self.OnSelect, self.selM_sel)
        self.Bind(wx.EVT_MENU, self.OnClearSelections, self.selM_clr) 
        self.Bind(wx.EVT_MENU, self.OnSaveLU, self.selM_svs)
        self.Bind(wx.EVT_MENU, self.OnLoadLU, self.selM_lds)
        # Bind plot methods
        self.Bind(wx.EVT_MENU, self.OnPlotPointing, self.pltM_ptg)
        self.Bind(wx.EVT_MENU, self.OnPlotAngles, self.pltM_ang)
        self.Bind(wx.EVT_MENU, self.OnPlotAllBackgrounds, self.pltM_bkg)
        self.Bind(wx.EVT_MENU, self.OnPlotBkgSubLC, self.pltM_lc)
        self.Bind(wx.EVT_MENU, self.OnPlotResiduals, self.pltM_res)
        # Bind export options
        self.Bind(wx.EVT_MENU, self.OnExportPHAII, self.expM_pii)
        self.Bind(wx.EVT_MENU, self.OnExportASCLC, self.expM_alc)
        self.Bind(wx.EVT_MENU, self.OnExportPHA, self.expM_pha)
        self.Bind(wx.EVT_MENU, self.OnExportOccultation, self.expM_occ)
		# Bind rebin options
        self.Bind(wx.EVT_MENU, self.onRebin, self.rebM_inv )
        self.Bind(wx.EVT_MENU, self.onLogCounts, self.rebM_counts )
        # Bind closing 
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        #wx.EVT_PAINT(self, self.OnPaint)
        self.canvas.mpl_connect('motion_notify_event', self.OnHoverPoint)

    def OnHoverPoint(self, evt):
        
        if evt.inaxes:
            self.xposTxt.SetValue(str(round(evt.xdata,2)))
            self.yposTxt.SetValue(str(round(evt.ydata,2)))
        if  self.selectId is not False:
            if evt.inaxes:
                self.UpdateStatusBar("Click on graph to make selections")
            else:
               self.UpdateStatusBar("Click to finish selections")

    def InitData(self, orbsub):
        ''' Take in data '''
        self.orbsub = orbsub
        self.dets = list(orbsub.data.keys())
        self.dets.sort()        
        # Either generate default lookup or load one
        # if one exists and autoLoadLU has been set
        # _val is just a boolean keyword we use to 
        # see if the lookups get loaded
        luPath = False
        _val    = False
        if self.orbsub.opts.autoLoadLU:
            # AutoLoad lookup
            # print 'auto loading LookUps'
            luPath = False
            _val = self.OnLoadLU(False,  noGUI = True)
        if not _val:
            self._LU = getLUCfg(self.orbsub.opts.autoLoadLU, luPath,)
        self.IterDet()
        self.doPlotColors()

    def IterDet(self, det = False, resolution = False):
        '''
        Iterate currently selected detector. Takes in a detector and extracts 
        the data relevant to it. It then calls plot() which updates the
        axis with the selected data.
        '''
        if not self.curDet:
            self.curDet = self.dets[0]
        if det:
            self.curDet = det

        # the data is stored in a dictionary indexed by detector short name,
        # e.g. 'b0'
        data = self.orbsub.data[self.curDet]
        if not resolution:
            # data at native resolution
            # First extract the lightcurve info
            # This has the form: x,y,exp,err
            # time has the form (xi, xj)
            t               = data.data['src'][0] - self.orbsub.opts.tzero
            self.srcExp     = data.data['src'][2]
            self.t          = (t[:,1] - t[:,0] )/ 2. + t[:,0]
            self.src        = data.data['src'][1]
            self.srcErr     = data.data['src'][3]
            self.bkg        = data.background['all']
            self.bkgErr     = data.background['allerr']      
            self.bkgAll     = data.background      
            self.bkgExp     = data.bkgExp['all']
            self.bkgExpPre  = data.bkgExp['pre']
            self.bkgExpPos  = data.bkgExp['pos']
        else:
            # rebin data to desired resolution            
            t = data.data['src'][0] - self.orbsub.opts.tzero
            self.t, self.src, self.srcExp, self.srcErr = util.rebin_gbm(t, data.data['src'][1], data.data['src'][2], resolution = resolution)
            self.t, self.bkg, self.bkgExp, self.bkgErr = util.rebin_gbm(t, data.background['all'], data.bkgExp['all'], resolution = resolution)
            
            self.bkgAll = {}            
            self.t, bkgPre, self.bkgExpPre, bkgPreErr = util.rebin_gbm(t, data.background['pre'], data.bkgExp['pre'], resolution = resolution)
            self.t, bkgPos, self.bkgExpPos, bkgPosErr = util.rebin_gbm(t, data.background['pos'], data.bkgExp['pos'], resolution = resolution)
            self.bkgAll = {'pre': bkgPre, 'preerr':bkgPreErr, 'pos': bkgPos, 'poserr': bkgPosErr}
            self.t = (self.t[:,1] - self.t[:,0] )/ 2. + self.t[:,0]
        
        # Now get count spectra
        self.eEdgeMin = data.eEdgeMin
        self.eEdgeMax = data.eEdgeMax
        self.e, _, self.eExp = util.counts_spec(self.src, self.eEdgeMin, 
                                                      self.eEdgeMax)
        self.e, _, self.eExp = util.counts_spec(self.bkg, self.eEdgeMin,
                                                       self.eEdgeMax)
        self.axes[0].set_title(self.curDet, fontname = self.pltCfg['font'],
                                fontsize = self.pltCfg['fontsize'],)
        # Check for gti & occ steps
        self.gti = False
        self.occTI = False
        if self.orbsub.opts.doGTI:
            if self.orbsub.pos:
                self.gti = self.orbsub.pos.gti[self.curDet]
                self.occTI = self.orbsub.pos.occTI
        self.plot()
        
    def plotTI(self, index):
        ''' 
        plot time intervals - this includes occultation steps (occ) and 
        good time intervals based on detector angles (gti). The intervals to be 
        plotted are dictated by index, which can be either 'occ' or 'gti'.

        This method is seperate from hatchSelections as for occ & gti we 
        want to fill a region, rather than under the graph.
        '''
        if not self.orbsub.opts.doGTI:
            print("gti not set")
            return
        if index != 'gti' and index != 'occ':
            print('incorrect index passed!', index)
            return
        # The following was true - but didn't fully work because of autoscale
        # # if index is occ, check if we have already drawn the TI. If so,
        # # do not bother redrawing them
        # if index == 'occ':
        #     if len(self.pltLines[index][0]):
        #         return

        # Get fill colour from pltCfg
        clr = self.pltCfg[index + 'Fill']

        if self.gti:
            yMax = self.axes[0].axis()[-1]
            yMin = self.axes[0].axis()[-2]
            tRange = self.orbsub.opts.tRange
            
            if index == 'occ':
                ti = self.occTI
            else:
                ti = self.gti
            
            # ti are in MET - subtract tzero to get same units as tRange
            tiStart = np.asarray(ti[0]) - self.orbsub.opts.tzero
            tiEnd =   np.asarray(ti[1]) - self.orbsub.opts.tzero

            endLoop = False
            for i,j in zip(tiStart, tiEnd):
                # if index != "gti":
                #     print "Rise:Set, duration %.1f,%.f: -> %.1f s "%(i,j,j-i)
                # else: 
                #     continue
                # print i,j
                # The time interval may not fall within the scope of the graph.
                # This is due to somewhat lazy coding in the poshist class.
                # To avoid plotting all the time intervals (ti) we instead check if either 
                # edge falls within the scope of the graph, which is the same as checking
                # if it falls within opts.tRange.
                inRange = False

                if index == "gti":
                    # gti should always be in the graph
                    inRange = True
                else:
                    # print i,j,
                    # check if this occ ti is in graph interval                    
                    if i>=tRange[0] and i<= tRange[1]:
                        if j <= tRange[1]:
                            inRange = True
                        elif j >= tRange[1]:
                            j = tRange[1]
                            inRange = True
                            # i is in the graph, but j is not. As the TI are temporally sorted we can break
                            # after this iteration
                            endLoop = True
                    elif i < tRange[0] and j >tRange[0]:
                        inRange = True
                        i = tRange[0]
                    # if inRange:
                    #     print "in ->", i,j
                    # else:
                    #     print ""
                if inRange:
                    fill = self.axes[0].fill([i, j, j, i], [0, 0, yMax, yMax], 
                                             color = clr, fill = True, hatch = '', #/', 
                                             alpha = 0.4)                
                    # we use extend rather than append as axes.fill returns a list rather than 
                    # a single object
                    self.pltLines[index][0].extend(fill)
                if endLoop:
                    break
        else:
            pass
    def OnPlotAngles(self, event):
        ''' 
        Plot detector source angles
        '''
        if not self.orbsub:
            return
        if not self.orbsub.pos:
            mes = "In order to view detector angles you must pass the source location at run time"
            self.ErrorMes(mes, title = "Error")
            return
        if not self.anglesPlot:
            self.anglesPlot = extras.PlotAngles(self, title = 'Detector Angles', plotDimensions = (7,2), plotRatio = (8.,7.))
            times = self.orbsub.pos.times['src'] - self.orbsub.opts.tzero
            self.anglesPlot.InitData(times, self.orbsub.pos.det_angles, self.pltCfg)
            self.anglesPlot.Show()
        else:
            self.anglesPlot.Raise()
    def OnPlotPointing(self, event):
        ''' 
        Plot detector source angles
        '''
        if not self.orbsub:
            return
        if not self.orbsub.pos:
            mes = "In order to view pointing you must pass the source location at run time"
            self.ErrorMes(mes, title = "Error")
            return            
        if not self.pointingPlot:
            self.pointingPlot = extras.PlotPointing(self, title = 'S/C Pointing', plotDimensions = (1,1), plotRatio = (8.,4.))
            times = self.orbsub.pos.times
            self.pointingPlot.InitData(times, self.orbsub.pos.pointing, self.pltCfg, tzero = self.orbsub.opts.tzero)
            self.pointingPlot.Show()
        else:
            self.pointingPlot.Raise()

    def OnPlotBkgSubLC(self, event):
        if not self.orbsub:
            return
        if self.bkgSubLC:
            self.bkgSubLC.Destroy()
        if self.orbsub.opts.spec_type.lower() =="cspec":
            nominalExp = 4.096
        else:
            nominalExp = 1.024

        eMin =  "%.f"%self.eEdgeMin[self.specMask][0]
        eMax = "%.f"%self.eEdgeMax[self.specMask][-1]
        if float(eMin) >1e3:
            eMin = "%s,%s"%(eMin[:-3], eMin[-3:])
        if float(eMax) >1e3:
            eMax = "%s,%s"%(eMax[:-3], eMax[-3:])            
        title = 'Bkg Sub LC %s: %s -- %s keV'%(self.curDet, eMin, eMax)
        self.bkgSubLC = extras.BkgSubLC(self, title = title, plotDimensions = (1,1), plotRatio = (8.,4.))
        src  = self.src[:, self.specMask].sum(1)/ self.srcExp
        srcErr = np.sqrt(self.src[:, self.specMask].sum(1))/ self.srcExp
        bkg = self.bkg[:, self.specMask].sum(1)/ self.bkgExp
        bkgErr = np.sqrt(self.bkg[:, self.specMask].sum(1))/ self.bkgExp
        self.bkgSubLC.makePlot( self.t[self.lcMask], 
                                src[self.lcMask],
                                srcErr[self.lcMask],
                                bkg[self.lcMask],
                                bkgErr[self.lcMask],
                                np.ones(src[self.lcMask].size) * nominalExp/2.,
                                self.t[self.lcMask][0] - nominalExp/2.,
                                self.t[self.lcMask][-1] + nominalExp/2.,
                                self.pltCfg )
    
    def OnPlotResiduals(self, event):
        if not self.orbsub:
            return
        
        if self.plotResiduals:
            self.plotResiduals.Destroy()

        if self.orbsub.opts.spec_type.lower() =="cspec":
            nominalExp = 4.096
        else:
            nominalExp = 1.024

        eMin =  "%.f"%self.eEdgeMin[self.specMask][0]
        eMax = "%.f"%self.eEdgeMax[self.specMask][-1]

        if float(eMin) >1e3:
            eMin = "%s,%s"%(eMin[:-3], eMin[-3:])
        if float(eMax) >1e3:
            eMax = "%s,%s"%(eMax[:-3], eMax[-3:])            
        
        title = ' Residuals %s: %s -- %s keV'%(self.curDet, eMin, eMax)
        
        src  = self.src[:, self.specMask].sum(1)/ self.srcExp
        srcErr = np.sqrt(self.src[:, self.specMask].sum(1))/ self.srcExp
        bkg = self.bkg[:, self.specMask].sum(1)/ self.bkgExp
        bkgErr = np.sqrt(self.bkg[:, self.specMask].sum(1))/ self.bkgExp

        self.plotResiduals = extras.ResLC(self, title = title, plotDimensions = (1,1), plotRatio = (8.,4.))
        self.plotResiduals.makePlot( self.t[self.lcMask], 
                                src[self.lcMask],
                                srcErr[self.lcMask],
                                bkg[self.lcMask],
                                bkgErr[self.lcMask],
                                np.ones(src[self.lcMask].size) * nominalExp/2.,
                                self.t[self.lcMask][0] - nominalExp/2.,
                                self.t[self.lcMask][-1] + nominalExp/2.,
                                self.pltCfg)
    
    def OnPlotSummedResiduals(self, event):
        if not self.orbsub:
            return
        
        if self.plotResiduals:
            self.plotResiduals.Destroy()

        if self.orbsub.opts.spec_type.lower() =="cspec":
            nominalExp = 4.096
        else:
            nominalExp = 1.024

        eMin =  "%.f"%self.eEdgeMin[self.specMask][0]
        eMax = "%.f"%self.eEdgeMax[self.specMask][-1]

        if float(eMin) >1e3:
            eMin = "%s,%s"%(eMin[:-3], eMin[-3:])
        if float(eMax) >1e3:
            eMax = "%s,%s"%(eMax[:-3], eMax[-3:])            
        
        title = ' Residuals %s: %s -- %s keV'%(self.curDet, eMin, eMax)
        
        src  = self.src[:, self.specMask].sum(1)/ self.srcExp
        srcErr = np.sqrt(self.src[:, self.specMask].sum(1))/ self.srcExp
        
        bkg = self.bkg[:, self.specMask].sum(1)/ self.bkgExp
        bkgErr = np.sqrt(self.bkg[:, self.specMask].sum(1))/ self.bkgExp

        self.plotResiduals = extras.ResLC(self, title = title, plotDimensions = (1,1), plotRatio = (8.,4.))
        self.plotResiduals.makePlot( self.t[self.lcMask], 
                                src[self.lcMask],
                                srcErr[self.lcMask],
                                bkg[self.lcMask],
                                bkgErr[self.lcMask],
                                np.ones(src[self.lcMask].size) * nominalExp/2.,
                                self.t[self.lcMask][0] - nominalExp/2.,
                                self.t[self.lcMask][-1] + nominalExp/2.,
                                self.pltCfg)
    
    def OnPlotAllBackgrounds(self, event):
        self.plotAllBackgrounds = not self.plotAllBackgrounds
        self.doLegends()
        self.plot()

    def doPlotColors(self):
        ''' 
        set plot fore and background colours
        '''           
        for ax in self.axes:
            # ax.set_axis_bgcolor(self.pltCfg['background']) deprecated
            ax.set_facecolor(self.pltCfg['background'])
            plt.setp(list(ax.spines.values()), color = self.pltCfg['foreground'])
            ax.tick_params(axis='both', which='major', 
                            labelsize = self.pltCfg['fontsizeLabel'],
                            color = self.pltCfg['foreground'])
            ax.tick_params(axis='both', which='minor',
                            labelsize = self.pltCfg['fontsizeLabel'],
                            color = self.pltCfg['foreground'])
        self.Draw()

    def doLegends(self, ):
        for ax in self.axes:
            ax.legend_ = None
            l1, = ax.plot([1,2,3], ls = '-', marker = '', c=self.pltCfg['srcLine'] ) 
            l2, = ax.plot([1,2,3], ls = '-', marker = '', c=self.pltCfg['bkgLine'] ) 
            l1.remove() 
            l2.remove()
            if self.plotAllBackgrounds and ax._lblId == "lc":
                l3, = ax.plot([1,2,3], ls = '-', marker = '', c=self.pltCfg['preCol'])
                l4, = ax.plot([1,2,3], ls = '-', marker = '', c=self.pltCfg['posCol'])
                l3.remove() 
                l4.remove()
                leg = ax.legend([l1,l2,l3,l4], ["Source","Background", "Pre Background", "Post Background"], loc = 'upper right',
                            prop = {'family': self.pltCfg['font'] , 'size': self.pltCfg['fontsizeLegend'] })
            else:
                leg = ax.legend([l1,l2], ["Source","Background"], loc = 'upper right',
                            prop = {'family': self.pltCfg['font'] , 'size': self.pltCfg['fontsizeLegend'] })
            leg.get_frame().set_alpha(0.5)
    
    def plot(self, ):
        ''' 
        Plot selected data. This method should be called after any selection is made.
        '''
        # Remove any current lines on plot
        to_clear = ['lines', 'patches', 'vLines', 'gti', 'occ']
        for i in to_clear:
            self.clearLines(i)
        # Get selection masks from lookup
        # Lightcurve selections are applied to counts spectra
        # and spectrum selections are applied to light curve
        lcLu        = self._LU[self.curDet]['lc']
        specLu      = self._LU[self.curDet]['spec']
        # Default - no selections made - select all
        self.lcMask     = self.t != -99999999
        self.specMask   = self.e != -99999999
        if len(lcLu):
            # we have selections - first invert the mask array
            # We can then loop over each selection and create
            # a mask array which is True for those regions.
            # This array can be combined with the inverted array
            # via an or operation. 
            self.lcMask = ~self.lcMask                
            for i in range(0, len(lcLu), 2):
                sel = lcLu[i:i+2]
                tempMask = (self.t > sel[0]) & (self.t < sel[1])
                self.lcMask = self.lcMask | tempMask

        if len(specLu):
            # Same as for above
            self.specMask = ~self.specMask                
            for i in range(0, len(specLu), 2):
                sel = specLu[i:i+2]
                tempMask = (self.eEdgeMin >= sel[0]) & (self.eEdgeMax <= sel[1])
                self.specMask = self.specMask | tempMask            

        # Draw new lines - also add them to variable lines so we can remove them later
        self.pltLines['lines'][0].extend(self.axes[0].step(self.t, self.src[:, self.specMask].sum(1)/ self.srcExp,
                                         color = self.pltCfg['srcLine'], where = 'mid'))
        self.pltLines['lines'][0].extend(self.axes[0].step(self.t, self.bkg[:, self.specMask].sum(1)/ self.bkgExp,
                                         color = self.pltCfg['bkgLine'], where = 'mid'))
        if self.plotAllBackgrounds:
            self.pltLines['lines'][0].extend(self.axes[0].step(self.t, self.bkgAll['pre'][:, self.specMask].sum(1)/ self.bkgExpPre,
                                             color = self.pltCfg['preCol'], where = 'mid', ))
            self.pltLines['lines'][0].extend(self.axes[0].step(self.t, self.bkgAll['pos'][:, self.specMask].sum(1)/ self.bkgExpPos,
                                             color = self.pltCfg['posCol'], where = 'mid', ))
        
        # Due to the way matplotlib plots step, we need to do a small bit of messing here
        x = self.e
        x = np.concatenate((np.array(self.eEdgeMin[:1]),x))
        x = np.concatenate((x, np.array(self.eEdgeMax[-1:]))) 
        y = self.src[self.lcMask,:].sum(0)/self.eExp/ self.srcExp[self.lcMask].sum()
        y = np.concatenate((y[:1] ,y))
        y = np.concatenate((y ,y[-1:]))
        y2 = self.bkg[self.lcMask,:].sum(0)/self.eExp/ self.bkgExp[self.lcMask].sum()
        y2 = np.concatenate((y2[:1] ,y2))
        y2 = np.concatenate((y2 ,y2[-1:]))
        self.pltLines['lines'][1].extend(self.axes[1].step(x,y,
                                         color = self.pltCfg['srcLine'], where = 'mid'))
        self.pltLines['lines'][1].extend(self.axes[1].step(x,y2,
                                         color = self.pltCfg['bkgLine'], where = 'mid'))
        # Autoscale limits
        self.doAutoscale() # necessary to see the signal

        # Hatch selected regions (if any)
        self.hatchSelections('lc')
        self.hatchSelections('spec')
        # Draw time intervals (if any)
        self.plotTI('occ')        
        self.plotTI('gti')
        # Finally, draw the changes            
        self.Draw()

    def doAutoscale(self):
        ''' Autoscale graph limits '''
        yMax = max((self.src[:, self.specMask].sum(1)/self.srcExp).max(), (self.bkg[:, self.specMask].sum(1)/self.bkgExp).max())
        yMin = min((self.src[:, self.specMask].sum(1)/self.srcExp).min(), (self.bkg[:, self.specMask].sum(1)/self.bkgExp).min())        
        
        self.axes[1].relim()
        self.axes[1].autoscale_view()
        # set the x_limits based on energy range
        self.axes[1].set_xlim(self.eEdgeMin[self.specMask][0], self.eEdgeMax[self.specMask][-1])
        #set the y_limits based on spectral counts in data

        xlim = self.orbsub.opts.tRange
        self.axes[0].set_xlim(xlim[0] -150, xlim[1] + 150)            
        self.axes[0].set_ylim(yMin *0.9, yMax*1.1)

    def clearLines(self, index):
        '''
        Remove lines from axes. Index is what is used to index the pltLines dictionary.
        This can be - 'lines', 'vLines' or 'patches' 
        '''
        if index == 'patches':
            for axis in list(self.pltLines[index].keys()):
                for line in self.pltLines[index][axis]:
                    try:
                        # for fill_between
                        # TODO self.axes[axis].collections.remove(line)
                        line.remove()
                        
                    except TypeError: 
                        # for fill
                        for i in line:
                            # TODO self.axes[axis].patches.remove(i)
                            i.remove()
                self.pltLines[index][axis] = []
        elif index == 'gti' or index == 'occ':
            for i in self.pltLines[index][0]:
                # print 'removing gti/occ ', i
                # TODO self.axes[0].patches.remove(i)
                i.remove()
            self.pltLines[index][0] = []
        else:
            for axis in list(self.pltLines[index].keys()):
                for line in self.pltLines[index][axis]:
                    # TODO self.axes[axis].lines.remove(line)
                    line.remove()
                self.pltLines[index][axis] = []
    def popUpMenu(self,event):
        ''' When called, pop menu up at mouse location. '''
        # get event id, then compare to btn ids to find out what menu we 
        #  should open
        id = event.GetId()
        pos = wx.GetMousePosition()
        #for i, j in enumerate(self.btns):
        #    if j.GetId() == id:
        #        self.menus[i].Popup( pos, self)
        #        return 
        #for btn in self.btns.values():
        #    if btn.GetId() == id:
        #        self.menus[btn.label].Popup( pos, self)
        #        return
    
        for label, btn in self.btns.items():
            if btn.GetId() == id:
                # print "Opening menu for %s"%label
                self.menus[label].Popup( pos, self)
                return

    def OnSelect(self, event):
        ''' User wants to select data '''
        id = event.GetId()
        if id == self.selM_sel.GetId():
            self.selectId = self.canvas.mpl_connect('button_press_event', 
                                                    self.flagClick)
            self.ToggleButtons(False)
            self.UpdateStatusBar("Click on graph to make selections")

    def disconnectClick(self):
        '''Disconnect selection method from graph '''
        if self.selectId:
            self.canvas.mpl_disconnect(self.selectId)
            self.selectId = False
            self.ToggleButtons(True)
            self.UpdateStatusBar("")
    def flagClick(self, event):
        ''' Register one click event on mpl axes'''
        #print event, event.x, event.y, event.inaxes, type(event.inaxes)
        if not event.inaxes:
            # Interaction is outside the plot - Disconnect interactions
            self.disconnectClick()
            # Remove vertical lines
            self.clearLines('vLines')
            # Check if any selections were made
            for i, lbl in zip([0, 1], ['lc', 'spec']):
                edges = self._pltSelections[i]
                # If user has made an odd number (N) of selections, only include
                # N -1 selections
                if len(edges) % 2:
                    edges = edges[:-1]
                # Need at least two values
                if len(edges) >= 2:
                    # We currently have the user selected values 
                    # We want the nearest bin edge 
                    edges = self.orbsub.data[self.curDet].getNearestBinEdges(edges, lbl, self.orbsub.opts.tzero)
                    # If nearest edges cannot be found - edges will
                    # be boolean false - else it will be a list
                    if edges:
                        self._LU[self.curDet][lbl].extend(edges)
            # Clear list holding selected data
            self._pltSelections[0] = []
            self._pltSelections[1] = []
            # Redraw plot with new data
            self.plot()
        else:
            # Top axis is lightcurve - bottom is energy spectrum
            # Have to find out what axis the user clicked
            # We have added an attribute (_lblId) to the axes instances
            # when they are defined - this is used to check for type which
            # can be either 'lc' or 'spec'. The check is done as 
            # `if id not in self._axesIds: return`
            id = event.inaxes._lblId
            if id not in self._axesIds:
                return
            # Draw line showing where selection was made
            self.drawVLine(event.xdata, id)
            # The selected data is stored in an list. The data
            # is seperate for each axis. To do this - we store 
            # each list in a dictionary called _pltSelections 
            # which is indexed by axis index (0,1).
            # When the user clicks off the axes then this 
            # dictionary is used to fill the lookup variable.
            # The list contents of _pltSelections are then set back to
            # empty lists.
            axisIndex = self._axesLbltoInd[id]
            self._pltSelections[axisIndex].append(event.xdata)
            #                selString = ("Made selection in range: %.1f : %.1f" 
            #                             %(self.selections[0], self.selections[1],))
            #                self.UpdateStatusBar(selString)
    def OnClearSelections(self, event):
        '''
        Clear current selections - remove selections from both LookUps
        and from plot
        '''
        # Remove data from lookups
        self._LU[self.curDet]['lc'] = []
        self._LU[self.curDet]['spec'] = []
        # Remove hatchings
        self.plot()
    def hatchSelections(self, lbl, edges = False):
        '''
        Hatch selected regions on axis specified by lbl. 
        If edges is passed - then convert 
        that N x 1-D list into a N/2 2-D list. Then fill between these 
        values. If edges is not passed, then fill between the lookup regions
        '''
        self.axes[0].autoscale(enable = False)
        self.axes[1].autoscale(enable = False)
        if not edges:
            edges = self._LU[self.curDet][lbl]
        axisId = self._axesLbltoInd[lbl]
        axis = self.axes[axisId]
        # We want to fill under the data line
        if lbl == 'lc':
            x = self.t
            y = self.src.sum(1)/ self.srcExp
            x, y = util.steppify(x, y, self.srcExp)
        elif lbl == 'spec':
            x = self.e
            y = self.src.sum(0)/self.eExp
            x, y = util.steppify(x, y, self.eExp)
        else:
            return
        for i in range(0, len(edges), 2):            
            e1, e2 = edges[i:i+2][0],edges[i:i+2][1]
            # fillMask = ((x >= e1) & (x <= e2))
            # patch = axis.fill_between(x[fillMask], y[fillMask], 1e-6, color = self.pltCfg['srcFill'], alpha = 0.5)
            y1, y2 = axis.axis()[2], axis.axis()[3]
            patch = axis.fill([e1,e1,e2,e2], [y1,y2,y2,y1], color = self.pltCfg['srcFill'], alpha = 0.5)
            self.pltLines['patches'][axisId].append(patch)    
        
    def drawVLine(self, x, axisLbl):
        ''' 
        Draw a vertical line on the specified axis. Also add line to 
        variable so we can delete it later if wanted. 
        '''
        axisId = self._axesLbltoInd[axisLbl]
        axis = self.axes[axisId]
        self.pltLines['vLines'][axisId].append(axis.axvline(x, ))
        self.Draw()        
    def OnSaveLU(self, event):
        ''' Save lookup file '''
        fileName = self.orbsub.opts.name + '_OSV_V00.lu'
        dlg = wx.FileDialog(self, "Save LU", os.getcwd(), fileName,
                            "*.lu", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            fo = open(dlg.GetPath(), 'wb') # TODO check if all the open need binary r/w
            pickle.dump(self._LU, fo)
            fo.close()
        dlg.Destroy()
    def OnLoadLU(self, event, noGUI = False):
        ''' Load lookup file '''
        fileName = self.orbsub.opts.name + '_OSV_V00.lu'
        if not noGUI:
            dlg = wx.FileDialog(self, "Load LU", os.getcwd(), fileName,
                                "*.lu", wx.FD_OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                fo = open(dlg.GetPath(), 'rb')
                self._LU = pickle.load(fo)
                fo.close()
            dlg.Destroy()    
        else:
            if os.path.isfile(fileName):
                fo = open(fileName, 'rb')
                self._LU = pickle.load(fo)
                fo.close()
            else:
                return False
        return True
    def OnShowLog(self, event):
        ''' show log '''
        self.log.show(self)
    def onRebin(self, event):
        '''
        Create a widget to get desired resolution, then rebin to that resolution
        '''
        # self.ErrororMes('Feature not yet enabled!')
        # return
        dlg = osv_classes.RebinDialog(self, False, title = 'Rebin Dialog')
        dlg.Centre()
        if (dlg.ShowModal() == wx.ID_OK):
            newRes = float(dlg.resTxt.GetValue())
            self.IterDet(resolution = newRes)
        else:
            pass
        dlg.Destroy()  
    def onLogCounts(self, event):
        '''
        Rebins to Logscale the Counts/s Axis (y axis)
        '''
        #Add a log options for Counts
        if self.axes[0].get_yscale() != 'log' :
            self.axes[0].set_yscale('log')
        else :
            self.axes[0].set_yscale('linear')
        self.IterDet() #Replots
        return
    
    def _compute_plot_data(self): #!HERE
        """Cache expensive computations"""
        if not hasattr(self, '_cached_data') or self._data_dirty:
            self._cached_src_sum = self.src[:, self.specMask].sum(1) / self.srcExp
            self._cached_bkg_sum = self.bkg[:, self.specMask].sum(1) / self.bkgExp
            self._data_dirty = False

    def OnAbout(self, event):
        """Show the about dialog"""
        
        info = AboutDialogInfo()

        licence = """Orbsub is free software; you can redistribute 
        it and/or modify it under the terms of the GNU General Public License as 
        published by the Free Software Foundation; either version 2 of the License, 
        or (at your option) any later version.

        Orbsub is distributed in the hope that it will be useful, 
        but WITHOUT ANY WARRANTY; without even the implied warranty of 
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
        See the GNU General Public License for more details. You should have 
        received a copy of the GNU General Public License along with File Hunter; 
        if not, write to the Free Software Foundation, Inc., 59 Temple Place, 
        Suite 330, Boston, MA  02111-1307  USA"""
        # Populate with information
        info.SetName("OSV")
        info.SetVersion("%s"%orbSubVersion)

        #        info.SetIcon(wx.Icon('temp.png', wx.BITMAP_TYPE_PNG))
        # info.SetIcon(wx.Icon('osvLogo.png', wx.BITMAP_TYPE_PNG))
        # info.SetDescription(description)
        # info.SetCopyright('(C) 2007 - 2012 Gerard Fitzpatrick')
        info.SetWebSite('http://fermi.gsfc.nasa.gov/ssc/data/analysis/user/')
        info.SetLicence(licence)
        # info.AddDeveloper('Gerard Fitzpatrick')
        # info.AddDocWriter('Gerard Fitzpatrick')

        # Create and show the dialog
        AboutBox(info)  
    def OnConfig(self, event):
        '''
        Create GUI instance for viewing of config file. We check if the GUI 
        has already been called - don't want to overload the user with
        multiple identical windows. If it does exist, focus attention
        on it.
        '''
        if self.cfgGUI:
            self.cfgGUI.Show()
            self.cfgGUI.Raise() 
            self.cfgGUI.Iconize(False)            
            return
        else:
            self.cfgGUI = GUI_showConfig(self, title = 'LOG', size = (750, 750))
    def OnExportPHAII(self, event):
        names = self.getOutputName( 'phaii')
        if not len(names): return 
        print(self.curDet, names)
        self.orbsub.data[self.curDet].write_phaii(self.orbsub.opts, names = names,)
    def OnExportPHA(self,event):
        names = self.getOutputName( 'pha')
        if not len(names): return
        self.orbsub.data[self.curDet].write_pha(self.orbsub.opts, names = names, lcMask = self.lcMask,)
    def OnExportASCLC(self,event):
        names = self.getOutputName( 'ascii')
        if not len(names): return
        self.orbsub.data[self.curDet].write_ascii(self.orbsub.opts, names = names, lcMask = self.lcMask, specMask = self.specMask)
    
    def OnExportOccultation(self, event):
        '''
        Export occultation time intervals to a text file
        '''
        if not self.orbsub:
            self.ErrorMes("No data loaded", title="Error")
            return
            
        if not self.orbsub.pos or not self.orbsub.pos.occTI:
            self.ErrorMes("No occultation data available. Make sure source coordinates are provided.", title="Error")
            return
        
        # Get default filename
        defaultName = f"glg_osv_occultation_{self.orbsub.opts.name}.txt"
        
        # Show file dialog
        dlg = wx.FileDialog(self, "Export Occultation Times", os.getcwd(), defaultName,
                           "Text files (*.txt)|*.txt|All files (*.*)|*.*", 
                           wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            try:
                self._writeOccultationFile(filepath)
                wx.MessageBox(f"Occultation times exported successfully to:\n{filepath}", 
                             "Export Complete", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                self.ErrorMes(f"Error writing occultation file:\n{str(e)}", title="Export Error")
        
        dlg.Destroy()
    
    def _writeOccultationFile(self, filepath):
        '''
        Write occultation time intervals to a text file
        '''
        occTI = self.orbsub.pos.occTI
        occStart = np.asarray(occTI[0])  # Start times
        occEnd = np.asarray(occTI[1])    # End times
        
        with open(filepath, 'w') as f:
            # Write header
            f.write("# Occultation Time Intervals\n")
            f.write(f"# Source: {self.orbsub.opts.name}\n")
            f.write(f"# Coordinates: RA={self.orbsub.opts.coords[0]:.6f}, DEC={self.orbsub.opts.coords[1]:.6f}\n")
            f.write(f"# Time zero (MET): {self.orbsub.opts.tzero:.6f}\n")
            f.write("# Columns: Start_Time(MET) End_Time(MET) Duration(s) Start_Time(rel_to_tzero) End_Time(rel_to_tzero)\n")
            f.write("#\n")
            
            # Write data
            for start_met, end_met in zip(occStart, occEnd):
                duration = end_met - start_met
                start_rel = start_met - self.orbsub.opts.tzero
                end_rel = end_met - self.orbsub.opts.tzero
                
                f.write(f"{start_met:.6f} {end_met:.6f} {duration:.6f} {start_rel:.6f} {end_rel:.6f}\n")
            
            f.write(f"\n# Total occultation intervals: {len(occStart)}\n")
            f.write(f"# Total occultation time: {np.sum(occEnd - occStart):.6f} seconds\n")
    
    def getOutputName(self, otype):
        ''' getoutput name for files
        '''
        exts = {'phaii': ['PHA', 'BAK'], 'pha': ['PHA1', 'BAK1'], 'ascii': ['src', 'bkg']}
        defaultName = ("glg_osv-%s_%s_%s.XX" %(self.orbsub.opts.spec_type.lower(), self.orbsub.opts.name, self.curDet))
        names = []
        for i,j in zip(exts[otype], ['source', 'background']):
            name = defaultName.replace(".XX",".%s"%i) 
            dlg = wx.FileDialog(self, "Name for %s file" %j, os.getcwd(), name,
                            "*.%s"%i, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                name = dlg.GetPath()
            else:
                dlg.Destroy()
                return []
            dlg.Destroy()
            names.append(name)


        return names
    
    def dismiss(self, event):
        ''' dismiss instance '''
        self.Close()
    
    def restore(self):
        ''' Restore '''
        self.Show()
    
    def OnClose(self, event):
        '''Handle close event'''    
        val = self.YesNoMes("Are you sure you want to quit?", "Exit?")
        if val:
            event.Skip()

    def ErrorMes(self, mes, title = 'Error', style =wx.OK|wx.ICON_ERROR ):
        wx.MessageBox(mes, title, style=style)
    
    def YesNoMes(self, mes, title='', style=wx.YES_NO | wx.YES_DEFAULT):
            '''Show yes/no message'''
            dlg = wx.MessageDialog(self, mes, title, style=style)
            result = dlg.ShowModal() == wx.ID_YES
            dlg.Destroy()
            return result

    def OnChangeDet(self, event,):
        if not self.curDet or len(self.dets) == 1:
            return
        
        detIndex = self.dets.index(self.curDet)
        nDets = len(self.dets)
        newDet = None
        
        event_id = event.GetId()
        
        if event_id == self.detM_sel.GetId():
            dlg = DetSelection(self, self.dets)
            if dlg.ShowModal() == wx.ID_OK:
                newDet = dlg.detSelected
            dlg.Destroy()
        elif event_id == self.detM_for.GetId():
            newDet = self.dets[0] if detIndex == nDets - 1 else self.dets[detIndex + 1]
        elif event_id == self.detM_bak.GetId():
            newDet = self.dets[-1] if detIndex == 0 else self.dets[detIndex - 1]
        
        if newDet:
            self.IterDet(newDet)

    def Draw(self):
        ''' Update Canvas '''
        self.canvas.draw()    

    def OnPaint(self, event):
        '''Update Canvas'''
        self.canvas.draw()
        event.Skip()

    def UpdateStatusBar(self, mes):
        self.statusBar.SetStatusText((mes), 0)

class DetSelection(wx.Dialog):
    '''
    GBM Detector Selection Dialog - for a subset of detectors
    '''

    def __init__(self, parent, detectors, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.detSelected = None
        self._setup_ui(detectors)
        self.Centre()
    
    def _setup_ui(self, detectors) -> None:
        """Setup dialog UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        for detector in detectors:
            btn = wx.ToggleButton(self, -1, detector)
            btn.Bind(wx.EVT_TOGGLEBUTTON, self._on_selected)
            sizer.Add(btn, 0, wx.EXPAND | wx.ALL, 2)
        
        self.SetSizer(sizer)
        self.SetInitialSize()
    
    def _on_selected(self, event) -> None:
        """Handle detector selection"""
        self.detSelected = event.GetEventObject().GetLabel()
        self.EndModal(wx.ID_OK)
