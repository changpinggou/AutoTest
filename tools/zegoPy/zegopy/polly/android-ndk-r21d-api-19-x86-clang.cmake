# Copyright (c) 2020, ZEGO
# All rights reserved.

if(DEFINED POLLY_ANDROID_NDK_R21D_API_19_X86_CLANG_CMAKE_)
  return()
else()
  set(POLLY_ANDROID_NDK_R21D_API_19_X86_CLANG_CMAKE_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_clear_environment_variables.cmake")

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

set(ANDROID_NDK_VERSION "r21d")
set(CMAKE_SYSTEM_VERSION "19")
set(CMAKE_ANDROID_ARCH_ABI "x86")
set(CMAKE_ANDROID_NDK_TOOLCHAIN_VERSION "clang")
# set(CMAKE_ANDROID_STL_TYPE "c++_static") # LLVM libc++ static

polly_init(
    "Android NDK ${ANDROID_NDK_VERSION} / \
API ${CMAKE_SYSTEM_VERSION} / ${CMAKE_ANDROID_ARCH_ABI} / \
Clang / c++11 support / libc++ static"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake") # before toolchain!

include("${CMAKE_CURRENT_LIST_DIR}/os/android.cmake")

if(ENABLE_ASAN)
    include("${CMAKE_CURRENT_LIST_DIR}/flags/asan.cmake")   # must at file tail
endif()
