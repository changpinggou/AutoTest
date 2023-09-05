#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""sign_windows 用户给 Windows 库文件和可执行文件签名
   你可以作为一个模块导入使用
   也可以直接当成一个独立脚本执行
"""

import os
import re
import sys
import json
import argparse
import requests


def sign_files(target_dir, names_pattern):
    # 签名工具路径
    from shutil import which
    sign_path = "sign_tool/SignDll.exe"
    if which("SignDll.exe") is not None:
        sign_path = "SignDll.exe"  # 如果系统环境变量里面有，那么就使用环境变量的

    for parent, dir_names, file_names in os.walk(os.path.normpath(target_dir)):
        for filename in file_names:
            for re_str in names_pattern:
                if re.match(re_str, filename) is None:
                    continue

                cmd = os.path.normpath(sign_path) + " -file " + os.path.join(parent, filename)
                print(cmd)
                os.system(cmd)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='对指定目录下的文件进行签名')
    parser.add_argument('-t', '--target_dir', dest='target_dir', help='目标文件夹')
    parser.add_argument('-n', '--names', dest='names', nargs='+', help='文件名列表，支持正则表达式')
    args = parser.parse_args()
    if not args.target_dir or not os.path.exists(args.target_dir):
        print("Target dir not exist!")
        sys.exit(1)
    sign_files(args.target_dir, args.names)
