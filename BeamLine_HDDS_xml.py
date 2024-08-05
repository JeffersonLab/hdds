#!/usr/bin/env python3
#
# Generates BeamLine_HDDS.xml from literal xml source below
# with formulas instead of numerical values for many offsets.
#
# author: richard.t.jones at uconn.edu
# version: june 3, 2024

# dimensions are in cm
inches = 2.54

# outer boundaries of alcove area
cave_height = 270 
cave_width = 450
cave_length = 1250
wall_thickness = 1500
beam_to_floor = 100

# beam pipe parameters
profiler_start = 57.4
activecol_start = 70.6
taghall_pipelength = 30
taghall_piperadius = (12.4, 12.7)
presweep_pipe_start = 259.3
presweep_flange_thick = 1
presweep_flange_window = 0.1
presweep_piperadius = (1.935*inches/2, 2*inches/2)
postsweep_piperadius = (2.435*inches/2, 2.5*inches/2)

# inner shield wall dimensions
concrete_wall1_height = beam_to_floor
concrete_wall1_width = cave_width - 91.4
concrete_wall1_beamhole = 2.2*inches
concrete_wall1_thickness = 111
concrete_wall1_start = 275.4
concrete_wall1_leadthick = 10
concrete_wall2_height = beam_to_floor
concrete_wall2_width = cave_width - 91.4
concrete_wall2_beamhole = 2.2*inches
concrete_wall2_thickness = 111
concrete_wall2_start = 482.8

# cave exit wall stack
exitwall_inner_beamhole = 2.7*inches
exitwall_inner_boxsize = 25
exitwall_inner_boxlength = 20
exitwall_middle_boxsize = 80
exitwall_outer_width = 135.9 + 138.4
exitwall_outer_height = 199
exitwall_start = 1004.9
exitwall_thickness = 1126.8 - 1004.9
exitwall_side_thickness = 61.0
exitwall_lead_thickness = 5
exitwall_steel_thickness = 0.25*inches

# sweep magnet
sweep_magnet_length = 355.6
sweep_magnet_start = 602.6

# KLF target - origin is upstream face of borated poly
klftarget_assy_start = 85.4
klftarget_be_start = 40.16
klftarget_be_length = 40
klftarget_be_radius = 3.0
klftarget_uphole_size = 15.2
klftarget_downhole_size = 7.6
klftarget_w_gap = 0.5
klftarget_w_length = 10
klftarget_w_radius = 7.5
klftarget_full_length = 162.56
klftarget_full_width = 137.2
klftarget_full_height = 127.3
klftarget_poly_thickness = 10.16


xml_source = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--DOCTYPE HDDS>

  Hall D Geometry Data Base: KLF Beam Line
  ****************************************

     version 1.0: Initial version	-rtj
     - based on https://halldweb.jlab.org/wiki/images/f/ff/KPT_Collimator_cave_layout.pdf


<HDDS specification="v1.0" xmlns="http://www.gluex.org/hdds">
-->

<section name        = "BeamLine"
         version     = "1.0"
         date        = "2024-06-01"
         author      = "R.T. Jones"
         top_volume  = "collimatorPackage"
         specification = "v1.0">

<!-- Origin of collimatorPackage is center of the beam at the entrance face to
     of the Hall D alcove, as assigned z=0 in the KPT_Collimator_cave_layout drawing.	-->

  <composition name="collimatorPackage">
    <posXYZ volume="ShieldedCollimator" X_Y_Z="0.0  0.0  {(cave_length - wall_thickness)/2}" />
  </composition>

  <box name="SHLD" X_Y_Z="{cave_width + wall_thickness*2}
                          {cave_height + wall_thickness*2}
                          {cave_length + wall_thickness}" material="Concrete" />
  <composition name="ShieldedCollimator" envelope="SHLD">
    <posXYZ volume="pipeFromTaggerHall" X_Y_Z="0.0  0.0 {-cave_length/2}" />
    <posXYZ volume="collimatorCave" X_Y_Z="0.0 {cave_height/2 - beam_to_floor} {wall_thickness/2}" />
  </composition>  
 
  <box  name="CAVE" X_Y_Z="{cave_width} {cave_height} {cave_length}" material="Air" />
  <composition name="collimatorCave" envelope="CAVE">
    <posXYZ volume="collimatorStack" X_Y_Z="0.0  {beam_to_floor - cave_height/2}  {-cave_length}" />
    <posXYZ volume="DET3" X_Y_Z="0.0  {cave_height/2 - 3}  0.0" />
  </composition>
 
  <composition name="collimatorSubCave">
    <posXYZ volume="collimatorStack" />
  </composition>

  <composition name="collimatorStack">
    <posXYZ volume="BeamPipe0"     X_Y_Z="0 0 0" />
    <!--posXYZ volume="PFLD"          X_Y_Z="0.0  0.0  {profiler_start}" />
    <posXYZ volume="PFSC"          X_Y_Z="0.0  0.0  {profiler_start + 2}" />
    <posXYZ volume="PFSC"          X_Y_Z="0.0  0.0  {profiler_start + 6}" /-->
    <posXYZ volume="DET1"          X_Y_Z="0.0  0.0  60.0" />
    <!--posXYZ volume="ColDetector"   X_Y_Z="0.0  0.0  {activecol_start}" /-->
    <posXYZ volume="KLFtargetAssy" X_Y_Z="0.0  0.0  {klftarget_assy_start}" />
    <posXYZ volume="Flange1"       X_Y_Z="0.0  0.0  {presweep_pipe_start - presweep_flange_thick}" />
    <posXYZ volume="BeamPipe1"     X_Y_Z="0.0  0.0  {presweep_pipe_start}" />
    <posXYZ volume="ConcreteWall1" X_Y_Z="{-(cave_width - concrete_wall1_width)/2}  0.0  {concrete_wall1_start}" />
    <posXYZ volume="LeadWall1"     X_Y_Z="{-(cave_width - concrete_wall1_width)/2}  0.0  {concrete_wall1_start + concrete_wall1_thickness}" />
    <posXYZ volume="BeamPipe2"     X_Y_Z="0.0  0.0 {concrete_wall1_start + concrete_wall1_thickness + concrete_wall1_leadthick}" />
    <posXYZ volume="ConcreteWall2" X_Y_Z="{+(cave_width - concrete_wall1_width)/2}  0.0  {concrete_wall2_start}" />
    <posXYZ volume="BeamPipe3"     X_Y_Z="0.0  0.0  {concrete_wall2_start + concrete_wall2_thickness}" />
    <posXYZ volume="sweepMagnet1"  X_Y_Z="0.0  0.0  {sweep_magnet_start}" />
    <posXYZ volume="BeamPipe4"     X_Y_Z="0.0  0.0  {sweep_magnet_start + sweep_magnet_length}" />
    <posXYZ volume="shieldingWall" X_Y_Z="0.0  0.0  {exitwall_start}" />
    <posXYZ volume="BeamPipe5"     X_Y_Z="0.0  0.0  {exitwall_start + exitwall_thickness + exitwall_lead_thickness + 2*exitwall_steel_thickness}" />
  </composition>
  
