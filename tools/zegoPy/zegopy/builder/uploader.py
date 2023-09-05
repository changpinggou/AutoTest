#!/usr/bin/env python3
# coding: utf-8

"""
上传文件/文件夹/文件列表至指定服务器上。
目前支持类型：
    1 FTP 服务器
    2 SMB 服务器
"""

import os
from datetime import datetime

from zegopy.common.ftputil import SimpleFTP
from zegopy.common.mount import Mount


class SimpleUploader:
    SERVER_TYPE_FTP = 1     # 上传至 FTP
    SERVER_TYPE_SMB = 2     # 上传至 Share

    _DEFAULT_FTP_SERVER_IP = "192.168.100.36"
    _DEFAULT_FTP_WRITE_USER_NAME = "writer"
    _DEFAULT_FTP_WRITE_PASSWD = "ugSX51pqKM40whBE"

    _DEFAULT_SMB_SERVER_IP = "192.168.1.3"
    _DEFAULT_SMB_ROOT_FOLDER = "share"
    _DEFAULT_SMB_USER_NAME = "share"
    _DEFAULT_SMB_USER_PASSWD = "share@zego"

    def __init__(self, server_type=SERVER_TYPE_SMB, root_folder="share"):
        """
        默认上传至 smb 服务器的 share 目录
        :param server_type: 服务器类型。 1 为 ftp server, 2 为 smb server
        :param root_folder: SMB 根目录，仅在 server_type 为 2 时有效，默认会为 share。目前支持 share、share02、share03
        """
        self.server_type = server_type
        if server_type == SimpleUploader.SERVER_TYPE_FTP:
            self.ftp_server_ip = SimpleUploader._DEFAULT_FTP_SERVER_IP
            self.ftp_user_name = SimpleUploader._DEFAULT_FTP_WRITE_USER_NAME
            self.ftp_passwd = SimpleUploader._DEFAULT_FTP_WRITE_PASSWD
            self.ftp = None
        elif server_type == SimpleUploader.SERVER_TYPE_SMB:
            self.smb_server_ip = SimpleUploader._DEFAULT_SMB_SERVER_IP
            if root_folder:
                self.smb_root_folder = root_folder
            else:
                self.smb_root_folder = SimpleUploader._DEFAULT_SMB_ROOT_FOLDER
            self.smb_user_name = SimpleUploader._DEFAULT_SMB_USER_NAME
            self.smb_user_passwd = SimpleUploader._DEFAULT_SMB_USER_PASSWD
            self.mount = None
        else:
            raise Exception("unsupported server type: {} just now".format(server_type))

    def __del__(self):
        if self.server_type == SimpleUploader.SERVER_TYPE_FTP and self.ftp:
            self.ftp.logout()
            self.ftp = None

        if self.server_type == SimpleUploader.SERVER_TYPE_SMB and self.mount:
            self.mount.umount()
            self.mount = None

    def _get_ftp(self):
        if not self.ftp:
            self.ftp = SimpleFTP(self.ftp_server_ip)
            self.ftp.login(self.ftp_user_name, self.ftp_passwd)

        return self.ftp

    def _get_mount(self):
        if not self.mount:
            self.mount = Mount(self.smb_server_ip, self.smb_root_folder)
            self.mount.set_user(self.smb_user_name, self.smb_user_passwd)
            self.mount.mount()

        return self.mount

    @staticmethod
    def _tag_print(msg):
        print("[uploader] {}".format(msg))

    @staticmethod
    def _convert_path(remote_folder):
        year_str = str(datetime.today().year)
        sep_pos = remote_folder.find('/', 1)
        if sep_pos < 0:
            sep_pos = remote_folder.find('\\', 1)

        new_path = os.path.join(remote_folder, year_str)
        if sep_pos > 0:
            new_path = os.path.join(remote_folder[: sep_pos], year_str, remote_folder[sep_pos + 1:])
        return new_path.replace('\\', '/')

    def _get_down_url(self, remote_folder, local_file):
        _tmp_sub_folder = remote_folder.replace('\\', '/')
        if _tmp_sub_folder.startswith('/'):
            _tmp_sub_folder = _tmp_sub_folder[1:]
        if _tmp_sub_folder.endswith('/'):
            _tmp_sub_folder = _tmp_sub_folder[:-1]

        target_name = os.path.basename(local_file)
        if self.server_type == SimpleUploader.SERVER_TYPE_FTP:
            return "ftp://{}/{}/{}".format(self.ftp_server_ip, _tmp_sub_folder, target_name)
        elif self.server_type == SimpleUploader.SERVER_TYPE_SMB:
            return "smb://{}/{}/{}/{}".format(self.smb_server_ip, self.smb_root_folder, _tmp_sub_folder, target_name)

        raise Exception("unsupported just now")

    def upload(self, local_path, remote_folder, auto_group=False) -> str:
        """
        上传文件至 FTP 服务器指定远程目录
        :param local_path: 支持文件、文件夹、软链接， 当为 link 时，上传的是 link 指向的文件内容，暂不支持上传 link 本身
        :param remote_folder: 远程根目录
        :param auto_group: 是否在 remote_folder 下按年份组织子目录，如 av-sdk/master, 实际为 av-sdk/2020/master，默认为 True
        :return: 返回下载地址
        """
        def _upload_with_ftp(_local_path, _remote_folder):
            ftp = self._get_ftp()
            return ftp.upload(_local_path, _remote_folder)

        def _upload_with_smb(_local_path, _remote_folder):
            mount = self._get_mount()
            mount.push(_local_path, _remote_folder)
            return True

        if not os.path.exists(local_path):
            self._tag_print("{} not exists".format(local_path))
            return None

        if not remote_folder or len(remote_folder.strip()) == 0:
            self._tag_print("remote root folder can't be null")
            return None

        if auto_group:
            remote_folder = self._convert_path(remote_folder)

        if self.server_type == SimpleUploader.SERVER_TYPE_FTP:
            success = _upload_with_ftp(local_path, remote_folder)
        elif self.server_type == SimpleUploader.SERVER_TYPE_SMB:
            success = _upload_with_smb(local_path, remote_folder)

        return self._get_down_url(remote_folder, local_path) if success else None

    def upload_list(self, file_list, remote_folder, auto_group=False) -> str:
        """
        上传一组文件/文件夹至 FTP 服务器指定目录
        :param file_list: 待上传文件/文件夹列表
        :param remote_folder: 远程根目录
        :param auto_group: 是否在 remote_folder 下按年份组织子目录，默认为 True
        :return: 返回下载地址
        """
        if not file_list:
            self._tag_print("will be upload list is empty")
            return None

        if not remote_folder or len(remote_folder.strip()) == 0:
            self._tag_print("remote root folder can't be null")
            return None

        if auto_group:
            remote_folder = self._convert_path(remote_folder)

        success = False
        for _file_path in file_list:
            if not os.path.exists(_file_path):
                self._tag_print("{} not exists, ignore upload")
                continue

            if self.server_type == SimpleUploader.SERVER_TYPE_FTP:
                _success = self._get_ftp().upload(_file_path, remote_folder)
                if not _success:
                    self._tag_print("{} upload failed".format(_file_path))
            elif self.server_type == SimpleUploader.SERVER_TYPE_SMB:
                self._get_mount().push(_file_path, remote_folder)
                _success = True

            success = _success or success

        return self._get_down_url(remote_folder, "") if success else None

    def update_ftp_server_info(self, server_ip, user_name, user_passwd):
        """
        更新 FTP 服务器信息，默认为 192.168.100.36
        :param server_ip: ftp server ip
        :param user_name: ftp login user name
        :param user_passwd: ftp login user password
        :return: None
        """
        if self.server_type == SimpleUploader.SERVER_TYPE_FTP:
            self.ftp_server_ip = server_ip
            self.ftp_user_name = user_name
            self.ftp_passwd = user_passwd
            if self.ftp:
                self.ftp.logout()
            self.ftp = None

    def update_smb_server_info(self, server_ip, root_folder, user_name, user_passwd):
        """
        更新 SMB 服务器信息，默认为 192.168.1.3/share
        :param server_ip: share server ip
        :param root_folder: share root folder
        :param user_name: login user name
        :param user_passwd: login user password
        :return: None
        """
        if self.server_type == SimpleUploader.SERVER_TYPE_SMB:
            self.smb_server_ip = server_ip
            self.smb_root_folder = root_folder
            self.smb_user_name = user_name
            self.smb_user_passwd = user_passwd
            if self.mount:
                self.mount.umount()
            self.mount = None


if __name__ == "__main__":
    uploader = SimpleUploader(root_folder="share")
    down_url = uploader.upload(__file__, '/test')
    print("download: " + down_url)
    down_url = uploader.upload(__file__, 'test/2', auto_group=False)
    print("download: " + down_url)
