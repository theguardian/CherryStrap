from cherrystrap import logger
from cherrystrap.configCheck import CheckSection, check_setting_int, check_setting_bool, check_setting_str

EXAMPLE_BOOLEAN_VARIABLE = False
EXAMPLE_INTEGER_VARIABLE = 0
EXAMPLE_STRING_VARIABLE = None

def injectVarCheck(CFG):

    global EXAMPLE_BOOLEAN_VARIABLE, EXAMPLE_INTEGER_VARIABLE, \
    EXAMPLE_STRING_VARIABLE

    CheckSection(CFG, 'AppVariables')

    EXAMPLE_BOOLEAN_VARIABLE = check_setting_bool(CFG, 'AppVariables', 'exampleBool', False)
    EXAMPLE_INTEGER_VARIABLE = check_setting_int(CFG, 'AppVariables', 'exampleInt', 1)
    EXAMPLE_STRING_VARIABLE = check_setting_str(CFG, 'AppVariables', 'exampleStr', 'testValue')

def injectDbSchema():

    schema = {}
    schema['exampleTable'] = {} #this is a table name
    schema['exampleTable']['columnName'] = 'TEXT' #this is a column name and format

    return schema

def injectApiConfigGet():

    injection = {
        "AppVariables": {
            "exampleBool": EXAMPLE_BOOLEAN_VARIABLE,
            "exampleInt": EXAMPLE_INTEGER_VARIABLE,
            "exampleStr": EXAMPLE_STRING_VARIABLE
        }
    }

    return injection

def injectApiConfigPut(kwargs, errorList):
    global EXAMPLE_BOOLEAN_VARIABLE, EXAMPLE_INTEGER_VARIABLE, \
    EXAMPLE_STRING_VARIABLE

    if 'exampleBool' in kwargs:
        EXAMPLE_BOOLEAN_VARIABLE = kwargs.pop('exampleBool', False) == 'true'
    if 'exampleInt' in kwargs:
        try:
            EXAMPLE_INTEGER_VARIABLE = int(kwargs.pop('exampleInt', 1))
        except:
            EXAMPLE_INTEGER_VARIABLE = 1
            errorList.append("exampleInt must be an integer")
            kwargs.pop('exampleInt', 1)
    if 'exampleStr' in kwargs:
        EXAMPLE_STRING_VARIABLE = kwargs.pop('exampleStr', 'testValue')

    return kwargs, errorList

def injectVarWrite(new_config):
    new_config['AppVariables'] = {}
    new_config['AppVariables']['exampleBool'] = EXAMPLE_BOOLEAN_VARIABLE
    new_config['AppVariables']['exampleInt'] = EXAMPLE_INTEGER_VARIABLE
    new_config['AppVariables']['exampleStr'] = EXAMPLE_STRING_VARIABLE

    return new_config
