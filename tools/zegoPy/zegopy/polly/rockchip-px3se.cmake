# Copyright (c) 2015, Ruslan Baratov
# All rights reserved.

if(DEFINED POLLY_ROCKCHIP_PX3_SE_LINUX_)
  return()
else()
  set(POLLY_ROCKCHIP_PX3_SE_LINUX_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "rockchip px3-se / gcc / neon / 16-bit thumb / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(_error_msg) #if empty, then no errors!
string(COMPARE EQUAL
    "$ENV{ROCKCHIP_HOME}"
    ""
    _is_empty
)
if(_is_empty)
  set(_error_msg
    "${_error_msg}\nROCKCHIP_HOME environment variable not set"
  )
endif()

string(COMPARE NOTEQUAL
    "${_error_msg}"
    ""
    _has_errors
)
if(_has_errors)
  polly_fatal_error(
      "Rockchip Toolchain configuration failed:"
      ${_error_msg}
  )
endif()

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "arm-rockchip-linux-gnueabihf")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{ROCKCHIP_HOME}/px3se/usr/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{ROCKCHIP_HOME}/px3se/usr/arm-rockchip-linux-gnueabihf/sysroot")

include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

# will use this when enable qt, otherwise can't find qt header files
include_directories("${CROSS_COMPILE_SYSROOT}/usr/include/qt5")

set(
    _flags
    -march=armv7-a
    -mtune=cortex-a7
    -mfloat-abi=hard
    -mfpu=neon-vfpv4
    -mthumb
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()
