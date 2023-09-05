#!/usr/bin/env python3
# coding:utf-8


import os
import sys
import shutil
import tempfile
import threading
import time

from sys import platform

if sys.version_info.major < 3:
    import urllib
else:
    import urllib.request as urllib

from zegopy.common import osutil
from zegopy.common import io as zegoio
from zegopy.common import command as zegocmd


class _AbsMount:
    def __init__(self, host, root_folder):
        self._host = host
        self._root = root_folder
        self._username = None
        self._password = None

    def set_user(self, user_name, password):
        self._username = user_name
        self._password = password

    def mount(self, mount_node=None):
        pass

    def umount(self):
        pass

    def pull(self, src_server_path, to_local_path, overwrite=False):
        pass

    def push(self, src_local_path, to_server_path, overwrite=False):
        pass

    @staticmethod
    def _get_safe_target(src, target, overwrite=False):
        if target is None:
            raise Exception("target is None")
        elif target.startswith("~"):
            target = os.path.realpath(os.path.expanduser(target))

        if (os.path.exists(target) and os.path.isdir(target)) or not os.path.exists(target):
            target = os.path.join(target, os.path.basename(src))

        if not overwrite:
            target = zegoio.get_safe_filename(target)

        return target


class _WindowsMountImpl(_AbsMount):
    def __init__(self, host, root_folder):
        _AbsMount.__init__(self, host, root_folder)
        self.__is_mounted = False

    def __del__(self):
        self.umount()

    def mount(self, mount_node=None):
        if self.__is_mounted:
            return

        remote_ipc = '''\\\\{}\\{}'''.format(self._host, self._root)
        mount_cmd = '''net use {} {} /user:192.168.1.3\{}'''.format(remote_ipc, self._password, self._username)
        code = zegocmd.execute_and_print(mount_cmd)
        if code != 0:
            print('[ERROR] "net use" encounter some issue!')
            # Do not raise exception, it maybe ok even throw error code
            # raise Exception(code, "mount failed")

        self.__is_mounted = True

    def umount(self):
        if not self.__is_mounted:
            return

        remote_ipc = '''\\\\{}\\{}'''.format(self._host, self._root)
        zegocmd.execute_and_print('net use {} /del'.format(remote_ipc))

    def pull(self, src_server_path, to_local_path, overwrite=False):
        is_tmp_mount = False
        if not self.__is_mounted:
            self.mount()
            is_tmp_mount = True

        to_local_path = to_local_path.replace('/', '\\')
        remote_ipc = '''\\\\{}\\{}\\{}'''.format(self._host, self._root, src_server_path)
        safe_target_path = self._get_safe_target(src_server_path, to_local_path, overwrite)
        zegoio.copy2(remote_ipc, safe_target_path)

        if is_tmp_mount:
            self.umount()

    def push(self, src_local_path, to_server_path, overwrite=False):
        is_tmp_mount = False
        if not self.__is_mounted:
            self.mount()
            is_tmp_mount = True

        to_server_path = to_server_path.replace('/', '\\')
        remote_ipc = '''\\\\{}\\{}\\{}'''.format(self._host, self._root, to_server_path)
        zegoio.copy(src_local_path, remote_ipc, overwrite)

        # safe_target_path = self._get_safe_target(src_local_path, remote_ipc, overwrite)
        # zegoio.copy2(src_local_path, safe_target_path)

        if is_tmp_mount:
            self.umount()


