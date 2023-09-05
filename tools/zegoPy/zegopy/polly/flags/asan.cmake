# Copyright (c) 2013, Ruslan Baratov
# All rights reserved.

# see @ref: https://developer.android.com/ndk/guides/asan

if(DEFINED POLLY_FLAGS_ASAN_CMAKE)
  return()
else()
  set(POLLY_FLAGS_ASAN_CMAKE 1)
endif()

include(polly_add_cache_flag)
include(polly_fatal_error)
include(polly_status_print)

polly_status_debug("Enable address sanitizer")

polly_add_cache_flag(CMAKE_CXX_FLAGS "-fsanitize=address")
polly_add_cache_flag(CMAKE_CXX_FLAGS "-fno-omit-frame-pointer")
polly_add_cache_flag(CMAKE_CXX_FLAGS "-g")

set(
    CMAKE_CXX_FLAGS_RELEASE
    "-O1 -DNDEBUG"
    CACHE
    STRING
    "C++ compiler flags"
    FORCE
)

polly_add_cache_flag(CMAKE_C_FLAGS "-fsanitize=address")
polly_add_cache_flag(CMAKE_C_FLAGS "-fno-omit-frame-pointer")
polly_add_cache_flag(CMAKE_C_FLAGS "-g")

set(
    CMAKE_C_FLAGS_RELEASE
    "-O1 -DNDEBUG"
    CACHE
    STRING
    "C compiler flags"
    FORCE
)

polly_add_cache_flag(CMAKE_SHARED_LINKER_FLAGS "-fsanitize=address")
set(CMAKE_ANDROID_STL_TYPE "c++_shared") # LLVM libc++ shared
set(ANDROID_ARM_MODE "arm")
