import wx

from . import options
from . import gui_classes
from . import wx_classes
from . import orbsub
import lib

gbmConsts = lib.util.gbmVals()

def genDataMissingMessage(missingFileDictionary, internetAccess = True):
    missingFiles = ''
    if len(missingFileDictionary['pos']):
        missingFiles += 'Missing poshist Files for days:\n'
        for i in missingFileDictionary['pos']:
            missingFiles += "%s\n" %i       
    mes  = 'Error: Missing data files\n'
    mes += missingFiles

    if internetAccess:
        mes += "\nWould you like to create a download script?\n\n"
    else:
        mes += "" #You do not seem to have internet access."
    return mes

class OSV_Instance:
    ''' An instance of OSV
    '''
    def __init__(self, opts, osvParent = False):
        self.opts = opts
        self.gui = False
        self.orbsub = False
        self.log = False
    def close(self):
        if self.gui:
            self.gui.Close()
    def delete(self):
        if self.gui:
            self.gui.delete()
    def runOrbSub(self, flag_nogui = False):
        self.orbsub = orbsub.OrbSub(self.opts)
        mes = 'Running OrbSub Code:'
        mes = ' Finding Files...'
        # Locate Files
        self.orbsub.find_files()
        if self.orbsub.files.error:
            # If there was an error with finding the files let the user know. 
            if self.gui.log:
                self.gui.log.update(self.orbsub.files.errMes)            
                downloadData = self.gui.YesNoMes(genDataMissingMessage(self.orbsub.files.missingFiles, ),
                                    'Data Files not found',
                                    style =  wx.YES_NO|wx.ICON_ERROR|wx.YES_DEFAULT)
                if downloadData:
                    # create downloader instance 
                    downloader = lib.ftp.Downloader(self.orbsub.files.missingFiles, self.opts.spec_type)
                    downloader.createDownloadScript(self.opts.data_dir)
                    downloader.save()
                    mes = self.gui.ErrorMes("Download script saved in current working directory",
                                    'Download Script',
                                    style =  wx.OK)
                else:
                    self.gui.log.show(self.gui)
            else:
                print(self.orbsub.files.errMes)
            return
        else:
            self.gui.log.update(self.orbsub.files.__str__())
        # Recalculate orbit. If the new period is suitably different
        # from that the current value then orbsub.find_files() will be
        # called from inside the method. This will not be reflected in the
        # log - a message will state that it is being recalculated but 
        # if the files change this will not be stated in the log. This will
        # have to be fixed at some point.
        if self.opts.reCalcOrbit:
            mes = ' Recalculating Period ...'
            perValid = self.orbsub.calc_period()            
            if perValid:
                self.gui.log.update(self.orbsub.perMes)
            else:
                self.gui.log.update(self.orbsub.perErrMes)
                self.gui.ErrorMes('Recalculation of period ran into trouble. Please consult the log for full details',
                                  'Recalculation of period failed')
                self.gui.log.show(self.gui)
                return
        # Calculate Good Time Intervals, Occultation Steps
        # Currently get_gti calls poshist.calculate_angles(), It would be
        # nice if we could call this without necessarily calling get_gti.
        if self.opts.doGeom:
            # GTI
            gtiValid = self.orbsub.get_gti()
            if gtiValid:
               self.gui.log.update(self.orbsub.gtiMes)
            else:
                self.gui.log.update(self.orbsub.gtiErrMes)
                self.gui.ErrorMes('Calculation of G.T.I. ran into trouble. Please consult the log for full details',
                                  'Calculation of G.T.I. failed')
                self.gui.log.show(self.gui)
            # Occ Steps
            occValid = self.orbsub.get_steps()
            if occValid:
               self.gui.log.update(self.orbsub.occMes)
            else:
                self.gui.log.update(self.orbsub.occErrMes)
                self.gui.ErrorMes('Calculation of Occultation Steps ran into trouble. Please consult the log for full details',
                                  'Calculation of Occultation Steps  failed')
                self.gui.log.show(self.gui)
        # Get Backgrounds
        orbValid = self.orbsub.do_orbsub()
        if not orbValid:
                self.gui.log.update(self.orbsub.orbErrMes)
                self.gui.ErrorMes('Oribital Subtraction ran into trouble. Please consult the log for full details',
                                  'Oribital Subtraction failed')
                self.gui.log.show(self.gui)

        # All done - make make display data
        if self.gui:
            self.gui.InitData(self.orbsub)
        # Add a Flag for nogui, where the data is saved in a file (?)
        # The data is in self.orbsub.data ['b0'] like dictionary
        # initData of gui_classes extracts all the data so look there
            
    def restore(self):
        if self.gui:
            self.gui.Show()
    def dismiss(self):
        if self.gui:
            self.gui.Hide()
            
