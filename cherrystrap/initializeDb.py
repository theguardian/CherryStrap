import os
from warnings import filterwarnings
from cherrystrap import logger, formatter

def createDb(DATABASE_TYPE, DATADIR, APP_NAME, MYSQL_HOST, MYSQL_PORT,
    MYSQL_USER, MYSQL_PASS):

    # User should have a choice between sqlite and mysql

    if DATABASE_TYPE == "sqlite":
        try:
            import sqlite3
        except Exception as e:
            logger.warn("SQLite is not installed: %s" % e)

        try:
            DBFILE = os.path.join(DATADIR, '%s.db' % APP_NAME)
            conn = sqlite3.connect(DBFILE)
            c = conn.cursor()
        except Exception as e:
            logger.warn("Could not connect to SQLite database: %s" % e)

        #===============================================================
        # Import a schema injection system per your  app's __init__.py
        try:
            from appfiles import injectDbSchema
            injection = injectDbSchema()
            for table, schema in injection.items():
                c.execute('CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY)' % table)
                for columnName, columnFormat in schema.items():
                    try:
                        c.execute('SELECT %s from %s' % (columnName, table))
                    except sqlite3.OperationalError:
                        c.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table, columnName, columnFormat))
                        logger.info('Column %s created in table %s' % (columnName, table))
        except Exception as e:
            logger.warn("There was a problem initializing SQLite database schema: %s" % e)
        #===============================================================

        conn.commit()
        c.close()

    elif DATABASE_TYPE == "mysql":
        try:
            import MySQLdb
            filterwarnings('ignore', category = MySQLdb.Warning)
        except ImportError:
            logger.warn("The MySQLdb module is missing. Install this " \
                "module to enable MySQL. Please revert to SQLite.")

        try:
            conn_ini = MySQLdb.Connection(host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, passwd=formatter.decode('obscure', MYSQL_PASS),
            charset='utf8', use_unicode=True)
            c_ini = conn_ini.cursor(MySQLdb.cursors.DictCursor)
            c_ini.execute('CREATE DATABASE IF NOT EXISTS %s CHARACTER SET = %s COLLATE = %s' % (APP_NAME, 'utf8', 'utf8_unicode_ci'))
            conn_ini.commit()
            c_ini.close()
        except Exception as e:
            logger.warn("There was a problem creating the MySQL database: %s" % e)

        # Now we're free to build our schema
        try:
            conn = MySQLdb.Connection(host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, passwd=formatter.decode('obscure', MYSQL_PASS),
            charset='utf8', use_unicode=True, db=APP_NAME)
            c = conn.cursor(MySQLdb.cursors.DictCursor)

            #===============================================================
            # Import a schema injection system per your  app's __init__.py
            from appfiles import injectDbSchema
            injection = injectDbSchema()
            for table, schema in injection.items():
                c.execute('CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY)' % table)
                for columnName, columnFormat in schema.items():
                    try:
                        c.execute('SELECT %s from %s' % (columnName, table))
                    except MySQLdb.OperationalError:
                        c.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table, columnName, columnFormat))
                        logger.info('Column %s created in table %s' % (columnName, table))
            #===============================================================

            conn.commit()
            c.close()
        except Exception as e:
            logger.warn("There was a problem initializing MySQL database schema: %s" % e)

    else:
        pass
