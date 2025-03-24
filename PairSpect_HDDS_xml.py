#!/usr/bin/env python3
#
# Generates PairSpect_HDDS.xml from literal xml source below
# with formulas instead of numerical values for some offsets.
#
# author: richard.t.jones at uconn.edu
# version: june 3, 2024

# dimensions are in cm
inches = 2.54

# z start positions are relative to cave-hall boundary
psflange1_radius = (4.0*inches/2, 4.2*inches/2)
psflange1_length = 1*inches
psflange1_start = 0

psmagnet_start = psflange1_start + psflange1_length
psmagnet_length = 132.842
psmagnet_gap = 0
psmagpipe_length = psmagnet_length
psmagpipe_radius = (2.8*inches/2, 2.9*inches/2)

pspipe2_length = 460.0
pspipe2_radius = (4.0*inches/2, 4.2*inches/2)
pspipe2_wall_start = 480.0
pspipe2_wall_size = (16.1, 240.0, 60.0)
pspipe2_pwall_size = (16.1, 240.0, 10.0)
pspipe2_donut_size = (3.0, 15.0, 20.0)

pspipe3_start = pspipe2_wall_start
pspipe3_length = 516.5
pspipe3_radius = (2.75, 8.0)


xml_source = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--DOCTYPE HDDS>

  Hall D Geometry Data Base: Pair Spectrometer in KLF Beam Line
  *************************************************************

     version 1.0: Initial version	-rtj
     - based on https://halldweb.jlab.org/wiki/images/f/ff/KPT_Collimator_cave_layout.pdf

<HDDS specification="v1.0" xmlns="http://www.gluex.org/hdds">
-->

<section name        = "PairSpectrometer"
         version     = "1.0"
         date        = "2024-06-01"
         author      = "R.T. Jones"
         top_volume  = "HALL"
         specification = "v1.0">


<!-- The pair spectrometer is situated in the detector hall 
     after the collimator cave.  Origin of PairSpectrometer
     is center of the beam at the entrance to the hall.
-->


  <composition name="PairSpectrometer">
    <posXYZ volume="PairPipe1" X_Y_Z="0.0  0.0  {psflange1_start}"/>
    <posXYZ volume="PairMagnet" X_Y_Z="0.0   0.0  {psmagnet_start}" />
    <!--posXYZ volume="PairVacChamb" X_Y_Z="0.0   0.0   -114.6007" /-->
    <posXYZ volume="PairHodoscopeNorth" X_Y_Z="+36.261    0.0   345.3074"  rot="0.0  4.57077 0.0"/>
    <posXYZ volume="PairHodoscopeSouth" X_Y_Z="-36.3013   0.0   345.3392"  rot="0.0 -4.65958 0.0"/> 
    <posXYZ volume="PairCoarseNorth" X_Y_Z="+43.5331 0.0 394.4875" rot="0.0  4.6742 0.0" /> 
    <posXYZ volume="PairCoarseSouth" X_Y_Z="-43.5345 0.0 394.4855" rot="0.0 -4.7067  0.0" />
    <posXYZ volume="PairPipe2" X_Y_Z="0.0   0.0   {psmagnet_start + psmagnet_length}"/> 
    <posXYZ volume="DET5" X_Y_Z="0.0   0.0   {psmagnet_start + psmagnet_length + pspipe3_start + pspipe3_length + 0.2}"/> 
    <posXYZ volume="DET7" X_Y_Z="0.0   0.0   {psmagnet_start + psmagnet_length + pspipe3_start + pspipe3_length + 1337}"/> 
    <!--posXYZ volume="PairShielding" X_Y_Z="0.0   0.0  432.6500" /-->
    <!--The following models the SEG blocks and additional lead shielding-->
    <!-- removed for the KLF flux detector
    <posXYZ volume="SEG1" X_Y_Z="-87.63 0.0 428.82"/>
    <posXYZ volume="SEG1" X_Y_Z="+87.63 0.0 428.82"/>
    <posXYZ volume="SEG2" X_Y_Z="-153.6 0.0 395.74"/> 
    <posXYZ volume="SEG2" X_Y_Z="+153.6 0.0 395.74"/>
    -->
  </composition>
	

