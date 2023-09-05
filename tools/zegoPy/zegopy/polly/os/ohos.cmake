# Copyright (c) 2015, Ruslan Baratov
# All rights reserved.

if(DEFINED POLLY_HARMONY_OS_CMAKE_)
  return()
else()
  set(POLLY_HARMONY_OS_CMAKE_ 1)
endif()

include(polly_fatal_error)

set(_ohos_native "$ENV{OHOS_NATIVE_HOME}")
string(COMPARE EQUAL "${_ohos_native}" "" _is_empty)
if(_is_empty)
  polly_fatal_error(
      "Environment variable 'OHOS_NATIVE_HOME' not set"
  )
endif()

include("${_ohos_native}/build/cmake/ohos.toolchain.cmake")
