#!/bin/bash
#
# snap.sh - grab a snapshort of the GlueX hdds geometry from ccdb
#           for a given run number.
#
# author: richard.t.jones at uconn.edu
# version: may 17, 2018

function usage() {
    echo "Usage: snap.sh <run_number> [ <variation> ]"
    exit 1
}

if ! echo $1 | grep -q '^[0-9][0-9]*$'; then
    usage
elif [[ $# -gt 1 ]]; then
    var=$2
else
    var=default
fi
run=$1

mkdir -p $run.$var
for sys in ForwardEMcal_HDDS.xml \
           cpp_HDDS.xml \
           ForwardTOF_HDDS.xml \
           ForwardDC_HDDS.xml \
           main_HDDS.xml \
           UpstreamEMveto_HDDS.xml \
           CentralDC_HDDS.xml \
           StartCntr_HDDS.xml \
           BarrelEMcal_HDDS.xml \
           Target_HDDS.xml \
           Material_HDDS.xml \
           DIRC_HDDS.xml \
           PairSpect_HDDS.xml \
           Solenoid_HDDS.xml \
           ForwardMWPC_HDDS.xml \
           CerenkovCntr_HDDS.xml \
           Regions_HDDS.xml \
           BeamLine_HDDS.xml \
           GapEMcal_HDDS.xml \
           ComptonEMcal_HDDS.xml \
           DIRC_HDDS_original.xml \
           HDDS-1_1.xsd \
           TargetCPP_HDDS.xml
 do
    ccdb -r $run -v "$var" dump /GEOMETRY/$sys \
    | awk '/Working run is/{next}/^#Copied from/{next}/^ *<\?xml/{print substr($0,3);next}{print}' \
    | head -n -1 >$run.$var/$sys
 done
