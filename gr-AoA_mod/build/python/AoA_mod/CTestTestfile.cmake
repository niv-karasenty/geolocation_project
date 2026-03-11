# CMake generated Testfile for 
# Source directory: /Users/nivkarasenty/Desktop/niv/Delta/geolocation_project/geolocation_project/gr-AoA_mod/python/AoA_mod
# Build directory: /Users/nivkarasenty/Desktop/niv/Delta/geolocation_project/geolocation_project/gr-AoA_mod/build/python/AoA_mod
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(qa_phase_to_angle "/bin/sh" "qa_phase_to_angle_test.sh")
set_tests_properties(qa_phase_to_angle PROPERTIES  _BACKTRACE_TRIPLES "/opt/homebrew/lib/cmake/gnuradio/GrTest.cmake;119;add_test;/Users/nivkarasenty/Desktop/niv/Delta/geolocation_project/geolocation_project/gr-AoA_mod/python/AoA_mod/CMakeLists.txt;39;GR_ADD_TEST;/Users/nivkarasenty/Desktop/niv/Delta/geolocation_project/geolocation_project/gr-AoA_mod/python/AoA_mod/CMakeLists.txt;0;")
add_test(qa_send_to_server "/bin/sh" "qa_send_to_server_test.sh")
set_tests_properties(qa_send_to_server PROPERTIES  _BACKTRACE_TRIPLES "/opt/homebrew/lib/cmake/gnuradio/GrTest.cmake;119;add_test;/Users/nivkarasenty/Desktop/niv/Delta/geolocation_project/geolocation_project/gr-AoA_mod/python/AoA_mod/CMakeLists.txt;40;GR_ADD_TEST;/Users/nivkarasenty/Desktop/niv/Delta/geolocation_project/geolocation_project/gr-AoA_mod/python/AoA_mod/CMakeLists.txt;0;")
subdirs("bindings")
