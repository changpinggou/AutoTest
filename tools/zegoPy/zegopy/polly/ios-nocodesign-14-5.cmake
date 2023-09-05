# Copyright (c) 2014-2016, Ruslan Baratov
# All rights reserved.

if(DEFINED POLLY_IOS_NOCODESIGN_14_5_CMAKE_)
  return()
else()
  set(POLLY_IOS_NOCODESIGN_14_5_CMAKE_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_clear_environment_variables.cmake")

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

set(IOS_SDK_VERSION 14.5)

set(POLLY_XCODE_COMPILER "clang")

polly_init(
    "iOS ${IOS_SDK_VERSION} ${IOS_VARIANT} / \
${POLLY_XCODE_COMPILER} / \
No code sign / \
c++14 support"
    "Xcode"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")

include(polly_fatal_error)

# Fix try_compile
include(polly_ios_bundle_identifier)
set(CMAKE_MACOSX_BUNDLE YES)

#include("${CMAKE_CURRENT_LIST_DIR}/flags/ios_nocodesign.cmake")

# set(archs armv7;arm64)
# if("${IOS_VARIANT}" STREQUAL "MACCATALYST")
#   set(CMAKE_SYSTEM_NAME "iOS")
#   set(archs armv7;arm64;x86_64)
# endif()
set(IPHONEOS_ARCHS armv7;arm64)
set(IPHONESIMULATOR_ARCHS x86_64)
set(IOS_DEPLOYMENT_SDK_VERSION "9.0") # Xcode 12 does not support iOS 8.0 anymore

include("${CMAKE_CURRENT_LIST_DIR}/compiler/xcode.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/os/iphone.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx14.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/flags/bitcode.cmake") # after os/iphone.cmake

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_ios_development_team.cmake")

# if("${IOS_VARIANT}" STREQUAL "MACCATALYST")
#     include("${CMAKE_CURRENT_LIST_DIR}/flags/ios_catalyst.cmake")   # must at file tail
# endif()

if(ENABLE_ASAN)
    include("${CMAKE_CURRENT_LIST_DIR}/flags/sanitize_address.cmake")   # must at file tail
endif()
