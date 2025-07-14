#!/usr/bin/python -tt
"""OSV Application - Orbital Subtraction Tool"""

import sys
import time
from pathlib import Path

import wx

import lib
import lib.osv_classes as osv_classes
import lib.gui_classes as gui_classes
import lib.dep_ver_checker as setup

__version__ = "1.3"

class OSV(wx.App):
    """Main OSV Application class"""

    def OnInit(self,):
        return True
    
    def OnLaunch(self, opts = None):
        """Launch application with optional command line options""" 
        if opts is None:
            self.OnNew()
        else:
            self.createInstance(opts)
        return True        
    
    def OnNew(self):
        """Show options dialog and create instance"""
        with osv_classes.OptDialog(None, False, title="OSV Options") as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
                
            self.opts = dlg.opts
            self.opts.check()
            
            if self.opts.error:
                self._show_dialog(self.opts.err_mes)
                return
            elif self.opts.warnAll and self.opts.warning:
                self._show_dialog(self.opts.warning_mes, title='Warnings')
                
            self.createInstance(dlg.opts)
    
    def createInstance(self, opts):
        ''' 
        Create instance of OSV GUI & run with given options
        '''
        timestamp = time.strftime("%H:%M:%S", time.gmtime())   
        inst = osv_classes.OSV_Instance(opts)
        title = '%s @ %s' %(inst.opts.name, timestamp)
        
        inst.gui = gui_classes.OrbsubGUI(
            None, -1, 
            title = title,
             plotDimensions = (2,1,)
        )
        inst.gui.log.update(str(opts)) 
        inst.runOrbSub()
        return inst #add a return, shouldn't break anything 

    def _show_dialog(self, message, title='Error encountered'):
        """Show message dialog"""
        wx.MessageBox(message, title, style=wx.OK | wx.ICON_ERROR)

    # Alias for backward compatibility
    DialogBox = _show_dialog

class CommandHandler:
    """Handle command line operations"""
    
    COMMANDS = {
        'doconfig'  : setup.doConfig,
        'getdata'   : lambda: lib.getData.main(argv=sys.argv[2:]),
        'checkdeps' : setup.doCheckDeps,
        'checkvers' : setup.doCheckVersions,
        'getconfig' : lambda: setup.getConfig(printflag=True),
        'convert'   : '_handle_convert',
        'ver'       : lambda: print(f"osv v{__version__}"),
        'version'   : lambda: print(f"osv v{__version__}")
    }
    
    @staticmethod
    def _handle_convert():
        """Handle date to MET conversion"""
        args = sys.argv[1:]
        if len(args) <= 1:
            print("Usage: python osv.py convert YYYY-MM-DD [hh:mm:ss[.f]]")
            print("Examples:")
            print("  python osv.py convert 2023-05-15")
            print("  python osv.py convert \"2023-05-15 14:30\"")
            print("  python osv.py convert \"2023-05-15 14:30:22\"")
            print("  python osv.py convert \"2023-05-15 14:30:22.500\"")
            return
            
        try:
            from lib.util.util import date_to_met
            met = date_to_met(args[1])
            print(f"Date: {args[1]}")
            print(f"Fermi MET: {met}")
        except ValueError as e:
            print(f"Error: {e}")
    
    @classmethod
    def handle(cls, command):
        """Execute command if it exists"""
        command_lower = command.lower()
        
        # Handle version commands
        if "ver" in command_lower:
            command_lower = "ver"
            
        if command_lower in cls.COMMANDS:
            cmd = cls.COMMANDS[command_lower]
            if isinstance(cmd, str):
                getattr(cls, cmd)()
            else:
                cmd()
            return True
        return False

def main():
    """Main entry point"""
    args = sys.argv[1:]
    
    if args:
        if CommandHandler.handle(args[0]):
            return
        # If not a recognized command, treat as options
        opts = lib.options.cmdLineOptions()
    else:
        opts = None

    app = OSV(False)
    app.OnLaunch(opts)
    app.MainLoop()


if __name__ == '__main__':
    main()