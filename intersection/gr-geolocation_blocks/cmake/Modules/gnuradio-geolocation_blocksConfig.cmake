find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_GEOLOCATION_BLOCKS gnuradio-geolocation_blocks)

FIND_PATH(
    GR_GEOLOCATION_BLOCKS_INCLUDE_DIRS
    NAMES gnuradio/geolocation_blocks/api.h
    HINTS $ENV{GEOLOCATION_BLOCKS_DIR}/include
        ${PC_GEOLOCATION_BLOCKS_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_GEOLOCATION_BLOCKS_LIBRARIES
    NAMES gnuradio-geolocation_blocks
    HINTS $ENV{GEOLOCATION_BLOCKS_DIR}/lib
        ${PC_GEOLOCATION_BLOCKS_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-geolocation_blocksTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_GEOLOCATION_BLOCKS DEFAULT_MSG GR_GEOLOCATION_BLOCKS_LIBRARIES GR_GEOLOCATION_BLOCKS_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_GEOLOCATION_BLOCKS_LIBRARIES GR_GEOLOCATION_BLOCKS_INCLUDE_DIRS)
