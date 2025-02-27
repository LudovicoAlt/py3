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
    def runOrbSub(self, flag_nogui=False):
        """
        Run the orbital subtraction analysis.
        
        This method manages the full workflow:
        1. Finding files
        2. Recalculating orbit (optional)
        3. Getting GTI and occultation steps
        4. Performing orbital subtraction
        5. Initializing data display
        
        Args:
            flag_nogui (bool): If True, run without GUI feedback
        """
        try:
            # Initialize orbital subtraction object
            self.orbsub = orbsub.OrbSub(self.opts)
            
            # Step 1: Find necessary files
            self.orbsub.find_files()
            
            # Handle missing files
            if self.orbsub.files.error:
                return self._handle_missing_files()
            elif self.gui and self.gui.log:
                self.gui.log.update(self.orbsub.files.__str__())
                
            # Step 2: Recalculate orbit if requested
            if self.opts.reCalcOrbit and not self._recalculate_orbit():
                return
                
            # Step 3: Calculate geometry (GTI and occultation steps)
            if self.opts.doGeom and not self._calculate_geometry():
                return
                
            # Step 4: Perform orbital subtraction
            if not self._perform_orbital_subtraction():
                return
                
            # Step 5: Initialize data display if GUI is available
            if self.gui:
                self.gui.InitData(self.orbsub)
                
        except Exception as e:
            import traceback
            error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            if self.gui and self.gui.log:
                self.gui.log.update(error_msg)
                self.gui.ErrorMes("An unexpected error occurred. Check log for details.",
                                "Error in Orbital Subtraction")
            else:
                print(error_msg)
            
    def _handle_missing_files(self):
        """Handle missing files with appropriate user interaction."""
        if not self.gui or not self.gui.log:
            print(self.orbsub.files.errMes)
            return False
        
        # Update log with error message
        self.gui.log.update(self.orbsub.files.errMes)
        
        # Ask user if they want to download missing files
        message = genDataMissingMessage(self.orbsub.files.missingFiles)
        downloadData = self.gui.YesNoMes(message, 'Data Files not found',
                            style=wx.YES_NO|wx.ICON_ERROR|wx.YES_DEFAULT)
                            
        if downloadData:
            # Create downloader instance
            downloader = lib.ftp.Downloader(self.orbsub.files.missingFiles, self.opts.spec_type)
            
            # Generate Python download script instead of shell script
            try:
                # If createPythonDownloadScript method exists, use it
                if hasattr(downloader, 'createPythonDownloadScript'):
                    downloader.createPythonDownloadScript(self.opts.data_dir)
                    msg = "Python download script (download.py) saved in current directory"
                else:
                    # Fall back to shell script
                    downloader.createDownloadScript(self.opts.data_dir)
                    downloader.save()
                    msg = "Download script saved in current working directory"
                    
                # Show confirmation message (won't close the app)
                self.gui.ErrorMes(msg, 'Download Script', style=wx.OK)
            except Exception as e:
                self.gui.ErrorMes(f"Error creating download script: {str(e)}",
                                'Download Script Error', style=wx.OK|wx.ICON_ERROR)
        else:
            # Show the log with error messages
            self.gui.log.show(self.gui)
            
        return False
        
    def _recalculate_orbit(self):
        """Recalculate orbit period if requested."""
        if not self.gui or not self.gui.log:
            return self.orbsub.calc_period()
            
        perValid = self.orbsub.calc_period()
        
        if perValid:
            self.gui.log.update(self.orbsub.perMes)
            return True
        else:
            self.gui.log.update(self.orbsub.perErrMes)
            self.gui.ErrorMes('Recalculation of period ran into trouble. Please consult the log for full details',
                            'Recalculation of period failed')
            self.gui.log.show(self.gui)
            return False
        
    def _calculate_geometry(self):
        """Calculate GTI and occultation steps."""
        if not self.gui or not self.gui.log:
            return (self.orbsub.get_gti() and self.orbsub.get_steps())
            
        # Calculate GTI
        gtiValid = self.orbsub.get_gti()
        if gtiValid:
            self.gui.log.update(self.orbsub.gtiMes)
        else:
            self.gui.log.update(self.orbsub.gtiErrMes)
            self.gui.ErrorMes('Calculation of G.T.I. ran into trouble. Please consult the log for full details',
                            'Calculation of G.T.I. failed')
            self.gui.log.show(self.gui)
            return False
        
        # Calculate occultation steps    
        occValid = self.orbsub.get_steps()
        if occValid:
            self.gui.log.update(self.orbsub.occMes)
            return True
        else:
            self.gui.log.update(self.orbsub.occErrMes)
            self.gui.ErrorMes('Calculation of Occultation Steps ran into trouble. Please consult the log for full details',
                            'Calculation of Occultation Steps failed')
            self.gui.log.show(self.gui)
            return False
        
    def _perform_orbital_subtraction(self):
        """Perform the orbital subtraction."""
        if not self.gui or not self.gui.log:
            return self.orbsub.do_orbsub()
            
        orbValid = self.orbsub.do_orbsub()
        if orbValid:
            return True
        else:
            self.gui.log.update(self.orbsub.orbErrMes)
            self.gui.ErrorMes('Orbital Subtraction ran into trouble. Please consult the log for full details',
                            'Orbital Subtraction failed')
            self.gui.log.show(self.gui)
            return False
    
