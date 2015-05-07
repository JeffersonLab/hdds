//
// $Id:$
//
// This can be used to quickly generate a GDML file from a ROOT
// macro produced by hdds-root. The one line execution is something
// like:
//
// > root -b -q $BMS_OSNAME/src/hddsroot.C mkGDML.C
//
// This will automatically generate a file named "hddsroot.gdml" from
// the $BMS_OSNAME/src/hddsroot.C mkGDML.C file.

void mkGDML(string fname=""){
	if(fname.length() ==0){
		fname = string(gGeoManager->GetName()) + ".gdml";
	}
	gGeoManager->Export(fname.c_str());
}


