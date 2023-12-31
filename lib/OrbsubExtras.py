'''
OrbsubExtras.py
'''

import wx
import numpy as np
import astropy.io.fits as pf
import matplotlib

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wx import _load_bitmap
from . import osv_classes
from lib.config.plotConfig import getPltCfg
import lib.util.util as util

class GUI_plotFrame(wx.Frame):
    '''
    Frame which contains a single matplotlib figure. 
    Shortcuts are: Ctrl - d: close instance
    '''
    def __init__(self, *args, **kwargs):
        # pop plotDimensions from kwargs if present
        self.plotDimensions = kwargs.pop('plotDimensions',[(1,1)])
        # pop plot ratio from kwargs if present
        self.plotRatio = kwargs.pop('plotRatio',[(8,6)])
        super(GUI_plotFrame, self).__init__(*args, **kwargs)
        self.InitUI()
        self.InitBindings()
        self.Centre() 
        self.Show()
    def InitUI(self):
        '''
        Initialise User Interface
        '''
        self.figure = Figure(self.plotRatio, dpi = 100)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.axes = []
        nAxes = self.plotDimensions[0] * self.plotDimensions[1]
        for i in range(nAxes):
            axis = self.figure.add_subplot(self.plotDimensions[0], 
                                            self.plotDimensions[1], i + 1,)
            self.axes.append(axis)
        #ToolBar
        self.toolbar = NavigationToolbar2WxAgg(self.canvas, )
        self.toolbar.Realize()         
        self.canvasBox = wx.BoxSizer(wx.VERTICAL)
        PltBox = wx.BoxSizer(wx.HORIZONTAL)
        #Fix for ToolBar        
        if wx.Platform == '__WXMAC__':
            # Mac platform (OSX 10.3, MacPython) does not seem to cope with
            # having a toolbar in a sizer. This work-around gets the buttons
            # back, but at the expense of having the toolbar at the top
            self.SetToolBar(self.toolbar)
        else:
            # On Windows platform, default window size is incorrect, so set
            # toolbar width to figure width.
            tw, th = self.toolbar.GetSize() # deprecated GetSizeTuple()
            fw, fh = self.canvas.GetSize() # deprecated GetSizeTuple()
            # By adding toolbar in sizer, we are able to put it at the bottom
            # of the frame - so appearance is closer to GTK version.
            # As noted above, doesn't work for Mac.
            self.toolbar.SetSize(wx.Size(fw, th))
            PltBox.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)

        self.canvasBox.Add(PltBox, 0, wx.EXPAND)
        self.canvasBox.Add(self.canvas, 1 ,wx.EXPAND | wx.ALL, 5)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvasBox, 5,  wx.ALL | wx.EXPAND)

        self.statusBar = wx.StatusBar(self, -1)
        self.statusBar.SetFieldsCount(1)
        self.SetStatusBar(self.statusBar)

        self.SetSizer(sizer)
        self.SetInitialSize()


    def InitBindings(self):
        ''' 
        Setup bindings b/w events and methods. Must be called after InitUI()
        '''
        dismissId = wx.NewId()
        saveId = wx.NewId()
        
        self.Bind(wx.EVT_MENU, self.dismiss, id = dismissId)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL,  ord('d'), 
                                          dismissId ),])
        self.SetAcceleratorTable(accel_tbl)
    def doLegend(self, leg):
        leg.get_frame().set_alpha(0.5)
        ltext  = leg.get_texts()
        llines = leg.get_lines()
        frame  = leg.get_frame()
        frame.set_facecolor('0.80')
        plt.setp(ltext, fontsize = self.pltCfg['fontsizeLegend'])
        plt.setp(llines, linewidth = 1.5) 
    def dismiss(self, event):
        ''' close instance '''
        # self.Close()
        self.Hide()

class PlotAngles(GUI_plotFrame):
    def InitData(self, t, det_angles, pltCfg, ):
        ''' '''
        self.pltCfg = pltCfg
        for ax in self.axes:
            # deprecated ax.set_axis_bgcolor(self.pltCfg['background'])
            ax.set_facecolor(self.pltCfg['background'])
            plt.setp(list(ax.spines.values()), color = self.pltCfg['foreground'])
            ax.tick_params(axis='both', which='major', 
                            labelsize = self.pltCfg['fontsizeLabel'],
                            color = self.pltCfg['foreground'])
            ax.tick_params(axis='both', which='minor',
                            labelsize = self.pltCfg['fontsizeLabel'],
                            color = self.pltCfg['foreground'])
        dets = list(det_angles.keys())
        dets.sort()
        for i, ax in zip(dets, self.axes):
                ax.plot(t, det_angles[i], color = pltCfg['srcLine'], )
                ax.set_ylim(0, 180)
                if i[0] == 'b':
                    ang = 90
                else:
                    ang = 60
                fillMask = (det_angles[i] < ang)
                ax.fill_between(t, 0,  det_angles[i], where=(det_angles[i] <= ang), color = self.pltCfg['srcFill'], alpha = 0.5)    
                if i == "na" or i == "nb":
                    ax.tick_params(axis='both', which='major', labelsize=self.pltCfg["fontsizeLegend"])
                else:
                    ax.tick_params(axis = "x", which = "both", labelbottom = "off")
                ax.yaxis.set_ticks(np.arange(0, 180, 30) )
                ax.text(0.85, 0.85, i, ha = "left", fontsize = self.pltCfg['fontsizeLegend'], transform=ax.transAxes, family = "serif")
        
        self.figure.text(0.05, 0.5, 'Angular Seperation (deg)', va = 'center', ha = 'center', rotation = 90.,
                                fontname = self.pltCfg['font'], fontsize = self.pltCfg['fontsize'])
        self.figure.text(0.5, 0.05, 'Time (s)', va = 'center', ha = 'center',fontname = self.pltCfg['font'],
                                fontsize = self.pltCfg['fontsize'])
        self.figure.subplots_adjust(hspace = 0.001, )

