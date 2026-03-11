# Copyright 2020 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

########################################################################
# Check if there is C++ code at all
########################################################################
if(NOT geolocation_blocks_sources)
    message(STATUS "No C++ sources... skipping python bindings")
    return()
endif(NOT geolocation_blocks_sources)

########################################################################
# Check for pygccxml
########################################################################
gr_python_check_module_raw("pygccxml" "import pygccxml" PYGCCXML_FOUND)

include(GrPybind)

########################################################################
# Python Bindings
########################################################################

list(APPEND geolocation_blocks_python_files python_bindings.cc)

gr_pybind_make_oot(geolocation_blocks ../../.. gr::geolocation_blocks "${geolocation_blocks_python_files}")

# copy bindings extension for use in QA test module
add_custom_command(
    TARGET geolocation_blocks_python
    POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:geolocation_blocks_python>
            ${PROJECT_BINARY_DIR}/test_modules/gnuradio/geolocation_blocks/)

install(
    TARGETS geolocation_blocks_python
    DESTINATION ${GR_PYTHON_DIR}/gnuradio/geolocation_blocks
    COMPONENT pythonapi)