<!-- Beam Pipe 0 -->

  <composition name="pipeFromTaggerHall" envelope="PFTH">
    <posXYZ volume="PFTV" />
  </composition>

  <tubs name="PFTH" Rio_Z="0.0 {taghall_piperadius[1]} {taghall_pipelength}" material="Iron" />
  <tubs name="PFTV" Rio_Z="0.0 {taghall_piperadius[0]} {taghall_pipelength}" material="Vacuum" />

  <composition name="BeamPipe0">
    <posXYZ volume="BeamPipe0Tube"    X_Y_Z="0.0  0.0  25.0" />
    <posXYZ volume="BeamPipe0Flange1" X_Y_Z="0.0  0.0  48.58" />
    <posXYZ volume="BeamPipe0ExitWindow" X_Y_Z="0.0  0.0  50.0" />
    <posXYZ volume="BeamPipe0Flange2" X_Y_Z="0.0  0.0  51.42" />
  </composition>

  <composition name="BeamPipe0Tube" envelope="BPTO">
    <posXYZ volume="BPTI" />
  </composition>

  <tubs name="BPTO" Rio_Z="0.0  12.7  50.0" material="Iron" />
  <tubs name="BPTI" Rio_Z="0.0  12.4  50.0" material="Vacuum" />

  <composition name="BeamPipe0Flange1">
    <posXYZ volume="BFO1" />
  </composition>

  <tubs name="BFO1" Rio_Z="12.7  15.24  2.84" material="Iron" />

  <composition name="BeamPipe0ExitWindow">
    <posXYZ volume="FCAP" X_Y_Z="0.0  0.0  0.0125" />
  </composition>

  <tubs name="FCAP" Rio_Z="0.0   10.16   0.025" material="Kapton" />

  <composition name="BeamPipe0Flange2">
    <posXYZ volume="BFO2" />
  </composition>

  <tubs name="BFO2" Rio_Z="10.16  15.24  2.84" material="Iron" />


