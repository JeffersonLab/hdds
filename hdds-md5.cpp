/*
 *  hdds-geant :   an interface utility that reads in a HDDS document
 *                   (Hall D Detector Specification) and writes out a
 *                   GEANT-3 geometry description in the form of a
 *                   fortran subroutine.
 *
 *  Revision - Richard Jones, November 25, 2006.
 *   -added output of optical properties for materials with optical
 *    properties defined
 *
 *  Revision - Richard Jones, January 25, 2005.
 *   -added the sphere section as a new supported volume type
 *
 *  Original version - Richard Jones, May 19 2001.
 *
 *  Notes:
 *  ------
 * 1. Output is sent to standard out through the ordinary c++ i/o library.
 * 2. As a by-product of using the DOM parser to access the xml source,
 *    hdds-geant verifies the source against the schema before translating it.
 *    Therefore it may also be used as a validator of the xml specification
 *    (see the -v option).
 */

#define APP_NAME "hdds-md5"

#include <xercesc/util/PlatformUtils.hpp>
#include <xercesc/util/XMLString.hpp>
#include <xercesc/util/XMLStringTokenizer.hpp>
#include <xercesc/sax/SAXParseException.hpp>
#include <xercesc/parsers/XercesDOMParser.hpp>
#include <xercesc/framework/LocalFileFormatTarget.hpp>
#include <xercesc/dom/DOM.hpp>
#include <xercesc/util/XercesDefs.hpp>
#include <xercesc/sax/ErrorHandler.hpp>

using namespace xercesc;

#include "XString.hpp"
#include "XParsers.hpp"
#include "hddsCommon.hpp"

#include <assert.h>
#include <stdlib.h>
#include <ctype.h>
#include <stdio.h>
#include <math.h>

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <iomanip>
#include <vector>
#include <list>
#include <map>

#define X(str) XString(str).unicode_str()
#define S(str) str.c_str()

void usage()
{
    std::cerr
         << "Usage:    " << APP_NAME << " [-v] {HDDS file}"
         << std::endl <<  "Options:" << std::endl
         << "    -v   validate only" << std::endl;
}



int main(int argC, char* argV[])
{
   try
   {
      XMLPlatformUtils::Initialize();
   }
   catch (const XMLException& toCatch)
   {
      XString message(toCatch.getMessage());
      std::cerr
           << APP_NAME << " - error during initialization!"
           << std::endl << S(message) << std::endl;
      return 1;
   }

   if (argC < 2)
   {
      usage();
      return 1;
   }
   else if ((argC == 2) && (strcmp(argV[1], "-?") == 0))
   {
      usage();
      return 2;
   }

   XString xmlFile;
   int argInd;
   for (argInd = 1; argInd < argC; argInd++)
   {
      if (argV[argInd][0] != '-')
         break;

      if ( ! (strcmp(argV[argInd], "-v") == 0))
         std::cerr
              << "Unknown option \'" << argV[argInd]
              << "\', ignoring it\n" << std::endl;
   }

   if (argInd != argC - 1)
   {
      usage();
      return 1;
   }
   xmlFile = argV[argInd];

	// Parse the XML input file, calculating the checksum at the end
	// and leaving it in the global variable "last_md5_checksum"
	//DOMDocument* document =  // commented out to avoid compiler warnings
	parseInputDocument(xmlFile,false);
	
	std::cout << "HDDS Geometry MD5 Checksum: " << last_md5_checksum << std::endl;
	

   XMLPlatformUtils::Terminate();
   return 0;
}

