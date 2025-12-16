#!/usr/bin/env python3
##################################################################################
#     Title: pgchksum
#    Author: Zaihua Ji, zji@ucar.edu
#      Date: 05/24/2021
#             2025-04-09 transferred to package rda_python_dbms from
#             https://github.com/NCAR/rda-utility-programs.git
#             2025-12-15 convert to class PgChksum
#   Purpose: re-evaluate checksums, data sizes and timestamps for files archived
#            on glade, object store and Globus Quasar server; and optionally to fix them
#    Github: https://github.com/NCAR/rda-python-dbms.git
##################################################################################
import sys
import re
import time
from rda_python_common.pg_file import PgFile
from rda_python_common.pg_cmd import PgCMD
from rda_python_common.pg_split import PgSplit

class PgChksum(PgFile, PgCMD, PgSplit):

   def __init__(self):
      super().__init__()  # initialize parent class
      self.PGSUM = {
         'd' : [],   # delay mode option, value array
         's' : [],   # specialist login name array for email notice, default to none
         'f' : [],   # file name array, default to none
         'i' : [],   # dataset id array, default for all
         'o' : '',   # r - random, s - sequencial
         'p' : '',   # working path, default to self.PGLOG['UPDTWKP']/pgchksum
         'c' : 0,    # number of files to re-evauate checksums, default 0 for all
         'k' : 0,    # skip the number of files to re-evauate checksums
         'm' : 0,    # 1 for check/fix files missing checksum only
         'n' : 0,    # 1 for not sending email
         'r' : 0,    # running time in unit of hour
         't' : '',   # file type, W(Web), S(Saved) or Q(Quasar)
         'x' : 0     # 1 for fixing checksum, data size and timestamp
      }
      self.PVALS = {
         'STEP' : None,
         'CND' : None,
         'TYPE' : None,
         'OFFSET' : '',
         'emllog' : self.LOGWRN,
         'emlsum' : self.LOGWRN,
         'emlerr' : self.LOGERR,
         'begin' : 0,
         'end' : 0
      }
      self.pgname = "pgchksum"
      self.pgcmd = None

   # function to read parameters
   def read_parameters(self):
      argv = sys.argv[1:]
      option = None
      for arg in argv:
         ms = re.match(r'^-(.+)$', arg)
         if ms:
            option = ms.group(1)
            if option == 'b':
               self.PGLOG['BCKGRND'] = 1   # processing in backgroup mode
               option = None
            elif option in self.PGSUM:
               if option in ['m', 'n', 'x']:
                  self.PGSUM[option] = 1
                  option = None
            else:
               self.pglog(arg + ": Unknown option", self.LGEREX)
         elif option:
            if isinstance(self.PGSUM[option], list):
               if option == 'i': arg = self.format_dataset_id(arg)
               self.PGSUM[option].append(arg)
            elif not self.PGSUM[option]:
               if option == 'o' and arg not in ['s', 'r']:
                  self.pglog("{}: Value must be 'r' or 's' for Option -{}".format(arg, option), self.LGEREX)
               self.PGSUM[option] = int(arg) if self.PGSUM[option] == 0 else arg
               option = None
            else:
               self.pglog("{}: value specified already for Option -{}".format(arg, option), self.LGEREX)
         else:
            self.pglog(arg + ": value passed without leading Option", self.LGEREX)
      if not self.PGSUM['t']:
         print("Usage: pgchksum -t (W|S|Q) [-b] [-m] [-n] [-x] [-c FileCount] \\")
         print("                [-d [Hostnames] [RerunCount]] [-f FileNames] [-i DatasetIDs] \\")
         print("                [-k SkipCount] [-o r|s] [-s Specialists]")
         print("  -b - background process and no screen output")
         print("  -c - File count to re-evaluate checksum; for all gathered files if not specified")
         print("  -d - delayed mode background/batch processes on RDA machines/DAV SLURM nodes")
         print("  -f - Re-evaluate the specify File names only")
         print("  -i - Dataset IDs the files belong; for all files if not specified")
         print("  -k - skip the given file count to re-evaluate checksum")
         print("  -m - check/fix files missing checksum only, works with a single dsid provided via option -i")
         print("  -n - do not send email notice to anybody")
         print("  -o - order files radomly (r) or sequencially (s) by file ID, default to not ordering")
         print("  -p - working path, default to self.PGLOG['UPDTWKP']/pgchksum")
         print("  -r - batch running hours, works with -d")
         print("  -s - specialists to receive email notice in addtion to the running specialist")
         print("  -t - mandatory file type: W-Web, S-Saved or Q-Quasar files")
         print("  -x - fix the missing and wrong checksum, data size and tiemstamp")
         self.pgexit(0)
      elif self.PGSUM['t'] not in 'QSW':
         self.pglog(self.PGSUM['t'] + ": Unknown File Type, must be one of 'QSW'", self.LGEREX)
       # set different log file
      self.PGLOG['LOGFILE'] = self.pgname + '.log'
      self.set_suid(self.PGLOG['EUID'])
      self.PVALS['begin'] = int(time.time())
      self.pgcmd = "{} {}".format(self.pgname, self.argv_to_string(argv, 1))
      self.cmdlog("{} {}".format(self.pgcmd, self.PVALS['begin']))
      if not self.PGSUM['n']:
         self.PVALS['emllog'] = self.LGWNEM
         self.PVALS['emlsum'] = self.LOGWRN|self.EMLSUM
         self.PVALS['emlerr'] = self.LOGERR|self.EMEROL
         self.PGDBI['LOGACT'] = self.PVALS['emlerr']
         if self.PGSUM['s']: self.add_carbon_copy(self.PGSUM['s'])
      if not self.PGSUM['p']: self.PGSUM['p'] = self.PGLOG['UPDTWKP']+ "/pgchksum"

   # function to start actions
   def start_actions(self):
      self.change_local_directory(self.PGSUM['p'], self.PVALS['emlerr'])
      if self.PGSUM['d']:
         if self.PGSUM['r'] > 0: self.set_one_boption('qoptions', "-l walltime={}:00:00".format(self.PGSUM['r']))
         self.init_dscheck(0, '', self.pgname, '', 'C'+self.PGSUM['t'], '', None, self.PGSUM['d'])
      if self.PGSUM['t'] == 'W':
         cnt = self.get_checksum_wfilelist() 
      elif self.PGSUM['t'] == 'S':
         cnt = self.get_checksum_sfilelist() 
      elif self.PGSUM['t'] == 'Q':
         cnt = self.get_checksum_bfilelist() 
      else:
         self.pglog(self.PGSUM['t'] + ": Unknown File Type", self.LGEREX)
      if self.PGSUM['d']:
         if self.PGSUM['r'] > 0: self.set_one_boption('qoptions', "-l walltime={}:00:00".format(self.PGSUM['r']))
         self.init_dscheck(0, '', self.pgname, '', 'C'+self.PGSUM['t'], '', None, self.PGSUM['d'])
      if cnt:
         fcnt = self.PGSUM['c']
         pgrecs = self.PGSUM['f']
         if self.PGLOG['DSCHECK']: self.set_dscheck_fcount(fcnt, self.PVALS['emlerr'])
         self.PVALS['STEP'] = fcnt/100
         if self.PVALS['STEP'] < 10: self.PVALS['STEP'] = 10   # minimum incremental step
         if self.PVALS['STEP'] > 500: self.PVALS['STEP'] = 500   # maximum incremental step
         msg = 'Check '
         if self.PGSUM['x']: msg += 'and Fix '
         msg += "checksum/size/timestamp for {} {} files{}".format(fcnt, self.PVALS['TYPE'], self.PVALS['OFFSET'])
         self.pglog(msg, self.PVALS['emlsum'])
         cnts = {'cnt' : 0, 'pcnt' : 0, 'xcnt' : 0, 'ecnt' : 0, 'mcnt' : 0, 'ncnt' : 0, 'tcnt' : 0, 'scnt' : 0}
         if self.PGSUM['t'] == 'W':
            self.evaluate_webfile_checksum(fcnt, pgrecs, cnts)
         elif self.PGSUM['t'] == 'S':
            self.evaluate_savedfile_checksum(fcnt, pgrecs, cnts)
         else:
            self.evaluate_backfile_checksum(fcnt, pgrecs, cnts)
         self.dump_progress(fcnt, fcnt, cnts, self.PVALS['emlsum'])
         self.PVALS['end'] = int(time.time())
         if not self.PGSUM['n']: self.send_check_email(cnts['cnt'], fcnt)
      if self.PGLOG['DSCHECK']:
         if self.PGLOG['ERRMSG']:
            self.record_dscheck_error(self.PGLOG['ERRMSG'])
         else:
            self.record_dscheck_status("D")
      self.cmdlog(None, self.PVALS['end'])

   # send an email for checking result
   def send_check_email(self, cnt, fcnt):
      s = 'es' if cnt > 1 else ''
      cstr = 'With {} Mismatch{}'.format(cnt, s)
      subject = "PGCHKSUM for {} {} Files {}".format(self.PVALS['TYPE'], fcnt, cstr)
      buf = self.cmd_execute_time(self.pgcmd, self.PVALS['end']-self.PVALS['begin']) + " Finished  on " + self.PGLOG['HOSTNAME']
      if self.PVALS['CND']: buf += "\n{} Files: {}".format(self.PVALS['TYPE'], self.PVALS['CND'])   
      self.set_email(buf, self.EMLTOP)
      if self.PGLOG['DSCHECK']:
         self.build_customized_email("dscheck", "einfo", "cindex = {}".format(self.PGLOG['DSCHECK']['cindex']),
                                      subject, self.LOGWRN)
      else:
         self.pglog(subject, self.LOGWRN|self.SNDEML)
   
   # get the checksum filelist for wfile
   def get_checksum_wfilelist(self):
      self.PVALS['TYPE'] = "Web"
      self.PVALS['BUCKET'] = 'rda-data'
      flds = "wid, wfile, type, locflag, data_size, checksum, date_modified, time_modified"
      if self.PGSUM['f']:
         pgrecs = self.pgmhget('wfile', 'wid, dsid', {'wfile' : self.PGSUM['f']})
         cnt = len(pgrecs['wid']) if pgrecs else 0
         if cnt > 0:
            self.PGSUM['f'] = {}
            for i in range(cnt):
               dsid = pgrecs['dsid'][i]
               pgrec = self.pgget_wfile(dsid, flds, 'wid = {}'.format(pgrecs['wid'][i]))
               pgrec['dsid'] = dsid
               self.addrecord(self.PGSUM['f'], pgrec, i)
         return cnt
      fcnt = self.PGSUM['c']
      self.PVALS['CND'] = ''
      dscnt = len(self.PGSUM['i'])
      if dscnt == 1:
         dsid = self.PGSUM['i'][0]
         if self.PGLOG['DSCHECK']: self.set_dscheck_attribute("dsid", dsid, self.PVALS['emlerr'])
         if self.PGSUM['m']: self.PVALS['CND'] += "(checksum IS NULL OR checksum < ' ') "
      elif dscnt > 1:
         self.PVALS['CND'] = "dsid IN ({}) ".format(','.join(self.PGSUM['i']))
      if self.PGSUM['o']: self.PVALS['CND'] += "ORDER BY {} ".format('wid' if self.PGSUM['o'] == 's' else "RANDOM()")
      if fcnt: self.PVALS['CND'] += "LIMIT {} ".format(fcnt)
      if self.PGSUM['k']:
         self.PVALS['OFFSET'] = "OFFSET {}".format(self.PGSUM['k'])
         self.PVALS['CND'] += self.PVALS['OFFSET']
      if dscnt == 1:
         wfrecs = self.pgmget_wfile(dsid, flds, self.PVALS['CND'])
         cnt = len(wfrecs['wid']) if wfrecs else 0
      else:
         pgrecs = self.pgmget('wfile', 'wid, dsid', self.PVALS['CND'])
         cnt = len(pgrecs['wid']) if pgrecs else 0
         wfrecs = {}
         if cnt > 0:
            for i in range(cnt):
               dsid = pgrecs['dsid'][i]
               pgrec = self.pgget_wfile(dsid, flds, 'wid = {}'.format(pgrecs['wid'][i]))
               pgrec['dsid'] = dsid
               self.addrecord(wfrecs, pgrec, i)
      if cnt > 0:
         if fcnt == 0 or fcnt > cnt: self.PGSUM['c'] = cnt
         self.PGSUM['f'] = wfrecs
      else:
         self.pglog("No {} file found for {}".format(self.PVALS['TYPE'], self.PVALS['CND']), self.PVALS['emlerr'])
      return cnt
   
   # get the checksum filelist for sfile
   def get_checksum_sfilelist(self):
      self.PVALS['TYPE'] = "Saved"
      self.PVALS['BUCKET'] = 'rda-decsdata'
      flds = "sid, sfile, dsid, type, locflag, data_size, checksum, date_modified, time_modified"
      hcnd = {}
      fcnt = self.PGSUM['c']
      cnt = len(self.PGSUM['f'])
      if cnt > 0:
         self.PGSUM['f'] = self.pgmhget('sfile', flds, {'sfile' : self.PGSUM['f']})
         return (len(self.PGSUM['f']['sid']) if self.PGSUM['f'] else 0)
      self.PVALS['CND'] = ''
      cnt = len(self.PGSUM['i'])
      if cnt == 1:
         dsid = self.PGSUM['i'][0]
         self.PVALS['CND'] = "dsid = '{}'".format(dsid)
         if self.PGLOG['DSCHECK']: self.set_dscheck_attribute("dsid", dsid, self.PVALS['emlerr'])
      elif cnt > 1:
         self.PVALS['CND'] = "dsid IN ({})".format(','.join(self.PGSUM['i']))
      if self.PGSUM['m']:
         if self.PVALS['CND']: self.PVALS['CND'] += " AND "
         self.PVALS['CND'] += "(checksum IS NULL OR checksum < ' ')"
      if self.PGSUM['o']: self.PVALS['CND'] += " ORDER BY " + ('sid' if self.PGSUM['o'] == 's' else "RANDOM()")
      if fcnt: self.PVALS['CND'] += " LIMIT {}".format(fcnt)
      if self.PGSUM['k']:
         self.PVALS['OFFSET'] = " OFFSET {}".format(self.PGSUM['k'])
         self.PVALS['CND'] += self.PVALS['OFFSET']
      pgrecs = self.pgmget('sfile', flds, self.PVALS['CND'])
      cnt = len(pgrecs['sid']) if pgrecs else 0
      if cnt > 0:
         if fcnt == 0 or fcnt > cnt: self.PGSUM['c'] = cnt
         self.PGSUM['f'] = pgrecs
      else:
         self.pglog("No {} file found for {}".format(self.PVALS['TYPE'], self.PVALS['CND']), self.PVALS['emlerr'])
      return cnt
   
   # get the checksum filelist for bfile
   def get_checksum_bfilelist(self):
      self.PVALS['TYPE'] = "Quasar"
      flds = "bid, bfile, dsid, type, data_size, checksum, date_modified, time_modified"
      fcnt = self.PGSUM['c']
      cnt = len(self.PGSUM['f'])
      if cnt > 0:
         self.PGSUM['f'] = self.pgmhget('bfile', flds, {'bfile' : self.PGSUM['f']})
         return (len(self.PGSUM['f']['bid']) if self.PGSUM['f'] else 0)
      self.PVALS['CND'] = ''
      cnt = len(self.PGSUM['i'])
      if cnt == 1:
         dsid = self.PGSUM['i'][0]
         self.PVALS['CND'] = "dsid = '{}' AND ".format(dsid)
         if self.PGLOG['DSCHECK']: self.set_dscheck_attribute("dsid", dsid, self.PVALS['emlerr'])
      elif cnt > 1:
         self.PVALS['CND'] = "dsid IN ({}) AND ".format(','.join(self.PGSUM['i']))
      if self.PGSUM['m']:
         self.PVALS['CND'] += "(checksum IS NULL OR checksum < ' ') AND "
      self.PVALS['CND'] += "status = 'A'"
      if self.PGSUM['o']: self.PVALS['CND'] += " ORDER BY " + ('bid' if self.PGSUM['o'] == 's' else "RANDOM()")
      if fcnt: self.PVALS['CND'] += " LIMIT {}".format(fcnt)
      if self.PGSUM['k']:
         self.PVALS['OFFSET'] = " OFFSET {}".format(self.PGSUM['k'])
         self.PVALS['CND'] += self.PVALS['OFFSET']
      pgrecs = self.pgmget('bfile', flds, self.PVALS['CND'])
      cnt = len(pgrecs['bid']) if pgrecs else 0
      if cnt > 0:
         if fcnt == 0 or fcnt > cnt: self.PGSUM['c'] = cnt
         self.PGSUM['f'] = pgrecs
      else:
         self.pglog("No {} file found for {}".format(self.PVALS['TYPE'], self.PVALS['CND']), self.PVALS['emlerr'])
      return cnt
   
   # dump the program running progress
   def dump_progress(self, ccnt, fcnt, cnts, logact):
      cntmsg = str(ccnt)
      chkmsg = "Integrity-Checked"
      ttlmsg = " of {}".format(fcnt) if fcnt > ccnt else ""
      if cnts['pcnt'] > 0:
         cntmsg += "/{}".format(cnts['pcnt'])
         chkmsg += "/Passed-checking"
      if cnts['xcnt'] > 0:
         cntmsg += "/{}".format(cnts['xcnt'])
         chkmsg += "/Fixed"
      if cnts['mcnt'] > 0:
         cntmsg += "/{}".format(cnts['mcnt'])
         chkmsg += "/Checksum-mismatch"
      if cnts['ncnt'] > 0:
         cntmsg += "/{}".format(cnts['ncnt'])
         chkmsg += "/Checksum-miss"
      if cnts['scnt'] > 0:
         cntmsg += "/{}".format(cnts['scnt'])
         chkmsg += "/Size-mismatch"
      if cnts['tcnt'] > 0:
         cntmsg += "/{}".format(cnts['tcnt'])
         chkmsg += "/Timestamp-mismatch"
      if cnts['ecnt'] > 0:
         cntmsg += "/{}".format(cnts['ecnt'])
         chkmsg += "/Nonexist"
      self.pglog("{}{} {} files{} {}".format(cntmsg, ttlmsg, self.PVALS['TYPE'], self.PVALS['OFFSET'], chkmsg), logact)
   
   # evaluate checksums for web files
   def evaluate_webfile_checksum(self, fcnt, pgrecs, cnts):
      for i in range(fcnt):
         if i and i%self.PVALS['STEP'] == 0:
            if self.PGLOG['DSCHECK']: self.add_dscheck_dcount(self.PVALS['STEP'], 0, self.PVALS['emlerr'])
            self.dump_progress(i, fcnt, cnts, self.LOGWRN)
         pgrec = self.onerecord(pgrecs, i)
         locflag = pgrec['locflag']
         if locflag == 'O':
            fname = "{}/{}".format(pgrec['dsid'], pgrec['wfile'])
            self.evaluate_object_file(fname, pgrec, 'rda-data', cnts)
         else:
            fname = pgrec['wfile']
            if not re.match(r'^/', fname):
               fname = "{}/{}/{}".format(self.PGLOG['DSDHOME'], pgrec['dsid'], fname)
            self.evaluate_disk_file(fname, pgrec, cnts)
   
   # evaluate checksums for saved files
   def evaluate_savedfile_checksum(self, fcnt, pgrecs, cnts):
      for i in range(fcnt):
         if i and i%self.PVALS['STEP'] == 0:
            if self.PGLOG['DSCHECK']: self.add_dscheck_dcount(self.PVALS['STEP'], 0, self.PVALS['emlerr'])
            self.dump_progress(i, fcnt, cnts, self.LOGWRN)
         pgrec = self.onerecord(pgrecs, i)
         locflag = pgrec['locflag']
         if locflag == 'O':
            fname = "{}/{}".format(pgrec['dsid'], pgrec['sfile'])
            self.evaluate_object_file(fname, pgrec, 'rda-decsdata', cnts)
         else:
            fname = pgrec['sfile']
            if not re.match(r'^/', fname):
               fname = "{}/{}/{}/{}".format(self.PGLOG['DECSHOME'], pgrec['dsid'], pgrec['type'], fname)
            self.evaluate_disk_file(fname, pgrec, cnts)
   
   # evaluate checksums for quasar backup files (check size and timestamp only for now)
   def evaluate_backfile_checksum(self, fcnt, pgrecs, cnts):
      for i in range(fcnt):
         if i and i%self.PVALS['STEP'] == 0:
            if self.PGLOG['DSCHECK']: self.add_dscheck_dcount(self.PVALS['STEP'], 0, self.PVALS['emlerr'])
            self.dump_progress(i, fcnt, cnts, self.LOGWRN)
         pgrec = self.onerecord(pgrecs, i)
         fname = "/{}/{}".format(pgrec['dsid'], pgrec['bfile'])
         self.evaluate_quasar_file(fname, pgrec, 'gdex-quasar', cnts)
   
   # evaluate a disk file
   def evaluate_disk_file(self, fname, pgrec, cnts):
      info = self.check_local_file(fname, 33, self.PVALS['emlerr'])   # 33 = 1+32
      if info:
         self.evaluate_file_status('DSK', fname, pgrec, info, cnts)
      else:
         self.pglog("{}: Type {} {} file is missing on Disk".format(fname, pgrec['type'], self.PVALS['TYPE']), self.PVALS['emllog'])
         cnts['ecnt'] += 1
   
   # evaluate an object file
   def evaluate_object_file(self, fname, pgrec, bucket, cnts):
      info = self.check_object_file(fname, bucket, 1, self.PVALS['emlerr'])
      if info:
         self.evaluate_file_status('OBS', "{}-{}".format(bucket, fname), pgrec, info, cnts)
      else:
         self.pglog("{}: Type {} {} file is missing in Object Store".format(fname, pgrec['type'], self.PVALS['TYPE']), self.PVALS['emllog'])
         cnts['ecnt'] += 1
   
   # evaluate a quasar file
   def evaluate_quasar_file(self, fname, pgrec, endpoint, cnts):
      info = self.check_backup_file(fname, endpoint, 65, self.PVALS['emlerr'])
      if info:
         self.evaluate_file_status('QSR', "{}-{}".format(endpoint, fname), pgrec, info, cnts)
      else:
         self.pglog("{}: Type {} {} file is missing on Quasar".format(fname, pgrec['type'], self.PVALS['TYPE']), self.PVALS['emllog'])
         cnts['ecnt'] += 1
   
   # evaluate a file status
   def evaluate_file_status(self, lname, fname, pgrec, info, cnts):
      msg = ''
      checksum = info['checksum'] if 'checksum' in info else ''
      diffsum = diffsize = 0
      if checksum:
         if not pgrec['checksum']:
            msg = "Checksum misses"
            cnts['ncnt'] += 1
            diffsum = 2
         elif checksum != pgrec['checksum']:
            msg = "Checksum mismatch"
            cnts['mcnt'] += 1
            diffsum = 1
      if info['data_size'] != pgrec['data_size']:
         if msg: msg += ", "
         msg += "Size mismatch"
         cnts['scnt'] += 1
         diffsize = 1
      difftime = self.cmptime(info['date_modified'], info['time_modified'], pgrec['date_modified'], pgrec['time_modified'])
      if difftime < 0 or msg and difftime > 0:
         if msg: msg += ", "
         msg += "Timestamp mismatch"
         cnts['tcnt'] += 1
      if msg:
         cnts['cnt'] += 1
         msg = "{}. {}: {}".format(cnts['cnt'], fname, msg)
         msg += "\n{}:".format(lname)
         msg += "{}/{}/{}/{}".format(checksum, info['data_size'], info['date_modified'], info['time_modified'])
         msg += "\nDBS:"
         msg += "{}/{}/{}/{}".format(pgrec['checksum'], pgrec['data_size'], pgrec['date_modified'], pgrec['time_modified'])
         self.pglog(msg, self.PVALS['emllog'])
         if self.PGSUM['x']:
            record = {}
            if diffsize: record['data_size'] = info['data_size']
            if diffsum: record['checksum'] = checksum
            if difftime < 0 or record and difftime:
               record['date_modified'] = info['date_modified'] 
               record['time_modified'] = info['time_modified']
            if record: cnts['xcnt'] += self.fix_file_info(self.PGSUM['t'], record, pgrec)
      else:
         cnts['pcnt'] += 1
   
   # fix file info
   def fix_file_info(self, type, record, pgrec):
      if type == 'W':
         return self.pgupdt_wfile(pgrec['dsid'], record, "wid = {}".format(pgrec['wid']))
      elif type == 'S':
         return self.pgupdt('sfile', record, "sid = {}".format(pgrec['sid']))
      else:
         return self.pgupdt('bfile', record, "bid = {}".format(pgrec['bid']))

# main function to excecute this script
def main():
   object = PgChksum()
   object.read_parameters()
   object.start_actions()
   object.pgexit(0)

# call main() to start program
if __name__ == "__main__": main()
