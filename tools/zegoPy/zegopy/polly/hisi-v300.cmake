# Copyright (c) 2015, Ruslan Baratov
# All rights reserved.

if(DEFINED POLLY_HISI_V300_LINUX_)
  return()
else()
  set(POLLY_HISI_V300_LINUX_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "hisiv300 / gcc / neon / 16-bit thumb / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(_error_msg) #if empty, then no errors!
string(COMPARE EQUAL
    "$ENV{HISI_HOME}"
    ""
    _is_empty
)
if(_is_empty)
  set(_error_msg
    "${_error_msg}\nHISI_HOME environment variable not set"
  )
endif()

string(COMPARE NOTEQUAL
    "${_error_msg}"
    ""
    _has_errors
)
if(_has_errors)
  polly_fatal_error(
      "HISIV300 Toolchain configuration failed:"
      ${_error_msg}
  )
endif()

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "arm-hisiv300-linux")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{HISI_HOME}/arm-hisiv300-linux/target/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{HISI_HOME}/arm-hisiv300-linux/target")

include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

# some device not support ipv6
add_definitions("-DNOT_SUPPORT_AF_INET6")
add_definitions("-DARM_LINUX")

set(
    _flags
    -march=armv7-a
    -mtune=cortex-a9
    -mfloat-abi=softfp
    -mfpu=neon
    -mthumb
    -L"$ENV{HISI_HOME}/arm-hisiv300-linux/lib"
    -I"$ENV{HISI_HOME}/arm-hisiv300-linux/include"
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()

# gcc-ar of hisi toolchain is lack of lib_lto_plugin.so
set(CMAKE_AR           "${CROSS_COMPILE_TOOLCHAIN_PATH}/${CROSS_COMPILE_TOOLCHAIN_PREFIX}-ar"      CACHE PATH "Archiver" FORCE)