<!-- KLF Target Assembly -->

  <composition name="KLFtargetAssy" envelope="KLFA">
    <posXYZ volume="KLFtargetEnclosure" X_Y_Z="0.0  0.0  0.0" />
    <posXYZ volume="KLFE" X_Y_Z="0.0  0.0  {-(klftarget_full_length - klftarget_poly_thickness)/2}" />
    <posXYZ volume="KLFE" X_Y_Z="0.0  0.0  {+(klftarget_full_length - klftarget_poly_thickness)/2}" />
  </composition>

  <composition name="KLFtargetEnclosure" envelope="KLFB">
    <posXYZ volume="KLFtargetCavity" X_Y_Z="0.0  0.0  {-klftarget_full_length/2 + klftarget_poly_thickness +
                          (klftarget_be_start - klftarget_poly_thickness + klftarget_be_length + klftarget_w_gap + klftarget_w_length + 1)/2}" />
    <posXYZ volume="KLFD" X_Y_Z="0.0  0.0  {klftarget_full_length/2 - klftarget_poly_thickness -
                          (klftarget_be_start - klftarget_poly_thickness + klftarget_be_length + klftarget_w_gap + klftarget_w_length + 1)/2}" />
  </composition>

  <composition name="KLFtargetCavity" envelope="KLFC">
    <posXYZ volume="KLFT" X_Y_Z="0.0  0.0  {klftarget_be_start - klftarget_poly_thickness + klftarget_be_length/2}" />
    <posXYZ volume="KLFW" X_Y_Z="0.0  0.0  {klftarget_be_start - klftarget_poly_thickness + klftarget_be_length + klftarget_w_gap + klftarget_w_length/2}" />
  </composition>

  <box name="KLFA" X_Y_Z="{klftarget_full_width}
                          {klftarget_full_height}
                          {klftarget_full_length}"
       material="Polyethylene" />
  <box name="KLFB" X_Y_Z="{klftarget_full_width - klftarget_poly_thickness*2}
                          {klftarget_full_height - klftarget_poly_thickness*2}
                          {klftarget_full_length - klftarget_poly_thickness*2}"
       material="Lead" />
  <box name="KLFC" X_Y_Z="{klftarget_uphole_size} 
                          {klftarget_uphole_size}
                          {klftarget_be_start - klftarget_poly_thickness + klftarget_be_length + klftarget_w_gap + klftarget_w_length + 1}"
       material="Air" />
  <box name="KLFD" X_Y_Z="{klftarget_downhole_size} 
                          {klftarget_downhole_size}
                          {klftarget_full_length - klftarget_poly_thickness - klftarget_be_start - klftarget_be_length - klftarget_w_gap - klftarget_w_length - 1}"
       material="Air" />
  <box name="KLFE" X_Y_Z="{klftarget_downhole_size} 
                          {klftarget_downhole_size}
                          {klftarget_poly_thickness}"
       material="Air" />
  <tubs name="KLFT" Rio_Z="0.0 {klftarget_be_radius} {klftarget_be_length}" material="Beryllium" />
  <tubs name="KLFW" Rio_Z="0.0 {klftarget_w_radius} {klftarget_w_length}" material="Beryllium" />

<!-- First section of vacuum pipe -->

  <composition name="Flange1">
    <posXYZ volume="BF1R" X_Y_Z="0.0  0.0  {presweep_flange_thick/2}" />
    <posXYZ volume="BF1W" X_Y_Z="0.0  0.0  {presweep_flange_thick/2}" />
  </composition>

  <tubs name="BF1R" Rio_Z="{presweep_piperadius[0]} {presweep_piperadius[1] + 3} {presweep_flange_thick}" material="Iron" />
  <tubs name="BF1W" Rio_Z="0.0  {presweep_piperadius[0]}  {presweep_flange_window}" material="Aluminum" />

  <composition name="BeamPipe1">
    <posXYZ volume="BeamPipe1Tube" X_Y_Z="0.0  0.0 {(concrete_wall1_start - presweep_pipe_start)/2}" />
  </composition>

  <composition name="BeamPipe1Tube" envelope="BP1O">
    <posXYZ volume="BP1I" />
  </composition>

  <tubs name="BP1O" Rio_Z="0.0  {presweep_piperadius[1]}  {concrete_wall1_start - presweep_pipe_start}" material="Iron" />
  <tubs name="BP1I" Rio_Z="0.0  {presweep_piperadius[0]}  {concrete_wall1_start - presweep_pipe_start}" material="Vacuum" />

<!-- First concrete shielding wall -->

  <composition name="ConcreteWall1">
    <posXYZ volume="ConcreteWall1BeamBox" X_Y_Z="0.0  0.0  {concrete_wall1_thickness/2}" />
  </composition>

  <composition name="ConcreteWall1BeamBox" envelope="CW1B">
    <posXYZ volume="ConcreteWall1BeamHole" X_Y_Z="{+(cave_width - concrete_wall1_width)/2}  0.0  0.0" />
  </composition>

  <composition name="ConcreteWall1BeamHole" envelope="CW1H">
    <posXYZ volume="ConcreteWall1BeamPipe" />
  </composition>

  <composition name="ConcreteWall1BeamPipe" envelope="CW1P">
    <posXYZ volume="CW1V" />
  </composition>

  <box name="CW1B" X_Y_Z="{concrete_wall1_width}  {concrete_wall1_height}  {concrete_wall1_thickness}" material="Concrete"/>
  <box name="CW1H" X_Y_Z="{concrete_wall1_beamhole}  {concrete_wall1_beamhole}  {concrete_wall1_thickness}" material="Air"/>
  <tubs name="CW1P" Rio_Z="0.0  {presweep_piperadius[1]}  {concrete_wall1_thickness}" material="Iron" />
  <tubs name="CW1V" Rio_Z="0.0  {presweep_piperadius[0]}  {concrete_wall1_thickness}" material="Vacuum" />

  <composition name="LeadWall1">
    <posXYZ volume="LeadWall1Box" X_Y_Z="0.0  0.0  {concrete_wall1_leadthick/2}" />
  </composition>

  <composition name="LeadWall1Box" envelope="LW1B">
    <posXYZ volume="LeadWall1BeamHole" X_Y_Z="{+(cave_width - concrete_wall1_width)/2}  0.0  0.0" />
  </composition>

  <composition name="LeadWall1BeamHole" envelope="LW1H">
    <posXYZ volume="LeadWall1BeamPipe" />
  </composition>

  <composition name="LeadWall1BeamPipe" envelope="LW1P">
    <posXYZ volume="LW1V" />
  </composition>

  <box name="LW1B" X_Y_Z="{concrete_wall1_width}  {concrete_wall1_height}  {concrete_wall1_leadthick}" material="Lead"/>
  <box name="LW1H" X_Y_Z="{concrete_wall1_beamhole}  {concrete_wall1_beamhole}  {concrete_wall1_leadthick}" material="Air"/>
  <tubs name="LW1P" Rio_Z="0.0  {presweep_piperadius[1]}  {concrete_wall1_leadthick}" material="Iron" />
  <tubs name="LW1V" Rio_Z="0.0  {presweep_piperadius[0]}  {concrete_wall1_leadthick}" material="Vacuum" />

