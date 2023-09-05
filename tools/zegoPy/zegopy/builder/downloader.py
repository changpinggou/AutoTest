#!/usr/bin/env python3
# coding: utf-8

"""
    仅简单支持 Zego 内部 192.168.1.3 Share 服务器 及 192.168.100.36 FTP 服务器文件下载
"""


import os

from zegopy.common.ftputil import SimpleFTP
from zegopy.common.mount import Mount


class SimpleDownloader:
    """
    仅简单支持 Zego 内部 192.168.1.3 Share 服务器 及 192.168.100.36 FTP 服务器文件下载
    """
    _FTP_SCHEME = "ftp"
    _SMB_SCHEME = "smb"

    _SMB_SERVER_IP = "192.168.1.3"
    _SMB_USER_NAME = "share"
    _SMB_USER_PASSWD = "share@zego"

    # 配置带端口号的 FTP 服务器信息时，key 为 ip:port, eg: "192.168.100.36:21"
    _FTP_SERVER_INFO = {
        "192.168.100.36": {
            "name": "reader",
            "passw": "hiVX62pzSI53maEC",
        }
    }

    def __init__(self):
        self._mount = None
        self._last_mount_root = None
        self._cached_ftps = {}  # {<server_ip>: <ftp_obj>}

    def __del__(self):
        if self._mount:
            self._mount.umount()
            self._mount = None

        while self._cached_ftps:
            ip, _ftp = self._cached_ftps.popitem()
            _ftp.logout()
            _ftp = None

    @staticmethod
    def _get_scheme_type_(url):
        if not url:
            return None

        url = url.lower()
        if url.startswith('ftp://'):
            return SimpleDownloader._FTP_SCHEME
        elif url.startswith('smb://'):
            return SimpleDownloader._SMB_SCHEME

        pos = url.find('://')
        return url[:pos] if pos > 0 else None

    def _get_mount(self, root_folder):
        if not self._mount or self._last_mount_root != root_folder:
            if self._mount:
                self._mount.umount()

            self._mount = Mount(SimpleDownloader._SMB_SERVER_IP, root_folder)
            self._mount.set_user(SimpleDownloader._SMB_USER_NAME, SimpleDownloader._SMB_USER_PASSWD)
            self._mount.mount()

            self._last_mount_root = root_folder

        return self._mount

    def _get_ftp(self, ip_port):
        if ip_port not in self._cached_ftps:
            if ip_port not in SimpleDownloader._FTP_SERVER_INFO:
                raise Exception("[zegodown] Unsupported ftp: {}, please config '_FTP_SERVER_INFO' first".format(ip_port))

            user_info = SimpleDownloader._FTP_SERVER_INFO[ip_port]

            ip, port = ip_port, 21
            if ":" in ip_port:
                server_info = ip_port.split(':')
                ip = server_info[0]
                port = int(server_info[1])

            _ftp = SimpleFTP(ip, port)
            _ftp.login(user_info["name"], user_info["passw"])
            self._cached_ftps[ip] = _ftp

        return self._cached_ftps[ip_port]

    def _download_with_smb(self, url, target_dir, use_cache):
        no_scheme_url = url.replace("smb://", "")
        url_parts = no_scheme_url.split('/')    # return [ip, root_folder, rel_path_item, basename]
        if SimpleDownloader._SMB_SERVER_IP != url_parts[0]:
            raise Exception("not support {}'s smb share just now".format(url_parts[0]))

        local_file_path = os.path.realpath(os.path.join(target_dir, url_parts[-1]))
        if use_cache and os.path.exists(local_file_path):
            print("use cache file: {}".format(local_file_path))
        else:
            rel_path = '/'.join(url_parts[2:])
            mount = self._get_mount(url_parts[1])
            mount.pull(rel_path, target_dir, overwrite=True)

        return local_file_path

    def _download_with_ftp(self, url, target_dir, use_cache):
        no_scheme_url = url.replace("ftp://", "")
        url_parts = no_scheme_url.split('/')    # return [ip_port, root_folder, rel_path_item, basename]
        local_file_path = os.path.join(target_dir, url_parts[-1])
        if use_cache and os.path.exists(local_file_path):
            print("use cache file: {}".format(local_file_path))
        else:
            rel_path = '/'.join(url_parts[1:])
            ftp = self._get_ftp(url_parts[0])
            ftp.download(rel_path, target_dir)

        return os.path.realpath(local_file_path)

    def is_cache_exists(self, url: str, target_dir: str) -> bool:
        """Check whether there is an "url" cache on local disk

        Args:
            url (str): Full URL of the artifact to be download
            target_dir (str): Full local dir path where the artifact should be downloaded to

        Returns:
            bool: Is the cache exists
        """
        if self._get_scheme_type_(url) == SimpleDownloader._FTP_SCHEME:
            if os.path.exists(os.path.join(target_dir, url.replace("ftp://", "").split('/')[-1])):
                return True
        elif self._get_scheme_type_(url) == SimpleDownloader._SMB_SCHEME:
            if os.path.exists(os.path.realpath(os.path.join(target_dir, url.replace("smb://", "").split('/')[-1]))):
                return True
        return False

    def download(self, url, target_dir, use_cache=False):
        """
        下载 url 指向的文件至 target_dir 目录下，并返回本地文件地址
        :param url: 指定要下载的 URL
        :param target_dir: 本地存放目录
        :param use_cache: 为 True 时使用上次下载的缓存文件，默认重新下载
        :return: 下载下来的本地文件路径
        """
        scheme_type = self._get_scheme_type_(url)
        if scheme_type == SimpleDownloader._FTP_SCHEME:
            return self._download_with_ftp(url, target_dir, use_cache)
        elif scheme_type == SimpleDownloader._SMB_SCHEME:
            return self._download_with_smb(url, target_dir, use_cache)
        else:
            print("[zegodown] Unsupported url: {}".format(url))

        return None


if __name__ == "__main__":
    print("test download")
    downloader = SimpleDownloader()
    downloader.download("ftp://192.168.100.36/avroom_common/test/xplatform/hisi/xplatform_hisi_200225_225949_gheads_refactory_compile_script-0-g48276e6b.zip", "./")
    downloader.download("smb://192.168.1.3/share/zego_sdk/zegoconnection_master/200115_104425-sdk_adapter-0-g829490e-bn169_android/android/zegoconnection-android-200115_104425-sdk_adapter-0-g829490e-bn169-all.zip", "./")
