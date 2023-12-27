#!/usr/bin/python -tt

import time
import sys

import wx

import lib
import lib.osv_classes as osv_classes
import lib.gui_classes as gui_classes
import lib.dep_ver_checker as setup

__version__ = "1.3"

class OSV(wx.App):
    def OnInit(self,):
        return True
    def OnLaunch(self, opts = None): 
        if opts is None:
            self.OnNew()
        else:
            self.createInstance(opts)
        return True        
    def OnNew(self):
        '''
        Dialog box for option selection
        '''
        dlg = osv_classes.OptDialog(None, False, title = "OSV Options")
        if (dlg.ShowModal() == wx.ID_OK):
            self.opts = dlg.opts
            self.opts.check()
            if self.opts.error:
                self.DialogBox(self.opts.err_mes)
                return
            elif self.opts.warnAll:
                if self.opts.warning:
                    self.DialogBox(self.opts.warning_mes, title = 'Warnings')
            self.createInstance(dlg.opts)
        else:
            pass
        dlg.Destroy()
    def createInstance(self, opts):
        ''' 
        Create instance of OSV GUI & run with given options
        '''
        curTime = time.strftime("%H:%M:%S", time.gmtime())   
        inst = osv_classes.OSV_Instance(opts)
        title = '%s @ %s' %(inst.opts.name, curTime)
        inst.gui = gui_classes.OrbsubGUI(None, -1, title = title,
                                            plotDimensions = (2,1,),)
        inst.gui.log.update(opts.__str__())
        inst.runOrbSub()
    def DialogBox(self, mes, title = 'Error encountered'):
        ''' Show an error widget '''
        wx.MessageBox(mes, title,
                      style = wx.OK | wx.ICON_ERROR)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args):
        if args[0].lower()=='doconfig':
            setup.doConfig()
            exit()
        elif args[0].lower() == "getdata":            
            lib.getData.main(argv = sys.argv[2:])
            exit()
        elif args[0].lower() == "checkdeps":
            setup.doCheckDeps()
            exit()
        elif args[0].lower() == "checkvers":
            setup.doCheckVersions()
            exit()            
        elif "ver" in args[0].lower():
            print(("osv v%s"%__version__))
            exit()
        else:
            opts = lib.options.cmdLineOptions()
    else:
        opts = None

    app = OSV(False,)
    app.OnLaunch(opts)
    app.MainLoop()