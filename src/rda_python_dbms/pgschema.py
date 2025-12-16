#!/usr/bin/env python3
##################################################################################
#     Title : pgschema
#    Author : Zaihua Ji, zji@ucar.edu
#      Date : 2025-09-27
#             2025-12-15 convert to class PgSchema
#   Purpose : copy tables of a schema to teh same schema name in a different database
#             on the same server
#    Github : https://github.com/NCAR/rda-python-dbms.git
##################################################################################
import sys
import os
import re
from os import path as op
from time import time as tm
from rda_python_common.pg_util import PgUtil

class PgSchema(PgUtil):
   def __init__(self):
      super().__init__()  # initialize parent class
      self.PVALS = {
         'db' : 'rdadb',
         'nd' : None,
         'sc' : None,
         'us' : None,
         'ht' : 'rda-db.ucar.edu',
         'mp' : 16,      # number of concurrent processes (one for a table at a time)
         'pn' : 5432,
         'tb' : []
      }

   # function to read parameters
   def read_parameters(self):
      argv = sys.argv[1:]
      opt = None
      for arg in argv:
         if re.match(r'-(\w+)$', arg):
            opt = arg[1:]
            if opt == "b":
               self.PGLOG['BCKGRND'] = 1
               opt = None
            elif opt not in self.PVALS:
               self.pglog(arg + ": Invalid Option", self.LGWNEX)
         elif opt:
            if isinstance(self.PVALS[opt], list):
               self.PVALS[opt].append(arg)
            elif isinstance(self.PVALS[opt], int):
               self.PVALS[opt] = int(arg)
               opt = None
            else:
               self.PVALS[opt] = arg
               opt = None
         else:
            self.pglog(arg + ": parameter misses leading option", self.LGWNEX)
      self.PGLOG['LOGFILE'] = "pgschema.log"
      sc = self.PVALS['sc']
      if not sc:
         print("Dump all or specified tables in a Schema in the current directory; Restore")
         print("the dumped schema to a different Database name with the same schema name.")
         print("Existing tables in the target database.schema will not be overriden. If the")
         print("target schema exists already, try to login to the new database to drop the")
         print("schema: 'drop schema SchemaName cascade;', for a fresh new schema stransfer.")
         print("Usage:\npgschema [-b] [-m PMAX] [-ht HOSTNAME] [-db DATABASE] -sc SCHEMA  \\")
         print("      [-nd NEWDATABASE] [-us USERNAME] [-tb TABLES] [-pn PORTNO]")
         print("  Option -tb - specify the table names, use wildcard '*' to match mutiple tables")
         print("  Option -ht - host name of database server is running on; default to 'rda-db.ucar.edu'")
         print("  Option -sc - the schema for tables to be transferred from")
         print("  Option -db - the database name, default to 'rdadb'")
         print("  Option -nd - the new database for schema to be transferred to; defaults to <DATABASE>_test")
         print("  Option -us - specify the user name, default to -sc")
         print("  Option -pn - the port number to connect to database, default to 5432")
         print("  Option -mp - the number of processes to dump/restore schema; default to 16")
         print("NOTE: To transfer schema, set both database password entries in file .pgpass")
         print("      under your home directory as HOSTNAME:5432:DATABASE:USERNAME:password.")
         print("For Example to transfer schema wagtail in Dababase rdadb to Database rdadb_test:")
         print("      rda-db.ucar.edu:5432:rdadb:wagtail:<WagtailPassword>")
         print("      rda-db.ucar.edu:5432:rdadb_test:wagtail:<WagtailPassword>")
         sys.exit(0)
      if not self.PVALS['us']: self.PVALS['us'] = sc
      if not self.PVALS['nd']: self.PVALS['nd'] = f"{self.PVALS['db']}_test"
      if self.PVALS['nd'] == self.PVALS['db']:
         self.pglog(f"Must transfer schema {sc} to a Database other than {self.PVALS['db']}", self.LGWNEX)
      self.cmdlog("pgschema {}".format(' '.join(argv)))

   # function to start actions
   def start_actions(self):
      self.PVALS['pgsc'] = self.pgname(self.PVALS['sc'])
      self.transfer_schema()
      self.cmdlog()

   # transfer a schema from one database to another
   def transfer_schema(self):
      sc = self.PVALS['sc']
      db = self.PVALS['db']
      nd = self.PVALS['nd']
      tables = self.PVALS['tb']
      topt = self.get_table_options(tables)
      # dump schema
      dumpdir = "{}_dump_{}".format(sc, self.curdate())
      if op.exists(dumpdir):
         self.pglog(dumpdir + ": Local directory exists, remove it before running pgschema", self.LGEREX)
      pgsc = self.PVALS['pgsc']
      dbsc = f"{db}.{sc}: "
      tstr = f"\nFor tables in '{tables}'" if tables else ""
      if pgsc != sc: pgsc = "'{}'".format(pgsc)
      cmd = f"pg_dump {db} -h {self.PVALS['ht']} -n {pgsc}{topt} -U {self.PVALS['us']} -w -Fd -j {self.PVALS['mp']} -f {dumpdir}/"
      if self.pgsystem(cmd, self.LOGWRN, 4):   # 4 + 1
         msg = f"Schema dumped in {dumpdir}"
         logact = self.LOGWRN
      else:
         msg = "Error dumping schema"
         logact = self.LGEREX
      self.pglog(dbsc + msg + tstr, logact)
      # restore schema
      dbsc = f"{nd}.{sc}: "
      cmd = f"pg_restore -d {nd} -h {self.PVALS['ht']}{topt} -U {self.PVALS['us']} -w -j {self.PVALS['mp']} -Fd {dumpdir}"
      if self.pgsystem(cmd, self.LOGWRN, 6):
         msg = f"Schema Restored from {dumpdir}"
         logact = self.LOGWRN
         self.pglog(dbsc + msg + tstr, logact)
      # remove dumped directory
      cmd = f"rm -rf {dumpdir}"
      if self.pgsystem(cmd, self.LOGWRN, 4):
         msg = "Directory removed"
         logact = self.LOGWRN
      else:
         msg = "Error removing directory"
         logact = self.LOGERR
      self.pglog(f"{dumpdir}: {msg}", logact)

   # add -t in front of each table
   def get_table_options(self, tables):
      tstr = ''
      for tb in tables: tstr += " -t {}".format(self.pgname(tb))
      return tstr

# main function to excecute this script
def main():
   object = PgSchema()
   object.read_parameters()
   object.start_actions()
   object.pgexit(0)

# call main() to start program
if __name__ == "__main__": main()
