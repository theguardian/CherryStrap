#  This file is part of cherrystrap.
#
#  cherrystrap is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  cherrystrap is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with cherrystrap.  If not, see <http://www.gnu.org/licenses/>.

import os
import threading
import logging
import json
from logging import handlers

import cherrystrap
from cherrystrap import formatter

MAX_SIZE = 1000000 # 1mb
MAX_FILES = 5


# Simple rotating log handler that uses RotatingFileHandler
class RotatingLogger(object):

    def __init__(self, filename, max_size, max_files):

        self.filename = filename
        self.max_size = max_size
        self.max_files = max_files


    def initLogger(self, loglevel=1):

        l = logging.getLogger('cherrystrap')
        l.setLevel(logging.DEBUG)

        self.filename = os.path.join(cherrystrap.LOGDIR, self.filename)

        filehandler = handlers.RotatingFileHandler(self.filename, maxBytes=self.max_size, backupCount=self.max_files)
        filehandler.setLevel(logging.DEBUG)

        fileformatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}', '%d-%b-%Y %H:%M:%S')

        filehandler.setFormatter(fileformatter)
        l.addHandler(filehandler)

        if loglevel:
            consolehandler = logging.StreamHandler()
            if loglevel == 1:
                consolehandler.setLevel(logging.INFO)
            if loglevel == 2:
                consolehandler.setLevel(logging.DEBUG)
            consoleformatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}', '%d-%b-%Y %H:%M:%S')
            consolehandler.setFormatter(consoleformatter)
            l.addHandler(consolehandler)

    def log(self, message, level):

        logger = logging.getLogger('cherrystrap')

        threadname = threading.currentThread().getName()

        if message[0]!="{":
            message = json.dumps(message)

        if level != 'DEBUG':
            cherrystrap.LOGLIST.insert(0, (formatter.now(), message, level, threadname))

        if level == 'DEBUG':
            logger.debug(message)
        elif level == 'INFO':
            logger.info(message)
        elif level == 'WARNING':
            logger.warn(message)
        else:
            logger.error(message)

# todo: This needs to be abstracted for CherryStrap..
cherrystrap_log = RotatingLogger('CherryStrap.log', MAX_SIZE, MAX_FILES)

def debug(message):
    cherrystrap_log.log(message, level='DEBUG')

def info(message):
    cherrystrap_log.log(message, level='INFO')

def warn(message):
    cherrystrap_log.log(message, level='WARNING')

def error(message):
    cherrystrap_log.log(message, level='ERROR')