class OptDialog(wx.Dialog):
    '''
    Runtime Option Selection Dialog
    '''
    def __init__(self, parent, opts, *args, **kwargs):
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        # The code may have been run before - therefore we check if opts is
        # already defined - this could be useful if user wanted to change dets
        # whilst maintaining the same offset, tzero, etc...
        if not opts:
            self.opts = options.OSV_Args()
        else:
            self.opts = opts
        self.InitUI()
        self.InitBindings()
        self.InitVals()
        self.Centre()
    def InitUI(self):
        '''
        Layout the controls
        '''
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        # Make the labels/buttons & set defaults
        #self.panel = panel = wx.Panel(self)
        # Temporal settings
        tmpBox = wx.StaticBox(self, -1, 'Temporal Settings', 
                              )#size = (200, -1))
        tmpBoxSizer = wx.StaticBoxSizer(tmpBox, wx.VERTICAL)  
        tzoLbl = wx.StaticText(self, label="tZero (MET):",)        
        self.tzoId = wx.NewId()
        self.tzoTxt = wx.TextCtrl(self, self.tzoId, str(self.opts.tzero), size = (200, -1),
                                   validator = wx_classes.FltRangeValidator(eLabel = 'tZero', min_ = gbmConsts.minMet, max_ = gbmConsts.maxMet, ))
        tngLbl = wx.StaticText(self, label = "Negative offset (s):")
        self.tngId = wx.NewId()
        self.tngTxt = wx.TextCtrl(self, self.tngId, str(self.opts.tRange[0]),
                                  validator = wx_classes.FltRangeValidator(eLabel = 'Negative Offset', negAllowed = True))
        tpsLbl = wx.StaticText(self, label = "Positive offset (s):")
        self.tpsId = wx.NewId()        
        self.tpsTxt = wx.TextCtrl(self, self.tpsId, str(self.opts.tRange[1]),
                                  validator = wx_classes.FltRangeValidator(eLabel = 'Positive Offset', negAllowed = True))
        tmpBoxSizer.Add(tzoLbl, 0,wx.ALL, 0)
        tmpBoxSizer.Add(self.tzoTxt, 0, wx.ALL, 2)
        tmpBoxSizer.Add(tngLbl, 0, wx.ALL, 0)
        tmpBoxSizer.Add(self.tngTxt, 0, wx.ALL, 2)
        tmpBoxSizer.Add(tpsLbl, 0, wx.ALL, 0)
        tmpBoxSizer.Add(self.tpsTxt,0, wx.ALL, 2)
        # Data Directory 
        dirBox = wx.StaticBox(self, -1, 'Data Directory',)# size = (00, -1))
        dirBoxSizer = wx.StaticBoxSizer(dirBox, wx.VERTICAL)
        self.dirTxt = wx.TextCtrl(self, -1, str(self.opts.data_dir),
                                 style = wx.TE_READONLY,)# size =(400, -1))
        dirBoxSizer.Add(self.dirTxt, 0, wx.EXPAND, 5)
        # Data Type Settings: spec type & detectors
        spcBox = wx.StaticBox(self, -1, 'Data Options',)# size = (200, -1))
        spcBoxSizer = wx.StaticBoxSizer(spcBox, wx.VERTICAL)
        self.cspBtn = wx.RadioButton(self, -1, 'CSPEC')
        self.ctmBtn = wx.RadioButton(self, -1, 'CTIME')
        if self.opts.spec_type == 'CSPEC':
            self.cspBtn.SetValue(True)
        elif self.opts.spec_type == 'CTIME':
            self.ctmBtn.SetValue(True)
        self.detBtn = wx.Button(self, label = "Detector Selection")                  
        spcBoxSizer.Add(self.cspBtn)
        spcBoxSizer.Add(self.ctmBtn)
        spcBoxSizer.Add(self.detBtn, 0, wx.ALL, 0)
        # Offset box
        offBox = wx.StaticBox(self, -1, 'Background Regions',
                              size = (200, -1))
        offBoxSizer = wx.StaticBoxSizer(offBox, wx.VERTICAL)
        offTxtLbl = wx.StaticText(self, 
                                    label = "# orbits offset (space separated)")
        offTxtMes = " ".join(str(i) for i in self.opts.offset)
        self.offId = wx.NewId()
        self.offTxt = wx.TextCtrl(self, self.offId, offTxtMes,
                                     validator = wx_classes.IntsRangeValidator(eLabel = 'Orbit Offset'))
        offBoxSizer.Add(offTxtLbl, 0, wx.ALL, 0)
        offBoxSizer.Add(self.offTxt, 0, wx.ALL, 0)
        # Flag Options
        flgBox = wx.StaticBox(self, -1, 'Source Coords (Optional)',)
        flgBoxSizer = wx.StaticBoxSizer(flgBox, wx.VERTICAL)
        # self.gtiId = wx.NewId()
        # self.gtiBtn = wx.ToggleButton(self, self.gtiId,
                                    # 'Calculate G.T.I. + Occultation Steps')
        
        raLbl = wx.StaticText(self, label = "Source RA (deg):")
        self.raId = wx.NewId()
        self.raTxt = wx.TextCtrl(self, self.raId, str(self.opts.coords[0]),
                                validator = wx_classes.FltRangeValidator(eLabel = 'Right Ascension', 
                                                                         negAllowed = True,
                                                                         required = False))
        # self.raTxt.Enable(False)
        decLbl = wx.StaticText(self, label = "Source Dec (deg):")
        self.decId = wx.NewId()
        self.decTxt = wx.TextCtrl(self, self.decId, str(self.opts.coords[1]),
                                  validator = wx_classes.FltRangeValidator(eLabel = 'Declination', 
                                                                           negAllowed = True,
                                                                           required = False))
        # self.decTxt.Enable(False)
        # self.perId = wx.NewId()
        # self.perBtn = wx.ToggleButton(self, self.perId, 'Re-Calculate Period')
        # self.bkgId = wx.NewId()
        # self.bkgBtn = wx.ToggleButton(self, self.bkgId, 'No background')
        flgBoxSizer.Add(raLbl)
        flgBoxSizer.Add(self.raTxt)
        flgBoxSizer.Add(decLbl)
        flgBoxSizer.Add(self.decTxt)
        # flgBoxSizer.Add(self.gtiBtn)        
        # flgBoxSizer.Add(self.perBtn)
        # flgBoxSizer.Add(self.bkgBtn)
        # Misc Options
        mscBox = wx.StaticBox(self, -1, 'Misc. Options', 
                              size = (200, -1))
        mscBoxSizer = wx.StaticBoxSizer(mscBox, wx.VERTICAL)
        nmeLbl = wx.StaticText(self,label = "Output File Stem (Optional)")   
        self.nmeId = wx.NewId()            
        self.nmeTxt = wx.TextCtrl(self, self.nmeId, str(self.opts.name), size = (200, -1))
        mscBoxSizer.Add(nmeLbl, 0, wx.EXPAND, 0)
        mscBoxSizer.Add(self.nmeTxt, 0, wx.EXPAND, 0)       
                 
        # ok/cancel buttons
        okb = wx.Button(self, wx.ID_OK)
        cancelb = wx.Button(self, wx.ID_CANCEL)
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)# 5, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        btnsizer.Add(okb, 0, wx.EXPAND, 0)
        btnsizer.Add(cancelb, 0, wx.EXPAND, 0)

        #Fill sizer
        sizerSpacing = 10
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(tmpBoxSizer, 0, wx.ALL|wx.EXPAND, 0)
        sizer.AddSpacer(sizerSpacing) 
        sizer.Add(dirBoxSizer, 0, wx.EXPAND, 0)
        sizer.AddSpacer(sizerSpacing) 
        sizer.Add(spcBoxSizer, 0, wx.ALL|wx.EXPAND, 0)
        sizer.AddSpacer(sizerSpacing) 
        sizer.Add(offBoxSizer, 0, wx.ALL|wx.EXPAND, 0)
        sizer.AddSpacer(sizerSpacing) 
        sizer.Add(flgBoxSizer, 0, wx.ALL|wx.EXPAND, 0)
        sizer.AddSpacer(sizerSpacing) 
        sizer.Add(mscBoxSizer, 0, wx.ALL|wx.EXPAND, 0)
        sizer.AddSpacer(sizerSpacing) 
        sizer.Add(btnsizer, 0, wx.ALL|wx.CENTER, 0)
        sizer.AddSpacer(sizerSpacing) 
        #! Awful hack to stop ok/cancel buttons being cutoff
        #! TODO Fix this god forsaken hack
        dim = 40
        if "__WXMSW__" in wx.Platform:
            dim = 0
        sizer.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, dim)
        sizer.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, dim)
        sizer.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, dim)        
        sizer.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, dim)        
        
        # Finally assign the main outer sizer to the panel
        self.SetSizer(sizer)
        self.SetInitialSize()

    def InitBindings(self):
        ''' Bind methods to buttons '''
        self.dirTxt.Bind(wx.EVT_LEFT_DOWN, self.DirectoryDialog)
        self.Bind(wx.EVT_RADIOBUTTON,self.SpecSelect, self.cspBtn)
        self.Bind(wx.EVT_RADIOBUTTON,self.SpecSelect, self.ctmBtn)
        self.Bind(wx.EVT_BUTTON, self.DetectorDialog, self.detBtn) 
        self.Bind(wx.EVT_TEXT, self.TypeFloat, self.tzoTxt) 
        self.Bind(wx.EVT_TEXT, self.TypeFloat, self.tngTxt) 
        self.Bind(wx.EVT_TEXT, self.TypeFloat, self.tpsTxt) 
        self.Bind(wx.EVT_TEXT, self.TypeList, self.offTxt) 
        self.Bind(wx.EVT_TEXT, self.TypeFloat, self.raTxt) 
        self.Bind(wx.EVT_TEXT, self.TypeFloat, self.decTxt) 
        self.Bind(wx.EVT_TEXT, self.TypeString, self.nmeTxt)
        # self.Bind(wx.EVT_TOGGLEBUTTON, self.TypeBool, self.perBtn) 
        # self.Bind(wx.EVT_TOGGLEBUTTON, self.TypeBool, self.gtiBtn) 
        # self.Bind(wx.EVT_TOGGLEBUTTON, self.TypeBool, self.bkgBtn) 
             
    def InitVals(self):
        ''' Set options to starting values '''        
        
    def TypeString(self,event):
        id = event.GetId()
        if id == self.nmeId:
            self.opts.name = self.nmeTxt.GetValue()
    def TypeList(self,event):
        id = event.GetId()
        if id == self.offId:
            self.opts.offset = self.offTxt.GetValue().split()
    def TypeFloat(self,event):
        id = event.GetId()
        if id == self.tzoId:
            self.opts.tzero = self.tzoTxt.GetValue()
        elif id == self.tngId:
            self.opts.tRange[0] = self.tngTxt.GetValue()
        elif id == self.tpsId:
            self.opts.tRange[1] = self.tpsTxt.GetValue()
        elif id == self.raId:
            self.opts.coords[0] = self.raTxt.GetValue()
        elif id == self.decId:
            self.opts.coords[1] = self.decTxt.GetValue()
    def TypeBool(self, event):
        id = event.GetId()
        # if id == self.perId:
        #     self.opts.reCalcOrbit =  self.perBtn.GetValue()
        # elif id == self.bkgId:
        #     self.opts.doBack = self.bkgBtn.GetValue()
        # elif id == self.gtiId:
            # self.GeomSelect(self.gtiBtn.GetValue())
    def GeomSelect(self, boolVal):
        if boolVal:
            # self.raTxt.Enable(True)
            # self.decTxt.Enable(True)
            self.opts.doGeom = True
        else:
            # self.raTxt.Enable(False)
            # self.decTxt.Enable(False)
            self.opts.doGeom = False
    def SpecSelect(self,event):
        if self.cspBtn.GetValue():
            self.opts.spec_type = 'CSPEC'
        elif self.ctmBtn.GetValue():
            self.opts.spec_type = 'CTIME'
    def DirectoryDialog(self, event):
        '''Directory Selection Dialog'''
        dlg = wx.DirDialog(self, "Choose a folder")
        if dlg.ShowModal() == wx.ID_OK:
            self.dirTxt.SetValue(dlg.GetPath())
            self.opts.data_dir = dlg.GetPath()
        dlg.Destroy()
    def DetectorDialog(self, event):
        dlg = DetDialog(self, self.opts, title = "Detector Selection")
        dlg.Centre()
        dets = []
        if dlg.ShowModal() == wx.ID_OK:
            for i in range(0,14):
                label = dlg.labels[i]
                if dlg.btns[label].GetValue() == True:
                    dets.append(dlg.dets[i])
        self.opts.dets = dets
        dlg.Destroy()
        
