/*
 * XString:  a simple class for translation between 
 *           XMLCh strings and local coding
 *
 * Class implementation
 * September 21, 2003
 * Richard Jones
 */

#include "XString.hpp"
#include <iostream>

int dumper = 0;

XString::XString(void)
 : fUnicode(0)
{}

XString::XString(const XMLCh* const x)
 : fUnicode(0)
{
   if (x)
   {
      char* str = xercesc::XMLString::transcode(x);
      (std::string&)*this = str;
      xercesc::XMLString::release(&str);
   }
}

XString::XString(const char* const s)
 : fUnicode(0)
{
   if (s)
   {
      (std::string&)*this = s;
   }
}

XString::XString(const std::string& s)
 : std::string(s),
   fUnicode(0)
{}

XString::XString(const XString& X)
 : std::string(X),
   fUnicode(0)
{}

XString::~XString()
{
   if (fUnicode)
   {
      xercesc::XMLString::release(&fUnicode);
   }
}

XString& XString::operator=(const XString& X)
{
   (std::string&)*this = (std::string&)X;
   if (fUnicode)
   {
      xercesc::XMLString::release(&fUnicode);
   }
   return *this;
}

const XMLCh* XString::unicode_str()
{
   if (fUnicode == 0)
   {
      fUnicode = xercesc::XMLString::transcode(this->c_str());
   }
   return fUnicode;
}

const XString XString::basename() const
{
   XString s(*this);
   size_type p = s.find_last_of("/");
   if (p != npos)
   {
      s = s.substr(p+1,s.size());
   }
   return s;
}

void XString::dump()
{
   std::cout << *this << std::endl;
}
