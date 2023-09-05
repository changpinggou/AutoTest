# Copyright (c) 2015, Ruslan Baratov
# All rights reserved.

if(DEFINED POLLY_HISI_MIX200_LINUX_)
  return()
else()
  set(POLLY_HISI_MIX200_LINUX_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "himix200 / gcc / neon / 16-bit thumb / c++11 support"
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
      "HIMIX200 Toolchain configuration failed:"
      ${_error_msg}
  )
endif()

# warning must export LC_ALL=C, else report error: "loadlocale.c:130: _nl_intern_locale_data: Assertion `cnt < (sizeof (_nl_value_type_LC_TIME) / sizeof (_nl_value_type_LC_TIME[0]))' failed"
if(NOT ("C" STREQUAL "$ENV{LC_ALL}"))
  polly_fatal_error(
      "Error: Must export LC_ALL before call cmake with:"
      "'export LC_ALL=C'"
  )
endif()

set(CROSS_COMPILE_TOOLCHAIN_PREFIX "arm-himix200-linux")
set(CROSS_COMPILE_TOOLCHAIN_PATH "$ENV{HISI_HOME}/arm-himix200-linux/bin")
set(CROSS_COMPILE_SYSROOT "$ENV{HISI_HOME}/arm-himix200-linux/target")

include(
    "${CMAKE_CURRENT_LIST_DIR}/compiler/gcc-cross-compile.cmake"
)
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")

polly_status_print("*** set flags for 360 access control system ***")

set(
    _flags
    -mcpu=cortex-a9
    -mfloat-abi=softfp
    -mfpu=neon-vfpv4
    -fno-aggressive-loop-optimizations
    -ffunction-sections
    -fdata-sections
    -fstack-protector
    -Wno-error=implicit-function-declaration
    -Wno-date-time
    -L"$ENV{HISI_HOME}/arm-himix200-linux/lib"
    -I"$ENV{HISI_HOME}/arm-himix200-linux/include"
    )

foreach(_flag ${_flags})
    polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
    polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()

set(
    _defines
    -DHI_XXXX
    -DHI_RELEASE
    -Dhi3519av100
    -DVER_X=1
    -DVER_Y=0
    -DVER_Z=0
    -DVER_P=0
    -DVER_B=10
    -DUSER_BIT_32
    -DKERNEL_BIT_32 
    -DSENSOR0_TYPE=SONY_IMX334_MIPI_8M_30FPS_12BIT
    -DSENSOR1_TYPE=SONY_IMX290_SLAVE_MIPI_2M_60FPS_10BIT 
    -DSENSOR2_TYPE=SONY_IMX290_SLAVE_MIPI_2M_60FPS_10BIT
    -DSENSOR3_TYPE=SONY_IMX290_SLAVE_MIPI_2M_60FPS_10BIT
    -DSENSOR4_TYPE=SONY_IMX334_MIPI_8M_30FPS_12BIT
    -DHI_ACODEC_TYPE_INNER -DHI_ACODEC_TYPE_HDMI
    -DISP_V2)

foreach(_def ${_defines})
    add_definitions("${_def}")
endforeach()

# some device not support ipv6
add_definitions("-DNOT_SUPPORT_AF_INET6")

# gcc-ar of hisi toolchain is lack of lib_lto_plugin.so
set(CMAKE_AR           "${CROSS_COMPILE_TOOLCHAIN_PATH}/${CROSS_COMPILE_TOOLCHAIN_PREFIX}-ar"      CACHE PATH "Archiver" FORCE)