class DetDialog(wx.Dialog):
    '''
    GBM Detector Selection Dialog
    '''
    def __init__(self, parent, opts,*args, **kwargs):
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        # Attributes
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.btn0 = wx.ToggleButton(self, -1, 'NaI 0', (20,25 ), (-1,25))
        self.btn1 = wx.ToggleButton(self, -1, 'NaI 1', (20,50 ), (-1,25))
        self.btn2 = wx.ToggleButton(self, -1, 'NaI 2', (20,75 ), (-1,25))
        self.btn3 = wx.ToggleButton(self, -1, 'NaI 3', (20,100), (-1,25))
        self.btn4 = wx.ToggleButton(self, -1, 'NaI 4', (20,125), (-1,25))
        self.btn5 = wx.ToggleButton(self, -1, 'NaI 5', (20,150), (-1,25))
        self.btn6 = wx.ToggleButton(self, -1, 'NaI 6', (20,175), (-1,25))
        self.btn7 = wx.ToggleButton(self, -1, 'NaI 7', (20,200), (-1,25))
        self.btn8 = wx.ToggleButton(self, -1, 'NaI 8', (20,225), (-1,25))
        self.btn9 = wx.ToggleButton(self, -1, 'NaI 9', (20,250), (-1,25))
        self.btna = wx.ToggleButton(self, -1, 'NaI A', (20,275), (-1,25))
        self.btnb = wx.ToggleButton(self, -1, 'NaI B', (20,300), (-1,25))
        self.btnA = wx.ToggleButton(self, -1, 'BGO 0', (20,325), (-1,25))
        self.btnB = wx.ToggleButton(self, -1, 'BGO 1', (20,350), (-1,25))
        self.btnAll = wx.ToggleButton(self, -1, 'All', (20,350), (-1,25))
        self.btnNone = wx.ToggleButton(self, -1, 'None', (20,350), (-1,25))
        self.btns = [self.btn0, self.btn1, self.btn2, self.btn3, self.btn4,
                     self.btn5, self.btn6, self.btn7, self.btn8, self.btn9,
                     self.btna, self.btnb, self.btnA, self.btnB]
        self.labels = ['NaI 0', 'NaI 1', 'NaI 2', 'NaI 3', 'NaI 4', 'NaI 5', 
                       'NaI 6', 'NaI 7', 'NaI 8', 'NaI 9', 'NaI A', 'NaI B', 
                       'BGO 0', 'BGO 1']
        self.dets = ['n0', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8', 'n9',
                     'na', 'nb', 'b0', 'b1']
        self.btns = {'NaI 0': self.btn0, 'NaI 1': self.btn1, 'NaI 2': self.btn2, 
                     'NaI 3': self.btn3, 'NaI 4': self.btn4, 'NaI 5': self.btn5,
                     'NaI 6': self.btn6, 'NaI 7': self.btn7, 'NaI 8': self.btn8,
                     'NaI 9': self.btn9, 'NaI A': self.btna, 'NaI B': self.btnb,
                     'BGO 0': self.btnA, 'BGO 1': self.btnB}

        for det in self.dets:
            if det in opts.dets:
                det_lbl = self.labels[self.dets.index(det)]
                self.btns[det_lbl].SetValue(True)
        # Layout
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer1.Add(self.btn0, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer1.Add(self.btn6, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add(self.btn1, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer2.Add(self.btn7, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer3 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer3.Add(self.btn2, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer3.Add(self.btn8, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer4 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer4.Add(self.btn3, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer4.Add(self.btn9, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)        
        hsizer5 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer5.Add(self.btn4, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer5.Add(self.btna, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer6 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer6.Add(self.btn5, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer6.Add(self.btnb, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer7 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer7.Add(self.btnA, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer7.Add(self.btnB, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer8 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer8.Add(self.btnAll, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        hsizer8.Add(self.btnNone, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)

        #Add Detector butttons to Sizers
        sizer.Add(hsizer1, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(hsizer2, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(hsizer3, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(hsizer4, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(hsizer5, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(hsizer6, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(hsizer7, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(hsizer8, 0, wx.EXPAND|wx.ALL, 5)

        #Detector Button Bindings
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getAll, id=self.btnAll.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getNone, id=self.btnNone.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btn0.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btn1.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btn2.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btn3.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btn4.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btn5.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btn6.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btn7.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btn8.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btn9.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btna.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btnb.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btnA.GetId())
        self.Bind(wx.EVT_TOGGLEBUTTON, self.getOne, id=self.btnB.GetId())

        # Add some buttons to the dialog
        okb = wx.Button(self, wx.ID_OK)
        #cancelb = wx.Button(self, wx.ID_CANCEL)
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add(okb, 5, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        #btnsizer.Add(cancelb, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        #btnsizer = wx.StdDialogButtonSizer()
        sizer.Add(btnsizer, 0, wx.EXPAND|wx.ALL, 10)
        #sizer.Add(btnsizer, 0, wx.ALL|wx.ALIGN_RIGHT, 8)
        self.SetSizer(sizer)
        self.SetInitialSize()
    def getOne(self,event):
        '''Individual Detector Selected, set None & all buttons to False'''
        self.btnNone.SetValue(False)
        self.btnAll.SetValue(False)
    def getAll(self,event):
        '''Set All Detectors to True, set None button to False'''
        self.btn0.SetValue(True)
        self.btn1.SetValue(True)
        self.btn2.SetValue(True)
        self.btn3.SetValue(True)
        self.btn4.SetValue(True)
        self.btn5.SetValue(True)
        self.btn6.SetValue(True)
        self.btn7.SetValue(True)
        self.btn8.SetValue(True)
        self.btn9.SetValue(True)
        self.btna.SetValue(True)
        self.btnb.SetValue(True)
        self.btnA.SetValue(True)
        self.btnB.SetValue(True)
        self.btnNone.SetValue(False)
    def getNone(self,event):
        '''Set All Decectors to False, set All button to False'''
        self.btn0.SetValue(False)
        self.btn1.SetValue(False)
        self.btn2.SetValue(False)
        self.btn3.SetValue(False)
        self.btn4.SetValue(False)
        self.btn5.SetValue(False)
        self.btn6.SetValue(False)
        self.btn7.SetValue(False)
        self.btn8.SetValue(False)
        self.btn9.SetValue(False)
        self.btna.SetValue(False)
        self.btnb.SetValue(False)
        self.btnA.SetValue(False)
        self.btnB.SetValue(False)
        self.btnAll.SetValue(False)

class RebinDialog(wx.Dialog):
    def __init__(self, parent, *args, **kwargs):
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        tmpBox = wx.StaticBox(self, -1, 'Resolution', 
                              )#size = (200, -1))
        tmpBoxSizer = wx.StaticBoxSizer(tmpBox, wx.VERTICAL)  
        self.resId = wx.NewId()
        self.resTxt = wx.TextCtrl(self, self.resId, '', size = (200, -1),
                                   validator = wx_classes.FltRangeValidator(eLabel = 'resolution',))
        
        tmpBoxSizer.Add(self.resTxt, 0,wx.ALL, 0)
        
        okb = wx.Button(self, wx.ID_OK)
        cancelb = wx.Button(self, wx.ID_CANCEL)
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add(okb, 5, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        btnsizer.Add(cancelb, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(tmpBoxSizer, 0, wx.ALL|wx.EXPAND, 0)
        sizer.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(btnsizer, 0, wx.ALL|wx.CENTER, 0)
        # Finally assign the main outer sizer to the panel
        self.SetSizer(sizer)
        self.SetInitialSize()
