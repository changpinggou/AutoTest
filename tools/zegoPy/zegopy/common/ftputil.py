#!/usr/bin/env python3
# coding: utf-8

"""
ftp util
"""

import os
import re
import warnings
import time
from ftplib import *

from zegopy.common import io as zegoio


class SimpleFTP:
    @staticmethod
    def _tag_print(msg):
        print("[zegoftp] {}".format(msg))

    @staticmethod
    def _join_remote_path(*pathseg):
        _tmp_path = os.path.join(*pathseg)

        # fix path error on windows OS
        return _tmp_path.replace('\\', '/')

    def __init__(self, host, port=21):
        """
        Return a new instance of the FTP class then connect the server
        :param host:
        :param port:
        """
        default_timeout_seconds = 30
        self._tag_print("connect server {} ...".format(host))
        if port != 21:
            self.ftp = FTP(host, source_address=(host, port), timeout=default_timeout_seconds)
        else:
            self.ftp = FTP(host, timeout=default_timeout_seconds)

        self.is_debug = False
        self.last_dir_name = ''
        self.host = host

    def _save_last_directory(self):
        self.last_dir_name = self.ftp.pwd()

    def _recover_last_directory(self):
        self.ftp.cwd(self.last_dir_name)

    def _is_dir(self, pathname) -> bool:
        if pathname in ('/', '.', './'):
            return True

        if pathname.endswith('/') or pathname.endswith('\\'):
            pathname = pathname[0: -1]

        dir_name, basename = os.path.split(pathname)
        items = self.list_dir(dir_name)
        for item in items:
            if item[0] == basename:
                return item[1] == 'd'

        return False

    def _turn_on_debug(self):
        if self.is_debug:
            self.ftp.set_debuglevel(2)

    def _turn_off_debug(self):
        self.ftp.set_debuglevel(0)

    def set_debug(self, is_debug):
        self.is_debug = is_debug

    def login(self, username="anonymous", passwd='', acct='') -> bool:
        """
        login the ftp server with username & passwd
        :param username:
        :param passwd:
        :param acct:
        :return:
        """
        self._tag_print("login server: {} ...".format(self.host))
        self.ftp.login(username, passwd, acct)
        return True

    def logout(self) -> bool:
        """
        logout the ftp server
        :return:
        """
        self._tag_print("logout server: {} ...".format(self.host))
        self.ftp.close()
        return True

    def curdir(self) -> str:
        return self.ftp.pwd()

    def chdir(self, pathname) -> str:
        """
        change to pathname,
        :param pathname:
        :return: current directory
        """
        self.ftp.cwd(pathname)
        return self.ftp.pwd()

    def list_dir(self, pathname) -> list:
        """
        like os.listdir
        :param pathname:
        :return: [(name, type, size, owner, group, date, perm),], 
            eg: [("test.txt", "d", 4321, "ftp", "ftp", "Jan 17 08:46", "rw-r--r--"),]
        """
        _items = []

        def _parse(item):
            pattern = re.compile("(^[-dl])([rwx-]{9})[^\d]+([\d])[\s]+([\S]+)[\s]+([\S]+)[\s]+([\d]+)[\s]([\S]+[\s][\d]+[\s][\d]{2}:[\d]{2})[\s]([\s\S]+)$")
            g = pattern.search(item)
            if g:
                _info = g.groups()
                _items.append((_info[7], _info[0], _info[5], _info[3], _info[4], _info[6], _info[1]))
            else:
                warnings.warn("unknown the line: " + item)

        self.ftp.retrlines('LIST ' + pathname, _parse)
        return _items

    def walk(self, remote_top_dir) -> iter:
        """
        like os.walk
        :param remote_top_dir:
        :return:
        """
        if not self.exist(remote_top_dir):
            warnings.warn("remote: {} not exists".format(remote_top_dir))
            return remote_top_dir, [], []

        top = remote_top_dir
        dirs = []
        nondirs = []
        items = self.list_dir(remote_top_dir)
        for item in items:
            if item[1] == 'd':
                dirs.append(item[0])
            else:
                nondirs.append(item[0])

        yield top, dirs, nondirs

        for folder in dirs:
            new_top = self._join_remote_path(top, folder)
            yield from self.walk(new_top)

    def exist(self, pathname) -> bool:
        """
        judge the directory has exists just now
        :param pathname:
        :return:
        """
        if pathname in ('/', '.', './'):
            return True

        if pathname.endswith('/') or pathname.endswith('\\'):
            pathname = pathname[0: -1]

        dir_name, basename = os.path.split(pathname)
        # noinspection PyBroadException
        try:
            self._save_last_directory()
            self.ftp.cwd(dir_name)
            _tmp_files = self.ftp.nlst('')
            return basename in _tmp_files
        except Exception as error_permission:
            print(error_permission)
            return False
        finally:
            self._recover_last_directory()

    def mkdirs(self, dir_name) -> bool:
        """
        create directory and it's sub directories
        :param dir_name: 待创建的目录(支持多级目录)
        :return:
        """
        def _safe_mkdir(pathname):
            parent, name = os.path.split(pathname)
            if not self.exist(pathname):
                if not self.exist(parent):
                    _safe_mkdir(parent)
                    self.ftp.mkd(pathname)
                else:
                    self.ftp.mkd(pathname)

        if dir_name.endswith('/') or dir_name.endswith('\\'):
            dir_name = dir_name[0: -1]

        dir_name = self._join_remote_path(dir_name)
        if not (dir_name.startswith('/') or dir_name.startswith('./')):
            dir_name = "./" + dir_name

        self._tag_print("create folder: " + dir_name)
        _safe_mkdir(dir_name)

        return True

    def upload(self, local_path, to_remote_path) -> bool:
        """
        upload local_path to remote_path
        :param local_path: the src file/folder
        :param to_remote_path: the target folder path
        :return:
        """
        def _store_single_file(src, dst, target_name):
            if os.path.islink(src):
                warnings.warn(">>> " + src + " is link file, not support just now!")
                return

            remote_file = self._join_remote_path(dst, target_name)
            self._tag_print("upload >>>\r\n   {}\r\n      --> {}".format(src, remote_file))
            self._turn_on_debug()

            last_error = None
            max_retry_cnt = 5
            for i in range(max_retry_cnt):
                fr = None
                # noinspection PyBroadException
                try:
                    fr = open(src, 'rb')
                    self.ftp.storbinary("STOR " + remote_file, fr)
                    self._tag_print("upload successful")
                    last_error = None
                    break
                except Exception as e:
                    last_error = e
                    self._tag_print("upload fail, because: {}".format(e))
                    self._tag_print("retry {} ....".format(i))
                    time.sleep(0.5)     # wait 0.5s
                finally:
                    if fr:
                        fr.close()

            self._turn_off_debug()

            if last_error:
                raise last_error

        if not os.path.exists(local_path):
            warnings.warn(local_path + " not exists")
            return False

        if os.path.isdir(local_path):
            if not (local_path[-1] == '/' or local_path[-1] == '\\'):
                local_path += os.path.sep

            folder_name = os.path.basename(local_path[: -1])
            _remote_root_path = self._join_remote_path(to_remote_path, folder_name)
            self.mkdirs(_remote_root_path)
            for root, dir_names, fnames in os.walk(local_path):
                _relpath = root.replace(local_path, "")
                _target_path = self._join_remote_path(_remote_root_path, _relpath)
                if _relpath :
                    self.mkdirs(_target_path)

                for fname in fnames:
                    _store_single_file(os.path.join(root, fname), _target_path, fname)
        else:
            self.mkdirs(to_remote_path)
            _store_single_file(local_path, to_remote_path, os.path.basename(local_path))

        return True

    def download(self, remote_path, to_local_path) -> bool:
        """
        download remote_path to local path
        :param remote_path: the src file/folder
        :param to_local_path: the target folder path
        :return:
        """
        def _download_single_file(src, dst, target_name):
            local_file = os.path.join(dst, target_name)
            self._tag_print("download <<<\r\n   {}\r\n      --> {}".format(src, local_file))
            self._turn_on_debug()

            last_error = None
            max_retry_cnt = 5
            for i in range(max_retry_cnt):
                fw = None
                # noinspection PyBroadException
                try:
                    fw = open(local_file, "wb")
                    self.ftp.retrbinary("RETR " + src, fw.write)
                    last_error = None
                    break
                except Exception as e:
                    last_error = e
                    self._tag_print("download fail, because: {}".format(e))
                    self._tag_print("retry {} ....".format(i))
                    time.sleep(0.5)  # wait 0.5s
                finally:
                    if fw:
                        fw.close()

            self._turn_off_debug()

            if last_error:
                raise last_error

        if not self.exist(remote_path):
            warnings.warn("remote: {} not exists".format(remote_path))
            return False

        zegoio.insure_dir_exists(to_local_path)

        is_dir = self._is_dir(remote_path)
        if not is_dir:
            remote_path = self._join_remote_path(remote_path)
            _download_single_file(remote_path, to_local_path, os.path.basename(remote_path))
            return True

        remote_path = remote_path[: -1] if remote_path not in ('/', '.', './') and remote_path[-1] in ('/', '\\') else remote_path
        folder_name = os.path.basename(remote_path)
        local_root_path = os.path.join(to_local_path, folder_name)
        for top, dirs, names in self.walk(remote_path):
            rel_path = top.replace(remote_path, '')
            if rel_path.startswith('/') or rel_path.startswith('\\'):
                rel_path = rel_path[1:]

            for name in names:
                remote_file = self._join_remote_path(top, name)
                local_relpath = os.path.join(local_root_path, rel_path)
                zegoio.insure_dir_exists(local_relpath)
                _download_single_file(remote_file, local_relpath, name)

        return True


def __test():
    print("simple ftp util")
    print("usage: {} {} <host> <username> <passwd>".format(sys.executable, os.path.basename(__file__)))
    ftp = SimpleFTP(sys.argv[1])
    ftp.login(sys.argv[2], sys.argv[3])

    print("cur dir: " + ftp.curdir())
    print("====" * 6)
    items = ftp.list_dir('.')
    for item in items:
        print(item)

    print("====" * 6)
    for top, dirs, names in ftp.walk('/'):
        print(top)
        for _name in names:
            print(os.path.join(top, _name))

    print("create dir ...")
    ftp.mkdirs('ftp test')

    print("====" * 6)
    for top, dirs, names in ftp.walk('/'):
        print(top)
        for _name in names:
            print(os.path.join(top, _name))

    ftp.logout()
    print("end.")


if __name__ == "__main__":
    import sys
    __test()
