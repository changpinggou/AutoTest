# Copyright (c) 2021, realuei
# All rights reserved.

if(DEFINED POLLY_LINARO_V4.9.4_ARM-LINUX-GNUEABIHF_)
  return()
else()
  set(POLLY_LINARO_V4.9.4_ARM-LINUX-GNUEABIHF_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "linaro v4.9.4 arm-linux-gnueabihf / gcc / armv7-a / 16-bit thumb / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "arm-linux-gnueabihf")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{LINARO_HOME}/v4.9.4/arm-linux-gnueabihf/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{LINARO_HOME}/v4.9.4/arm-linux-gnueabihf/arm-linux-gnueabihf/libc")

set(POLLY_SKIP_SYSROOT TRUE)
include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

# the socket does not support ipv6
add_definitions("-DNOT_SUPPORT_AF_INET6")

set(
    _flags
    -march=armv7-a
    -mtune=cortex-a9
    -mfloat-abi=hard
    -mfpu=neon
    -mthumb
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()
