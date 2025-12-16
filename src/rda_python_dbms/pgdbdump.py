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
from rda_python_common.pg_Util import PgUtil

class PgDBDump(PgUtil):
   def __init__(self):
      super().__init__()  # initialize parent class
      self.USNAME = 'postgres'
      self.LOGACT = self.LGWNEM
      self.ERRACT = self.LGEREM
      self.SNDACT = self.LOGWRN|self.SNDEML
      self.pname = self.hname = self.dname = None

   # function to read_parameters
   def read_parameters(self):
      # check command line for options
      self.PGLOG['LOGFILE'] = "pgbackup.log"   # set log file
      argv = sys.argv[1:]
      option = None
      options = ['b', 'd', 'h', 'p']
      for arg in argv:
         ms = re.match(r'^-(\w)$', arg)
         if ms:
            option = ms.group(1)
            if option not in options: self.pglog("{}: unknow option".format(arg), self.LGEREX)
            if option == 'b': self.PGLOG['BCKGRND'] = 1
         elif option == 'd':
            self.dname = arg
         elif option  == 'h':
            self.hname = arg
         elif option  == 'p':
            self.pname = arg
      if not (self.dname and self.hname):
         print("Usage: pgdbdump [-b] -d DBNAME -h HostName [-p LocalPath]")
         print("  -b - background process and no screen output")
         print("  -d - PostgreSQL database name to dump at the current directory")
         print("  -h - Hostname the PostgreSQL server is running on")
         print("  -p - Local relative path to dump the database, defaults to <DBNAME>_backup_<TODAY>")
         sys.exit(0)
      self.cmdlog("pgdbdump {}".format(' '.join(argv)))
      if not self.pname: self.pname = "{}_backup_{}".format(self.dname, self.curdate())

   # function to start_actions
   def start_actions(self):
      self.pg_database_dbdump()
      title = "pgdbdump: {}:{}".format(self.hname, self.dname, self.pname)
      tmsg = "{} to {} under {}!".format(title, self.pname, os.getcwd())
      self.set_email(tmsg, self.EMLTOP)
      self.pglog(title, self.SNDACT)
      self.cmdlog()   

   #  bacup one database
   def pg_database_dbdump(self):
      cmd = "pg_dump {} -h {} -U {} -w -Fd -j 16 -f {}/".format(self.dname, self.hname, self.USNAME, self.pname)
      if op.exists(self.pname):
         self.pglog(self.pname + ": Dumping directory exists, remove it", self.ERRACT)
      elif not self.pgsystem(cmd, self.LOGACT, 257):
         self.pglog("{}: Error dumping database\n{}".format(self.dname, self.PGLOG['SYSERR']), self.ERRACT)

# main function to excecute this script
def main():
   object = PgDBDump()
   object.read_parameters()
   object.start_actions()
   object.pgexit(0)

# call main() to start program
if __name__ == "__main__": main()