class _LinuxMountImpl(_AbsMount):
    def pull(self, src_server_path, to_local_path, overwrite=False):
        """
        从 Share 服务器上拉取一个文件到本地
        :param src_server_path Share 服务器上的文件地址（为一个相对路径，且不包含 Host 和 Root Folder 信息），如 zego_sdk/zegoliveroom_master/zegoliveroom_v1.zip
        :param to_local_path 目标地址，可以是文件，也可以是目录。如果 overwrite 为 False 且目标文件已存在时，会取一个新的名字
        :param overwrite 当目标文件已经存在时，是否覆盖。默认为 False
        """
        server = "//{}/{}".format(self._host, self._root)
        src_server_path = src_server_path.replace("\\", "/")
        safe_target_path = self._get_safe_target(src_server_path, to_local_path, overwrite)
        zegoio.insure_dir_exists(os.path.dirname(safe_target_path))

        smb_copy_cmd = '''smbclient {} -t 1800 -c "get {} {}" -U {}%{}'''.format(server, src_server_path, safe_target_path, self._username, self._password)
        code = zegocmd.execute_and_print(smb_copy_cmd)
        if code != 0:
            raise Exception(code, "pull failed")

        if not os.path.exists(safe_target_path):
            raise Exception("pull {} failed".format(src_server_path))

    def push(self, src_local, to_server_path, overwrite=True):
        """
        上传一个本地文件至 Share 服务器指定路径，overwrite 在此平台上无效，始终为 True
        :param src_local 本地文件路径
        :param to_server_path Share 服务器上存储目录
        :param overwrite 在此平台上该参数无效，始终为 True
        """
        if not os.path.exists(src_local):
            raise Exception("file {} not exists".format(src_local))

        server = "//{}/{}".format(self._host, self._root)
        to_server_path = to_server_path.replace("\\", "/")

        to_server_path_segments = to_server_path.split('/')
        mkdir_cmd = ''''''
        for i in range(0, len(to_server_path_segments)):
            mkdir_cmd += "mkdir {};".format('/'.join(to_server_path_segments[:i + 1]))

        smb_mkdir_cmd = '''smbclient {} -c "{}" -U {}%{}'''.format(server, mkdir_cmd, self._username, self._password)
        code = zegocmd.execute_and_print(smb_mkdir_cmd)
        if code != 0:
            raise Exception(code, "push failed")

        to_server_path = os.path.join(to_server_path, os.path.basename(src_local))
        smb_put_cmd = '''smbclient {} -c "put {} {}" -U {}%{}'''.format(server, src_local, to_server_path, self._username, self._password)
        code = zegocmd.execute_and_print(smb_put_cmd)
        if code != 0:
            raise Exception(code, "push failed")


class _NotExistsError(Exception):
    def __init__(self, *args, **kwargs):
        super(Exception, self).__init__(args, kwargs)


class _OtherOSMountImpl(_AbsMount):
    def __init__(self, host, root_folder):
        _AbsMount.__init__(self, host, root_folder)
        self.__mount_node = None

    def __del__(self):
        self.umount()

    def __get_mount_list(self):
        mount_node_list = []
        code, text = zegocmd.execute("mount")
        for line in text.split(os.linesep):
            if self._host not in line:
                continue
            remote, local_and_flags = line.split(' on ')
            pos = local_and_flags.rfind('(')
            local = local_and_flags[:pos]
            flags = local_and_flags[pos:-1]
            user = flags.split(',')[-1].replace('mounted by', '').strip()

            mount_node_list.append((remote, local, user))

        return mount_node_list

    def __mount(self, remote_path, local_path):
        mount_url_no_authority = '''//{}/{}'''.format(self._host, remote_path)
        mount_url_with_authority = '''//{}:{}@{}/{}'''.format(self._username, urllib.pathname2url(self._password),
                                                              self._host, remote_path)
        print("<< going to mount share {} to {}".format(mount_url_no_authority, local_path))

        code, text = 0, ""
        for mount_url in (mount_url_with_authority, mount_url_no_authority):
            retry = True
            while True:
                mount_cmd = "mount -t smbfs {} {}".format(mount_url, local_path)
                code, text = zegocmd.execute(mount_cmd)
                if code != 0 and retry:
                    if "File exists" in text:
                        print("the {} has been mounted, mount node list:".format(mount_url))
                        _mounted_nodes = self.__get_mount_list()
                        for _node_info in _mounted_nodes:
                            print("{} mounted in {} by {}".format(*_node_info))

                        print("\r\nretry after wait 30s ...")
                        time.sleep(30)

                        retry = False
                        continue
                    elif "No such file or directory" in text:
                        raise _NotExistsError(code, "mount failed: %s".format(text))

                break

            if code == 0:
                print("mount success")
                break

        if code != 0:
            raise Exception(code, "mount failed: %s".format(text))

    @staticmethod
    def __umount(mount_node):
        code = zegocmd.execute_and_print('umount -f {0}'.format(mount_node))
        if code == 0:
            print("umount success")
        else:
            print("* umount {} failed".format(mount_node))

    def __get_mount_node(self):
        return tempfile.mkdtemp() if self.__mount_node is None else self.__mount_node

    def mount(self, mount_node=None):
        if mount_node is not None and os.path.exists(mount_node) and len(os.path.listdir(mount_node)) > 0:
            raise Exception("mount target: {} not empty".format(mount_node))

        self.__mount_node = mount_node

    def umount(self):
        self.__mount_node = None

    def pull(self, src_server_path, to_local_path, overwrite=False):
        rel_path, basename = os.path.split(src_server_path)
        mount_node = self.__get_mount_node()
        self.__mount(os.path.join(self._root, rel_path), mount_node)
        try:
            src_path = os.path.join(mount_node, basename)
            safe_local_path = self._get_safe_target(src_path, to_local_path, overwrite)
            print("copy {} to {} with overwrite? {}".format(src_path, safe_local_path, overwrite))
            err_code = zegoio.copy2(src_path, safe_local_path, overwrite)

            if err_code != 0:
                raise Exception(err_code, "pull to {} from {} failed".format(to_local_path, src_server_path))
        finally:
            self.__umount(mount_node)

    def push(self, src_local_path, to_server_path, overwrite=False):
        rel_path, basename = os.path.split(to_server_path)

        mount_node = self.__get_mount_node()
        while True:
            try:
                self.__mount(os.path.join(self._root, rel_path), mount_node)
                break
            except _NotExistsError:
                if rel_path == "":
                    raise Exception("mount failed: unknown")
                rel_path, _folder_name = os.path.split(rel_path)
                basename = os.path.join(_folder_name, basename)

        try:
            to_path = os.path.join(mount_node, basename)
            print("copy {} to {} with overwrite? {}".format(src_local_path, to_path, overwrite))
            err_code = zegoio.copy(src_local_path, to_path, overwrite)

            # safe_target_path = self._get_safe_target(src_local_path, to_path, overwrite)
            # err_code = zegoio.copy2(src_local_path, safe_target_path)

            if err_code != 0:
                raise Exception(err_code, "push {} to {} failed".format(src_local_path, to_server_path))
        finally:
            self.__umount(mount_node)