class PlotPointing(GUI_plotFrame):
    def InitData(self, times, pointing, pltCfg, tzero = 0):
        ''' '''
        linestyles = ['--', '-.', '-',  ] 
        self.pltCfg = pltCfg
        for ax in self.axes:
            # deprecated ax.set_axis_bgcolor(self.pltCfg['background'])
            ax.set_facecolor(self.pltCfg['background'])
            plt.setp(list(ax.spines.values()), color = self.pltCfg['foreground'])
            ax.tick_params(axis='both', which='major', 
                            labelsize = self.pltCfg['fontsizeLabel'],
                            color = self.pltCfg['foreground'])
            ax.tick_params(axis='both', which='minor',
                            labelsize = self.pltCfg['fontsizeLabel'],
                            color = self.pltCfg['foreground'])        
        # Time arrays may be unequal length, this bit of code will 
        # deal with this
        x = []
        t = times['src']
        for i in times:
            if i == 'src':
                continue
            tDif =  t[0] - times[i][0] 
            times[i] = times[i] + tDif -tzero
        t = t - tzero
        
        counter = 0
        keys = list(pointing.keys())
        keys.sort()
        for i in keys:
            if i == 'src':
                continue
            else:
                if "pre" in i:
                    col = color = pltCfg['preCol']
                else:
                    col = color = pltCfg['posCol']
                self.axes[0].plot(times[i], pointing[i], label = i, color = col, 
                                    linestyle = linestyles[counter], )
                leg = self.axes[0].legend(shadow = True, fancybox = True, loc = 'best',)
                self.doLegend(leg)                            
            counter = (counter+1)%len(linestyles)

        self.axes[0].plot(t, pointing['src'], color = pltCfg['srcLine'], label = 'src' )

        self.axes[0].set_ylabel('Ang. sep. from source', fontsize = pltCfg['fontsize'], fontname = self.pltCfg['font'],)
        self.axes[0].set_xlabel('Time (s)', fontsize = pltCfg['fontsize'], fontname = self.pltCfg['font'],)
        

class BkgSubLC(GUI_plotFrame):
    def makePlot(self, x, src, srcErr, bkg, bkgErr, widths, tStart, tStop, pltCfg):
        ''' '''
        self.pltCfg = pltCfg        
        for ax in self.axes:
            # deprecated ax.set_axis_bgcolor(self.pltCfg['background'])
            ax.set_facecolor(self.pltCfg['background'])
            plt.setp(list(ax.spines.values()), color = self.pltCfg['foreground'])
            ax.tick_params(axis='both', which='major', 
                            labelsize = self.pltCfg['fontsizeLabel'],
                            color = self.pltCfg['foreground'])
            ax.tick_params(axis='both', which='minor',
                            labelsize = self.pltCfg['fontsizeLabel'],
                            color = self.pltCfg['foreground'])

        ax = self.axes[0]
        self.x = x
        self.net = src - bkg
        self.err = np.sqrt(srcErr**2 + bkgErr**2)
        ax.step(self.x, self.net, where = "mid", color = self.pltCfg['srcLine'], lw=1.2, label = "Net Rate")
        ax.errorbar(self.x, self.net, yerr = self.err, marker = "", ls = "", capsize = 0, color = self.pltCfg['srcLine'])
        ax.set_xlim(x[0], x[-1])

        self.tStart = tStart
        self.tStop = tStop
        self.widths = widths

        self.axes[0].axhline(0, ls = "--", color = "k")

        self.axes[0].set_ylabel('Rate (counts/s)', fontsize = pltCfg['fontsize'], fontname = self.pltCfg['font'],)
        self.axes[0].set_xlabel('Time (s)', fontsize = pltCfg['fontsize'], fontname = self.pltCfg['font'],)

        leg = self.axes[0].legend()
        self.doLegend(leg)