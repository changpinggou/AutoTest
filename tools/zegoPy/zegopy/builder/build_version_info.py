#!/usr/bin/env python -u
# coding: utf-8

import os
import sys

from zegopy.builder import build_config_info
from zegopy.builder import zego_helper
from zegopy.common.jenkinsutil import get_bool

def get_version_number(git_repo_root):
    version_file = os.path.join(git_repo_root, "kernel", "version.json")
    import json
    with open(version_file) as of:
        c = of.read()
        j = json.loads(c)
        return j['major'], j['minor'], j['patch']


def gen_version_info(git_repo, build_type='', business_id='', time_str=''):
    print ("[*] Generate avkit version info")

    version_info = []
    if time_str:
        version_info.append(time_str)
    else:
        version_info.append(zego_helper.get_time_str())

    git_ver = zego_helper.get_git_version(git_repo)
    version_info.append(git_ver)

    if build_type:
        version_info.append(build_type)

    k_clientType = 'ZEGO_CLOUD_RECORD'
    if get_bool(k_clientType):
        version_info.append("cloud_record")
        
    k_build_num = 'BUILD_NUMBER'
    if k_build_num in os.environ:
        build_num = os.environ[k_build_num]
        print ('[*] Build Num:{0}'.format(build_num))
        version_info.append("bn{}".format(build_num))
    else:
        build_num = 0

    sdk_type = []
    k_chn = 'AVKIT_MAX_PLAY_CHANNELS'
    if k_chn in os.environ:
        max_channels = os.environ[k_chn]
        build_config_info.update_config_info("AVKIT_MAX_PLAY_CHANNELS", max_channels)
        print ('[*] VE MAX Play Channel: {0}'.format(max_channels))
        sdk_type.append(max_channels)

    version_info.extend(sdk_type)    
    avkit_version_str = '_'.join(version_info)
    if len(str.strip(business_id)) > 0:
        avkit_version_str += "_" + business_id
    build_config_info.update_config_info("ZEGO_SDK_VER", avkit_version_str)

    print ("[*] SDK version: {0}".format(avkit_version_str))

    sdk_type_str = '_'.join(sdk_type)

    if sys.platform == 'win32':
        version = get_version_number(git_repo)
        build_config_info.update_config_info("PRODUCT_VERSION_MAJOR", version[0])
        build_config_info.update_config_info("PRODUCT_VERSION_MINOR", version[1])
        build_config_info.update_config_info("PRODUCT_VERSION_PATCH", version[2])
        build_config_info.update_config_info("PRODUCT_VERSION_BUILD", build_num)

    return avkit_version_str, sdk_type_str


if __name__ == "__main__":
    os.environ['AVKIT_MAX_PLAY_CHANNELS'] = '20'
    os.environ['AVKIT_EARPHONE_NO_AEC'] = 'true'
    os.environ['AVKIT_EDUCATION_VERSION'] = 'true'
    os.environ['AVKIT_AUDIO_HD'] = 'true'
    gen_version_info("~/data/zego/code/zegoavkit", "")
