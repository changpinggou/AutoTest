if(DEFINED POLLY_UNIX_OSX_11_1_DEP_10_10_CMAKE_)
  return()
else()
  set(POLLY_UNIX_OSX_11_1_DEP_10_10_CMAKE_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

set(OSX_SDK_VERSION "11.1")
set(POLLY_XCODE_COMPILER "clang")
polly_init(
    "Unix (OS X ${OSX_SDK_VERSION} | Deployment 10.10) / \
${POLLY_XCODE_COMPILER} / \
LLVM Standard C++ Library (libc++) / c++11 support"
    "Unix Makefiles"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/compiler/xcode-clang.cmake")

set(CMAKE_OSX_DEPLOYMENT_TARGET "10.10" CACHE STRING "OS X Deployment target" FORCE)

include("${CMAKE_CURRENT_LIST_DIR}/library/std/libcxx.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/flags/cxx11.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/os/osx.cmake")

polly_add_cache_flag(CMAKE_C_FLAGS "-arch ${CMAKE_SYSTEM_PROCESSOR} -isysroot ${CMAKE_OSX_SYSROOT} -mmacosx-version-min=${CMAKE_OSX_DEPLOYMENT_TARGET} -DAPPLE_OSX -fembed-bitcode")
polly_add_cache_flag(CMAKE_CXX_FLAGS "-arch ${CMAKE_SYSTEM_PROCESSOR} -isysroot ${CMAKE_OSX_SYSROOT} -mmacosx-version-min=${CMAKE_OSX_DEPLOYMENT_TARGET} -DAPPLE_OSX -fembed-bitcode")
polly_add_cache_flag(CMAKE_SHARED_LINKER_FLAGS "-arch ${CMAKE_SYSTEM_PROCESSOR} -isysroot ${CMAKE_OSX_SYSROOT} -mmacosx-version-min=${CMAKE_OSX_DEPLOYMENT_TARGET}")