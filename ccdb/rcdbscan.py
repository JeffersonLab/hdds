#!/usr/bin/env python
#
# rcdbscan.py - does a scan of the GlueX rcdb looking up run conditions
#               related to the beamline, namely which primary collimator
#               was in place and which TPOL converter.

import os
import sys
import rcdb

# Open database connection
connect = os.environ["RCDB_CONNECTION"]
db = rcdb.RCDBProvider(connect)

conds = ["collimator_diameter", "polarimeter_converter"]
values = db.select_values(val_names=conds)
run = -1
col = 0
con = 0
for value in values.rows:
   lastcol = col
   lastcon = con
   run = value[0]
   if value[1] == "5.0mm hole":
      col = 50
   elif value[1] == "3.4mm hole":
      col = 34
   elif value[1] == "Blocking":
      col = 0
   if value[2] == "Retracted":
      con = 0
   elif value[2] == "Be 75um":
      con = 75
   elif value[2] == "Be 750um":
      con = 750
   if col != lastcol or con != lastcon:
      print run, col, con
