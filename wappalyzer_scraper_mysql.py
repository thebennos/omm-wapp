# Imports
import MySQLdb
from _mysql_exceptions import OperationalError, InterfaceError, IntegrityError
from wappalyzer import Wappalyzer, WebPage
from datetime import datetime
import sys

# Basic settings
MYSQL_HOST = "188.138.56.200"
MYSQL_USER = "bennos"
MYSQL_PASS = "isdn300"
MYSQL_DB = "domains"

# MySQL connect
def mysql_connect():
    try:
        print("Connecting to MySQL database...")
        db = MySQLdb.connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASS, MYSQL_DB, charset="utf8")
        db.autocommit(True)
        c = db.cursor()
        print("Success!")
        return db, c

    except Exception as e:
        print("Error: MySQL connection error {}".format(e))
        input("Press enter to exit")
        sys.exit()

# Get domain
def get_domain(c, tld):
    try:
        c.execute("""SELECT id, domain FROM inbox_dev WHERE tld = "%s" AND revison = 1 AND status = 0 LIMIT 1;""" % tld)
        result = c.fetchone()

        try:
            id, domain = result[0], result[1]
        except:
            print("Error: No result found from database.")
            input("Press enter to exit")
            sys.exit()

        return id, domain

    except Exception as e:
        print("Error: Domain get error {}".format(e))
        input("Press enter to exit")
        sys.exit()

# Update DB
def update_db(c, id, data):
    try:
        c.execute("""UPDATE inbox_dev SET wappalyzer_json = "%s", checked = "%s", status = 10 WHERE id = "%s";""" % (data, datetime.now(), id))

    except Exception as e:
        print("Error: DB update error {}".format(e))
        input("Press enter to exit")
        sys.exit()

# Run wappalyzer
def run_wappalyzer(domain):
    try:
        wappalyzer = Wappalyzer.latest()
        webpage = WebPage.new_from_url("http://{}".format(domain))
        data = wappalyzer.analyze(webpage)
        return data

    except Exception as e:
        print("Warning: Wappalyzer error {}".format(e))

if __name__ == "__main__":
    try:
        if sys.argv[1] == "-tld":
            tld = sys.argv[2]

            db, c = mysql_connect()
            while True:
                id, domain = get_domain(c, tld)
                print("Checking {}".format(domain))
                data = run_wappalyzer(domain)
                if data: data = repr(data)
                else: data = None
                update_db(c, id, data)

        else:
            print("Error: Unexpected argument {} passed".format(sys.argv[1]))
            input("Press enter to exit")
            sys.exit()
    except:
        print("Error: TLD argument needed. Use -tld to pass. [eg: -tld com]")
        input("Press enter to exit")
        sys.exit()
