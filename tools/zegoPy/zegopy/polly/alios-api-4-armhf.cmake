# Copyright (c) 2020, Zego Corp.
# All rights reserved.

if(DEFINED POLLY_ALIOS_API_4_ARMEABI_V7A_HARD_)
  return()
else()
  set(POLLY_ALIOS_API_4_ARMEABI_V7A_HARD_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "AliOS API 4 armeabi-v7a hard / gcc / vfpv3-d16 / 16-bit thumb / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(_error_msg) #if empty, then no errors!
string(COMPARE EQUAL
    "$ENV{ALIOS_HOME}"
    ""
    _is_empty
)
if(_is_empty)
  set(_error_msg
    "${_error_msg}\nALIOS_HOME environment variable not set"
  )
endif()

string(COMPARE NOTEQUAL
    "${_error_msg}"
    ""
    _has_errors
)
if(_has_errors)
  polly_fatal_error(
      "AliOS api 4 armeabi-v7a Toolchain configuration failed:"
      ${_error_msg}
  )
endif()

set(NDK_ROOT "$ENV{ALIOS_HOME}")
set(CROSS_COMPILE_TOOLCHAIN_PREFIX "arm-linux-gnueabihf")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{ALIOS_HOME}/standalone/yunos-4-armhf/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{ALIOS_HOME}/standalone/yunos-4-armhf/sysroot")

include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

set(
    _flags
    -march=armv7-a
    -mtune=cortex-a9
    -mfloat-abi=hard
    -mfpu=vfpv3-d16
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()

# gcc-ar of hisi toolchain is lack of lib_lto_plugin.so
set(CMAKE_AR  "${CROSS_COMPILE_TOOLCHAIN_PATH}/${CROSS_COMPILE_TOOLCHAIN_PREFIX}-ar"   CACHE PATH "Archiver" FORCE)
