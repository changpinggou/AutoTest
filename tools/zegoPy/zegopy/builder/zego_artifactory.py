#!/usr/bin/env python3

import os
import json
import hashlib
import requests
import ssl
# To fix the issue of "<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1129)>"
ssl._create_default_https_context = ssl._create_unverified_context

try:
    from clint.textui import progress
except ImportError as e:
    os.system("pip3 install clint")
    os.system("pip install clint")
    from clint.textui import progress

"""
Script for upload/download artifacts to/from Zego Artifactory.

Details: http://confluence.zego.cloud/pages/viewpage.action?pageId=12969890

If you want to clear download cache,
delete the "zegopy/builder/zego_artifactory_cache.json" file

"""


class ZegoArtifactory:
    def __init__(self) -> None:
        # (username, password)
        self.auth = ('bno-cicd', 'AtGhFiW4wg92wreqFfxC')

        # e.g. '1.0.2.666' or 'g1234abcd' or any sring you want,
        # if not set, we will overwrite it
        self.version: str = ''

        # Whether to throw the exception to outside when
        # downloading/uploading failed (e.g. network error)
        self.is_raise_exception = False

        # Maximum number of retries for download/upload
        self.max_retry = 5

        # We put the cache information in this repo
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zego_artifactory_cache.json')
        self.cache_data = {}
        self.load_cache()

    def set_version(self, version: str):
        self.version = version

    def set_auth(self, username: str, password: str):
        self.auth = (username, password)

    def set_raise_exception(self, is_raise: bool):
        self.is_raise_exception = is_raise

    def is_cache_exists(self, artifact_url: str, dst_folder: str) -> bool:
        """Check whether there is an "artifact_url" cache on local disk

        Args:
            artifact_url (str): Full http URL of the artifact to be download
            dst_folder (str): Full local dir path where the artifact should be downloaded to

        Returns:
            bool: Is the cache exists
        """
        artifact_name = artifact_url.split('/')[-1].split('?')[0]  # remove url version
        dst_path = os.path.join(dst_folder, artifact_name)
        if not os.path.exists(dst_path):
            return False
        if dst_path not in self.cache_data:
            return False
        if self.cache_data[dst_path] != artifact_url:
            return False
        return True

    def download(self, artifact_url: str, dst_folder: str, use_cache=False, check_file=True) -> str:
        """Download specific artifact from artifactory to dst_folder

        Args:
            artifact_url (str): Full http URL of the artifact to be download
                e.g. "https://artifact-master.zego.cloud/generic/roomkit/default/test/ttt.txt?version=1.0.0"

            dst_folder (str): Full local dir path where the artifact should be downloaded to
                e.g. "/Users/zego/Desktop" or "C:\\MyFolder"

            use_cache (boolean): If set to true, it will detect whether the file exists in the target
                directory, and if it exists, it will reuse the cache instead of downloading it.

            check_file (boolean): If set to true, it will check file md5

        Returns:
            str: Full local path to the artifact will be downloaded to
        """

        artifact_name = artifact_url.split('/')[-1].split('?')[0]  # remove url version
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)

        # Append version info to the url
        if '?version=' not in artifact_url and len(self.version) > 0:
            if self.version is None:
                artifact_url += '?version=latest'
            else:
                artifact_url += '?version={}'.format(self.version)

        # Get the artifact checksum md5
        try:
            if check_file:
                checksum_url = artifact_url.split('?')[0] + '.md5?' + artifact_url.split('?')[1]
                checksum = requests.get(checksum_url).text
        except Exception as e:
            print(e)
            print('\n[*] Get artifact md5 failed, please checkout your username/password, or the network.')
            if self.is_raise_exception:
                raise Exception("Download failed")
            return None

        try:
            dst_path = os.path.join(dst_folder, artifact_name)
            if use_cache and self.is_cache_exists(artifact_url, dst_folder):
                print('\n[*] Skip download, use cache "{0}" for "{1}"'.format(dst_path, artifact_url))
                return dst_path

            try_count = 0
            while try_count < self.max_retry:
                print('\n[*] Downloading "{0}" to "{1}" ({2} try)'.format(artifact_url, dst_path, try_count+1))
                with open(dst_path, 'wb') as f, requests.get(artifact_url, stream=True) as r:
                    r.raise_for_status()
                    total_length = int(r.headers.get('content-length'))
                    for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1):
                        if chunk:
                            f.write(chunk)
                            f.flush()

                if not check_file:
                    break
                else:
                    with open(dst_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    if checksum == file_hash:
                        break
                    else:
                        try_count += 1
                        print('\n[*] File md5 does not match server value: "{}", actual: "{}", retry download.'.format(checksum, file_hash))

            if try_count >= self.max_retry:
                print('\n[*] Retried download %s times, but there are still problems with the artifact.\n' % self.max_retry)
                if self.is_raise_exception:
                    raise Exception("Download failed")
                return None

            self.save_cache(dst_path, artifact_url)
            print('[*] Download succeed! \n')

        except Exception as e:
            print(e)
            print('\n[*] Download Zego artifacts failed, please checkout your username/password, or the network.')
            dst_path = None
            if self.is_raise_exception:
                raise Exception("Download failed")
        return dst_path

    def upload(self, project_name: str, group_name: str, artifact_name: str, src_path: str) -> str:
        """Upload artifact to artifactory.

        Args:
            project_name (str): Project name is predefine, contact the administer to get it

            group_name(str): There maybe a bunch of group under the project, contact the administer to get it,
                *** For most scene, set it to "public" ***

            artifact_name(str): Name of your artifact, you can separate it in different folder by '/'.
                eg. 'name/of/my/artifact.zip'

            src_path (str): Full local path of the artifact (.zip / .dmg / or anything you want) to be upload

        Returns:
            str: Full URL to your artifact
        """

        if not self.version:
            print("\n[*] [ERROR] Please set valid version before upload!")
            if self.is_raise_exception:
                raise Exception()
            return ""

        artifact_url = 'https://artifact-master.zego.cloud/generic/{proj}/{group}/{name}?version={ver}'.format(
            proj=project_name,
            group=group_name,
            name=artifact_name,
            ver=self.version
        )

        try:
            print('\n[*] Uploading "{0}" to "{1}"'.format(src_path, artifact_url))
            r = requests.post(artifact_url, files={'file': open(src_path, 'rb')}, auth=(self.auth[0], self.auth[1]))
            r.raise_for_status()
            print('[*] Upload succeed! status code: {0}, content: {1}\n'.format(r.status_code, r.text))
            return artifact_url
        except requests.exceptions.HTTPError as httperror:
            print("Request Exception:", httperror)
            print(str(httperror.response.text))
            if self.is_raise_exception:
                raise Exception("Upload failed")
            else:
                return ""
        except Exception as e:
            print(e)
            print('\n[*] Upload artifacts failed, please checkout your username/password, or the network.')
            if self.is_raise_exception:
                raise Exception("Upload failed")
            else:
                return ""

    def load_cache(self):
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, 'w') as fw:
                json.dump({}, fw)

        with open(self.cache_file) as fr:
            self.cache_data = json.load(fr)

    def save_cache(self, key_path: str, value_url: str):
        self.cache_data[key_path] = value_url
        with open(self.cache_file, 'w') as fw:
            json.dump(self.cache_data, fw, indent=4)

    def clear_cache(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

if __name__ == '__main__':
    # example

    # New an instance
    artifactory = ZegoArtifactory()

    # If you want to throw the exception to outside when
    # downloading/uploading failed (e.g. network error),
    # call this function and set it to True (default to False)
    artifactory.set_raise_exception(True)

    url = 'https://artifact-master.zego.cloud/generic/test/public/test.txt'
    # url = 'https://artifact-master.zego.cloud/generic/native_common/public/zegoconnection/stable/ios/zegoconnection-stable-ios-static.zip?version=2.0.2.1174'
    this_folder = os.path.dirname(os.path.abspath(__file__))

    print('\n------- Test Download -------\n')

    # Set download artifacts version
    artifactory.set_version('1.0.0')
    # Download from artifactory
    product_path = artifactory.download(artifact_url=url, dst_folder=this_folder)

    print('\n------- Test Upload -------\n')

    # Set download artifacts version
    import random

    artifactory.set_version('1.0.1.{}'.format(random.randint(0, 999999)))
    # Upload to artifactory
    artifactory.upload(project_name='test', group_name='public', artifact_name='test.txt',
                       src_path=product_path)