<!-- Second section of vacuum pipe -->

  <composition name="BeamPipe2">
    <posXYZ volume="BeamPipe2Tube" X_Y_Z="0.0  0.0  {(concrete_wall2_start - concrete_wall1_start -
                                                      concrete_wall1_thickness - concrete_wall1_leadthick)/2}" />
  </composition>

  <composition name="BeamPipe2Tube" envelope="BP2O">
    <posXYZ volume="BP2I" />
  </composition>

  <tubs name="BP2O" Rio_Z="0.0  {presweep_piperadius[1]}  {concrete_wall2_start - concrete_wall1_start - 
                                                           concrete_wall1_thickness - concrete_wall1_leadthick}"
        material="Iron" />
  <tubs name="BP2I" Rio_Z="0.0  {presweep_piperadius[0]}  {concrete_wall2_start - concrete_wall1_start -
                                                           concrete_wall1_thickness - concrete_wall1_leadthick}"
        material="Vacuum" />

<!-- Second concrete shielding wall -->

  <composition name="ConcreteWall2">
    <posXYZ volume="ConcreteWall2Box" X_Y_Z="0.0  0.0  {concrete_wall2_thickness/2}" />
  </composition>

  <composition name="ConcreteWall2Box">
    <posXYZ volume="ConcreteWall2BeamHole" X_Y_Z="{-(cave_width - concrete_wall2_width)/2}  0.0  0.0" />
  </composition>

  <composition name="ConcreteWall2BeamHole" envelope="CW2H">
    <posXYZ volume="ConcreteWall2BeamPipe" />
  </composition>

  <composition name="ConcreteWall2BeamPipe" envelope="CW2P">
    <posXYZ volume="CW2V" />
  </composition>

  <box name="CW2H" X_Y_Z="{concrete_wall2_beamhole}  {concrete_wall2_beamhole}  {concrete_wall2_thickness}" material="Air"/>
  <tubs name="CW2P" Rio_Z="0.0  {presweep_piperadius[1]}  {concrete_wall1_thickness}" material="Iron" />
  <tubs name="CW2V" Rio_Z="0.0  {presweep_piperadius[0]}  {concrete_wall1_thickness}" material="Vacuum" />

<!-- Third section of vacuum pipe -->

  <composition name="BeamPipe3">
    <posXYZ volume="BeamPipe3Tube" X_Y_Z="0.0  0.0  {(sweep_magnet_start - concrete_wall2_start - concrete_wall2_thickness)/2}" />
  </composition>

  <composition name="BeamPipe3Tube" envelope="BP3O">
    <posXYZ volume="BP3I" />
  </composition>

  <tubs name="BP3O" Rio_Z="0.0  {presweep_piperadius[1]}  {sweep_magnet_start - concrete_wall2_start - concrete_wall2_thickness}"
        material="Iron" />
  <tubs name="BP3I" Rio_Z="0.0  {presweep_piperadius[0]}  {sweep_magnet_start - concrete_wall2_start - concrete_wall2_thickness}"
        material="Vacuum" />

<!-- Permanent sweep magnet -->

  <composition name="sweepMagnet1">
    <posXYZ volume="sweepMagnet1Box" X_Y_Z="0.0  0.0  {sweep_magnet_length/2}" />
  </composition>

  <composition name="sweepMagnet1Box" envelope="MAG1">
    <posXYZ volume="POL1" X_Y_Z="0.0  +7.425  0.0" />
    <posXYZ volume="POL1" X_Y_Z="0.0  -7.425  0.0" />
    <posXYZ volume="GAP1" X_Y_Z="-9.855  0.0  0.0" />
    <posXYZ volume="GAP1" X_Y_Z="+9.855  0.0  0.0" />
    <posXYZ volume="MagnetPipe1" />
  </composition> 

  <box name="MAG1" X_Y_Z="29.2  24.8  {sweep_magnet_length}" material="Air" >
    <apply region="sweepDipoleBfield" /> 
  </box> 

  <box name="POL1" X_Y_Z="29.2  9.95  {sweep_magnet_length}" material="Iron" />
  <box name="GAP1" X_Y_Z="9.49   4.9  {sweep_magnet_length}" material="Iron" />

  <composition name="MagnetPipe1" envelope="MPO1">
    <posXYZ volume="MPI1" />
  </composition>

  <eltu name="MPO1" Rxy_Z="5.11  2.45  {sweep_magnet_length}" material="Iron" />
  <eltu name="MPI1" Rxy_Z="4.95  2.29  {sweep_magnet_length}" material="Vacuum" />