<!-- Vacuum Pipe Section 1 -->

  <composition name="PairPipe1">
    <posXYZ volume="PairPipeFlange1" X_Y_Z="0.0  0.0  {psflange1_length/2}" /> 
  </composition>
  <composition name="PairPipeFlange1" envelope="HPO1" >
    <posXYZ volume="HPI1" X_Y_Z="0.0 0.0 0.0"/> 
  </composition>

  <tubs name="HPO1" Rio_Z="0.0  {psflange1_radius[1]}  {psflange1_length}" material="Iron" /> 
  <tubs name="HPI1" Rio_Z="0.0  {psflange1_radius[0]}  {psflange1_length}" material="Vacuum" /> 


<!-- Pair Spectrometer Magnet -->

  <composition name="PairMagnet">
    <posXYZ volume="EffectRegion" X_Y_Z="0.0  0.0  {psmagnet_length/2}"/> 
  </composition>

  <composition name="EffectRegion" envelope="MAG3">
    <posXYZ volume="PairMagPipe" X_Y_Z="0.0  0.0  {-psmagnet_length/2}" />
    <posXYZ volume="POL3" X_Y_Z="0.0 +29.591  1.0" />
    <posXYZ volume="POL3" X_Y_Z="0.0 -29.591  1.0" />
    <posXYZ volume="GAP3" X_Y_Z="+75.2475 0.0 1.0" />
    <posXYZ volume="GAP3" X_Y_Z="-75.2475 0.0 1.0" />
  </composition>

  <box name="MAG3" X_Y_Z="209.55  110.744  {psmagnet_length}" material="Air" >
    <apply region="PairBfield" /> 
  </box> 
  <box name="POL3" X_Y_Z="209.55  51.562  91.44" material="Iron" />
  <box name="GAP3" X_Y_Z="59.055   7.62   91.44" material="Iron" />

  <composition name="PairMagPipe">
    <posXYZ volume="PairMagPipeTube" X_Y_Z="0.0  0.0  {psmagpipe_length/2}" /> 
  </composition>
  <composition name="PairMagPipeTube" envelope="HMPO" >
    <posXYZ volume="HMPI" X_Y_Z="0.0 0.0 0.0"/> 
  </composition>

  <tubs name="HMPO" Rio_Z="0.0  {psmagpipe_radius[1]}  {psmagpipe_length}" material="Iron" /> 
  <tubs name="HMPI" Rio_Z="0.0  {psmagpipe_radius[0]}  {psmagpipe_length}" material="Vacuum" /> 


<!-- Vacuum Pipe Section 2 -->

  <composition name="PairPipe2">
    <posXYZ volume="PairPipe2Tube" X_Y_Z="0.0  0.0  {pspipe2_length/2}" /> 
    <posXYZ volume="LWAD" X_Y_Z="0.0  0.0  {pspipe2_wall_start + pspipe2_wall_size[2]/2}" />
    <posXYZ volume="LeadDonut" X_Y_Z="0.0  0.0  {pspipe2_wall_start - pspipe2_donut_size[2]/2}" />
    <posXYZ volume="LPAD" X_Y_Z="0.0  0.0  {pspipe2_wall_start + pspipe2_wall_size[2] + pspipe2_pwall_size[2]/2}" />
    <posXYZ volume="PairPipe3Tube" X_Y_Z="0.0  0.0  {pspipe3_start + pspipe3_length/2}" />
  </composition>
  <composition name="PairPipe2Tube" envelope="HPO2" >
    <posXYZ volume="HPI2" X_Y_Z="0.0  0.0  0.0" />
  </composition>
  <composition name="PairPipe3Tube" envelope="HPO3" >
    <posXYZ volume="HPI3" X_Y_Z="0.0  0.0  0.0" />
  </composition>

  <tubs name="HPO2" Rio_Z="0.0  {pspipe2_radius[1]}  {pspipe2_length}" material="Iron" /> 
  <tubs name="HPI2" Rio_Z="0.0  {pspipe2_radius[0]}  {pspipe2_length}" material="Vacuum" /> 
  <tubs name="HPO3" Rio_Z="0.0  {pspipe3_radius[1]}  {pspipe3_length}" material="Iron" /> 
  <tubs name="HPI3" Rio_Z="0.0  {pspipe3_radius[0]}  {pspipe3_length}" material="Vacuum" /> 

  <pgon name="LWAD" segments="4" profile="-45 360" material="Lead">
    <polyplane Rio_Z="{pspipe2_wall_size[0]/2}  {pspipe2_wall_size[1]/2}  {-pspipe2_wall_size[2]/2}" />
    <polyplane Rio_Z="{pspipe2_wall_size[0]/2}  {pspipe2_wall_size[1]/2}  {+pspipe2_wall_size[2]/2}" />
  </pgon>
  <pgon name="LPAD" segments="4" profile="-45 360" material="Polyethylene">
    <polyplane Rio_Z="{pspipe2_pwall_size[0]/2}  {pspipe2_pwall_size[1]/2}  {-pspipe2_pwall_size[2]/2}" />
    <polyplane Rio_Z="{pspipe2_pwall_size[0]/2}  {pspipe2_pwall_size[1]/2}  {+pspipe2_pwall_size[2]/2}" />
  </pgon>

  <composition name="LeadDonut" envelope="LDAD" >
    <posXYZ volume="LDAI" X_Y_Z="0.0  0.0  0.0" />
  </composition>
  <tubs name="LDAD" Rio_Z="0  {pspipe2_donut_size[1]}  {pspipe2_donut_size[2]}" material="Lead" />
  <tubs name="LDAI" Rio_Z="0  {pspipe2_donut_size[0]}  {pspipe2_donut_size[2]}" material="Vacuum" />


