#!/usr/bin/env python -u
# coding: utf-8

import re
import os
import subprocess
from typing import List, Tuple

from zegopy.common import command
from zegopy.common import jenkinsutil


def get_git_version(git_repo):
    git_command = 'git -C {0} describe --all --long --abbrev=10'.format(git_repo)
    ok, ver = command.execute(git_command, False)

    if ok == 0:
        ver = ver.replace('/', '_')
        ver = ver.replace('remotes_origin_', '')
        return ver.strip()

    return ""


def get_ios_sdk_version():
    get_version_command = 'xcodebuild -showsdks'
    ok, result = command.execute(get_version_command, False)

    if ok == 0:
        index = result.index('-sdk iphoneos')
        index += len('-sdk iphoneos')
        version = result[index : index+4]
        version = version.replace('.', '-')
        version = version.strip('\n')

        print ('SDK Version: {0}'.format(version))

        return version

    return "11-0"


def get_osx_sdk_version():
    get_version_command = 'xcodebuild -showsdks'
    ok, result = command.execute(get_version_command, False)

    if ok == 0:
        index = result.index('-sdk macosx')
        index += len('-sdk macosx')
        version = result[index: index+5]
        version = version.replace('.', '-')
        version = version.strip('\n')
        print ('SDK Version: {0}'.format(version))
        return version

    return "10-13"


def get_xcode_sdk_version(platform):
    """获取 Xcode 各种平台的 SDK 版本

    Args:
        platform (str): 平台类型, [iphoneos/iphonesimulator/macosx/driverkit.macosx/appletvos/appletvsimulator/watchos/watchsimulator]

    Returns:
        [str]: Xcode 指定平台 SDK 版本 或 空字符串(若出错)
    """
    platform_list = ['iphoneos', 'iphonesimulator', 'macosx', 'driverkit.macosx', 'appletvos', 'appletvsimulator', 'watchos', 'watchsimulator']
    if platform not in platform_list:
        raise Exception('[get_xcode_sdk_version] 未知平台类型 `{0}`, 应为 `{1}` 其中之一'.format(platform, ','.join(platform_list)))

    cmd = 'xcodebuild -showsdks'
    status, result = command.execute(cmd)

    if status == 0:
        pattern = '-sdk {0}'.format(platform)
        index = result.index(pattern) + len(pattern)
        version = result[index:index+5].replace('.', '-').strip('\n')
        print('[get_xcode_sdk_version] Xcode {platform} SDK Version: {ver}'.format(platform=platform, ver=version))
        return version
    else:
        print('[get_xcode_sdk_version] Error: `{cmd}` return errorCode: {code}, result: {result}'.format(cmd=cmd, code=status, result=result))
        return ''


def get_cmake_bin_path() -> str:
    """返回 CMake 在本机的路径，若未安装，返回空字符串"""
    which_bin = 'where' if os.name == 'nt' else 'which'
    state, cmake_path = command.execute('{} cmake'.format(which_bin))
    return cmake_path if state == 0 else ''

def get_cmake_version() -> Tuple[str, List[int]]:
    """获取 CMake 版本号，如果未安装 CMake，返回元组 ('', [0,0,0])

    Returns:
        Tuple[str, List[int]]: 元组，版本号 String，和版本号三段 int 的数组，例如 ('3.19.2', [3, 19, 2])
    """
    cmake_path = get_cmake_bin_path()
    if len(cmake_path) == 0:
        print('[*] ERROR: CMake is not installed! Execute `brew install cmake` to install it!')
        return ('', [0,0,0])

    _, cmake_ver = command.execute('cmake --version')
    cmake_ver = cmake_ver.split()[2]
    print('[*] CMake Version: {0}, at {1}'.format(cmake_ver, cmake_path))

    major = int(cmake_ver.split('.')[0])
    minor = int(cmake_ver.split('.')[1])
    patch = int(cmake_ver.split('.')[2])
    return (cmake_ver, [major, minor, patch])


def get_certificate_name(ios=True):
    if ios:
        certificate = "iPhone Developer"
        identify_pattern = re.compile('''[^"]+"(iPhone Developer:[^"]+)"''')
    else:
        certificate = "Mac Developer"
        identify_pattern = re.compile('''[^"]+"(Mac Developer:[^"]+)"''')

    identify_pattern_new = re.compile('''[^"]+"(Apple Development:[^"]+)"''')

    identity_cmd = "security find-identity -p codesigning -v"

    try:
        result = subprocess.check_output(identity_cmd.split()).decode('utf8')
    except:
        return certificate

    found_identity = False
    for line in result.split('\n'):
        match = re.match(identify_pattern_new, line)
        if match is None:
            match = re.match(identify_pattern, line)

        if match is None:
            continue

        certificate = match.group(1)

        certificate_cmd = 'security find-certificate -c "{0}"'.format(certificate)
        match_zego = False
        ok1, result1 = command.execute(certificate_cmd, False)
        if ok1 != 0:
            continue

        for line in result1.split('\n'):
            line = line.strip()
            if line.startswith('''"subj"<blob>=''') and line.find('Shenzhen Zego Technology Co., Ltd.') > 0:
                match_zego = True
                # print ("match {0}".format(certificate))
                break

        if match_zego:
            found_identity = True
            break

    if found_identity:
        return certificate
    else:
        return "iPhone Developer"


def get_time_str():
    import time
    date = time.strftime('%y%m%d_%H%M%S')
    jenkins_date = jenkinsutil.get_string('JENKINS_PIPELINE_DATE')
    if jenkins_date and len(jenkins_date) > 0:
        # 优先使用 Jenkins 自定义的环境变量里的日期，为了并发构建时统一时间
        date = jenkins_date
    return date


def copy_dir(src, dst):
    """Copy directory src to dst

    :param src: eg. '/var/include'
    :param dst: eg. '/usr/local/xx-include'
    """
    import shutil
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)


def remove_development_team_id(pbxproj_file_path: str):
    """清除 Xcode 工程文件中 Team ID 字段的值 (DEVELOPMENT_TEAM)

    使发布出去的 Demo 内的 Team ID 保持为空

    Args:
        pbxproj_file_path (str): Xcode project 内的 project.pbxproj 文件的绝对路径（如 ./XXXX.xcodeproj/project.pbxproj ）
    """
    if not os.path.exists(pbxproj_file_path):
        raise Exception('[Remove Xcode Project Development Team ID] Error: pbxproj file path not exists at: {}'.format(pbxproj_file_path))

    with open(pbxproj_file_path, 'r', encoding='UTF-8') as fr:
        all_lines = fr.readlines()

    with open(pbxproj_file_path, 'w', encoding='UTF-8') as fw:
        for line in all_lines:
            if 'DEVELOPMENT_TEAM' in line:
                fw.write(re.sub(pattern='DEVELOPMENT_TEAM.+;', repl='DEVELOPMENT_TEAM = "";', string=line))
                continue
            fw.write(line)


if __name__ == "__main__":
    cmake_ver, cmake_ver_list = get_cmake_version()
    print(cmake_ver, cmake_ver_list)
    print(get_certificate_name())
