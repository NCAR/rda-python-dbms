#!/usr/bin/env python3
###############################################################################
#     Title : pgdbdump
#    Author : Zaihua Ji,  zji@ucar.edu
#      Date : 08/14/2025
#             2025-12-15 convert to class PgDBDump
#   Purpose : python code to dump PostgreSQL databases to specified
#             local directories.
#    Github : https://github.com/NCAR/rda-python-dbms.git
###############################################################################
import sys
import re
import os
from os import path as op
from rda_python_common.pg_util import PgUtil

class PgDBDump(PgUtil):
   def __init__(self):
      super().__init__()  # initialize parent class
      self.USNAME = 'postgres'
      self.LOGACT = self.LGWNEM
      self.ERRACT = self.LGEREM
      self.SNDACT = self.LOGWRN|self.SNDEML
      self.pname = self.hname = self.dname = None

   def read_parameters(self):
      """
      Parse command-line options and set instance variables.
      Usage: pgdbdump [-b] -d DBNAME -h HostName [-p LocalPath]
      """
      self.PGLOG['LOGFILE'] = "pgbackup.log"   # set log file
      argv = sys.argv[1:]
      option = None
      options = ['b', 'd', 'h', 'p']
      i = 0
      while i < len(argv):
         arg = argv[i]
         ms = re.match(r'^-(\w)$', arg)
         if ms:
            option = ms.group(1)
            if option not in options:
               self.pglog(f"{arg}: unknown option", self.LGEREX)
            if option == 'b':
               self.PGLOG['BCKGRND'] = 1
               option = None
               i += 1
               continue
            # For options that require a value
            if i + 1 >= len(argv):
               self.pglog(f"Option -{option} requires a value", self.LGEREX)
            val = argv[i+1]
            if option == 'd':
               self.dname = val
            elif option == 'h':
               self.hname = val
            elif option == 'p':
               self.pname = val
            i += 2
            option = None
         else:
            i += 1
      if not (self.dname and self.hname):
         print("Usage: pgdbdump [-b] -d DBNAME -h HostName [-p LocalPath]")
         print("  -b - background process and no screen output")
         print("  -d - PostgreSQL database name to dump at the current directory")
         print("  -h - Hostname the PostgreSQL server is running on")
         print("  -p - Local relative path to dump the database, defaults to <DBNAME>_backup_<TODAY>")
         sys.exit(1)
      self.cmdlog("pgdbdump {}".format(' '.join(argv)))
      if not self.pname:
         short_host = self.hname.split('.')[0] if self.hname else 'host'
         today = self.curdate()
         self.pname = f"{short_host}_{self.dname}_{today}"

   def start_actions(self):
      """Perform the database dump and log actions."""
      self.pg_database_dbdump()
      title = f"pgdbdump: {self.hname}:{self.dname}:{self.pname}"
      tmsg = f"{title} to {self.pname} under {os.getcwd()}!"
      self.set_email(tmsg, self.EMLTOP)
      self.pglog(title, self.SNDACT)
      self.cmdlog()

   def pg_database_dbdump(self):
      """Run pg_dump for the specified database and handle errors."""
      cmd = f"pg_dump {self.dname} -h {self.hname} -U {self.USNAME} -w -Fd -j 16 -f {self.pname}/"
      if op.exists(self.pname):
         self.pglog(self.pname + ": Dumping directory exists, aborting to avoid overwrite.", self.ERRACT)
         sys.exit(2)
      if not self.pgsystem(cmd, self.LOGACT, 257):
         self.pglog(f"{self.dname}: Error dumping database\n{self.PGLOG['SYSERR']}", self.ERRACT)
         sys.exit(3)

# main function to execute this script
def main():
   pgdb = PgDBDump()
   pgdb.read_parameters()
   pgdb.start_actions()
   pgdb.pgexit(0)

# call main() to start program
if __name__ == "__main__": main()