#!/usr/bin/env python3
# Created by Patrick Fu on 2021/3/23.
# Copyright 2021 ZEGO. All rights reserved.

import os
import base64
from typing import Dict
import urllib.request

"""
警告：此脚本为 Coding 制品库的上传/下载脚本，已废弃（ Coding 制品库不再允许使用 ），请使用 zego_artifactory.py

Script for upload/download artifacts to/from Coding.
"""

class Artifactory:
    def __init__(self) -> None:
        # (username, password)
        self.auth = ('', '')

        # e.g. '1.0.2.666' or 'g1234abcd' or any sring you want,
        # if not set, "Coding" will overwrite it
        self.version: str = ''

        # Whether to throw the exception to outside when
        # downloading/uploading failed (e.g. network error)
        self.is_raise_exception = False

    def set_version(self, version: str):
        self.version = version

    def set_auth(self, username: str, password: str):
        self.auth = (username, password)

    def set_raise_excpetion(self, is_raise: bool):
        self.is_raise_exception = is_raise

    def download(self, artifact_url: str, dst_folder: str) -> str:
        """Download specific artifact from coding to dst_folder

        Args:
            artifact (str): Full http URL of the artifact to be download
                e.g. "http://dev-generic.pkg.coding.zego.cloud/kiwi/kiwi_engine/android/kiwi_engine.tar.gz?version=1.0.3.29"

            dst_folder (str): Full local dir path where the artifact should be downloaded to
                e.g. "/Users/zego/Desktop" or "C:\\MyFolder"

        Returns:
            str: Full local path to the artifact will be downloaded to
        """

        artifact_name = artifact_url.split('/')[-1].split('?')[0] # remove url version
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)

        # Append version info to the url
        if '?version=' not in artifact_url and len(self.version) > 0:
            artifact_url += '?version={}'.format(self.version)

        auth_string = base64.standard_b64encode('{}:{}'.format(self.auth[0], self.auth[1]).encode('utf8'))
        request = urllib.request.Request(artifact_url)
        request.add_header('Authorization', 'Basic {}'.format(auth_string.decode('utf8')))
        try:
            dst_path = os.path.join(dst_folder, artifact_name)
            print('\n[*] Downloading "{0}" to "{1}"'.format(artifact_url, dst_path))
            u = urllib.request.urlopen(request)
            print('[*] Download succeed! status code: {}\n'.format(u.status))
            with open(dst_path, 'wb') as fw:
                fw.write(u.read())
        except Exception as e:
            print(e)
            print('\n[*] Download Coding artifacts failed, please checkout your username/password, or the network.')
            dst_path = None
            if self.is_raise_exception:
                raise Exception("Download failed")
        return dst_path


    def upload(self, artifact_url: str, src_path: str, meta_datas: Dict[str, str]={}):
        """Upload artifact to coding.

        Args:
            artifact_url (str): The url to be upload
                e.g. "http://dev-generic.pkg.coding.zego.cloud/kiwi/kiwi_engine/android/kiwi_engine.tar.gz"
                  or "http://dev-generic.pkg.coding.zego.cloud/kiwi/kiwi_engine/android/kiwi_engine.tar.gz?version=1.0.3.29"
                If the url does not contains version info, it will append "self.version" to url automatically

            src_path (str): Full local path of the artifact (.zip / .tar.gz / or anything you want) to be upload

            meta_datas (Dict[str, str]): Meta datas to be attached to the artifact
        """

        # Append version info to the url
        if '?version=' not in artifact_url and len(self.version) > 0:
            artifact_url += '?version={}'.format(self.version)

        with open(src_path, 'rb') as fr:
            files = fr.read()

        auth_string = base64.standard_b64encode('{}:{}'.format(self.auth[0], self.auth[1]).encode('utf8'))
        request = urllib.request.Request(url=artifact_url, data=files, method='PUT')
        request.add_header('Authorization', 'Basic {}'.format(auth_string.decode('utf8')))
        if meta_datas:
            content = ' '.join('{0}={1}'.format(key, meta_datas[key]) for key in meta_datas.keys())
            request.add_header('x-package-meta', content)
        try:
            print('\n[*] Uploading "{0}" to "{1}"'.format(src_path, artifact_url))
            u = urllib.request.urlopen(request)
            print('[*] Upload succeed! status code: {}\n'.format(u.status))
        except Exception as e:
            print(e)
            print('\n[*] Upload Coding artifacts failed, please checkout your username/password, or the network.')
            if self.is_raise_exception:
                raise Exception("Upload failed")


if __name__ == '__main__':
    # example

    # New an instance
    artifactory = Artifactory()

    # If you want to throw the exception to outside when
    # downloading/uploading failed (e.g. network error),
    # call this function and set it to True (default to False)
    artifactory.set_raise_excpetion(True)

    # Set auth (usually fill coding project token which set at 'ProjectSetting' -> 'Developer' -> 'ProjectToken')
    # This example token is the 'common_utils' project's 'Artifactory' token, which can only access coding artifacts
    artifactory.set_auth(username='ptd73lcn3h0a', password='113ffa4e41876b3f430bd1d041cd0adea285a8f8')

    url = 'http://dev-generic.pkg.coding.zego.cloud/common_utils/common_artifacts/utils/CodingDownloader.zip'
    this_folder = os.path.dirname(os.path.abspath(__file__))

    print('\n------- Test Download -------\n')

    # Set download artifacts version
    artifactory.set_version('1.0.0')
    # Download from coding
    product_path = artifactory.download(artifact_url=url, dst_folder=this_folder)

    print('\n------- Test Upload -------\n')

    # Set download artifacts version
    artifactory.set_version('1.0.0.888')
    # Init meta datas (you can only use string as key and value)
    meta_datas = {'Test': 'True', 'Author': 'PatrickFu', 'git-revision': 'g09deaa216d'}
    # Upload to coding
    artifactory.upload(artifact_url=url, src_path=product_path, meta_datas=meta_datas)