<!-- Fourth section of vacuum pipe -->

  <composition name="BeamPipe4">
    <posXYZ volume="BeamPipe4Tube" X_Y_Z="0.0  0.0  {(exitwall_start - sweep_magnet_start - sweep_magnet_length)/2}" />
  </composition>

  <composition name="BeamPipe4Tube" envelope="BP4O">
    <posXYZ volume="BP4I" />
  </composition>

  <tubs name="BP4O" Rio_Z="0.0  {postsweep_piperadius[1]}  {exitwall_start - sweep_magnet_start - sweep_magnet_length}"
        material="Iron" />
  <tubs name="BP4I" Rio_Z="0.0  {postsweep_piperadius[0]}  {exitwall_start - sweep_magnet_start - sweep_magnet_length}"
        material="Vacuum" />

<!-- Last shielding wall in the cave -->

  <composition name="shieldingWall">
    <posXYZ volume="shieldingWallBox" X_Y_Z="0.0  0.0  {exitwall_thickness/2}" />
    <posXYZ volume="shieldingWallPlates" X_Y_Z="0.0  0.0  {exitwall_thickness + exitwall_lead_thickness + exitwall_steel_thickness*2}" />
    <posXYZ volume="SWTB" X_Y_Z="0.0  {+(beam_to_floor/2 + exitwall_outer_height/4)}  {exitwall_thickness - exitwall_side_thickness/2}" />
    <posXYZ volume="SWTB" X_Y_Z="0.0  {-(beam_to_floor/2 + exitwall_outer_height/4)}  {exitwall_thickness - exitwall_side_thickness/2}" />
    <posXYZ volume="SWLR" X_Y_Z="0.0  {-(cave_width/4 + exitwall_outer_width/4)}  {exitwall_thickness - exitwall_side_thickness/2}" />
    <posXYZ volume="SWLR" X_Y_Z="0.0  {+(cave_width/4 + exitwall_outer_width/4)}  {exitwall_thickness - exitwall_side_thickness/2}" />
  </composition>

  <composition name="shieldingWallBox" envelope="SWOB">
    <posXYZ volume="shieldingWallBoxMiddle" />
  </composition>

  <composition name="shieldingWallBoxMiddle" envelope="SWMB">
    <posXYZ volume="shieldingWallBoxInner" />
  </composition>

  <composition name="shieldingWallBoxInner" envelope="SWIB">
    <posXYZ volume="shieldingWallLeadBox" X_Y_Z="0.0  0.0  {-exitwall_thickness/2 + exitwall_inner_boxlength/2}" />
    <posXYZ volume="shieldingWallLeadBox" X_Y_Z="0.0  0.0  {-exitwall_thickness/2 + exitwall_inner_boxlength*3/2}" />
    <posXYZ volume="shieldingWallLeadBox" X_Y_Z="0.0  0.0  {+exitwall_thickness/2 - exitwall_inner_boxlength/2}" />
    <posXYZ volume="shieldingWallHoleBox" X_Y_Z="0.0  0.0  {exitwall_inner_boxlength/2}" />
  </composition>

  <composition name="shieldingWallLeadBox" envelope="SWLB">
    <posXYZ volume="shieldingWallLeadHole" />
  </composition>

  <composition name="shieldingWallLeadHole" envelope="SWLH">
    <posXYZ volume="shieldingWallLeadPipe" />
  </composition>

  <composition name="shieldingWallLeadPipe" envelope="SWLP">
    <posXYZ volume="SWLV" />
  </composition>

  <composition name="shieldingWallHoleBox" envelope="SWHB">
    <posXYZ volume="shieldingWallHolePipe" />
  </composition>

  <composition name="shieldingWallHolePipe" envelope="SWHP">
    <posXYZ volume="SWHV" />
  </composition>

  <box name="SWOB" X_Y_Z="{exitwall_outer_width}  {exitwall_outer_height}  {exitwall_thickness}" material="Concrete" />
  <box name="SWMB" X_Y_Z="{exitwall_middle_boxsize}  {exitwall_middle_boxsize}  {exitwall_thickness}" material="Concrete" />
  <box name="SWIB" X_Y_Z="{exitwall_inner_boxsize}  {exitwall_inner_boxsize}  {exitwall_thickness}" material="Concrete" />
  <box name="SWLB" X_Y_Z="{exitwall_inner_boxsize}  {exitwall_inner_boxsize}  {exitwall_inner_boxlength}" material="Lead" />
  <box name="SWLH" X_Y_Z="{exitwall_inner_beamhole}  {exitwall_inner_beamhole}  {exitwall_inner_boxlength}" material="Air" />
  <tubs name="SWLP" Rio_Z="0.0  {postsweep_piperadius[1]}  {exitwall_inner_boxlength}" material="Iron" />
  <tubs name="SWLV" Rio_Z="0.0  {postsweep_piperadius[0]}  {exitwall_inner_boxlength}" material="Vacuum" />
  <box name="SWHB" X_Y_Z="{exitwall_inner_boxsize}  {exitwall_inner_boxsize}  {exitwall_thickness - 3*exitwall_inner_boxlength}" material="Air" />
  <tubs name="SWHP" Rio_Z="0.0  {postsweep_piperadius[1]}  {exitwall_thickness - 3*exitwall_inner_boxlength}" material="Iron" />
  <tubs name="SWHV" Rio_Z="0.0  {postsweep_piperadius[0]}  {exitwall_thickness - 3*exitwall_inner_boxlength}" material="Vacuum" />
  <box name="SWTB" X_Y_Z="{exitwall_outer_width}  {beam_to_floor - exitwall_outer_height/2}  {exitwall_side_thickness}" material="Concrete" />
  <box name="SWLR" X_Y_Z="{cave_width/2 - exitwall_outer_width/2}  {2*beam_to_floor}  {exitwall_side_thickness}" material="Concrete" />

  <composition name="shieldingWallPlates">
    <posXYZ volume="shieldingPlateSteelPlate" X_Y_Z="0.0  0.0  {exitwall_steel_thickness/2}" />
    <posXYZ volume="shieldingPlateLeadPlate" X_Y_Z="0.0  0.0  {exitwall_steel_thickness + exitwall_lead_thickness/2}" />
    <posXYZ volume="shieldingPlateSteelPlate" X_Y_Z="0.0  0.0  {exitwall_lead_thickness + exitwall_steel_thickness*3/2}" />
  </composition>

  <composition name="shieldingPlateSteelPlate" envelope="SWSP">
    <posXYZ volume="shieldingPlateSteelHole" />
  </composition>

  <composition name="shieldingPlateSteelHole" envelope="SWSH">
    <posXYZ volume="shieldingPlateSteelPipe" />
  </composition>

  <composition name="shieldingPlateSteelPipe" envelope="SWSI">
    <posXYZ volume="SWSV" />
  </composition>

  <composition name="shieldingPlateLeadPlate" envelope="SWPL">
    <posXYZ volume="shieldingPlateSteelHole" />
  </composition>

  <composition name="shieldingPlateLeadHole" envelope="SWPH">
    <posXYZ volume="shieldingPlateLeadPipe" />
  </composition>

  <composition name="shieldingPlateLeadPipe" envelope="SWPP">
    <posXYZ volume="SWPV" />
  </composition>

  <box name="SWSP" X_Y_Z="{exitwall_outer_width}  {exitwall_outer_height}  {exitwall_steel_thickness}" material="Iron" />
  <box name="SWSH" X_Y_Z="{exitwall_inner_beamhole}  {exitwall_inner_beamhole}  {exitwall_steel_thickness}" material="Air" />
  <tubs name="SWSI" Rio_Z="0.0  {postsweep_piperadius[1]}  {exitwall_steel_thickness}" material="Iron" />
  <tubs name="SWSV" Rio_Z="0.0  {postsweep_piperadius[0]}  {exitwall_steel_thickness}" material="Vacuum" />
  <box name="SWPL" X_Y_Z="{exitwall_outer_width}  {exitwall_outer_height}  {exitwall_lead_thickness}" material="Lead" />
  <box name="SWPH" X_Y_Z="{exitwall_inner_beamhole}  {exitwall_inner_beamhole}  {exitwall_lead_thickness}" material="Air" />
  <tubs name="SWPP" Rio_Z="{exitwall_inner_beamhole}  {exitwall_inner_beamhole}  {exitwall_lead_thickness}" material="Iron" />
  <tubs name="SWPV" Rio_Z="{exitwall_inner_beamhole}  {exitwall_inner_beamhole}  {exitwall_lead_thickness}" material="Vacuum" />