<!-- Hodoscope Counters -->

<!-- Add position of each individual counters instead of copying the volume. 
 These positions will be updated --> 

  <composition name="PairHodoscopeNorth" envelope="PSFN">
    <posXYZ volume="PSF2" X_Y_Z="12.3887  0.0  0.0"> <column value="1" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="12.1892  0.0  0.0"> <column value="2" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="11.9897  0.0  0.0"> <column value="3" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="11.7902  0.0  0.0"> <column value="4" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="11.5907  0.0  0.0"> <column value="5" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="11.3911  0.0  0.0"> <column value="6" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="11.1916  0.0  0.0"> <column value="7" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="10.9921  0.0  0.0"> <column value="8" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="10.7926  0.0  0.0"> <column value="9" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="10.5931  0.0  0.0"> <column value="10" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="10.3935  0.0  0.0"> <column value="11" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="10.194  0.0  0.0"> <column value="12" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="9.9945  0.0  0.0"> <column value="13" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="9.79499  0.0  0.0"> <column value="14" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="9.59547  0.0  0.0"> <column value="15" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="9.39595  0.0  0.0"> <column value="16" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="9.19643  0.0  0.0"> <column value="17" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="8.99691  0.0  0.0"> <column value="18" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="8.79739  0.0  0.0"> <column value="19" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="8.59788  0.0  0.0"> <column value="20" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="8.39836  0.0  0.0"> <column value="21" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="8.19884  0.0  0.0"> <column value="22" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="7.99932  0.0  0.0"> <column value="23" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="7.7998  0.0  0.0"> <column value="24" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="7.60028  0.0  0.0"> <column value="25" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="7.40076  0.0  0.0"> <column value="26" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="7.20125  0.0  0.0"> <column value="27" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="7.00173  0.0  0.0"> <column value="28" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="6.80221  0.0  0.0"> <column value="29" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="6.60269  0.0  0.0"> <column value="30" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="6.40317  0.0  0.0"> <column value="31" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="6.20365  0.0  0.0"> <column value="32" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="6.00414  0.0  0.0"> <column value="33" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="5.80462  0.0  0.0"> <column value="34" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="5.6051  0.0  0.0"> <column value="35" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="5.40558  0.0  0.0"> <column value="36" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="5.20606  0.0  0.0"> <column value="37" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="5.00654  0.0  0.0"> <column value="38" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="4.80703  0.0  0.0"> <column value="39" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="4.60751  0.0  0.0"> <column value="40" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="4.40799  0.0  0.0"> <column value="41" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="4.20847  0.0  0.0"> <column value="42" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="4.00895  0.0  0.0"> <column value="43" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="3.80943  0.0  0.0"> <column value="44" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="3.60992  0.0  0.0"> <column value="45" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="3.4104  0.0  0.0"> <column value="46" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="3.21088  0.0  0.0"> <column value="47" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="3.01136  0.0  0.0"> <column value="48" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="2.81184  0.0  0.0"> <column value="49" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="2.61232  0.0  0.0"> <column value="50" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="2.4128  0.0  0.0"> <column value="51" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="2.21329  0.0  0.0"> <column value="52" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="2.01377  0.0  0.0"> <column value="53" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="1.81425  0.0  0.0"> <column value="54" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="1.61473  0.0  0.0"> <column value="55" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="1.41521  0.0  0.0"> <column value="56" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="1.21569  0.0  0.0"> <column value="57" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="1.01618  0.0  0.0"> <column value="58" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="0.816658  0.0  0.0"> <column value="59" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="0.617139  0.0  0.0"> <column value="60" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="0.417621  0.0  0.0"> <column value="61" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="0.218102  0.0  0.0"> <column value="62" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="0.018584  0.0  0.0"> <column value="63" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-0.180934  0.0  0.0"> <column value="64" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-0.380453  0.0  0.0"> <column value="65" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-0.579971  0.0  0.0"> <column value="66" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-0.77949  0.0  0.0"> <column value="67" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-0.979008  0.0  0.0"> <column value="68" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-1.17853  0.0  0.0"> <column value="69" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-1.37804  0.0  0.0"> <column value="70" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-1.57756  0.0  0.0"> <column value="71" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-1.77708  0.0  0.0"> <column value="72" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-1.9766  0.0  0.0"> <column value="73" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-2.17612  0.0  0.0"> <column value="74" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-2.37564  0.0  0.0"> <column value="75" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-2.57516  0.0  0.0"> <column value="76" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-2.77467  0.0  0.0"> <column value="77" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-2.97419  0.0  0.0"> <column value="78" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-3.17371  0.0  0.0"> <column value="79" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-3.37323  0.0  0.0"> <column value="80" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-3.57275  0.0  0.0"> <column value="81" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-3.77227  0.0  0.0"> <column value="82" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-3.97178  0.0  0.0"> <column value="83" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-4.1713  0.0  0.0"> <column value="84" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-4.37082  0.0  0.0"> <column value="85" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-4.57034  0.0  0.0"> <column value="86" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-4.76986  0.0  0.0"> <column value="87" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-4.96938  0.0  0.0"> <column value="88" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-5.16889  0.0  0.0"> <column value="89" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-5.36841  0.0  0.0"> <column value="90" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-5.56793  0.0  0.0"> <column value="91" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-5.76745  0.0  0.0"> <column value="92" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-5.96697  0.0  0.0"> <column value="93" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-6.16649  0.0  0.0"> <column value="94" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-6.366  0.0  0.0"> <column value="95" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-6.56552  0.0  0.0"> <column value="96" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-6.76504  0.0  0.0"> <column value="97" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-6.96456  0.0  0.0"> <column value="98" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-7.16408  0.0  0.0"> <column value="99" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-7.3636  0.0  0.0"> <column value="100" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-7.56312  0.0  0.0"> <column value="101" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-7.76263  0.0  0.0"> <column value="102" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-7.96215  0.0  0.0"> <column value="103" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-8.16167  0.0  0.0"> <column value="104" /> </posXYZ>
    <posXYZ volume="PSF2" X_Y_Z="-8.36119  0.0  0.0"> <column value="105" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-8.51131  0.0  0.0"> <column value="106" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-8.61203  0.0  0.0"> <column value="107" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-8.71274  0.0  0.0"> <column value="108" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-8.81346  0.0  0.0"> <column value="109" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-8.91418  0.0  0.0"> <column value="110" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-9.0149  0.0  0.0"> <column value="111" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-9.11562  0.0  0.0"> <column value="112" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-9.21634  0.0  0.0"> <column value="113" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-9.31705  0.0  0.0"> <column value="114" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-9.41777  0.0  0.0"> <column value="115" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-9.51849  0.0  0.0"> <column value="116" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-9.61921  0.0  0.0"> <column value="117" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-9.71993  0.0  0.0"> <column value="118" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-9.82065  0.0  0.0"> <column value="119" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-9.92136  0.0  0.0"> <column value="120" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-10.0221  0.0  0.0"> <column value="121" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-10.1228  0.0  0.0"> <column value="122" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-10.2235  0.0  0.0"> <column value="123" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-10.3242  0.0  0.0"> <column value="124" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-10.425  0.0  0.0"> <column value="125" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-10.5257  0.0  0.0"> <column value="126" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-10.6264  0.0  0.0"> <column value="127" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-10.7271  0.0  0.0"> <column value="128" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-10.8278  0.0  0.0"> <column value="129" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-10.9285  0.0  0.0"> <column value="130" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-11.0293  0.0  0.0"> <column value="131" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-11.13  0.0  0.0"> <column value="132" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-11.2307  0.0  0.0"> <column value="133" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-11.3314  0.0  0.0"> <column value="134" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-11.4321  0.0  0.0"> <column value="135" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-11.5329  0.0  0.0"> <column value="136" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-11.6336  0.0  0.0"> <column value="137" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-11.7343  0.0  0.0"> <column value="138" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-11.835  0.0  0.0"> <column value="139" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-11.9357  0.0  0.0"> <column value="140" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-12.0365  0.0  0.0"> <column value="141" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-12.1372  0.0  0.0"> <column value="142" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-12.2379  0.0  0.0"> <column value="143" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-12.3386  0.0  0.0"> <column value="144" /> </posXYZ>
    <posXYZ volume="PSF1" X_Y_Z="-12.4393  0.0  0.0"> <column value="145" /> </posXYZ>    
  </composition>


