# Copyright (c) 2018, robotding
# All rights reserved.

if(DEFINED POLLY_MYIR_AM335X_)
  return()
else()
  set(POLLY_MYIR_AM335X_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "myir am335x / gcc / armv7-a / 16-bit thumb / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "arm-myir-linux-gnueabihf")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{MYIR_HOME}/am335x/usr/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{LINARO_HOME}/arm335x/usr/arm-myir-linux-gnueabihf/sysroot")

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
    -mtune=cortex-a8
    -mfloat-abi=hard
    -mfpu=neon
    -mthumb
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()
