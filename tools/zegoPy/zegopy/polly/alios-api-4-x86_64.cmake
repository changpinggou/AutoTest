# Copyright (c) 2020, Zego Corp.
# All rights reserved.

if(DEFINED POLLY_ALIOS_API_4_X86_64_)
  return()
else()
  set(POLLY_ALIOS_API_4_X86_64_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "AliOS API 4 x86_64 / gcc / c++11 support"
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
      "AliOS api 4 x86_64 Toolchain configuration failed:"
      ${_error_msg}
  )
endif()

set(NDK_ROOT "$ENV{ALIOS_HOME}")
set(CROSS_COMPILE_TOOLCHAIN_PREFIX "x86_64-linux-gnu")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{ALIOS_HOME}/standalone/yunos-4-x86_64/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{ALIOS_HOME}/standalone/yunos-4-x86_64/sysroot")

include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

set(
    _flags
    -march=x86-64
    -mtune=generic
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()

# gcc-ar of hisi toolchain is lack of lib_lto_plugin.so
set(CMAKE_AR  "${CROSS_COMPILE_TOOLCHAIN_PATH}/${CROSS_COMPILE_TOOLCHAIN_PREFIX}-ar"   CACHE PATH "Archiver" FORCE)
