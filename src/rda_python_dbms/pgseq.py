#!/usr/bin/env python3
##################################################################################
#     Title : pgseq
#    Author : Zaihua Ji, zji@ucar.edu
#      Date : 12/31/2020
#             2025-04-09 transferred to package rda_python_dbms from
#             https://github.com/NCAR/rda-database.git
#             2025-12-15 convert to class PgSeq
#   Purpose : check all tables for given schemas to reset the related sequences
#    Github : https://github.com/NCAR/rda-python-dbms.git
##################################################################################

import sys
import re
from rda_python_common.pg_dbi import PgDBI

class PgSeq(PgDBI):

   def __init__(self):
      super().__init__()  # initialize parent class
      self.SINFO = {
         'ht' : 'rda-pgdb-02.ucar.edu',
         'db' : 'rdadb',
         'pt' : 5432,
         'us' : '',
         'pw' : '',
      }
      self.scnames = []
      self.tbnames = []

   # function to read parameters
   def read_parameters(self):
      option = None
      alltb = 0
      argv = sys.argv[1:]
      for arg in argv:
         if arg == "-b":
            self.PGLOG['BCKGRND'] = 1
         elif re.match(r'^-([cdhptuw])$', arg):
            option = arg[1]
         elif re.match(r'^-', arg):
            self.pglog(arg + ": Invalid Option", self.LGWNEX)
         elif option:
            if option == 'd':
               self.SINFO['db'] = arg
            elif option == 'h':
               self.SINFO['ht'] = arg
            elif option == 'p':
               self.SINFO['pt'] = int(arg)
            elif option == 'w':
               self.SINFO['pw'] = arg
            elif option == 'u':
               self.SINFO['us'] = arg
            elif option == 'c':
               self.scnames.append(arg)
            elif option == 't':
               self.tbnames.append(arg)
         else:
            self.pglog(arg + ": Passed in without leading Option", self.LGWNEX)
      if not self.scnames:
         print("Usage: pgseq [-h HostName] [-d DatabaseName] -c SchemaNames  \\")
         print("             [-t TableNames] [-u UserName] [-p Password]")
         print("   -h: PostgreSQL Database server hostname, default to " + self.SINFO['ht'])
         print("   -p: PostgreSQL Database server port number, default to " + str(self.SINFO['pt']))
         print("   -d: PostgreSQL Database name, default to " + self.SINFO['db'])
         print("   -c: Reset sequences for the provided Schemas, at least provide one")
         print("   -t: Table names to reset sequences, default to all tables in the schema")
         print("   -u: Provide database login username if other than the schema name")
         print("   -w: database login password")
         sys.exit(0)
      self.cmdlog("pgseq {}".format(' '.join(argv)))
   
   # function to start actions
   def start_actions(self):
      for scname in self.scnames:
         self.reset_table_sequence(scname)
      self.cmdlog()
      sys.exit(0)
   
   def reset_table_sequence(self, scname):
      us = self.SINFO['us'] if self.SINFO['us'] else scname
      pw = self.SINFO['pw'] if self.SINFO['pw'] else us
      self.default_scinfo(self.SINFO['db'], scname, self.SINFO['ht'], us, pw, self.SINFO['pt'])
      scnd = "table_catalog = '{}' AND table_schema = '{}' AND table_type = 'BASE TABLE'".format(self.SINFO['db'], scname)
      if self.tbnames:
         cnd = " AND table_name "
         tcnt = len(self.tbnames)
         if tcnt == 1:
            cnd += "= '{}'".format(self.tbnames[0])
         else:
            cnd += "IN ('{}'".format(self.tbnames[0])
            for i in range(1, tcnt):
               cnd += ", '{}'".format(self.tbnames[i])
            cnd += ')'
      else:
         cnd = ''
      pgrecs = self.pgmget('information_schema.tables', 'table_name', scnd + cnd)
      self.tbnames = pgrecs['table_name'] if pgrecs else []
      tcnt = len(self.tbnames)
      if tcnt == 0:
         self.pglog("{}.{}: No Table Name found".format(self.SINFO['db'], scname), self.LOGWRN)
         return
      scnt = 0
      scnd = "sequence_catalog = '{}' AND sequence_schema = '{}' AND sequence_name LIKE ".format(self.SINFO['db'], scname)
      qscname = self.pgname(scname)
      for tbname in self.tbnames:
         cnd = "'{}_%_seq'".format(tbname)
         pgrecs = self.pgmget('information_schema.sequences', 'sequence_name', scnd + cnd)
         if not pgrecs: continue
         qscname = self.pgname(scname)
         qtname = '{}.{}'.format(qscname, self.pgname(tbname))
         for sname in pgrecs['sequence_name']:
            fname = sname[len(tbname)+1:-4]
            fcnd = "table_name = '{}' AND table_schema = '{}' AND column_name = '{}'".format(tbname, scname, fname)
            if not self.pgget('information_schema.columns', '', fcnd): continue
            pgrec = self.pgget(qtname, "MAX({}) mval".format(self.pgname(fname)))
            mval = pgrec['mval'] if pgrec and pgrec['mval'] else 1
            qsname = '{}.{}'.format(qscname, self.pgname(sname))
            qstr = "setval('{}', {})".format(qsname, mval)
            pgrec = self.pgget('', qstr)
            if pgrec:
               self.pglog("{}.{}: Sequence Value set to {}".format(scname, sname, pgrec['setval']), self.LOGWRN)
               scnt += 1
      if scnt > 1 and tcnt > 1:
         self.pglog("{}.{}: {}/{} Sequences/Tables Reset Values".format(self.SINFO['db'], scname, scnt, tcnt), self.LOGWRN)

# main function to excecute this script
def main():
   object = PgSeq()
   object.read_parameters()
   object.start_actions()
   object.pgexit(0)

# call main() to start program
if __name__ == "__main__": main()
