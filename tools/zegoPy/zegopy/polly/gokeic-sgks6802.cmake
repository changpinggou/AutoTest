# Copyright (c) 2019, robotding
# All rights reserved.

if(DEFINED POLLY_GOKEIC_SGKS6802)
  return()
else()
  set(POLLY_GOKEIC_SGKS6802 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "gokeic sgks6802 / gcc / armv7-a / 16-bit thumb / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "arm-buildroot-linux-gnueabi")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{GOKEIC_HOME}/sgks6802/arm-linux-gcc-4.8.5/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{GOKEIC_HOME}/sgks6802/arm-linux-gcc-4.8.5/arm-buildroot-linux-gnueabi/sysroot")

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
    -mtune=cortex-a7
    -mfloat-abi=softfp
    -mfpu=neon-vfpv4
    -mthumb
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()
