from os.path import join as osJoin

#from . import configobj
import configobj #import v5
from lib import validate

import lib.dep_ver_checker as setup
# yellow darkgreen skyblue
cfgSpec = """
foreground = string(default = 'black')
background = string(default = '0.7')
srcLine = string(default = 'green')
bkgLine = string(default = 'darkred')
srcFill = string(default = 'blue')
occFill = string(default = 'red')
gtiFill = string(default = 'green')
preCol = string(default = 'blue')
posCol = string(default = 'orange')
modCol = string(default = 'black')

font = string(default = 'serif')
fontColor = string(default = 'black')
fontsize = integer(default = 15)
fontsizeLabel = integer(default = 8)
fontsizeLegend = integer(default = 8)
"""

def getPltCfg(default = True):
    pltIni = 'plt.cgf'
    pltIniPath = osJoin(setup.iniDir, pltIni)
    spec = cfgSpec.split('\n')
    if default:
        config = configobj.ConfigObj(configspec = spec)
    else:
        config = configobj.ConfigObj(pltIniPath, configspec = spec)
    validator = validate.Validator()
    config.validate(validator, copy = True)
    return config