<composition name="PairHodoscopeSouth" envelope="PSFS">
  <posXYZ volume="PSF2" X_Y_Z="-12.4244  0.0  0.0"> <column value="1" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-12.2244  0.0  0.0"> <column value="2" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-12.0244  0.0  0.0"> <column value="3" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-11.8244  0.0  0.0"> <column value="4" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-11.6243  0.0  0.0"> <column value="5" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-11.4243  0.0  0.0"> <column value="6" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-11.2243  0.0  0.0"> <column value="7" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-11.0243  0.0  0.0"> <column value="8" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-10.8243  0.0  0.0"> <column value="9" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-10.6243  0.0  0.0"> <column value="10" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-10.4243  0.0  0.0"> <column value="11" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-10.2242  0.0  0.0"> <column value="12" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-10.0242  0.0  0.0"> <column value="13" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-9.82422  0.0  0.0"> <column value="14" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-9.62421  0.0  0.0"> <column value="15" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-9.42419  0.0  0.0"> <column value="16" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-9.22418  0.0  0.0"> <column value="17" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-9.02416  0.0  0.0"> <column value="18" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-8.82415  0.0  0.0"> <column value="19" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-8.62414  0.0  0.0"> <column value="20" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-8.42412  0.0  0.0"> <column value="21" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-8.22411  0.0  0.0"> <column value="22" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-8.02409  0.0  0.0"> <column value="23" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-7.82408  0.0  0.0"> <column value="24" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-7.62407  0.0  0.0"> <column value="25" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-7.42405  0.0  0.0"> <column value="26" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-7.22404  0.0  0.0"> <column value="27" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-7.02402  0.0  0.0"> <column value="28" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-6.82401  0.0  0.0"> <column value="29" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-6.624  0.0  0.0"> <column value="30" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-6.42398  0.0  0.0"> <column value="31" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-6.22397  0.0  0.0"> <column value="32" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-6.02396  0.0  0.0"> <column value="33" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-5.82394  0.0  0.0"> <column value="34" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-5.62393  0.0  0.0"> <column value="35" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-5.42391  0.0  0.0"> <column value="36" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-5.2239  0.0  0.0"> <column value="37" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-5.02389  0.0  0.0"> <column value="38" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-4.82387  0.0  0.0"> <column value="39" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-4.62386  0.0  0.0"> <column value="40" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-4.42384  0.0  0.0"> <column value="41" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-4.22383  0.0  0.0"> <column value="42" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-4.02382  0.0  0.0"> <column value="43" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-3.8238  0.0  0.0"> <column value="44" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-3.62379  0.0  0.0"> <column value="45" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-3.42378  0.0  0.0"> <column value="46" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-3.22376  0.0  0.0"> <column value="47" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-3.02375  0.0  0.0"> <column value="48" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-2.82373  0.0  0.0"> <column value="49" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-2.62372  0.0  0.0"> <column value="50" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-2.42371  0.0  0.0"> <column value="51" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-2.22369  0.0  0.0"> <column value="52" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-2.02368  0.0  0.0"> <column value="53" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-1.82366  0.0  0.0"> <column value="54" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-1.62365  0.0  0.0"> <column value="55" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-1.42364  0.0  0.0"> <column value="56" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-1.22362  0.0  0.0"> <column value="57" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-1.02361  0.0  0.0"> <column value="58" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-0.823594  0.0  0.0"> <column value="59" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-0.623581  0.0  0.0"> <column value="60" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-0.423567  0.0  0.0"> <column value="61" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-0.223553  0.0  0.0"> <column value="62" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="-0.0235389  0.0  0.0"> <column value="63" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="0.176475  0.0  0.0"> <column value="64" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="0.376489  0.0  0.0"> <column value="65" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="0.576503  0.0  0.0"> <column value="66" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="0.776517  0.0  0.0"> <column value="67" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="0.976531  0.0  0.0"> <column value="68" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="1.17654  0.0  0.0"> <column value="69" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="1.37656  0.0  0.0"> <column value="70" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="1.57657  0.0  0.0"> <column value="71" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="1.77659  0.0  0.0"> <column value="72" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="1.9766  0.0  0.0"> <column value="73" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="2.17661  0.0  0.0"> <column value="74" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="2.37663  0.0  0.0"> <column value="75" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="2.57664  0.0  0.0"> <column value="76" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="2.77666  0.0  0.0"> <column value="77" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="2.97667  0.0  0.0"> <column value="78" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="3.17668  0.0  0.0"> <column value="79" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="3.3767  0.0  0.0"> <column value="80" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="3.57671  0.0  0.0"> <column value="81" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="3.77672  0.0  0.0"> <column value="82" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="3.97674  0.0  0.0"> <column value="83" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="4.17675  0.0  0.0"> <column value="84" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="4.37677  0.0  0.0"> <column value="85" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="4.57678  0.0  0.0"> <column value="86" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="4.77679  0.0  0.0"> <column value="87" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="4.97681  0.0  0.0"> <column value="88" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="5.17682  0.0  0.0"> <column value="89" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="5.37684  0.0  0.0"> <column value="90" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="5.57685  0.0  0.0"> <column value="91" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="5.77686  0.0  0.0"> <column value="92" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="5.97688  0.0  0.0"> <column value="93" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="6.17689  0.0  0.0"> <column value="94" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="6.37691  0.0  0.0"> <column value="95" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="6.57692  0.0  0.0"> <column value="96" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="6.77693  0.0  0.0"> <column value="97" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="6.97695  0.0  0.0"> <column value="98" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="7.17696  0.0  0.0"> <column value="99" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="7.37698  0.0  0.0"> <column value="100" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="7.57699  0.0  0.0"> <column value="101" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="7.777  0.0  0.0"> <column value="102" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="7.97702  0.0  0.0"> <column value="103" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="8.17703  0.0  0.0"> <column value="104" /> </posXYZ>
  <posXYZ volume="PSF2" X_Y_Z="8.37704  0.0  0.0"> <column value="105" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="8.52766  0.0  0.0"> <column value="106" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="8.62887  0.0  0.0"> <column value="107" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="8.73009  0.0  0.0"> <column value="108" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="8.8313  0.0  0.0"> <column value="109" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="8.93251  0.0  0.0"> <column value="110" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="9.03373  0.0  0.0"> <column value="111" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="9.13494  0.0  0.0"> <column value="112" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="9.23616  0.0  0.0"> <column value="113" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="9.33737  0.0  0.0"> <column value="114" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="9.43858  0.0  0.0"> <column value="115" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="9.5398  0.0  0.0"> <column value="116" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="9.64101  0.0  0.0"> <column value="117" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="9.74223  0.0  0.0"> <column value="118" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="9.84344  0.0  0.0"> <column value="119" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="9.94465  0.0  0.0"> <column value="120" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="10.0459  0.0  0.0"> <column value="121" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="10.1471  0.0  0.0"> <column value="122" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="10.2483  0.0  0.0"> <column value="123" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="10.3495  0.0  0.0"> <column value="124" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="10.4507  0.0  0.0"> <column value="125" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="10.5519  0.0  0.0"> <column value="126" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="10.6532  0.0  0.0"> <column value="127" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="10.7544  0.0  0.0"> <column value="128" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="10.8556  0.0  0.0"> <column value="129" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="10.9568  0.0  0.0"> <column value="130" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="11.058  0.0  0.0"> <column value="131" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="11.1592  0.0  0.0"> <column value="132" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="11.2604  0.0  0.0"> <column value="133" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="11.3616  0.0  0.0"> <column value="134" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="11.4629  0.0  0.0"> <column value="135" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="11.5641  0.0  0.0"> <column value="136" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="11.6653  0.0  0.0"> <column value="137" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="11.7665  0.0  0.0"> <column value="138" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="11.8677  0.0  0.0"> <column value="139" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="11.9689  0.0  0.0"> <column value="140" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="12.0701  0.0  0.0"> <column value="141" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="12.1714  0.0  0.0"> <column value="142" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="12.2726  0.0  0.0"> <column value="143" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="12.3738  0.0  0.0"> <column value="144" /> </posXYZ>
  <posXYZ volume="PSF1" X_Y_Z="12.475  0.0  0.0"> <column value="145" /> </posXYZ>
