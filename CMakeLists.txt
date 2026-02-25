cmake_minimum_required(VERSION 3.16)
project(hdds LANGUAGES C CXX Fortran)

# --- 1. Settings & Dependencies ---
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(XercesC REQUIRED)
find_package(ROOT QUIET COMPONENTS Geom)
set(HAS_GDML_SUPPORT ${ROOT_FOUND})

# Global Flags
add_compile_options(-g -fPIC -Wall)
if(CMAKE_Fortran_COMPILER_ID STREQUAL "GNU" AND CMAKE_Fortran_COMPILER_VERSION VERSION_GREATER_EQUAL 10)
    add_compile_options($<$<COMPILE_LANGUAGE:Fortran>:-fallow-argument-mismatch>)
endif()

# --- 2. Source Definitions ---
set(COMMON_SRC hddsCommon.cpp XParsers.cpp XString.cpp md5.c)

# --- 3. Build Internal Tools ---
macro(add_hdds_tool name main_src)
    add_executable(${name} ${main_src} ${COMMON_SRC})
    target_link_libraries(${name} PRIVATE XercesC::XercesC)
endmacro()

add_hdds_tool(hdds-geant  hdds-geant.cpp)
add_hdds_tool(hdds-root   hdds-root.cpp)
add_hdds_tool(hdds-root_h hdds-root_h.cpp)
add_hdds_tool(hdds-md5    hdds-md5.cpp)

add_executable(findall findall.cpp hddsBrowser.cpp ${COMMON_SRC})
target_link_libraries(findall PRIVATE XercesC::XercesC)

# --- 4. Code Generation Logic ---
set(GEN_DIR ${CMAKE_BINARY_DIR}/gen)
file(MAKE_DIRECTORY ${GEN_DIR})

# Function to isolate the tool execution
function(add_isolated_gen_command output_file tool input_xml)
    add_custom_command(
        OUTPUT ${GEN_DIR}/${output_file}
        COMMAND sh -c "cd ${GEN_DIR} && ln -sf ${CMAKE_CURRENT_SOURCE_DIR}/*.xml . && ln -sf ${CMAKE_CURRENT_SOURCE_DIR}/*.xsd . && ${CMAKE_BINARY_DIR}/${tool} ${input_xml} > ${output_file} && rm -f *.xml *.xsd"
        DEPENDS ${tool} ${CMAKE_CURRENT_SOURCE_DIR}/${input_xml}
        VERBATIM
    )
endfunction()

add_isolated_gen_command(hddsroot.C   hdds-root   main_HDDS.xml)
add_isolated_gen_command(hddsroot.h   hdds-root_h main_HDDS.xml)
add_isolated_gen_command(hddsGeant3.F hdds-geant  main_HDDS.xml)
add_isolated_gen_command(cpproot.C    hdds-root   cpp_HDDS.xml)
add_isolated_gen_command(cpproot.h    hdds-root_h cpp_HDDS.xml)

# GDML Generation (Triggered after macros exist)
set(GDML_FILES "")
if(HAS_GDML_SUPPORT)
    # Generate Main GDML
    add_custom_command(
        OUTPUT ${GEN_DIR}/hddsroot.gdml
        COMMAND sh -c "cd ${GEN_DIR} && ${ROOT_BINARY_DIR}/root -l -b -q hddsroot.C '${CMAKE_CURRENT_SOURCE_DIR}/mkGDML.C(\"hddsroot.gdml\")'"
        DEPENDS ${GEN_DIR}/hddsroot.C ${CMAKE_CURRENT_SOURCE_DIR}/mkGDML.C
        VERBATIM
    )
    # Generate CPP GDML
    add_custom_command(
        OUTPUT ${GEN_DIR}/cpproot.gdml
        COMMAND sh -c "cd ${GEN_DIR} && ${ROOT_BINARY_DIR}/root -l -b -q cpproot.C '${CMAKE_CURRENT_SOURCE_DIR}/mkGDML.C(\"cpproot.gdml\")'"
        DEPENDS ${GEN_DIR}/cpproot.C ${CMAKE_CURRENT_SOURCE_DIR}/mkGDML.C
        VERBATIM
    )
    list(APPEND GDML_FILES ${GEN_DIR}/hddsroot.gdml ${GEN_DIR}/cpproot.gdml)
endif()

# --- 5. Targets & Libraries ---
add_custom_target(generate_sources ALL 
    DEPENDS 
        ${GEN_DIR}/hddsroot.C 
        ${GEN_DIR}/hddsroot.h 
        ${GEN_DIR}/cpproot.C 
        ${GEN_DIR}/cpproot.h 
        ${GEN_DIR}/hddsGeant3.F
        ${GDML_FILES}
)

add_library(hdds SHARED ${COMMON_SRC})
target_link_libraries(hdds PRIVATE XercesC::XercesC)

if(DEFINED ENV{CERN})
    add_library(hddsGeant3 STATIC ${GEN_DIR}/hddsGeant3.F)
    set_target_properties(hddsGeant3 PROPERTIES LINKER_LANGUAGE Fortran)
    add_dependencies(hddsGeant3 generate_sources)
endif()

# --- 6. Installation ---
install(TARGETS hdds-geant hdds-root hdds-root_h hdds-md5 findall hdds
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib)

if(TARGET hddsGeant3)
    install(TARGETS hddsGeant3 ARCHIVE DESTINATION lib)
endif()

set(INST_FILES 
    "${GEN_DIR}/hddsGeant3.F" 
    "${GEN_DIR}/hddsroot.C" 
    "${GEN_DIR}/hddsroot.h" 
    "${GEN_DIR}/cpproot.C" 
    "${GEN_DIR}/cpproot.h"
)
# Add GDML files to the install list if they were generated
if(HAS_GDML_SUPPORT)
    list(APPEND INST_FILES ${GDML_FILES})
endif()

install(FILES ${INST_FILES} DESTINATION src)
