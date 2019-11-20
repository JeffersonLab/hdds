#!/usr/bin/env python
#
# hddm2ccdb.py - script for reading and writing from the /GEOMETRY
#                tables in ccdb.
#
# author: richard.t.jones at uconn.edu
# version: may 17, 2018
#
# Usage: hddm2ccdb.py [-r <run>] [-v <var>] command
#  where command is one of
#    * ls <table>
#    * get <table>
#    * set <table> <comment>
#  with
#    <run> is a run number starting at 1 [1]
#    <var> is a variation string [default]
#    <table> is a GEOMETRY table name, eg BeamLine_HDDS.xml
#    <comment> is a log comment to go with the ccdb update, in quotes
#

import os
import sys
import ccdb

def usage():
   print """
   Usage: hddm2ccdb.py [-r <run>] [-v <var>] command
     where command is one of
       * ls <table>
       * get <table>
       * set <table> <comment>
     with
       <run> is a run number or range, like 10222 or 10222-10224 [1]
       <var> is a variation string [default]
       <table> is a GEOMETRY table name, eg BeamLine_HDDS.xml
       <comment> is a log comment to go with the ccdb update, in quotes
   """
   sys.exit(1)

def do_ls_table(tpath):
   """
   Print the metadata of the ccdb table identified in tpath 
   """
   table = provider.get_type_table(tpath)
   try:
      runs = run.split('-')
      ass = provider.get_assignment(tpath, runs[0], var)
   except:
      print "no entry found"
      return
   print "run range:", "{0}-{1}".format(ass.run_range.min, ass.run_range.max)
   print "variation:", ass.variation.name
   print "modified:", ass.modified
   print "comment:", ass.comment
   print "author:", ass.author.name

def do_get_table(tpath):
   """
   Print the contents of the ccdb table identified in tpath 
   """
   table = provider.get_type_table(tpath)
   try:
      runs = run.split('-')
      ass = provider.get_assignment(tpath, runs[0], var)
   except:
      print "no entry found"
      return
   sys.stdout.write(ass.constant_set.vault)

def do_set_table(tpath, comment):
   """
   Pull xml content from stdin, push into a new table row in ccdb
   """
   content = sys.stdin.read()
   runs = run.split('-')
   if len(runs) == 1:
      runs.append(ccdb.INFINITE_RUN)
   ass = provider.create_assignment([[content]], tpath, 
                                    runs[0], runs[1],
                                    var, comment)


run = "1"
var = "default"
ls_table = ""
get_table = ""
set_table = ""
comment = ""
i = 1
while i < len(sys.argv[1:]):
   if sys.argv[i][:2] == "-r":
      if len(sys.argv[i]) > 2:
         run = sys.argv[i][2:]
      else:
         i += 1
         run = sys.argv[i]
   elif sys.argv[i][:2] == "-v":
      if len(sys.argv[i]) > 2:
         var = sys.argv[i][2:]
      else:
         i += 1
         var = sys.argv[i]
   elif sys.argv[i] == "ls":
      i += 1
      ls_table = sys.argv[i]
   elif sys.argv[i] == "get":
      i += 1
      get_table = sys.argv[i]
   elif sys.argv[i] == "set":
      i += 1
      set_table = sys.argv[i]
      comment = " ".join(sys.argv[i+1:])
   i += 1

if not ls_table and not get_table and not set_table:
   usage()

# Connect to CCDB DB
sqlite_connect_str = os.environ["JANA_CALIB_URL"]
provider = ccdb.AlchemyProvider()
provider.connect(sqlite_connect_str)
provider.authentication.current_user_name = "jonesrt"

# Get list of users by id so we can print names later
users = {}
ccdb_users = provider.get_users()
for user in ccdb_users:
   users[user.id] = user.name

if ls_table:
   do_ls_table("/GEOMETRY/" + ls_table)
if get_table:
   do_get_table("/GEOMETRY/" + get_table)
if set_table:
   do_set_table("/GEOMETRY/" + set_table, comment)
