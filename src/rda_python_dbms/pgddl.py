#!/usr/bin/env python3
##################################################################################
#     Title : pgddl
#    Author : Zaihua Ji, zji@ucar.edu
#      Date : 11/15/2020
#             2025-04-04 transferred to package rda_python_dbms from
#             https://github.com/NCAR/rda-database.git
#   Purpose : process a ddl (Data Definition Language) file to manipulate data
#             definition of a table defined in tablename.json
#    Github : https://github.com/NCAR/rda-python-dbms.git
##################################################################################
import os
import sys
import re
import pwd
from os import path as op
from .pg_ddllib import PgDDLLib

class PgDDL(PgDDLLib):
   def __init__(self):
      super().__init__()  # initialize parent class
      self.PGACT = {
         'PKY' : ['', 'DEL', 'ADD'],  # DEL - to drop, ADD - to add primary key
         'UNQ' : ['', 'DEL', 'ADD'],  # DEL - to drop, ADD - to add unique constraint
         'CMT' : ['', 'DEL', 'ADD'],  # DEL - to set null, ADD to set comment 
         'DFT' : ['', 'DEL', 'ADD'],  # DEL - to drop, ADD - to set default value
         'JSN' : ['', 'ADD'],         # ADD - to add a new defination json file
         'NNL' : ['', 'DEL', 'ADD'],  # DEL - to drop, ADD - to set not null
         'IDX' : ['', 'DEL', 'ADD', 'CHG'],  # DEL/ADD/CHG - to drop, add and rename index
         'REF' : ['', 'DEL', 'ADD'],  # DEL - to drop, ADD - to add reference
         'TBL' : ['', 'DEL', 'ADD'],  # DEL - drop table, ADD - create table
         'FLD' : ['', 'DEL', 'ADD', 'MOD', 'CHG'],  # ADD/DEL/CHG/MOD - to add, drop, change and modify field
      }
      self.ACTIONS = {
         'a' : 'ADD',
         'c' : 'CHG',
         'd' : 'DEL',
         'm' : 'MOD'
      }
      self.OPTIONS = {
         'a' : ['TBL', 'IDX', 'REF'],
         'f' : 'FLD',
         'c' : 'CMT',
         'd' : 'DFT',
         'j' : 'JSN',
         'n' : 'NNL',
         'i' : 'IDX',
         'p' : 'PKY',
         'r' : 'REF',
         't' : 'TBL',
         'u' : 'UNQ'
      }
      self.VALUES = {
         'TBL' : [],
         'IDX' : [],
         'FLD' : [],
         'DFT' : [],
         'NNL' : [],
         'REF' : [],
         'UNQ' : []
      }
      self.DBFLDS = {
         'd' : 'dbname',
         'c' : 'scname',
         'h' : 'dbhost',
         'p' : 'dbport',
         'u' : 'lnname',
         'w' : 'pwname',
      }

   # function to read parameters
   def read_parameters(self):
      option = 't'
      actopt = False
      tablenames = action = None
      dbopt = getall = False
      argv = sys.argv[1:]
      for arg in argv:
         ms = re.match(r'^-([abcdefhlmpstTuwxy])$', arg)
         if ms:
            option = ms.group(1)
            actopt = False
            if option in 'abefm':
               if option == "b":
                  self.PGLOG['BCKGRND'] = 1
               elif option == "a":
                  getall= True
               elif option == "e":
                  self.PGDDL['override'] = True
               elif option == "f":
                  self.PGDDL['usefile'] = True
               elif option == "m":
                  self.PGDDL['mysqldb'] = True
               option = None
            continue
         ms = re.match(r'^-(\w)(\w)$', arg)
         if ms:
            action = ms.group(1)
            option = ms.group(2)
            actopt = True
            if option in self.OPTIONS and action in self.ACTIONS:
               act = self.ACTIONS[action]
               if option == 'a' and action != 'a':
                  self.pglog("{}: Invalid Action to {} ALL".format(arg, act), self.LGEREX)
               opt = self.OPTIONS['t'] if option == 'a' else self.OPTIONS[option]
               if act in self.PGACT[opt][1:]:
                  if option == 'a':
                     for opt in self.OPTIONS['a']:
                        self.PGACT[opt][0] = act
                  else:
                     self.PGACT[opt][0] = act
                  if 'ap'.find(option) > -1: option = 't'
                  continue
            self.pglog(arg + ": Invalid Action", self.LGEREX)
         if re.match(r'^-.*', arg): self.pglog(arg + ": Unknown Option", self.LGEREX)
         if not option: self.pglog(arg + ": Value passed in without leading Option", self.LGEREX)
         if actopt:
            self.VALUES[self.OPTIONS[option]].append(arg)
         elif option in self.DBFLDS:
            self.DBINFO[self.DBFLDS[option]] = arg
            dbopt = True
         elif option == 'T':
            self.PGDDL['TBPATH'] = arg
         elif option == 'l':
            self.PGDDL['username'] = arg
         elif option == 'x':
            self.PGDDL['suffix'].append(arg)
         elif option == 'y':
            self.PGDDL['prefix'].append(arg)
         elif option == 's':
            self.PGDBI['SCPATH'] = arg
         else:
            self.VALUES[self.OPTIONS[option]].append(arg)
      if dbopt:
         self.default_scinfo(self.DBINFO['dbname'], self.DBINFO['scname'], self.DBINFO['dbhost'],
                              self.DBINFO['lnname'], self.DBINFO['pwname'], self.DBINFO['dbport'])   
      if self.VALUES['TBL']:
         tablenames = self.VALUES['TBL']
      elif getall:
         tablenames = self.allschematables();         # action on all tables
      if not (tablenames and action): self.show_usage('pgddl')
      self.PGLOG['LOGFILE'] = "pgddl.log"
      self.cmdlog("pgddl {}".format(' '.join(argv)))

      # process all or given tables to add/drop table/pkey/index/reference/field
      def start_actions(self):
         act = self.PGACT['TBL'][0]
         if act: self.process_tables(tablenames, act, 'TBL')
         for opt in self.PGACT:
            act = self.PGACT[opt][0]
            if opt == 'TBL' or not act: continue
            names = self.VALUES[opt] if opt in self.VALUES and self.VALUES[opt] else None
            self.process_tables(tablenames, act, opt, names)
         self.cmdlog()

# main function to excecute this script
def main():
   object = PgDDL()
   object.read_parameters()
   object.start_actions()
   object.pgexit(0)

# call main() to start program
if __name__ == "__main__": main()
