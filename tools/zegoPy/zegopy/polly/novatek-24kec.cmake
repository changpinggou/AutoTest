# Copyright (c) 2015, Ruslan Baratov
# All rights reserved.

if(DEFINED POLLY_NOVATEK_MIPSEL_24KEC_LINUX_)
  return()
else()
  set(POLLY_NOVATEK_MIPSEL_24KEC_LINUX_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "novatek mipsel 24kec / gcc "
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(_error_msg) #if empty, then no errors!
string(COMPARE EQUAL
    "$ENV{NOVATEK_HOME}"
    ""
    _is_empty
)
if(_is_empty)
  set(_error_msg
    "${_error_msg}\nNOVATEK_HOME environment variable not set"
  )
endif()

string(COMPARE NOTEQUAL
    "${_error_msg}"
    ""
    _has_errors
)
if(_has_errors)
  polly_fatal_error(
      "NOVATEK_HOME Toolchain configuration failed:"
      ${_error_msg}
  )
endif()

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "mipsel-24kec-linux-uclibc")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{NOVATEK_HOME}/mipsel-24kec/usr/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{NOVATEK_HOME}/mipsel-24kec/usr/mipsel-24kec-linux-uclibc/sysroot")

include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

# the socket does not support ipv6
add_definitions("-DNOT_SUPPORT_AF_INET6")

set(
    _flags
    -march=24kec
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()

# gcc-ar of novatek toolchain is lack of lib_lto_plugin.so
set(CMAKE_AR           "${CROSS_COMPILE_TOOLCHAIN_PATH}/${CROSS_COMPILE_TOOLCHAIN_PREFIX}-ar"      CACHE PATH "Archiver" FORCE)