<!-- Fifth section of vacuum pipe -->

  <composition name="BeamPipe5">
    <posXYZ volume="BeamPipe5Tube" X_Y_Z="0.0  0.0  {(cave_length + exitwall_start + exitwall_thickness + exitwall_lead_thickness + 2*exitwall_steel_thickness)/2}" />
  </composition>

  <composition name="BeamPipe5Tube" envelope="BP5O">
    <posXYZ volume="BP5I" />
  </composition>

  <tubs name="BP5O" Rio_Z="0.0  {postsweep_piperadius[1]}  {cave_length - exitwall_start - exitwall_thickness - exitwall_lead_thickness - 2*exitwall_steel_thickness}"
        material="Iron" />
  <tubs name="BP5I" Rio_Z="0.0  {postsweep_piperadius[0]}  {cave_length - exitwall_start - exitwall_thickness - exitwall_lead_thickness - 2*exitwall_steel_thickness}"
        material="Vacuum" />

<!-- Pseudo volumes for background studies -->
    
  <tubs name="DET1" Rio_Z="0.0  50.0  2.0" material="Air" />
  <box name="DET2" X_Y_Z="450.0  270.0  0.1" material="Vacuum" />
  <box name="DET3" X_Y_Z="450.0  2.0  918.0" material="Air" />
  <box name="DET4" X_Y_Z="1700.0  1200.0  2.0" material="Vacuum" />
  <box name="DET5" X_Y_Z="1700.0  1198.0  2.0" material="Air" />
  <box name="DET6" X_Y_Z="1700.0  2.0  3000.0" material="Air" />
  <!--box name="DET7" X_Y_Z="1700.0  1198.0  2.0" material="Air" /-->
  <tubs name="DET7" Rio_Z="0.0 1.7399  2.0" material="Vacuum"
        comment="disk detector inside beam pipe at target entrance" />
  <box name="DET8" X_Y_Z="10.0  10.0  1.0" material="Scintillator" sensitive="true" />

<!-- Approximation for the beam profiler -->

