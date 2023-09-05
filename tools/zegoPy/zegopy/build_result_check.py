#!/usr/bin/env python3
# coding: utf-8

"""
use this script to check the build result is valid
"""

import json


def check_sdk_result(workspace, result_urls):
    """
    check av-sdk the build result is valid
    :param workspace: code src path
    :param result_urls: the build result with json string or json object
    :return:
    """
    print("workspace: {}".format(workspace))

    result_urls_json = result_urls
    if type(result_urls) != dict:
        result_urls_json = json.loads(result_urls)
    print("will check result: \r\n{}".format(json.dumps(result_urls_json, indent=4, sort_keys=True)))
    print("ignoring check just now")


if __name__ == "__main__":
    print("please usage:")
    print("from zegopy.build_result_check import *")
    print("check_sdk_result(...) or other func")
