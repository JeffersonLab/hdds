#/bin/tcsh
root -b -q make_xml.C
cat preamble.xml lgd.xml volume_defs.xml > ForwardEMcal_HDDS.xml

