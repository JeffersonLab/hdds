/*
 * XParsers: service classes to support parsing of xml domuments
 *           using standard DOM parsing tools
 *
 * Class definition
 * September 21, 2003
 * Richard Jones
 */

#ifndef SAW_XPARSERS
#define SAW_XPARSERS true

#include <xercesc/util/XercesDefs.hpp>
#include <xercesc/sax/ErrorHandler.hpp>
#include <xercesc/dom/DOM.hpp>
#include <xercesc/sax/EntityResolver.hpp>

#include <iostream>
#include <vector>
#include <string>

#include "XString.hpp"

//----------------------------------------------------------------------
// The following is to handle issues with compiling with c++20, but
// in a way that should be compatible with c++11 and all versions
// in-between. This handles printing the char16_t types which have
// been deprecated for some time and removed in c++20.
#include <string>
#include <locale>
#if __cplusplus >= 201103L && __cplusplus < 202002L  // C++11, C++14, C++17
#include <codecvt>  // Deprecated in C++17, removed in C++20
#endif
static std::string char16_to_utf8(const char16_t* u16_str) {
    if (!u16_str) return "(null)";

#if __cplusplus >= 202002L  // C++20+
    return std::string(reinterpret_cast<const char*>(u16_str));  // Works with UTF-8 `std::u8string`
#elif __cplusplus >= 201103L  // C++11 to C++17
    std::wstring_convert<std::codecvt_utf8_utf16<char16_t>, char16_t> converter;
    return converter.to_bytes(u16_str);
#else
    static_assert(false, "C++11 or newer is required");
#endif
}

// Overload operator<< for char16_t*
static std::ostream& operator<<(std::ostream& os, const char16_t* u16_str) {
    return os << char16_to_utf8(u16_str);
}
//----------------------------------------------------------------------

// Filled by parseInputDocument using MyEntityResolver class
extern std::string last_md5_checksum;


/* a simple error handler to install on XercesDOMParser */

class MyOwnErrorHandler : public xercesc::ErrorHandler
{
public:
   MyOwnErrorHandler();
   ~MyOwnErrorHandler();

   bool getSawErrors() const;

/* Implementation of the SAX ErrorHandler interface */
   void warning(const xercesc::SAXParseException& e);
   void error(const xercesc::SAXParseException& e);
   void fatalError(const xercesc::SAXParseException& e);
   void resetErrors();

private :
   MyOwnErrorHandler(const MyOwnErrorHandler&);
   void operator=(const MyOwnErrorHandler&);

   bool    fSawErrors;     // flag to record that an error occurred
};

inline bool MyOwnErrorHandler::getSawErrors() const
{
   return fSawErrors;
}

/* a simple error handler to install on DOMBuilder parser */

class MyDOMErrorHandler : public xercesc::DOMErrorHandler
{
public:
   MyDOMErrorHandler();
   ~MyDOMErrorHandler();

   bool getSawErrors() const;
   bool handleError(const xercesc::DOMError& domError);
   void resetErrors();

private :
    MyDOMErrorHandler(const MyDOMErrorHandler&);
    void operator=(const MyDOMErrorHandler&);
    bool fSawErrors;
};

inline bool MyDOMErrorHandler::getSawErrors() const
{
       return fSawErrors;
}

// A simple entity resolver to keep track of files being
// included from the top-level XML file so a full MD5 sum
// can be made
class MyEntityResolver : public xercesc::EntityResolver
{
public:
	MyEntityResolver(const XString& xmlFile);
        MyEntityResolver(const MyEntityResolver &src);
        MyEntityResolver &operator=(const MyEntityResolver &src);
	~MyEntityResolver();
	
	xercesc::InputSource* resolveEntity(const XMLCh* const publicId, const XMLCh* const systemId);

	std::vector<std::string> GetXMLFilenames(void);
	std::string GetMD5_checksum(void);

private:
	std::vector<std::string> xml_filenames;
	std::string path;
};

xercesc::DOMDocument* parseInputDocument(const XString& file, bool keep);
xercesc::DOMDocument* buildDOMDocument(const XString& file, bool keep);

#endif
