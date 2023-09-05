# Copyright (c) 2015, Ruslan Baratov
# All rights reserved.

if(DEFINED POLLY_COMPILER_XCODE_CLANG_CMAKE_)
  return()
else()
  set(POLLY_COMPILER_XCODE_CLANG_CMAKE_ 1)
endif()

include(polly_fatal_error)

string(COMPARE EQUAL "${POLLY_XCODE_COMPILER}" "" _is_empty)
if(_is_empty)
  polly_fatal_error("Please set POLLY_XCODE_COMPILER")
endif()

set(_cmd xcrun --find "${POLLY_XCODE_COMPILER}")

execute_process(
    COMMAND
    ${_cmd}
    OUTPUT_VARIABLE _compiler_path
    RESULT_VARIABLE _result
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT _result EQUAL 0)
  polly_fatal_error("Command failed: ${_cmd}")
endif()

set(
    CMAKE_C_COMPILER
    "${_compiler_path}"
    CACHE
    STRING
    "C compiler"
    FORCE
)

polly_status_debug("clang Compiler: ${_compiler_path}")

set(_cmd xcrun --find "clang++")

execute_process(
    COMMAND
    ${_cmd}
    OUTPUT_VARIABLE _cxx_compiler_path
    RESULT_VARIABLE _result
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT _result EQUAL 0)
  polly_fatal_error("Command failed: ${_cmd}")
endif()

set(
    CMAKE_CXX_COMPILER
    "${_cxx_compiler_path}"
    CACHE
    STRING
    "C++ compiler"
    FORCE
)

polly_status_debug("clang++ Compiler: ${_compiler_path}")

set(_cmd xcrun --find "ar")

execute_process(
    COMMAND
    ${_cmd}
    OUTPUT_VARIABLE _ar_path
    RESULT_VARIABLE _result
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT _result EQUAL 0)
  polly_fatal_error("Command failed: ${_cmd}")
endif()

set(
    CMAKE_ASM_COMPILER_AR
    "${_ar_path}"
    CACHE
    STRING
    "asm compiler ar"
    FORCE
)

polly_status_debug("AR: ${_ar_path}")

set(_cmd xcrun --find "ranlib")

execute_process(
    COMMAND
    ${_cmd}
    OUTPUT_VARIABLE _ranlib_path
    RESULT_VARIABLE _result
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT _result EQUAL 0)
  polly_fatal_error("Command failed: ${_cmd}")
endif()

set(
    CMAKE_ASM_COMPILER_RANLIB
    "${_ranlib_path}"
    CACHE
    STRING
    "asm compiler ranlib"
    FORCE
)

polly_status_debug("AR: ${_ranlib_path}")