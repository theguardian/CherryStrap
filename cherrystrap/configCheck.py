import ast
from cherrystrap import logger

def CheckSection(cfg, sec):
    """ Check if INI section exists, if not create it """
    try:
        cfg[sec]
        return True
    except:
        cfg[sec] = {}
        return False

################################################################################
# Check_setting_int                                                            #
################################################################################
def check_setting_int(config, cfg_name, item_name, def_val):
    try:
        my_val = int(config[cfg_name][item_name])
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
            logger.warn("Bad value for %s in config.ini. Reverting to default" % item_name)
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val
            logger.error("Bad default value for %s. Application may break" % item_name)
    logger.debug(item_name + " -> " + str(my_val))
    return my_val

################################################################################
# Check_setting_bool                                                            #
################################################################################
def check_setting_bool(config, cfg_name, item_name, def_val):
    try:
        my_val = ast.literal_eval(config[cfg_name][item_name])
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = ast.literal_eval(my_val)
            logger.warn("Bad value for %s in config.ini. Reverting to default" % item_name)
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val
            logger.error("Bad default value for %s. Application may break" % item_name)
    logger.debug(item_name + " -> " + str(my_val))
    return my_val

################################################################################
# Check_setting_str                                                            #
################################################################################
def check_setting_str(config, cfg_name, item_name, def_val):
    try:
        my_val = str(config[cfg_name][item_name])
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = ast.literal_eval(my_val)
            logger.warn("Bad value for %s in config.ini. Reverting to default" % item_name)
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val
            logger.error("Bad default value for %s. Application may break" % item_name)
    logger.debug(item_name + " -> " + str(my_val))
    return my_val
