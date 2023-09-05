#!/usr/bin/env python -u
# encoding: utf-8

import os
import json
import tempfile

from zegopy.common import command as zegocmd


__VE_KEY_BUSINESS_ID = "business_id"
__VE_PKG_INFO_JSON = "ve_pkg_info.json"


def _update_ve_pkg_info_file(ve_pkg_info_file, business_id, ve_packages):
    json_config = None
    if os.path.exists(ve_pkg_info_file):
        with open(ve_pkg_info_file) as file_config_r:
            json_config = json.loads(file_config_r.read())
            if business_id in json_config:
                for key in ve_packages:
                    if key == __VE_KEY_BUSINESS_ID:
                        continue

                    json_config[business_id][key] = ve_packages[key]
            else:
                json_config[business_id] = ve_packages
    else:
        print("\n<< create new json file: {}".format(ve_pkg_info_file))
        json_config = {business_id: ve_packages}

    with open(ve_pkg_info_file, "w") as file_config_w:
        config_content = json.dumps(json_config, indent=4, sort_keys=True)
        file_config_w.write(config_content)
        print('\n<< update {} done:'.format(ve_pkg_info_file))
        print(config_content)


def _update_ve_pkg_info_on_server_mac(business_id, ve_packages, ve_pkg_info_server_path):
    mount_temp = tempfile.mkdtemp()

    src_share_path_no_login = ve_pkg_info_server_path  # 不带鉴权的串

    k_login_info = 'share:share%40zego@'
    src_share_path = '//' + k_login_info + ve_pkg_info_server_path[2:]  # 拼出带鉴权的串

    print("<< going to mount share {0} to {1}".format(src_share_path_no_login, mount_temp))

    ok, result = zegocmd.execute('mount -t smbfs {0} {1}'.format(src_share_path, mount_temp))
    if ok != 0:
        print(result)
        ok, result = zegocmd.execute('mount -t smbfs {0} {1}'.format(src_share_path_no_login, mount_temp))
        if ok != 0:
            print(result)
            raise Exception(ok)

    ve_pkg_info_file = os.path.join(mount_temp, __VE_PKG_INFO_JSON)
    _update_ve_pkg_info_file(ve_pkg_info_file, business_id, ve_packages)

    zegocmd.execute('umount -f {0}'.format(mount_temp))
    print('')


def _update_ve_pkg_info_on_server_win(business_id, ve_packages, ve_pkg_info_server_path):
    src_share_path = ve_pkg_info_server_path.replace("/", "\\")

    ok, result = zegocmd.execute(r'net use {0} share@zego /user:192.168.1.3\share'.format(src_share_path))
    if ok != 0:
        print(result.decode('gbk'))
        raise Exception(ok, result.decode('gbk'))

    ve_pkg_info_file = os.path.join(src_share_path, __VE_PKG_INFO_JSON)
    _update_ve_pkg_info_file(ve_pkg_info_file, business_id, ve_packages)

    print('')


def _update_ve_pkg_info_on_server_linux(business_id, ve_packages, ve_pkg_info_server_path):
    server_username = "share"
    server_pass = "share@zego"

    if ve_pkg_info_server_path.startswith("//"):
        ve_pkg_info_server_path = ve_pkg_info_server_path[2:]

    path_fragments = ve_pkg_info_server_path.split('/')
    path_fragments.append(__VE_PKG_INFO_JSON)

    server = "//{}/{}".format(path_fragments[0], path_fragments[1])
    remote_path = '/'.join(path_fragments[2:])
    local_path = os.path.realpath(os.path.join(tempfile.mkdtemp(), __VE_PKG_INFO_JSON))

    smb_get_cmd = '''smbclient {} -c "get {} {}" -U {}%{}'''.format(server, remote_path, local_path, server_username, server_pass)
    zegocmd.execute(smb_get_cmd)

    _update_ve_pkg_info_file(local_path, business_id, ve_packages)

    smb_put_cmd = '''smbclient {} -c "put {} {}" -U {}%{}'''.format(server, local_path, remote_path, server_username, server_pass)
    zegocmd.execute(smb_put_cmd)

    print('')


def write_config(business_id, ve_packages, ve_pkg_info_server_path):
    """根据 ve 传递过来的产物，更新相应的配置信息"""

    ve_packages = json.loads(ve_packages)

    print('<< ve pkg info server path: {}'.format(ve_pkg_info_server_path))
    print('<< business id: {}'.format(business_id))
    print('<< ve products: \n{}\n'.format(json.dumps(ve_packages, indent=4, sort_keys=True)))

    from sys import platform
    # mac
    if platform == 'darwin':
        _update_ve_pkg_info_on_server_mac(business_id, ve_packages, ve_pkg_info_server_path)

    if platform == 'win32':
        _update_ve_pkg_info_on_server_win(business_id, ve_packages, ve_pkg_info_server_path)

    if platform == 'linux' or platform == 'linux2':
        _update_ve_pkg_info_on_server_linux(business_id, ve_packages, ve_pkg_info_server_path)
