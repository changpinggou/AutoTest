# Copyright (c) 2018, robotding
# All rights reserved.

if(DEFINED POLLY_LINUX_GNU_GCC_ARM_)
  return()
else()
  set(POLLY_LINUX_GNU_GCC_ARM_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "arm-linux-gnueabi / gcc / armv7-a / 16-bit thumb / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

# set system name, this sets the variable CMAKE_CROSSCOMPILING
set(CMAKE_SYSTEM_NAME Linux)
set(CROSS_COMPILE_TOOLCHAIN_PREFIX "arm-linux-gnueabi")
# set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{LINARO_HOME}/v5.5.0/arm-linux-gnueabi/bin")
# set(CROSS_COMPILE_SYSROOT "$ENV{LINARO_HOME}/v5.5.0/arm-linux-gnueabi/arm-linux-gnueabi/libc")

set(CMAKE_CROSSCOMPILING_EMULATOR qemu-arm) # used for try_run calls

include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile-simple-layout.cmake"
)

include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

# the socket does not support ipv6
add_definitions("-DNOT_SUPPORT_AF_INET6")

set(
    _flags
    -march=armv7-a
    -mtune=cortex-a9
    -mfloat-abi=softfp
    -mfpu=neon
    -mthumb
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()
