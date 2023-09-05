# Copyright (c) 2020, RealUei
# All rights reserved.

# replace cached old_flag with new_flag in variable. Do nothing if old_flag not exists.
#
# Note:
#   flags should be replaced one by one since this function check that
#   substring "flag" already exists in string "var_name".
#
# Bad:
#   polly_replace_cached_flag(CMAKE_CXX_FLAGS "-opt1 -opt2 -opt3" "-new_opt1 -new_opt2 -new_opt3")
#
# Good:
#   polly_replace_cached_flag(CMAKE_CXX_FLAGS "-opt1" "-new_opt1")
#   polly_replace_cached_flag(CMAKE_CXX_FLAGS "-opt2" "-new_opt2")
#   polly_replace_cached_flag(CMAKE_CXX_FLAGS "-opt3" "-new_opt3")
#
function(polly_replace_cached_flag var_name old_flag new_flag)
  set(spaced_string " ${${var_name}} ")
  string(FIND "${spaced_string}" " ${old_flag} " flag_index)
  if(flag_index EQUAL -1)
    return()
  endif()

  string(REPLACE " ${old_flag} " " ${new_flag} " spaced_string ${spaced_string})
  string(REGEX REPLACE "(^ +)|( +$)" "" _no_spaced_string ${spaced_string})
  set(
    "${var_name}"
    "${_no_spaced_string}"
    CACHE
    STRING
    ""
    FORCE)
endfunction()
