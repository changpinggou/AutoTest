# Copyright (c) 2018, robotding
# All rights reserved.

if(DEFINED POLLY_INGENIC_CAMERA_)
  return()
else()
  set(POLLY_INGENIC_CAMERA_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "ingenic camera mips / gcc "
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "mips-linux-gnu")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{INGENIC_HOME}/camera/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{INGENIC_HOME}/camera/mips-linux-gnu/libc/uclibc")

set(POLLY_SKIP_SYSROOT TRUE)
include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

# the socket does not support ipv6 on allwinner 
add_definitions("-DNOT_SUPPORT_AF_INET6")
add_definitions("-DNOT_SUPPORT_HTTPS")

set(
    _flags
    -ffunction-sections 
    -fdata-sections
    -muclibc
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()

set(
    _ldflags
    -Wl,--gc-sections 
)

foreach(_flag ${_ldflags})
  polly_add_cache_flag(CMAKE_SHARED_LINKER_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_EXE_LINKER_FLAGS "${_flag}")
endforeach()