class Mount:
    """
    pull file from or push file to smbshare server
    """
    _lock = threading.Lock()

    def __init__(self, host, root_folder):
        self.__mount_impl = None
        __is_windows_os = platform == "win32"
        __is_linux_os = (platform == "linux" or platform == "linux2")
        if __is_windows_os:
            self.__mount_impl = _WindowsMountImpl(host, root_folder)
        elif __is_linux_os:
            self.__mount_impl = _LinuxMountImpl(host, root_folder)
        else:   # like Darwin
            self.__mount_impl = _OtherOSMountImpl(host, root_folder)

    def set_user(self, username, password):
        self.__mount_impl.set_user(username, password)

    def mount(self, mount_node=None):
        self.__mount_impl.mount(mount_node)

    def umount(self):
        self.__mount_impl.umount()

    def pull(self, src_remote_file, to_local_dir, overwrite=False):
        """
        将 Share 服务器上的文件/文件夹下载至本地 to_local_path 目录下

        :param src_remote_file: Share 服务器上的文件/文件夹路径
        :param to_local_dir: 本地目录
        :param overwrite: 当目标目录/文件存在时，是否覆盖。部分平台不支持
        :return: None
        """
        Mount._lock.acquire()
        try:
            self.__mount_impl.pull(src_remote_file, to_local_dir, overwrite)
        finally:
            Mount._lock.release()

    def push(self, src_local_file, to_remote_dir, overwrite=False):
        """
        上传一个本地文件/文件夹至 Share 服务器指定路径

        :param src_local_file: 本地文件路径
        :param to_remote_dir: 服务器上存储目录
        :param overwrite: 当目标目录/文件存在时，是否覆盖。部分平台不支持
        :return: None
        """
        Mount._lock.acquire()
        try:
            self.__mount_impl.push(src_local_file, to_remote_dir, overwrite)
        finally:
            Mount._lock.release()


if __name__ == "__main__":
    print(Mount.__doc__)
    test_file = os.path.realpath(__file__)
    script_name = os.path.basename(test_file)
    print("push file: {} to 192.168.1.3/share/tmp".format(test_file))

    m = Mount("192.168.1.3", "share")
    m.set_user("share", sys.argv[1])  # sys.argv[1] is password
    m.push(test_file, "tmp/this/is/in/{}".format(osutil.get_current_os_name()))
    print("file list before pull: ", os.listdir('.'))
    m.pull("tmp/this/is/in/{}/{}".format(osutil.get_current_os_name(), script_name), "tmp_target")
    print("file list after pull: ", os.listdir('tmp_target'))
    if os.path.exists("tmp_target") and os.path.exists(os.path.join('tmp_target', script_name)):
        shutil.rmtree('tmp_target')
    else:
        print("pull failed")
