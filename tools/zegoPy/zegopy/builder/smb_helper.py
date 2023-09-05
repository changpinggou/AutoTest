#!/usr/bin/env python -u
# coding: utf-8

import os
import tempfile
import shutil
from zegopy.common import command as zegocmd
from zegopy.common import log

def copy_file_from_smb_server_apple(share_server_path, filename, to_local_path):
    """拷贝 share 中 share_server_path 目录中的文件到 to_local_path 目录中
    例如：
        share_server_path: '//192.168.1.3/share/zego_sdk/zegoavkit-master/180206_101316_master-0-gac7c649_bn24_12/iOS'
        filename: '180206_101316_master-0-gac7c649_bn24_12.zip'
        to_local_path: '.'
    """
    
    log.i ('going to copy {0} {1} to {2}'.format(share_server_path, filename, to_local_path))
    
    mount_temp = tempfile.mkdtemp()
    log.i('created temp dir: %s' % mount_temp)
    
    src_share_path_no_login = share_server_path  # 不带鉴权的串
    
    k_login_info = 'share:share%40zego@'
    src_share_path = '//' + k_login_info + share_server_path[2:]  # 拼出带鉴权的串
    
    log.i ('going to mount share {0} to {1}'.format(src_share_path_no_login, mount_temp))
    
    ok, result = zegocmd.execute('mount -t smbfs {0} {1}'.format(src_share_path, mount_temp))
    if ok != 0:
        print (result)
        ok, result = zegocmd.execute('mount -t smbfs {0} {1}'.format(src_share_path_no_login, mount_temp))
        if ok != 0:
            shutil.rmtree(mount_temp)
            log.e(result)
    
    src_pathname = os.path.join(mount_temp, filename)
    log.i('going to copy {0} to {1}'.format(filename, to_local_path))
    shutil.copy(src_pathname, to_local_path)
    
    ok, result = zegocmd.execute('umount -f {0}'.format(mount_temp))
    if ok:
        shutil.rmtree(mount_temp)
    