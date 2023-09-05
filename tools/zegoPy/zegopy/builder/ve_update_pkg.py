#!/usr/bin/env python -u
# encoding: utf-8

import os
import zipfile
import shutil
import time
import json
import sys

import tempfile

from zegopy.common import command as zegocmd
from zegopy.common import io as zegoio


def _update_pgk(include_dst, bin_lib_src, bin_lib_dst, zipfile_pathname, tmp_path, copy_include=True):
    print ("Unzip to " + tmp_path)

    include_src = os.path.join(tmp_path, "ve_release_pkg", "sdk", "include")

    zegoio.insure_empty_dir(tmp_path)

    try:
        zf = zipfile.ZipFile(zipfile_pathname)
        zf.extractall(tmp_path)
    except IOError as e:
        print (e)
        return False

    if copy_include:
        shutil.rmtree(include_dst, ignore_errors=True)
        shutil.copytree(include_src, include_dst)

    shutil.rmtree(bin_lib_dst, ignore_errors=True)
    shutil.move(bin_lib_src, bin_lib_dst)

    shutil.rmtree(tmp_path, ignore_errors=True)

    return True


def _copy_file_from_smb_server_apple(share_server_path, filename, to_local_path):
    """拷贝 share 中 share_server_path 目录中的文件到 to_local_path 目录中
    例如：
        share_server_path: 've_release/ve_dev_udp/agc-170-g7fd77b48_170418_164201/'
        to_local_path: '/Users/randyqiu/Desktop/tmp'
    """

    print ('<< going to copy {0} {1} to {2}'.format(share_server_path, filename, to_local_path))

    mount_temp = tempfile.mkdtemp()

    src_share_path_no_login = share_server_path                     # 不带鉴权的串

    k_login_info = 'share:share%40zego@'
    src_share_path = '//' + k_login_info + share_server_path[2:]    # 拼出带鉴权的串

    print ("<< going to mount share {0} to {1}".format(src_share_path_no_login, mount_temp))

    ok, result = zegocmd.execute('mount -t smbfs {0} {1}'.format(src_share_path, mount_temp))
    if ok != 0:
        print (result)
        ok, result = zegocmd.execute('mount -t smbfs {0} {1}'.format(src_share_path_no_login, mount_temp))
        if ok != 0:
            print (result)
            raise Exception(ok)

    src_pathname = os.path.join(mount_temp, filename)
    print ('<< going to copy {0} to {1}'.format(filename, to_local_path))
    shutil.copy(src_pathname, to_local_path)

    zegocmd.execute('umount -f {0}'.format(mount_temp))


def _read_config(vesdk_root, config_name):
    """根据平台读取配置"""
    with open(os.path.join(vesdk_root, 've_pkg_info.json')) as of:
        j = json.loads(of.read())

        if sys.platform == 'win32':
            return j[config_name]['windows'],
        else:
            return j[config_name]['apple'], j[config_name]['android']


def _copy_ve_to_updates_dir(vesdk_root, config_name='audio-video'):
    """复制 ve 库
    通过配置文件读取要拷贝的文件列表"""
    if sys.platform == 'win32':
        raise Exception('NOT SUPPORT YET')

    file_list = []

    pkg_list = _read_config(vesdk_root, config_name)
    for pkg in pkg_list:
        pkg = pkg[4:]   # 去掉 'smb:'
        filename = os.path.split(pkg)[-1]
        server_path = os.path.dirname(pkg)
        if os.path.exists(os.path.join(vesdk_root, 'updates', filename)):
            print ('>> ** Skip ** {0}'.format(filename))
            continue

        # 从 share 上复制文件
        _copy_file_from_smb_server_apple(server_path, filename, os.path.join(vesdk_root, 'updates'))
        file_list.append(filename)

    return file_list


def update_all_pkg(vesdk_root, copy_include=True, libs_dest_folder="libs", update_log=True):
    updates_path = os.path.join(vesdk_root, "updates")
    log_file = os.path.join(vesdk_root, "update_log.txt")

    for f in os.listdir(updates_path):
        if not f.endswith(".zip"):
            continue

        zipfile_pathname = os.path.join(updates_path, f)
        print (zipfile_pathname)

        ok = False
        if f.find("win32") != -1:
            print ("win32 package: " + f)

            tmp_path = os.path.join(updates_path, "tmp_win32")
            include_dst = os.path.join(vesdk_root, "include", "vs2015")
            bin_lib_src = os.path.join(tmp_path, "ve_release_pkg", "sdk", "win32", "libs")
            bin_lib_dst = os.path.join(vesdk_root, libs_dest_folder, "vs2015")

            ok = _update_pgk(include_dst, bin_lib_src, bin_lib_dst, zipfile_pathname, tmp_path, copy_include)

        elif f.find("android") != -1:
            print ("android package: " + f)

            tmp_path = os.path.join(updates_path, "tmp_android")
            include_dst = os.path.join(vesdk_root, "include", "android")
            bin_lib_src = os.path.join(tmp_path, "ve_release_pkg", "sdk", "Android", "libs")
            bin_lib_dst = os.path.join(vesdk_root, libs_dest_folder, "android")

            ok = _update_pgk(include_dst, bin_lib_src, bin_lib_dst, zipfile_pathname, tmp_path, copy_include)

        elif f.find("ios") != -1:
            print ("ios/mac package: " + f)
            tmp_path = os.path.join(updates_path, "tmp_apple")

            include_dst = os.path.join(vesdk_root, "include", "apple")
            bin_lib_src = os.path.join(tmp_path, "ve_release_pkg", "sdk", "ios", "libs")
            bin_lib_dst = os.path.join(vesdk_root, libs_dest_folder, "ios")

            ok = _update_pgk(include_dst, bin_lib_src, bin_lib_dst, zipfile_pathname, tmp_path, copy_include)

            if ok:
                bin_lib_src = os.path.join(tmp_path, "ve_release_pkg", "sdk", "mac", "libs")
                bin_lib_dst = os.path.join(vesdk_root, libs_dest_folder, "mac")
                ok = _update_pgk(include_dst, bin_lib_src, bin_lib_dst, zipfile_pathname, tmp_path, copy_include)

        else:
            print ("Unknown zip file {}".format(f))
            return False

        if ok:
            if update_log:
                update_description = time.strftime('[%Y-%m-%d %H:%M:%S] ') + f
                print ("Updated libs: " + update_description)

                with open(log_file, "a") as out_log:
                    out_log.write(update_description + "\n")
        else:
            print ("Update ERROR: " + f)
            return False

        print ("")

    return True


def update_audio_pkg(vesdk_root_path):
    added_file_list = _copy_ve_to_updates_dir(vesdk_root_path, 'audio-only')
    if len(added_file_list) == 0:
        print ("No Need to Update VE")
    else:
        update_all_pkg(vesdk_root_path, False, "aelibs", False)
        print ("Update aelibs finish.")