class OptDialog(wx.Dialog):
    '''
    Runtime Option Selection Dialog - Cross-Platform Implementation
    '''
    def __init__(self, parent, opts, *args, **kwargs):
        # Set a better default size that works across platforms
        if 'size' not in kwargs:
            kwargs['size'] = wx.Size(400, -1)
        
        # Add style for resizable dialog
        if 'style' not in kwargs:
            kwargs['style'] = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        else:
            kwargs['style'] |= wx.RESIZE_BORDER

        wx.Dialog.__init__(self, parent, *args, **kwargs)
        
        # Set up options object
        if not opts:
            self.opts = options.OSV_Args()
        else:
            self.opts = opts
            
        self.InitUI()
        self.InitBindings()
        self.InitVals()
        
        # Center the dialog on parent
        self.Centre()
        
        # Set a minimum size to prevent controls from being squished
        self.SetMinSize(wx.Size(380, -1))

    def InitUI(self):
        '''
        Layout the controls with proper cross-platform support
        '''
        # Create the main panel which will contain all controls
        panel = wx.Panel(self)
        
        # Main vertical sizer for all content
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # -----------------------------------
        # Temporal settings
        # -----------------------------------
        temp_box = wx.StaticBox(panel, label='Temporal Settings')
        temp_sizer = wx.StaticBoxSizer(temp_box, wx.VERTICAL)
        
        # TZero control
        tzo_label = wx.StaticText(panel, label="tZero (MET):")
        self.tzoId = wx.NewId()
        self.tzoTxt = wx.TextCtrl(
            panel, 
            id=self.tzoId,
            value=str(self.opts.tzero),
            validator=wx_classes.FltRangeValidator(
                eLabel='tZero', 
                min_=gbmConsts.minMet, 
                max_=gbmConsts.maxMet
            )
        )
        
        # Date/Time control 
        date_label = wx.StaticText(panel, label="Or enter date (YYYY-MM-DD HH:MM:SS.fff):")
        self.dateId = wx.NewId()
        self.dateTxt = wx.TextCtrl(panel, id=self.dateId)

        # Create a horizontal sizer for the date control with a Convert button
        date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        date_sizer.Add(self.dateTxt, 1, wx.EXPAND|wx.RIGHT, 5)
        self.dateBtn = wx.Button(panel, label="Convert", size=wx.Size(70, -1))
        date_sizer.Add(self.dateBtn, 0)

        temp_sizer.Add(date_label, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)
        temp_sizer.Add(date_sizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        # Negative offset control
        tng_label = wx.StaticText(panel, label="Negative offset (s):")
        self.tngId = wx.NewId()
        self.tngTxt = wx.TextCtrl(
            panel, 
            id=self.tngId,
            value=str(self.opts.tRange[0]),
            validator=wx_classes.FltRangeValidator(
                eLabel='Negative Offset', 
                negAllowed=True
            )
        )
        
        # Positive offset control
        tps_label = wx.StaticText(panel, label="Positive offset (s):")
        self.tpsId = wx.NewId()
        self.tpsTxt = wx.TextCtrl(
            panel, 
            id=self.tpsId,
            value=str(self.opts.tRange[1]),
            validator=wx_classes.FltRangeValidator(
                eLabel='Positive Offset',
                negAllowed=True
            )
        )
        
        # Add controls to the temporal sizer with consistent spacing
        for label, ctrl in [(tzo_label, self.tzoTxt), 
                           (tng_label, self.tngTxt), 
                           (tps_label, self.tpsTxt)]:
            temp_sizer.Add(label, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)
            temp_sizer.Add(ctrl, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
            
        # -----------------------------------
        # Data Directory
        # -----------------------------------
        dir_box = wx.StaticBox(panel, label='Data Directory')
        dir_sizer = wx.StaticBoxSizer(dir_box, wx.VERTICAL)
        
        self.dirTxt = wx.TextCtrl(
            panel, 
            value=str(self.opts.data_dir),
            style=wx.TE_READONLY
        )
        
        dir_sizer.Add(self.dirTxt, 0, wx.EXPAND|wx.ALL, 5)
        
        # -----------------------------------
        # Data Type Settings
        # -----------------------------------
        data_box = wx.StaticBox(panel, label='Data Options')
        data_sizer = wx.StaticBoxSizer(data_box, wx.VERTICAL)
        
        # Radio button group for data type
        radio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cspBtn = wx.RadioButton(panel, label='CSPEC')
        self.ctmBtn = wx.RadioButton(panel, label='CTIME')
        
        if self.opts.spec_type == 'CSPEC':
            self.cspBtn.SetValue(True)
        else:
            self.ctmBtn.SetValue(True)
            
        radio_sizer.Add(self.cspBtn, 0, wx.RIGHT, 15)
        radio_sizer.Add(self.ctmBtn, 0)
        
        # Detector selection button
        self.detBtn = wx.Button(panel, label="Detector Selection")
        
        data_sizer.Add(radio_sizer, 0, wx.ALL, 5)
        data_sizer.Add(self.detBtn, 0, wx.EXPAND|wx.ALL, 5)
        
        # -----------------------------------
        # Background Regions
        # -----------------------------------
        orbit_box = wx.StaticBox(panel, label='Background Regions')
        orbit_sizer = wx.StaticBoxSizer(orbit_box, wx.VERTICAL)
        
        orbit_label = wx.StaticText(panel, label="# orbits offset (space separated)")
        orbit_value = " ".join(str(i) for i in self.opts.offset)
        
        self.offId = wx.NewId()
        self.offTxt = wx.TextCtrl(
            panel,
            id=self.offId,
            value=orbit_value,
            validator=wx_classes.IntsRangeValidator(eLabel='Orbit Offset')
        )
        
        orbit_sizer.Add(orbit_label, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)
        orbit_sizer.Add(self.offTxt, 0, wx.EXPAND|wx.ALL, 5)
        
        # -----------------------------------
        # Source Coordinates
        # -----------------------------------
        src_box = wx.StaticBox(panel, label='Source Coords (Optional)')
        src_sizer = wx.StaticBoxSizer(src_box, wx.VERTICAL)
        
        # Right Ascension
        ra_label = wx.StaticText(panel, label="Source RA (deg):")
        self.raId = wx.NewId()
        self.raTxt = wx.TextCtrl(
            panel,
            id=self.raId,
            value=str(self.opts.coords[0]),
            validator=wx_classes.FltRangeValidator(
                eLabel='Right Ascension',
                negAllowed=True,
                required=False
            )
        )
        
        # Declination
        dec_label = wx.StaticText(panel, label="Source Dec (deg):")
        self.decId = wx.NewId()
        self.decTxt = wx.TextCtrl(
            panel,
            id=self.decId,
            value=str(self.opts.coords[1]),
            validator=wx_classes.FltRangeValidator(
                eLabel='Declination',
                negAllowed=True,
                required=False
            )
        )
        
        # Add coordinates to sizer
        for label, ctrl in [(ra_label, self.raTxt), (dec_label, self.decTxt)]:
            src_sizer.Add(label, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)
            src_sizer.Add(ctrl, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        
        # -----------------------------------
        # Misc Options
        # -----------------------------------
        misc_box = wx.StaticBox(panel, label='Misc. Options')
        misc_sizer = wx.StaticBoxSizer(misc_box, wx.VERTICAL)
        
        name_label = wx.StaticText(panel, label="Output File Stem (Optional)")
        self.nmeId = wx.NewId()
        self.nmeTxt = wx.TextCtrl(panel, id=self.nmeId, value=str(self.opts.name))
        
        misc_sizer.Add(name_label, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)
        misc_sizer.Add(self.nmeTxt, 0, wx.EXPAND|wx.ALL, 5)
        
        # -----------------------------------
        # OK/Cancel Buttons (using standard button sizer)
        # -----------------------------------
        btn_sizer = wx.StdDialogButtonSizer()
        ok_button = wx.Button(panel, wx.ID_OK)
        cancel_button = wx.Button(panel, wx.ID_CANCEL)
        
        btn_sizer.AddButton(ok_button)
        btn_sizer.AddButton(cancel_button)
        btn_sizer.Realize()
        
        # -----------------------------------
        # Putting it all together
        # -----------------------------------
        # Add all sections to the main sizer with consistent spacing
        sections = [
            temp_sizer, dir_sizer, data_sizer, 
            orbit_sizer, src_sizer, misc_sizer
        ]
        
        for section in sections:
            main_sizer.Add(section, 0, wx.EXPAND|wx.ALL, 5)
            
        # Add the buttons at the bottom
        main_sizer.Add(btn_sizer, 0, wx.EXPAND|wx.ALL, 10)
        
        # Set the panel's sizer
        panel.SetSizer(main_sizer)
        
        # Create a frame sizer to properly fit the panel
        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(frame_sizer)
        
        # Size everything properly
        panel.Fit()
        self.Fit()
        
    def InitBindings(self):
        ''' Bind methods to buttons and control events '''
        self.dirTxt.Bind(wx.EVT_LEFT_DOWN, self.DirectoryDialog)
        self.Bind(wx.EVT_RADIOBUTTON, self.SpecSelect, self.cspBtn)
        self.Bind(wx.EVT_RADIOBUTTON, self.SpecSelect, self.ctmBtn)
        self.Bind(wx.EVT_BUTTON, self.DetectorDialog, self.detBtn) 
        self.Bind(wx.EVT_BUTTON, self.ConvertDate, self.dateBtn)

        # Text change events
        text_bindings = [
            (self.tzoTxt, self.TypeFloat),
            (self.tngTxt, self.TypeFloat),
            (self.tpsTxt, self.TypeFloat),
            (self.offTxt, self.TypeList),
            (self.raTxt, self.TypeFloat),
            (self.decTxt, self.TypeFloat),
            (self.nmeTxt, self.TypeString)
        ]
        
        for ctrl, handler in text_bindings:
            self.Bind(wx.EVT_TEXT, handler, ctrl)
             
    def InitVals(self):
        ''' Set options to starting values - placeholder for future functionality '''
        pass
    
    # Helper methods remain the same
    def TypeString(self, event):
        id = event.GetId()
        if id == self.nmeId:
            self.opts.name = self.nmeTxt.GetValue()
            
    def TypeList(self, event):
        id = event.GetId()
        if id == self.offId:
            self.opts.offset = self.offTxt.GetValue().split()
            
    def TypeFloat(self, event):
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
        # Reserved for future toggle button functionality
        pass
        
    def GeomSelect(self, boolVal):
        self.opts.doGeom = boolVal
        
    def SpecSelect(self, event):
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
        dlg = DetDialog(self, self.opts, title="Detector Selection")
        dlg.Centre()
        dets = []
        if dlg.ShowModal() == wx.ID_OK:
            for i in range(0, 14):
                label = dlg.labels[i]
                if dlg.btns[label].GetValue():
                    dets.append(dlg.dets[i])
        self.opts.dets = dets
        dlg.Destroy()

    def ConvertDate(self, event):
        """Convert date string to MET and update tZero field"""
        try:
            # Get date string from text control
            date_str = self.dateTxt.GetValue().strip()
            
            # Make sure the date string matches expected format
            if not date_str:
                wx.MessageBox("Please enter a date in the format YYYY-MM-DD HH:MM:SS.fff", 
                            "Invalid Date Format", wx.ICON_ERROR)
                return
                
            # Try to convert the date string to MET
            from lib.util import date_to_met
            met = date_to_met(date_str)
            
            # Update the MET field
            self.tzoTxt.SetValue(str(met))
            self.opts.tzero = met
            
            # Show success message
            wx.MessageBox(f"Date converted to MET: {met}", 
                        "Conversion Successful", wx.ICON_INFORMATION)
                        
        except ValueError as e:
            # Show error if the date format is invalid
            wx.MessageBox(f"Invalid date format: {str(e)}\n\nPlease use YYYY-MM-DD HH:MM:SS.fff", 
                        "Date Format Error", wx.ICON_ERROR)
        except Exception as e:
            # Handle other errors
            wx.MessageBox(f"Error converting date: {str(e)}", 
                        "Conversion Error", wx.ICON_ERROR)
        
class DetDialog(wx.Dialog):
    '''
    GBM Detector Selection Dialog - Cross-platform implementation
    '''
    def __init__(self, parent, opts, *args, **kwargs):
        if 'style' not in kwargs:
            kwargs['style'] = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        else:
            kwargs['style'] |= wx.RESIZE_BORDER

        wx.Dialog.__init__(self, parent, *args, **kwargs)
        
        # Define detector information
        self.labels = ['NaI 0', 'NaI 1', 'NaI 2', 'NaI 3', 'NaI 4', 'NaI 5', 
                       'NaI 6', 'NaI 7', 'NaI 8', 'NaI 9', 'NaI A', 'NaI B', 
                       'BGO 0', 'BGO 1']
        self.dets = ['n0', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8', 'n9',
                     'na', 'nb', 'b0', 'b1']
        
        # Create a main vertical sizer for the dialog
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create a grid sizer for the detector toggle buttons - 2 columns
        grid_sizer = wx.GridSizer(rows=8, cols=2, vgap=5, hgap=10)
        
        # Create toggle buttons for each detector
        self.btns = {}
        for i, label in enumerate(self.labels):
            btn = wx.ToggleButton(self, -1, label)
            self.btns[label] = btn
            
            # Set initial state based on selected detectors
            if self.dets[i] in opts.dets:
                btn.SetValue(True)
            
            # Add to grid sizer
            grid_sizer.Add(btn, 0, wx.EXPAND)
            
            # Bind event handler
            btn.Bind(wx.EVT_TOGGLEBUTTON, self.getOne)
        
        # Add All/None buttons in the last row
        self.btnAll = wx.ToggleButton(self, -1, 'All')
        self.btnNone = wx.ToggleButton(self, -1, 'None')
        
        # Bind All/None events
        self.btnAll.Bind(wx.EVT_TOGGLEBUTTON, self.getAll)
        self.btnNone.Bind(wx.EVT_TOGGLEBUTTON, self.getNone)
        
        # Add All/None buttons to grid
        grid_sizer.Add(self.btnAll, 0, wx.EXPAND)
        grid_sizer.Add(self.btnNone, 0, wx.EXPAND)
        
        # Add grid sizer to main sizer with border
        main_sizer.Add(grid_sizer, 0, wx.ALL|wx.EXPAND, 10)
        
        # Add separator line
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        
        # Create standard button sizer for consistent button layout
        btn_sizer = wx.StdDialogButtonSizer()
        ok_button = wx.Button(self, wx.ID_OK)
        btn_sizer.AddButton(ok_button)
        btn_sizer.Realize()
        
        # Add button sizer with padding
        main_sizer.Add(btn_sizer, 0, wx.ALL|wx.EXPAND, 10)
        
        # Set the sizer and fit the dialog to its contents
        self.SetSizer(main_sizer)
        self.Fit()
        self.Centre()
    
    def getOne(self, event):
        '''Individual Detector Selected, set None & all buttons to False'''
        self.btnNone.SetValue(False)
        self.btnAll.SetValue(False)
    
    def getAll(self, event):
        '''Set All Detectors to True, set None button to False'''
        for label in self.labels:
            self.btns[label].SetValue(True)
        self.btnNone.SetValue(False)
    
    def getNone(self, event):
        '''Set All Detectors to False, set All button to False'''
        for label in self.labels:
            self.btns[label].SetValue(False)
        self.btnAll.SetValue(False)

class RebinDialog(wx.Dialog):
    def __init__(self, parent, *args, **kwargs):
        if 'style' not in kwargs:
            kwargs['style'] = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        else:
            kwargs['style'] |= wx.RESIZE_BORDER            

        wx.Dialog.__init__(self, parent, *args, **kwargs)
        
        # Create panel to contain all controls
        panel = wx.Panel(self)
        
        # Create box sizers with proper padding
        tmpBox = wx.StaticBox(panel, label='Resolution')
        tmpBoxSizer = wx.StaticBoxSizer(tmpBox, wx.VERTICAL)  
        
        # Create resolution text control with validator
        self.resId = wx.NewId()
        self.resTxt = wx.TextCtrl(
            panel, 
            id=self.resId, 
            value='',
            validator=wx_classes.FltRangeValidator(eLabel='resolution')
        )
        
        # Add text control with proper padding
        tmpBoxSizer.Add(self.resTxt, 0, wx.EXPAND|wx.ALL, 5)
        
        # Create standard button sizer for OK/Cancel buttons
        btn_sizer = wx.StdDialogButtonSizer()
        ok_button = wx.Button(panel, wx.ID_OK)
        cancel_button = wx.Button(panel, wx.ID_CANCEL)
        btn_sizer.AddButton(ok_button)
        btn_sizer.AddButton(cancel_button)
        btn_sizer.Realize()
        
        # Main vertical sizer for panel
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(tmpBoxSizer, 0, wx.EXPAND|wx.ALL, 10)
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND|wx.ALL, 10)
        
        # Set the panel's sizer
        panel.SetSizer(main_sizer)
        
        # Frame sizer to contain the panel
        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(frame_sizer)
        
        # Size everything properly
        panel.Fit()
        self.Fit()
        self.Centre()

