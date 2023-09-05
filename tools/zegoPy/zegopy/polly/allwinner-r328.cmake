# Copyright (c) 2021, Realuei
# All rights reserved.

if(DEFINED POLLY_ALLWINNER_R328_LINUX_)
  return()
else()
  set(POLLY_ALLWINNER_R328_LINUX_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "allwinner r328 / gcc / vfpv4 / 16-bit thumb / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(_error_msg) #if empty, then no errors!
string(COMPARE EQUAL
    "$ENV{ALLWINNER_HOME}"
    ""
    _is_empty
)
if(_is_empty)
  set(_error_msg
    "${_error_msg}\nALLWINNER_HOME environment variable not set"
  )
endif()

string(COMPARE NOTEQUAL
    "${_error_msg}"
    ""
    _has_errors
)
if(_has_errors)
  polly_fatal_error(
      "ALLWINNER_HOME Toolchain configuration failed:"
      ${_error_msg}
  )
endif()

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "arm-openwrt-linux")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{ALLWINNER_HOME}/r328/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{ALLWINNER_HOME}/r328")

include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

# the socket does not support ipv6 on allwinner 
add_definitions("-DNOT_SUPPORT_AF_INET6")

set(
    _flags
    -march=armv7-a
    -mtune=cortex-a7
    -mfloat-abi=hard
    -mfpu=vfpv4
    -mthumb
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()
