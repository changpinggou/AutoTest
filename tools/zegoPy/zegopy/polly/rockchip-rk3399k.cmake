# Copyright (c) 2015, Ruslan Baratov
# All rights reserved.

if(DEFINED POLLY_ROCKCHIP_RK3399K_LINUX_)
  return()
else()
  set(POLLY_ROCKCHIP_RK3399K_LINUX_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "rockchip rk3399k(armv8-a) / gcc / lp64 / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

set(_error_msg) #if empty, then no errors!
string(COMPARE EQUAL
    "$ENV{ROCKCHIP_HOME}"
    ""
    _is_empty
)
if(_is_empty)
  set(_error_msg
    "${_error_msg}\nROCKCHIP_HOME environment variable not set"
  )
endif()

string(COMPARE NOTEQUAL
    "${_error_msg}"
    ""
    _has_errors
)
if(_has_errors)
  polly_fatal_error(
      "Rockchip Toolchain configuration failed:"
      ${_error_msg}
  )
endif()

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "aarch64-linux-gnu")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{ROCKCHIP_HOME}/rk3399k/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{ROCKCHIP_HOME}/rk3399k")

set(POLLY_SKIP_SYSROOT TRUE)
include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

set(
    _flags
    -march=armv8-a
    -mtune=cortex-a72
    -mabi=lp64
    -L"$ENV{ROCKCHIP_HOME}/rk3399k/lib"
    -I"$ENV{ROCKCHIP_HOME}/rk3399k/include"
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()