</composition>

  <box name="PSF1" X_Y_Z="0.0986 3.0 1.0" material="Scintillator" sensitive="true"/> 
  <box name="PSF2" X_Y_Z="0.1974 3.0 1.0" material="Scintillator" sensitive="true"/>

  <box name="PSFN" X_Y_Z="25.2 3.0 1.0" material="Air" comment="Mother volume for pair spectrometer fine counters" />
  <box name="PSFS" X_Y_Z="25.2 3.0 1.0" material="Air" comment="Mother volume for pair spectrometer fine counters" />



  <composition name="PairCoarseNorth" envelope="PSCN">
    <mposX volume="PSCO" Y_Z="0.0  1.1" ncopy="4" X0="-9.8243" dX="7.85942">
      <module value="2" step="2"/>
    </mposX>
    <mposX volume="PSCO" Y_Z="0.0 -1.1" ncopy="4" X0="-13.754" dX="7.85942">
      <module value="1" step="2"/>
    </mposX>
  </composition>

  <composition name="PairCoarseSouth" envelope="PSCS">
    <mposX volume="PSCO" Y_Z="0.0 1.1" ncopy="4" X0="-13.754" dX="7.85942">
      <module value="16" step="-2"/>
    </mposX>
    <mposX volume="PSCO" Y_Z="0.0 -1.1" ncopy="4" X0="-9.8243" dX="7.85942">
      <module value="15" step="-2"/>
    </mposX>
  </composition>
  
  
  <box name="PSCO" X_Y_Z="4.4 6.0 2." material="Scintillator" sensitive="true"/>     
  <box name="PSCN" X_Y_Z="33.0 6.2 5." material="Air" comment="Mother volume for pair spectrometer coarse counters"/>
  <box name="PSCS" X_Y_Z="33.0 6.2 5." material="Air" comment="Mother volume for pair spectrometer coarse counters"/>	
  

<!--Pair Lead Shielding -->

  <composition name="PairShielding" envelope="PSHL">
    <posXYZ volume="PairShieldHole" X_Y_Z="0.0 0.0 0.0"/>
  </composition>

  <composition name="PairShieldHole" envelope="OPSH">
    <posXYZ volume="IPSH" X_Y_Z="0.0 0.0 0.0"/>
  </composition>

  <box  name="PSHL" X_Y_Z="10.16 10.16 40.64" material="Lead" />
  <box name="PSH2" X_Y_Z="10.16 27.94 40.64" material="Lead"/>
  <tubs name="OPSH" Rio_Z="0.0  {pspipe2_radius[1]}  40.64" material="Iron"/> 
  <tubs name="IPSH" Rio_Z="0.0  {pspipe2_radius[0]}  40.64" material="Vacuum"/> 

<!-- Pair spectrometer shielding SEG blocks. The properties of material of the SEG 
                       block are very close to Iron.
-->
<box name="SEG1" X_Y_Z="165.1 66.0 33.0" material="Iron"/>
<box name="SEG2" X_Y_Z="33.0 66.0 33.0" material="Iron"/>

</section>

<!-- </HDDS> -->
"""


import math

for line in xml_source.split('\n'):
    print(line)

