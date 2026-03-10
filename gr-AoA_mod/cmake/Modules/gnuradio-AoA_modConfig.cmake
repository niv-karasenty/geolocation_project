find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_AOA_MOD gnuradio-AoA_mod)

FIND_PATH(
    GR_AOA_MOD_INCLUDE_DIRS
    NAMES gnuradio/AoA_mod/api.h
    HINTS $ENV{AOA_MOD_DIR}/include
        ${PC_AOA_MOD_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_AOA_MOD_LIBRARIES
    NAMES gnuradio-AoA_mod
    HINTS $ENV{AOA_MOD_DIR}/lib
        ${PC_AOA_MOD_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-AoA_modTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_AOA_MOD DEFAULT_MSG GR_AOA_MOD_LIBRARIES GR_AOA_MOD_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_AOA_MOD_LIBRARIES GR_AOA_MOD_INCLUDE_DIRS)
