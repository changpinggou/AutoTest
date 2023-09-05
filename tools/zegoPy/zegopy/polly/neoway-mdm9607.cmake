# Copyright (c) 2015, Ruslan Baratov
# All rights reserved.

if(DEFINED POLLY_NEOWAY_MDM9607_LINUX_)
  return()
else()
  set(POLLY_NEOWAY_MDM9607_LINUX_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "neoway mdm9607 / gcc / neon / 16-bit thumb / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(_error_msg) #if empty, then no errors!
string(COMPARE EQUAL
    "$ENV{NEOWAY_HOME}"
    ""
    _is_empty
)
if(_is_empty)
  set(_error_msg
    "${_error_msg}\nNEOWAY_HOME environment variable not set"
  )
endif()

string(COMPARE NOTEQUAL
    "${_error_msg}"
    ""
    _has_errors
)
if(_has_errors)
  polly_fatal_error(
      "Neoway Toolchain configuration failed:"
      ${_error_msg}
  )
endif()

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "arm-oe-linux-gnueabi")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{NEOWAY_HOME}/arm-oe/sysroots/x86_64-oesdk-linux/usr/bin/arm-oe-linux-gnueabi")
set(CROSS_COMPILE_SYSROOT "$ENV{NEOWAY_HOME}/arm-oe/sysroots/armv7a-vfp-neon-oe-linux-gnueabi")

include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

set(
    _flags
    -march=armv7-a
    -mfloat-abi=softfp
    -mfpu=neon
    -mthumb
    -fexpensive-optimizations 
    -frename-registers 
    -fomit-frame-pointer 
    -fstack-protector-strong 
    -pie 
    -fpie 
    -Wa,--noexecstack
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()

set(
    _ldflags
    -Wl,-O1 
    -Wl,--hash-style=gnu 
    -Wl,--as-needed 
    -Wl,-z,relro,-z,now,-z,noexecstack
)

foreach(_flag ${_ldflags})
  polly_add_cache_flag(CMAKE_SHARED_LINKER_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_EXE_LINKER_FLAGS "${_flag}")
endforeach()
