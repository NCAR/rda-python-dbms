#!/usr/bin/env python3
###############################################################################
#     Title : pgdbrestore
#    Author : Zaihua Ji,  zji@ucar.edu
#      Date : 08/14/2025
#             2025-12-15 convert to class PgDBRestore
#   Purpose : python code to restore PostgreSQL databases from specified
#             local directories.
#    Github : https://github.com/NCAR/rda-python-dbms.git
###############################################################################
import sys
import re
import os
from os import path as op
from rda_python_common.pg_dbi import PgDBI

class PgDBRestore(PgDBI):
   def __init__(self):
      super().__init__()  # initialize parent class
      self.USNAME = 'postgres'
      self.LOGACT = self.LGWNEM
      self.ERRACT = self.LGEREM
      self.SNDACT = self.LOGWRN|self.SNDEML
      self.pname = self.hname = self.dname = None

   # function to read parameters
   def read_parameters(self):
      # check command line for options
      self.PGLOG['LOGFILE'] = "pgbackup.log"   # set log file
      argv = sys.argv[1:]
      option = None
      override = False
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
      if not (self.dname and self.hname and self.pname):
         print("Usage: pgdbrestore [-b] -d DBNAME -h HostName -p LocalPath")
         print("  -b - background process and no screen output")
         print("  -d - PostgreSQL database name to restore from the local path")
         print("  -h - Hostname the PostgreSQL server is running on")
         print("  -p - Local relative path the dumped database stored")
         sys.exit(0)
      self.cmdlog("pgdbrestore {}".format(' '.join(argv)))

   # function to start actions
   def start_actions(self):
      self.pg_database_dbrestore()
      title = "pgdbrestore: {}:{}".format(self.hname, self.dname)
      tmsg = "{} from {} under {}!".format(title, self.pname, os.getcwd())
      self.set_email(tmsg, self.EMLTOP)
      self.pglog(title, self.SNDACT)
      self.cmdlog()   

   #  bacup one database
   def pg_database_dbrestore(self):
      cmd = "pg_restore -d {} -h {} -U {} -w -j 16 -Fd {}".format(self.dname, self.hname, self.USNAME, self.pname)
      if not op.exists(self.pname):
         self.pglog(self.pname + ": Restoring local path not exists", self.ERRACT)
      elif not self.pgsystem(cmd, self.LOGACT, 257):
         self.pglog("{}: Error restoring database\n{}".format(self.dname, self.PGLOG['SYSERR']), self.ERRACT)

# main function to excecute this script
def main():
   object = PgDBRestore()
   object.read_parameters()
   object.start_actions()
   object.pgexit(0)

# call main() to start program
if __name__ == "__main__": main()
