# Copyright (c) 2015-2017, Ruslan Baratov
# All rights reserved.

if(DEFINED POLLY_VS_16_2019_WIN64_XP_CMAKE_)
  return()
else()
  set(POLLY_VS_16_2019_WIN64_XP_CMAKE_ 1)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_init.cmake")

# CMake Error: Could not create named generator Visual Studio 16 2019 Win64
# Generators
# * Visual Studio 16 2019        = Generates Visual Studio 2019 project files.
#                                  Use -A option to specify architecture.
#   Visual Studio 15 2017 [arch] = Generates Visual Studio 2017 project files.
#                                  Optional [arch] can be "Win64" or "ARM".

# 2019 does not support to set arch with generator, use "-A"
polly_init(
    "Visual Studio 16 2019"
    "Visual Studio 16 2019"
)

include("${CMAKE_CURRENT_LIST_DIR}/utilities/polly_common.cmake")
