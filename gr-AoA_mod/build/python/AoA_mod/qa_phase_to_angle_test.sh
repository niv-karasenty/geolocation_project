#!/bin/sh
export VOLK_GENERIC=1
export GR_DONT_LOAD_PREFS=1
export srcdir=/Users/nivkarasenty/Desktop/niv/Delta/geolocation_project/geolocation_project/gr-AoA_mod/python/AoA_mod
export GR_CONF_CONTROLPORT_ON=False
export PATH="/Users/nivkarasenty/Desktop/niv/Delta/geolocation_project/geolocation_project/gr-AoA_mod/build/python/AoA_mod":"$PATH"
export DYLD_LIBRARY_PATH="":$DYLD_LIBRARY_PATH
export PYTHONPATH=/Users/nivkarasenty/Desktop/niv/Delta/geolocation_project/geolocation_project/gr-AoA_mod/build/test_modules:$PYTHONPATH
/opt/homebrew/Cellar/gnuradio/3.10.12.0_10/libexec/venv/bin/python /Users/nivkarasenty/Desktop/niv/Delta/geolocation_project/geolocation_project/gr-AoA_mod/python/AoA_mod/qa_phase_to_angle.py 
