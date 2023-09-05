# Copyright (c) 2021, realuei
# All rights reserved.

if(DEFINED POLLY_LINARO_V7.3.1_AARCH64-LINUX-GNU_)
  return()
else()
  set(POLLY_LINARO_V7.3.1_AARCH64-LINUX-GNU_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "linaro v7.3.1 aarch64-linux-gnu / gcc / armv8-a / lp64 / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "aarch64-linux-gnu")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{LINARO_HOME}/v7.3.1/aarch64-linux-gnu/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{LINARO_HOME}/v7.3.1/aarch64-linux-gnu/aarch64-linux-gnu/libc")

set(POLLY_SKIP_SYSROOT TRUE)
include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

# the socket does not support ipv6
add_definitions("-DNOT_SUPPORT_AF_INET6")

set(
    _flags
    -march=armv8-a
    #-mfloat-abi=hard
    #-mfpu=neon-vfpv4
    -mtune=cortex-a53
    -mabi=lp64
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()
