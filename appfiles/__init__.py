from cherrystrap import logger
from cherrystrap.configCheck import CheckSection, check_setting_int, check_setting_bool, check_setting_str

# In this file you can declare additional variables specific to your app.
# Use cherrystrap/__init__.py as your guide... below is a commented-out
# example:
#CPU_INFO_PATH = None

def injectVarCheck(CFG):

#    global CPU_INFO_PATH

#    CheckSection(CFG, 'System')

#    CPU_INFO_PATH = check_setting_str(CFG, 'System', 'cpuInfoPath', '/proc/cpuinfo')

def injectDbSchema():

#    schema = {}
#    schema['logpaths'] = {} #this is a table name
#    schema['logpaths']['Program'] = 'TEXT' #this is a column name and format
#    schema['logpaths']['LogPath'] = 'TEXT'

    return schema

def injectApiConfigGet():

#    injection = {
#        "system": {
#            "cpuInfoPath": CPU_INFO_PATH
#        }
#    }

    return injection

def injectApiConfigPut(kwargs, errorList):
#    global CPU_INFO_PATH

#    if 'cpuInfoPath' in kwargs:
#        CPU_INFO_PATH = kwargs.pop('cpuInfoPath', '/proc/cpuinfo')

    return kwargs, errorList

def injectVarWrite(new_config):
#    new_config['System'] = {}
#    new_config['System']['cpuInfoPath'] = CPU_INFO_PATH

    return new_config