<box name="PFSC" X_Y_Z="0.8  12.8  0.2" material="Scintillator" sensitive="true" />
<box name="PFLD" X_Y_Z="0.0  10.0  0.1" material="Lead" />

<!-- Following is the definition of the active collimator.  It sits
     on the upstream end of the primary collimator and acts as an
     active absorber with segmented detection of the beam intensity.
-->

  <composition name="ColDetector" envelope="INSU">
    <posXYZ volume="ColAssemblyFinal" X_Y_Z="0.0 0.0 0.50" />
    <posXYZ volume="HOUF" X_Y_Z="0.0  0.0  -1.85" />
  </composition>

  <composition name="ColAssemblyFinal" envelope="HOUS">
    <posXYZ volume="ColAssemblyInitial" X_Y_Z="0.0  0.0  -0.15" />
  </composition>
  
  <composition name="ColAssemblyInitial" envelope="AIRH">
    <mposPhi volume="DIV1" ncopy="4" Phi0="0" dPhi="90" R_Z="3.375 0." />  
    <mposPhi volume="DIV2" ncopy="4" Phi0="45" dPhi="90" />  
    <mposPhi volume="innerPinCushionWedge" ncopy="4" Phi0="45" dPhi="90" />
    <mposPhi volume="outerPinCushionWedge" ncopy="4" Phi0="45" dPhi="90" />
  </composition>

  <tubs name="INSU" Rio_Z="0.25   7.36  4.20" material="BoronNitride" />
 
  <tubs name="HOUS" Rio_Z="0.25   6.70  3.20" material="Aluminum" />
 
  <tubs name="HOUF" Rio_Z="0.25   6.85  0.50" material="Aluminum" />
 
  <tubs name="AIRH" Rio_Z="0.25   6.5002  2.9" material="Air" />
  <box  name="DIV1" X_Y_Z="6.25  0.1  2.9" material="Aluminum" />
  <tubs name="DIV2" Rio_Z="2.7   2.8  2.9" profile="-42.870 85.740"
                                           material="Aluminum" />

  <composition name="innerPinCushionWedge" envelope="ACWI">
    <posXYZ volume="ACBI" X_Y_Z="0.0 0.0 -0.85" />
    <posXYZ volume="innerPinCushionRow_1" X_Y_Z="0.276 0.0 0.40" />
    <posXYZ volume="innerPinCushionRow_2" X_Y_Z="0.376 0.0 0.40" />
    <posXYZ volume="innerPinCushionRow_3" X_Y_Z="0.476 0.0 0.40" />
    <posXYZ volume="innerPinCushionRow_4" X_Y_Z="0.576 0.0 0.40" />
    <posXYZ volume="innerPinCushionRow_5" X_Y_Z="0.676 0.0 0.40" />
    <posXYZ volume="innerPinCushionRow_6" X_Y_Z="0.776 0.0 0.40" />
  </composition>
  <composition name="innerPinCushionRow_1" envelope="AIR1">
    <mposY volume="PIN1" ncopy="3" Y0="-0.10" dY="0.10" />
  </composition>
  <composition name="innerPinCushionRow_2" envelope="AIR2">
    <mposY volume="PIN1" ncopy="3" Y0="-0.10" dY="0.10" />
  </composition>
  <composition name="innerPinCushionRow_3" envelope="AIR3">
    <mposY volume="PIN1" ncopy="5" Y0="-0.20" dY="0.10" />
  </composition>
  <composition name="innerPinCushionRow_4" envelope="AIR4">
    <mposY volume="PIN1" ncopy="7" Y0="-0.30" dY="0.10" />
  </composition>
  <composition name="innerPinCushionRow_5" envelope="AIR5">
    <mposY volume="PIN1" ncopy="7" Y0="-0.30" dY="0.10" />
  </composition>
  <composition name="innerPinCushionRow_6" envelope="AIR6">
    <mposY volume="PIN1" ncopy="9" Y0="-0.40" dY="0.10" />
  </composition>

  <composition name="outerPinCushionWedge" envelope="ACWO">
    <posXYZ volume="ACBO" X_Y_Z="0.0 0.0 -0.85" />
    <posXYZ volume="outerPinCushionRow_1" X_Y_Z="2.625 -1.50 0.40" />
    <posXYZ volume="outerPinCushionRow_1" X_Y_Z="2.625 +1.50 0.40" />
    <posXYZ volume="outerPinCushionRow_2" X_Y_Z="2.725 -1.40 0.40" />
    <posXYZ volume="outerPinCushionRow_2" X_Y_Z="2.725 +1.40 0.40" />
    <posXYZ volume="outerPinCushionRow_3" X_Y_Z="2.825 -1.35 0.40" />
    <posXYZ volume="outerPinCushionRow_3" X_Y_Z="2.825 +1.35 0.40" />
    <posXYZ volume="outerPinCushionRow_4" X_Y_Z="2.925 -1.15 0.40" />
    <posXYZ volume="outerPinCushionRow_4" X_Y_Z="2.925 +1.15 0.40" />
    <posXYZ volume="outerPinCushionRow_5" X_Y_Z="3.025 0.0 0.40" />
    <posXYZ volume="outerPinCushionRow_6" X_Y_Z="3.125 0.0 0.40" />
    <posXYZ volume="outerPinCushionRow_7" X_Y_Z="3.225 0.0 0.40" />
    <posXYZ volume="outerPinCushionRow_8" X_Y_Z="3.325 0.0 0.40" />
    <posXYZ volume="outerPinCushionRow_9" X_Y_Z="3.425 0.0 0.40" />
    <posXYZ volume="outerPinCushionRow_10" X_Y_Z="3.525 0.0 0.40" />
    <posXYZ volume="outerPinCushionRow_11" X_Y_Z="3.625 0.0 0.40" />
  </composition>
  <composition name="outerPinCushionRow_1" envelope="AOR1">
    <posXYZ volume="PIN1" />
  </composition>
  <composition name="outerPinCushionRow_2" envelope="AOR2">
    <mposY volume="PIN1" ncopy="3" Y0="-0.10" dY="0.10" />
  </composition>
  <composition name="outerPinCushionRow_3" envelope="AOR3">
    <mposY volume="PIN1" ncopy="6" Y0="-0.25" dY="0.10" />
  </composition>
  <composition name="outerPinCushionRow_4" envelope="AOR4">
    <mposY volume="PIN1" ncopy="10" Y0="-0.45" dY="0.10" />
  </composition>
  <composition name="outerPinCushionRow_5" envelope="AOR5">
    <mposY volume="PIN1" ncopy="35" Y0="-1.70" dY="0.10" />
  </composition>
  <composition name="outerPinCushionRow_6" envelope="AOR6">
    <mposY volume="PIN1" ncopy="35" Y0="-1.70" dY="0.10" />
  </composition>
  <composition name="outerPinCushionRow_7" envelope="AOR7">
    <mposY volume="PIN1" ncopy="37" Y0="-1.80" dY="0.10" />
  </composition>
  <composition name="outerPinCushionRow_8" envelope="AOR8">
    <mposY volume="PIN1" ncopy="39" Y0="-1.90" dY="0.10" />
  </composition>
  <composition name="outerPinCushionRow_9" envelope="AOR9">
    <mposY volume="PIN1" ncopy="39" Y0="-1.90" dY="0.10" />
  </composition>
  <composition name="outerPinCushionRow_10" envelope="AORA">
    <mposY volume="PIN1" ncopy="41" Y0="-2.00" dY="0.10" />
  </composition>
  <composition name="outerPinCushionRow_11" envelope="AORB">
    <mposY volume="PIN1" ncopy="41" Y0="-2.00" dY="0.10" />
  </composition>

  <tubs name="ACWI" Rio_Z="0.25 2.5  2.5" profile="-33. 66."
         material="Air" comment="active collimator inner wedge" />  
  <tubs name="ACWO" Rio_Z="2.97  6.0  2.5" profile="-33. 66."
         material="Air" comment="active collimator outer wedge" />  
  <tubs name="ACBI" Rio_Z="0.25 2.5  0.8" profile="-32. 64."
         material="SoftTungsten" comment="inner wedge base plate" />  
  <tubs name="ACBO" Rio_Z="3.0  6.0  0.8" profile="-30. 60."
         material="SoftTungsten" comment="outer wedge base plate" />  

  <box name="AIR1" X_Y_Z="0.051 0.30 1.7" material="Air" />
  <box name="AIR2" X_Y_Z="0.051 0.40 1.7" material="Air" />
  <box name="AIR3" X_Y_Z="0.051 0.50 1.7" material="Air" />
  <box name="AIR4" X_Y_Z="0.051 0.70 1.7" material="Air" />
  <box name="AIR5" X_Y_Z="0.051 0.80 1.7" material="Air" />
  <box name="AIR6" X_Y_Z="0.051 0.90 1.7" material="Air" />

  <box name="AOR1" X_Y_Z="0.051 0.10 1.7" material="Air" />
  <box name="AOR2" X_Y_Z="0.051 0.30 1.7" material="Air" />
  <box name="AOR3" X_Y_Z="0.051 0.70 1.7" material="Air" />
  <box name="AOR4" X_Y_Z="0.051 1.00 1.7" material="Air" />
  <box name="AOR5" X_Y_Z="0.051 3.50 1.7" material="Air" />
  <box name="AOR6" X_Y_Z="0.051 3.50 1.7" material="Air" />
  <box name="AOR7" X_Y_Z="0.051 3.70 1.7" material="Air" />
  <box name="AOR8" X_Y_Z="0.051 3.90 1.7" material="Air" />
  <box name="AOR9" X_Y_Z="0.051 3.90 1.7" material="Air" />
  <box name="AORA" X_Y_Z="0.051 4.10 1.7" material="Air" />
  <box name="AORB" X_Y_Z="0.051 4.10 1.7" material="Air" />

  <box name="PIN1" X_Y_Z="0.051 0.051 1.7" material="SoftTungsten" />

  <composition name="beamPipe">
    <!-- not present in the KLF beamline -->
    <posXYZ volume="NULL" />
  </composition>

  <composition name="SixWayCross">
    <!-- not present in the KLF beamline -->
    <posXYZ volume="NULL" />
  </composition>

  <box name="NULL" X_Y_Z="0.0  0.0  0.0" material="Air" />
 
</section>

<!-- </HDDS> -->
"""


import math

for line in xml_source.split('\n'):
    print(line)

