#!/usr/bin/env python -u
# encoding: utf-8

import os
import sys
import shutil

from zegopy.common import command
from zegopy.common import io


def upload(share_folder, mount_path, mount_folder, copy_list):
    """usage:
    mount share server folder (share_folder) to mount_path
    create a folder (mount_folder) optional
    copy file list (copy_list) to mount_path/mount_folder"""
    print ("<< upload to share")

    if os.path.exists(mount_path):
        command.execute('umount -f {0}'.format(mount_path))

    print ("<< mount share")
    dest_share_path = '//share:share%40zego@192.168.1.3/share/{0}'.format(share_folder)
    state, result = command.execute('mount -t smbfs {0} {1}'.format(dest_share_path, mount_path))
    if state == 1:
        io.insure_dir_exists(mount_path)
        state, result = command.execute('mount -t smbfs {0} {1}'.format(dest_share_path, mount_path))

    if state != 0 and state != 64:
        raise Exception(state, result)

    dest_path = mount_path
    if len(mount_folder) != 0:
        dest_path = os.path.realpath(os.path.join(mount_path, mount_folder))
        io.insure_dir_exists(dest_path)

    print ("<< copy file")
    for item in copy_list:
        error_code = io.copy(item, dest_path, False)
        print ("copy {} to {} {}".format(item, dest_path, "success" if error_code == 0 else "failed"))

    state, text = command.execute('umount -f {0}'.format(mount_path))
    if state != 0:
        print ("** umount -f {0} failed **".format(mount_path))

    print ("<< upload to share finished")


def upload_win32(share_folder, mount_folder, copy_list):
    print ("<< upload to share")

    print ("<< mount share")
    dest_share_path = r'\\192.168.1.3\share\{0}'.format(share_folder)
    print ("<< dest share path {0}".format(dest_share_path))

    ok, result = command.execute(r'net use {0} share@zego /user:share'.format(dest_share_path))
    if ok != 0:
        print (result)
        raise Exception(ok, result)

    dest_path = dest_share_path
    if len(mount_folder) != 0:
        dest_path = os.path.realpath(os.path.join(dest_path, mount_folder))
        io.insure_dir_exists(dest_path)

    print ("<< copy file")

    for item in copy_list:
        print ("<< copy {0}".format(item))
        io.copy(item, dest_path, False)

    print ("<< upload to share finished")


def upload_linux(share_folder, mount_path, mount_folder, copy_list):
    """usage:
    mount share server folder (share_folder) to mount_path
    create a folder (mount_folder) optional
    copy file list (copy_list) to mount_path/mount_folder"""
    print ("<< upload to share")

    if os.path.exists(mount_path):
        command.execute('umount -f {0}'.format(mount_path))

    io.insure_dir_exists(mount_path)
    print ("<< mount share")
    dest_share_path = '//192.168.1.3/share/{0}'.format(share_folder)
    state, result = command.execute('mount -t cifs -o username=share,password=share@zego {0} {1}'.format(dest_share_path, mount_path))

    if state == 1:
        io.insure_dir_exists(mount_path)
        state, result = command.execute('mount -t cifs -o username=share,password=share@zego {0} {1}'.format(dest_share_path, mount_path))

    if state != 0:
        raise Exception(state, result)

    dest_path = mount_path
    if len(mount_folder) != 0:
        dest_path = os.path.realpath(os.path.join(mount_path, mount_folder))
        io.insure_dir_exists(dest_path)

    print ("<< copy file")
    for item in copy_list:
        error_code = io.copy(item, dest_path, False)
        print ("copy {} to {} {}".format(item, dest_path, "success" if error_code == 0 else "failed"))

    state, text = command.execute('umount -f {0}'.format(mount_path))
    if state != 0:
        print ("** umount -f {0} failed **".format(mount_path))

    print ("<< upload to share finished")


def get_default_share_path():
    return "smb://192.168.1.3/share"


if __name__ == '__main__':
    print ("<< zego upload")
    if sys.platform == 'win32':
        upload_win32(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        upload_apple(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
