# Copyright (c) 2015, Ruslan Baratov
# All rights reserved.

#########################################
### WARNING: This file is useless !!! ###
#########################################

if(DEFINED POLLY_FLAGS_IOS_MACCATALYST_CMAKE_)
  return()
else()
  set(POLLY_FLAGS_IOS_MACCATALYST_CMAKE_ 1)
endif()

include(polly_add_cache_flag)

polly_status_debug(
    "Build for iOS MacCatalyst"
)

# set(CMAKE_XCODE_ATTRIBUTE_OTHER_CFLAGS[arch=x86_64] "-target x86_64-apple-ios13.0-macabi -Wno-overriding-t-option")
# set(CMAKE_XCODE_ATTRIBUTE_OTHER_LDFLAGS[arch=x86_64] "-target x86_64-apple-ios13.0-macabi -Wno-overriding-t-option")

# set(CMAKE_XCODE_ATTRIBUTE_OTHER_CFLAGS[arch=arm64] "-target arm64-apple-ios13.0-macabi -Wno-overriding-t-option")
# set(CMAKE_XCODE_ATTRIBUTE_OTHER_LDFLAGS[arch=arm64] "-target arm64-apple-ios13.0-macabi -Wno-overriding-t-option")

set(MACCATALYST_FLAG_FOR_CLANG "-target x86_64-apple-ios13.0-macabi -Wno-overriding-t-option -isystem ${CMAKE_OSX_SYSROOT}/System/iOSSupport/usr/include -iframework ${CMAKE_OSX_SYSROOT}/System/iOSSupport/System/Library/Frameworks")

set(CMAKE_C_FLAGS "${MACCATALYST_FLAG_FOR_CLANG}")
set(CMAKE_CXX_FLAGS "${MACCATALYST_FLAG_FOR_CLANG}")
set(CMAKE_C_LINK_FLAGS "${MACCATALYST_FLAG_FOR_CLANG}")
set(CMAKE_CXX_LINK_FLAGS "${MACCATALYST_FLAG_FOR_CLANG}")

set(CMAKE_XCODE_ATTRIBUTE_SUPPORTED_PLATFORMS "macosx")
set(PLATFORM_NAME maccatalyst)
set(EFFECTIVE_PLATFORM_NAME -maccatalyst)
set(CMAKE_XCODE_EFFECTIVE_PLATFORMS "-maccatalyst")
set(CMAKE_XCODE_ATTRIBUTE_MACOSX_DEPLOYMENT_TARGET "10.15")
set(IOS_DEPLOYMENT_SDK_VERSION "13.0") # iOS MacCatalyst require at least 13.0
