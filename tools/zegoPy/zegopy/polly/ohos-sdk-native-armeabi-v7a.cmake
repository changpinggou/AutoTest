# Copyright (c) 2015, Ruslan Baratov
# Copyright (c) 2015, David Hirvonen
# Copyright (c) 2015, Alexandre Pretyman
# All rights reserved.

if(DEFINED POLLY_OHOS_SDK_NATIVE_ARMEABI_V7A_CMAKE_)
  return()
else()
  set(POLLY_OHOS_SDK_NATIVE_ARMEABI_V7A_CMAKE_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_clear_environment_variables.cmake")

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

polly_init(
    "${CMAKE_SYSTEM_NAME} / ${CMAKE_OHOS_ARCH_ABI}"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake") # before toolchain!

set(
    _flags
    -march=armv7-a
    -mthumb
)

foreach(_flag ${_flags})
  polly_add_cache_flag(CMAKE_C_FLAGS "${_flag}")
  polly_add_cache_flag(CMAKE_CXX_FLAGS "${_flag}")
endforeach()

include("${CMAKE_CURRENT_LIST_DIR}/os/ohos.cmake")