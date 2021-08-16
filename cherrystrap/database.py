from __future__ import with_statement

import os
import threading
import time

import cherrystrap
from cherrystrap import logger, formatter

db_lock = threading.Lock()

def dbFilename(filename):
    return os.path.join(cherrystrap.DATADIR, filename)

class SQLite_DBConnection:

    def __init__(self):
        filename = cherrystrap.APP_NAME+".db"
        try:
            global sqlite3
            import sqlite3
        except Exception as e:
            logger.error("There was an error importing SQLite: %s" % e)
        self.filename = filename
        self.connection = sqlite3.connect(dbFilename(filename), 20)
        self.connection.row_factory = sqlite3.Row

    def action(self, query, args=None):
        with db_lock:

            if query == None:
                return

            sqlResult = None
            attempt = 0

            while attempt < 5:

                try:
                    if args == None:
                        #logger.debug(self.filename+": "+query)
                        sqlResult = self.connection.execute(query)
                    else:
                        #logger.debug(self.filename+": "+query+" with args "+str(args))
                        sqlResult = self.connection.execute(query, args)
                    self.connection.commit()
                    break

                except sqlite3.OperationalError as e:
                    if "unable to open database file" in e.message or "database is locked" in e.message:
                        logger.warn('Database Error: %s' % e)
                        attempt += 1
                        time.sleep(1)
                    else:
                        logger.error('Database error: %s' % e)
                        raise

                except sqlite3.DatabaseError as e:
                    logger.error('Fatal error executing %s :: %s' % (query, e))
                    raise

            return sqlResult

    def select(self, query, args=None):
        sqlResults = self.action(query, args).fetchall()

        if sqlResults == None:
            return []

        return sqlResults

    def upsert(self, tableName, valueDict, keyDict):
        changesBefore = self.connection.total_changes

        genParams = lambda myDict : [x + " = ?" for x in list(myDict.keys())]

        query = "UPDATE "+tableName+" SET " + ", ".join(genParams(valueDict)) + " WHERE " + " AND ".join(genParams(keyDict))

        self.action(query, list(valueDict.values()) + list(keyDict.values()))

        if self.connection.total_changes == changesBefore:
            query = "INSERT INTO "+tableName+" (" + ", ".join(list(valueDict.keys()) + list(keyDict.keys())) + ")" + \
                        " VALUES (" + ", ".join(["?"] * len(list(valueDict.keys()) + list(keyDict.keys()))) + ")"

            self.action(query, list(valueDict.values()) + list(keyDict.values()))

class MySQL_DBConnection:

    def __init__(self):
        try:
            global MySQLdb
            import MySQLdb
        except ImportError:
            logger.warn("The MySQLdb module is missing. Install this " \
                "module to enable MySQL. Reverting to SQLite.")
            cherrystrap.DATABASE_TYPE = "sqlite"
        host = cherrystrap.MYSQL_HOST
        port = cherrystrap.MYSQL_PORT
        if port:
            try:
                port = int(cherrystrap.MYSQL_PORT)
            except:
                port = 3306
                logger.error("The port number supplied is not an integer")
        else:
            port = 3306
        if not host:
            host = 'localhost'

        user = cherrystrap.MYSQL_USER
        passwd = formatter.decode('obscure', cherrystrap.MYSQL_PASS)

        self.connection = MySQLdb.Connection(host=host, port=port, user=user, passwd=passwd, db=cherrystrap.APP_NAME, charset='utf8', use_unicode=True)

    def action(self, query, args=None):

        with self.connection:
            self.cursor = self.connection.cursor(MySQLdb.cursors.DictCursor)

            if query == None:
                return

            sqlResult = None

            try:
                if args == None:
                    self.cursor.execute(query)
                else:
                    self.cursor.execute(query,args)
                self.connection.commit()
            except MySQLdb.IntegrityError:
                logger.info("failed to make transaction")

            sqlResult = self.cursor
            return sqlResult

    def select(self, query, args=None):

        sqlResults = self.action(query, args).fetchall()

        if sqlResults == None:
            return []

        return sqlResults

    def upsert(self, tableName, valueDict, keyDict):

        genParams = lambda myDict : [x + " = %s" for x in list(myDict.keys())]

        entry_query = "SELECT * FROM "+tableName+" WHERE " + " AND ".join(genParams(keyDict))
        entry_count = self.action(entry_query, list(keyDict.values())).rowcount

        if entry_count != 0:
            query = "UPDATE "+tableName+" SET " + ", ".join(genParams(valueDict)) + " WHERE " + " AND ".join(genParams(keyDict))
            self.action(query, list(valueDict.values()) + list(keyDict.values()))
        else:
            query = "INSERT INTO "+tableName+" (" + ", ".join(list(valueDict.keys()) + list(keyDict.keys())) + ")" + \
                        " VALUES (" + ", ".join(["%s"] * len(list(valueDict.keys()) + list(keyDict.keys()))) + ")"
            self.action(query, list(valueDict.values()) + list(keyDict.values()))
