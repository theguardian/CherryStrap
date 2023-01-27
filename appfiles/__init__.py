from cherrystrap import logger
from cherrystrap.configCheck import CheckSection, check_setting_int, check_setting_bool, check_setting_str

# In this file you can declare additional variables specific to your app.
# Use cherrystrap/__init__.py as your guide... below is a commented-out
# example:

GIT_USER = 'theguardian'
GIT_REPO = 'CherryStrap'
GIT_BRANCH = 'master'

def injectVarCheck(CFG):

    global GIT_USER, GIT_REPO, GIT_BRANCH

    CheckSection(CFG, 'source')

    GIT_USER = check_setting_str(CFG, 'source', 'gitUser', 'theguardian')
    GIT_REPO = check_setting_str(CFG, 'source', 'gitRepo', 'CherryStrap')
    GIT_BRANCH = check_setting_str(CFG, 'source', 'gitBranch', 'master')

def injectDbSchema():

#    schema = {}
#    schema['logpaths'] = {} #this is a table name
#    schema['logpaths']['Program'] = 'TEXT' #this is a column name and format
#    schema['logpaths']['LogPath'] = 'TEXT'

    return schema

def injectApiConfigGet():

    injection = {
        "source": {
            "gitBranch": GIT_BRANCH,
            "gitUser": GIT_USER,
            "gitRepo": GIT_REPO
        }
    }

    return injection

def injectApiConfigPut(kwargs, errorList):

    global GIT_USER, GIT_REPO, GIT_BRANCH

    if 'gitUser' in kwargs:
        GIT_USER = kwargs.pop('gitUser', 'theguardian')
    if 'gitRepo' in kwargs:
        GIT_REPO = kwargs.pop('gitRepo', 'CherryStrap')
    if 'gitBranch' in kwargs:
        GIT_BRANCH = kwargs.pop('gitBranch', 'master')

    return kwargs, errorList

def injectVarWrite(new_config):

    new_config['source'] = {}
    new_config['source']['gitUser'] = GIT_USER
    new_config['source']['gitRepo'] = GIT_REPO
    new_config['source']['gitBranch'] = GIT_BRANCH

    return new_config
