#!/usr/bin/env python
#
#  Mar. 14, 2017  David Lawrence
#
# This script can be used to copy the HDDS XML and XSD files into
# the CCDB. It will use the CCDB pointed to by the CCDB_CONNECTION
# environment variable and the HDDS files pointed to by the
# HDDS_HOME environment variable.
#
# The run range, variation, and comment are all set by editing this
# script (see section below). This will copy all files with a ".xml"
# or ".xsd" suffix. 
# 
# Prior to running this script, the top-level GEOMETRY directory needs
# to exist. This can be done by hand using the following command:
#
#  ccdb mkdir GEOMETRY
#
# To use the geometry with sim-recon, one needs:
#
#  1. JANA 0.7.8 or greater
#  2. JANA_GEOMETRY_URL set to ccdb:///GEOMETRY/main_HDDS.xml
#
# Note that the file given in JANA_GEOMETRY_URL is the top-level
# geometry file. For example, setting it to:
# ccdb:///GEOMETRY/cpp_main.xml will cause the CPP-specific 
# geometry to be used.
#
# All files are copied completely by this script into CCDB. No explicit
# processing is done, but empirically it was noticed that an XML file
# that had \r\n instead of just \n had the \r characters stripped out
# at some point. This generally will not cause an issue unless you
# are checking the md5 checksum versus a file that still has those
# characters.
#

import ccdb
import io
import os
import sys
import glob

#-----------------------------------------------------
#--------------- EDIT THESE VALUES -------------------
MIN_RUN   = 30000
MAX_RUN   = 39999
VARIATION = 'default'
COMMENT   = 'Copied from HDDS'
#-----------------------------------------------------



CCDB_CONNECTION = os.getenv('CCDB_CONNECTION')
if not CCDB_CONNECTION:
	print 'CCDB_CONNECTION not set!'
	sys.exit(-1)

HDDS_HOME = os.getenv('HDDS_HOME')
if not HDDS_HOME:
	print 'HDDS_HOME not set!'
	sys.exit(-1)


# create CCDB api class
provider = ccdb.AlchemyProvider()     # this class has all CCDB manipulation functions
provider.connect(CCDB_CONNECTION)     # use usual connection string to connect to database
provider.authentication.current_user_name = os.getenv('USER')  # to have a name in logs


# Get list of all ML files in HDDS directory and loop over them
xmlfiles  = glob.glob('%s/*.xml' % HDDS_HOME)
xmlfiles += glob.glob('%s/*.xsd' % HDDS_HOME)
for xmlfile in xmlfiles:

	# read file
	xml_content = io.open(xmlfile, "r").read()

	# prepare content
	# create_assignment accepts tabled data
	# rows and columns number must correspond to table definition
	tabled_data = [[xml_content]]
	
	itemname = os.path.basename(xmlfile)
	#itemname = itemname.replace('.', '_')
	fullpath = '/GEOMETRY/' + itemname
	
	# Check if this type table already exists.
	try:
		provider.get_type_table(fullpath)
	except:
		print 'Type table ' + fullpath + ' doesn\'t exist. Creating ...'
		provider.create_type_table( itemname, '/GEOMETRY', 1, [('xml','string')], comment='created with hdds_2_ccdb.py')
	

	# add data to database
	print 'Writing file ' + xmlfile + ' to ' + itemname
	provider.create_assignment(
		data=tabled_data,
		path=fullpath,
		variation_name=VARIATION,
		min_run=MIN_RUN,
		max_run=MAX_RUN,
		comment=COMMENT)

	
