#!/usr/bin/env python3
#
###############################################################################
#
#     Title : pgdbdump
#    Author : Zaihua Ji,  zji@ucar.edu
#      Date : 08/14/2025
#   Purpose : python code to dump PostgreSQL databases to specified
#             local directories.
#
#    Github : https://github.com/NCAR/rda-python-dbms.git
#
###############################################################################
#
import sys
import re
import os
from os import path as op
from rda_python_common import PgLOG
from rda_python_common import PgFile
from rda_python_common import PgDBI

USNAME = 'postgres'
LOGACT = PgLOG.LGWNEM
ERRACT = PgLOG.LGEREM
SNDACT = PgLOG.LOGWRN|PgLOG.SNDEML

#
# main function to excecute this script
#
def main():

   # check command line for options
   PgLOG.PGLOG['LOGFILE'] = "pgbackup.log"   # set log file
   argv = sys.argv[1:]
   htname = dbname = option = None
   override = False
   options = ['b', 'd', 'h']
   for arg in argv:
      ms = re.match(r'^-(\w)$', arg)
      if ms:
         option = ms.group(1)
         if option not in options: PgLOG.pglog("{}: unknow option".format(arg), PgLOG.LGEREX)
         if option == 'b': PgLOG.PGLOG['BCKGRND'] = 1
      elif option == 'd':
         dbname = arg
      elif option  == 'h':
         htname = arg

   if dbname == None:
      print("Usage: pgdbdump [-b] -d DBNAME -h HostName")
      print("  -b - background process and no screen output")
      print("  -d - PostgreSQL database name to dump at the current directory")
      print("  -h - Hostname the PostgreSQL server is running on")
         
   PgLOG.cmdlog("pgdbdump {}".format(' '.join(argv)))

   pg_database_dbdump(dbname, htname)

   title = "pgdbdump: {}:{} at {}!".format(htname, dbname, os.getcwd())
   PgLOG.set_email(tmsg, PgLOG.EMLTOP)
   PgLOG.pglog(title, SNDACT)
   PgLOG.cmdlog()   
   PgLOG.pgexit(0)

#
#  bacup one database
#
def pg_database_dbdump(dbname, htname):

   backdir = "{}_backup_{}".format(dbname, PgUtil.curdate())
   cmd = "pg_dump {} -h {} -U {} -w -Fd -j 12 -f {}/".format(dbname, htname, USNAME, backdir)
   if op.exists(backdir):
      PgLOG.pglog(backdir + ": Dumping directory exists, remove it", ERRACT)
   elif not PgLOG.pgsystem(cmd, LOGACT, 257):
      PgLOG.pglog("{}: Error dumping database\n{}".format(dname, PgLOG.PGLOG['SYSERR']), ERRACT)

#
# call main() to start program
#
if __name__ == "__main__": main()
