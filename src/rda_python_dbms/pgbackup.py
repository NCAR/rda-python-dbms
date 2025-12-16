#!/usr/bin/env python3
###############################################################################
#     Title : pgbackup
#    Author : Zaihua Ji,  zji@ucar.edu
#      Date : 11/15/2020
#             2025-04-04 transferred to package rda_python_dbms from
#             https://github.com/NCAR/rda-database.git
#             2025-12-15 convert to PgBackup
#   Purpose : python code to backup PostgreSQL databases and/or schemas
#             to specified local directories.
#             (You must set login entries in your ~/.pgpass to skip password)
#    Github : https://github.com/NCAR/rda-python-dbms.git
###############################################################################
import sys
import re
from os import path as op
from rda_python_common.pg_file import PgFile

class PgBackup(PgFile):

   def __init__(self):
      super().__init__()  # initialize parent class
      self.USNAME = 'postgres'
      self.DBHOST = 'rda-pgdb-03.ucar.edu'
      #self.DBBACKS = ['ivaddb', 'ispddb', 'upadb']
      self.DBBACKS = []
      self.SCHOST = 'rda-pgdb-02.ucar.edu'
      self.SCDB = 'rdadb'
      self.SCBACKS = ['dssdb', 'citation', 'images', 'metautil', 'search', 'wagtail2',
                 'writable', 'IGrML', 'IObML', 'VFixML', 'VGrML', 'VObML',
                 'VSatML', 'WFixML', 'WGrML', 'WObML', 'WSatML', ]
      self.BACKDIR = "/data/pgbackup"
      self.LOGACT = self.LGWNEM
      self.ERRACT = self.LGEREM
      self.SNDACT = self.LOGWRN|self.SNDEML
      self.override = True

   # read parameters
   def read_parameters(self):
      # check command line for options
      self.PGLOG['LOGFILE'] = "pgbackup.log"   # set log file
      argv = sys.argv[1:]
      option = None
      for arg in argv:
         ms = re.match(r'^-(\w)$', arg)
         if ms:
            option = ms.group(1)
            if option == 'b':
               self.PGLOG['BCKGRND'] = 1
            elif option == 'o':
               self.override = True
            else:
               self.pglog("{}: unknow option".format(arg), self.LGEREX)
      self.cmdlog("pgbackup {}".format(' '.join(argv)))
   
   # start actions
   def start_actions(self):
      self.change_local_directory(self.BACKDIR, self.LOGACT)
      bcnt = 0
      for db in self.DBBACKS:
         bcnt += self.pg_database_backup(db)
      for sc in self.SCBACKS:
         bcnt += self.pg_schema_backup(sc, self.SCDB)
      s = 'ies' if bcnt > 1 else 'y'
      title = "pgbackup: {} Backup director{} dumped".format(bcnt, s)
      tmsg = "{} under {}!".format(title, self.BACKDIR)
      self.set_email(tmsg, self.EMLTOP)
      self.pglog(title, self.SNDACT)
      self.cmdlog()   
   
   #  bacup one database
   def pg_database_backup(self, db):
      backdir = db + "_backup"
      cmd = "pg_dump {} -h {} -U {} -w -Fd -j 8 -f {}/".format(db, self.DBHOST, self.USNAME, backdir)
      if op.exists(backdir):
         if self.override:
            self.pgsystem("rm -rf " + backdir, self.LOGACT, 5)
         else:
            self.pglog(backdir + ": Backup directory exists, add option -o to override", self.LOGACT)
            return 0
      if not self.pgsystem(cmd, self.LOGACT, 257):
         self.pglog("{}: Error dumping database\n{}".format(db, self.PGLOG['SYSERR']), self.ERRACT)
      return 1
   
   #  bacup one database schema
   def pg_schema_backup(self, sc, db):
      backdir = "{}_{}_backup".format(db, sc)
      pgsc = self.pgname(sc)
      if pgsc != sc: pgsc = "'{}'".format(pgsc)
      cmd = "pg_dump {} -h {} -n {} -U {} -w -Fd -j 8 -f {}/".format(db, self.SCHOST, pgsc, self.USNAME, backdir)
      if op.exists(backdir):
         if self.override:
            self.pgsystem("rm -rf " + backdir, self.LOGACT, 5)
         else:
            self.pglog(backdir + ": Backup directory exists, add option -o to override", self.LOGACT)
            return 0
      if not self.pgsystem(cmd, self.LOGACT, 257):
         self.pglog("{}.{}: Error dumping schema\n{}".format(db, sc, self.PGLOG['SYSERR']), self.ERRACT)
         return 0
      return 1

# main function to excecute this script
def main():
   object = PgBackup()
   object.read_parameters()
   object.start_actions()
   object.pgexit(0)

# call main() to start program
if __name__ == "__main__": main()
