'''
Lookup config file. Lookups are dictionaries which are indexed by
detector short name (e.g. n1, b0, na, etc...). The entries of these
are also dictionaries which are indexed by 'lc', 'spec' and 'gti'. 
These are lists. 
'''

from os.path import join as osJoin

#from . import configobj
import configobj #import v5
from lib import validate

import lib.config as setup

dfltLstType = 'force_list(default = list())'
dfltEntry = 'lc = {0}\n spec = {0} \n gti = {0}'.format(dfltLstType)

cfgSpec = """
[n0]
{0}
[n1]
{0}
[n2]
{0}
[n3]
{0}
[n4]
{0}
[n5]
{0}
[n6]
{0}
[n7]
{0}
[n8]
{0}
[n9]
{0}
[na]
{0}
[nb]
{0}
[b0]
{0}
[b1]
{0}
""".format(dfltEntry)

def getLUCfg(default = True, luPath = False):
    ''' lookup config '''
    spec = cfgSpec.split('\n')
    if not default:
        if not luPath:
            config = configobj.ConfigObj(configspec = spec)
        else:
            config = configobj.ConfigObj(luPath, configspec = spec)
    else:
        config = configobj.ConfigObj(configspec = spec)
    validator = validate.Validator()
    config.validate(validator, copy = True)
    return config