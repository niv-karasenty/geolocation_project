# Copyright 2020 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

########################################################################
# Check if there is C++ code at all
########################################################################
if(NOT AoA_mod_sources)
    message(STATUS "No C++ sources... skipping python bindings")
    return()
endif(NOT AoA_mod_sources)

########################################################################
# Check for pygccxml
########################################################################
gr_python_check_module_raw("pygccxml" "import pygccxml" PYGCCXML_FOUND)

include(GrPybind)

########################################################################
# Python Bindings
########################################################################

list(APPEND AoA_mod_python_files python_bindings.cc)

gr_pybind_make_oot(AoA_mod ../../.. gr::AoA_mod "${AoA_mod_python_files}")

# copy bindings extension for use in QA test module
add_custom_command(
    TARGET AoA_mod_python
    POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:AoA_mod_python>
            ${PROJECT_BINARY_DIR}/test_modules/gnuradio/AoA_mod/)

install(
    TARGETS AoA_mod_python
    DESTINATION ${GR_PYTHON_DIR}/gnuradio/AoA_mod
    COMPONENT pythonapi)
