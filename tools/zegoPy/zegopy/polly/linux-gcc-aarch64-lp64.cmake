# Copyright (c) 2021, realuei
# All rights reserved.

if(DEFINED POLLY_LINUX_GNU_GCC_AARCH64_LP64)
  return()
else()
  set(POLLY_LINUX_GNU_GCC_AARCH64_LP64 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "aarch64-linux-gnu / gcc / armv8-a / lp64 / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "aarch64-linux-gnu")

# set system name, this sets the variable CMAKE_CROSSCOMPILING
set(CMAKE_SYSTEM_NAME Linux)
set(CROSS_COMPILE_TOOLCHAIN_PREFIX "aarch64-linux-gnu")
set(CMAKE_CROSSCOMPILING_EMULATOR qemu-arm) # used for try_run calls

include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile-simple-layout.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")
# include("${CMAKE_CURRENT_LIST_DIR}/flags/hardfloat.cmake")
# include("${CMAKE_CURRENT_LIST_DIR}/flags/neon-vfpv4.cmake")

# the socket does not support ipv6
add_definitions("-DNOT_SUPPORT_AF_INET6")

set(
    _flags
    -march=armv8-a
    #-mfloat-abi=hard
    #-mfpu=neon-vfpv4
    -mtune=cortex-a53
    -mabi=lp64
    -L"/usr/aarch64-linux-gnu/lib"
    -I"/usr/aarch64-linux-gnu/include"
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()
