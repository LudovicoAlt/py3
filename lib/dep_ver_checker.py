#!/usr/bin/python -tt

'''
setup script for OSV
'''

import os
import sys

import configobj #essentially just installed v5
#from lib import validate
import validate

appName = 'osv'

iniDir = os.path.expanduser('~/.gbmOSV')
iniPath = os.path.join(iniDir, 'config.ini')

cfgSpec = """
dataDir = string(default='./')
specType = option('CSPEC', 'CTIME', default = 'CSPEC')
tRange = list(min = 2, max = 2, default = list(-100, 500))
offset = force_list(min = 1, default = list(30))
doGTI = boolean(default = True)
[gui]
autoLoadLU = boolean(default=True)
warnAll = boolean(default=True)
reScaleAxes = boolean(default=True)
"""

def doCheckVersions(verbose=True):
    ''' Get version numbers for python modules  '''
    modules = ['matplotlib', 'astropy', 'numpy', 'argparse', 'configobj', 'wxPython']
    nullVal = 'unknown'
    try:
        import matplotlib
        mplVer = matplotlib.__version__
    except:
        mplVer = nullVal
    try:
        import astropy
        pyfVer = astropy.__version__
    except:
        pyfVer = nullVal
    try:
        import numpy
        npyVer = numpy.__version__
    except:
        npyVer = nullVal
    try:
        import argparse
        argVer = argparse.__version__
    except:
        argVer = nullVal
    try:
        import wx
        wxPVer = wx.__version__
    except:
        wxPVer = nullVal
    try:
        #from lib.config import configobj
        import configobj
        cfgVer = configobj.__version__
    except:
        cfgVer = nullVal
    versions = [mplVer, pyfVer, npyVer, npyVer, cfgVer, wxPVer]
    mes = ''
    for i,j in zip(modules, versions):
        mes += '%s: %s\n' %(i,j)   
    print(mes)
    return mes
    
def getConfig(default=False, printflag=False):
    ''' Read config file and return dictionary with values  '''
    if not os.path.isdir(iniDir):
        os.makedirs(iniDir)
    spec = cfgSpec.split('\n')
    if default:
        config = configobj.ConfigObj(configspec = spec)
    else:
        config = configobj.ConfigObj(iniPath, configspec = spec)
    validator = validate.Validator()
    config.validate(validator, copy = True)   
    if printflag:
        print("The config file: ")
        print(config) 
    return config

def doValidateConfig(config):
    defaultCfg = getConfig(default = True)
    validator = validate.Validator()
    results = config.validate(validator,)
    if results != True:
        for (section_list, key, _) in configobj.flatten_errors(config, results):
            if key is not None:
                print('** The "%s" key in the section "%s" failed validation' % (key, ', '.join(section_list)))
                print('** Resetting to default value: %s = %s' % (key, defaultCfg[key]))
                config[key] =  defaultCfg[key]
            else:
                print('The following section was missing:%s ' % ', '.join(section_list))    
    return config

def doConfig():
    ''' 
    Read config file: then prompt user to either ok values or input their own.
    '''
    config = getConfig()
    print('Set the configuration for the current user.') 
    print('Press <return> to accept a default.')
    for i in list(config.keys()): 
        try:
            subKeys = list(config[i].keys())
            print("\n<><> %s configuration <><>" % i)
            for j in subKeys:
                print(('%s [%s] '  %(j, config[i][j])), end=' ')
                inp = input()
                if len(inp) > 0:
                    splitInp = inp.split()
                    if len(splitInp) > 1:
                        config[i][j] = splitInp
                    else:
                        config[i][j] = inp
        except AttributeError:
            print(('%s [%s] '  %(i, config[i])), end=' ')
            inp = input()
            if len(inp) > 0:
                splitInp = inp.split()
                if len(splitInp) > 1:
                    config[i] = splitInp
                else:
                    config[i] = inp
    print("validating inputs ...")
    config = doValidateConfig(config)
    print("validating done")
    # Save settings prompt
    prompt = 'Do you want to save the settings? [yes]'
    save_it = False
    while 1:
        inp = input(prompt).strip().lower()
        if not inp:
            inp = 'y'
        if inp in ('y', 'yes'):
            save_it = True
            break
        elif inp in ('n', 'no'):
            save_it = False
            break
        print('The answer %s is invalid.' % inp, end=' ')
        print('It must be one of "y" or "n".')

    config["dataDir"] = os.path.expanduser(config["dataDir"])
    if save_it:
        config.write()
    
def doCheckDeps():
    '''Check for required modules''' 
    # Lets look at what modules the user has installed
    print("Checking for python modules ...")
    importError = False
    missingModules = []
    try:
        import matplotlib
    except ImportError:
        print("*** Matplotlib not found - cannot continue without this module")
        importError = True
        missingModules.append('matplotlib')
    try: 
        import astropy
    except ImportError:
        print("*** astropy not found - cannot continue without this module")
        importError = True
        missingModules.append('astropy')
    try:
        import argparse
    except ImportError:
        print("*** Argparse not found - cannot continue without this module")
        print("*** This is standard in python 2.7 and greater - but can be")
        print("*** installed in earlier versions")
        importError = True
        missingModules.append('argparse')
    try: 
        import numpy
    except ImportError:
        print("*** Numpy not found - cannot continue without this module")
        importError = True
        missingModules.append('numpy')
    try: 
        import configobj
    except ImportError:
        print("*** ConfigObj not found - cannot continue without this module")
        importError = True
        missingModules.append('configobj')
    try: 
        import wx
    except ImportError:
        print("*** wx not found - cannot continue without this module")
        importError = True
        missingModules.append('wx')
    if importError:
        print("\nMissing %i module(s):"%len(missingModules))
        for i in missingModules: 
            print("\t%s"%i)
    else:
        print("Done - all required modules found")
    return
  
def doHelp():
    ''' '''
    print("help:")
    print('Options: config - checkDeps')
    
def main():
    if len(sys.argv[1:]) < 1:
        cmd = 'help'
    else:
        cmd = sys.argv[1]

    cmd = cmd.lower()
    if cmd == 'config':
        doConfig()
    elif cmd == 'checkdeps':
        doCheckDeps()
    elif cmd == 'test':
        doCheckVersions()
    else:
        doHelp()
        
if __name__=='__main__':
    main()