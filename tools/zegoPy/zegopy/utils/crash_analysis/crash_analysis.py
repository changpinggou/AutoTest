#!/usr/bin/env python3 -u
# coding:utf-8

import os
import sys
import tempfile
import argparse
import uuid
import re
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from zegopy.common import io as zegoio
from zegopy.common import command as zegocmd
from zegopy.builder import zip_folder as zegozip
from zegopy.builder.artifactory import Artifactory
from typing import List, Tuple

OUTPUT_TXT_PATH = os.path.join((os.path.dirname(__file__)), 'crash_stack.txt')

def __parse_args(args):
    parser = argparse.ArgumentParser(description='Crash Analyzer')
    parser.add_argument("--product-name", action='store', type=str, help="Specify product name for crash analyzer")
    parser.add_argument("--ios", action='store_true', default=False)
    parser.add_argument('--ios-arch', action='store', type=str, default='arm64',choices=['arm64', 'armv7', 'arm64-simulator', 'x86_64-simulator', 'arm64-catalyst', 'x86_64-catalyst'])

    parser.add_argument("--android", action='store_true', default=False)
    parser.add_argument("--android-arch", action='store', type=str, default='arm64-v8a', choices=['arm64-v8a', 'armeabi-v7a', 'x86', 'x86_64'])

    parser.add_argument("--mac", action='store_true', default=False)
    parser.add_argument("--mac-arch", action='store', type=str, default='arm64', choices=['arm64', 'x86_64'])
    parser.add_argument("--is-apple-framework", action='store_true', default=False, help='Is Apple Framework? else dylib')

    parser.add_argument('--symbol-download-url', action='store', type=str, default='')
    parser.add_argument('--symbol-binary-path', action='store', type=str, default='')

    parser.add_argument('--uuid', action='store', type=str, default='', help="specific uuid")
    parser.add_argument("--base-address", action='store', type=str, default='', help="base address")
    parser.add_argument("--crash-addresses", action='store', type=str, nargs='+', help="crash addresses")
    return parser.parse_args(args[1:])


class CrashAnalyzer():
    def __init__(self, product_name: str, target_os: str, arch: str) -> None:
        self.product_name = product_name
        self.target_os = target_os
        self.is_apple_framework = False
        self.arch = arch
        self.symbol_download_url = ''
        self.symbol_binary_path = ''
        self.symbol_base_folder = ''
        self.uuid = ''
        self.version = ''

    def set_uuid(self, uuid):
        self.uuid = uuid

    def analyze(self, symbol_download_url:str, symbol_binary_path:str, base_address: str, crash_addresses: List[str]):
        self.symbol_download_url = symbol_download_url
        self.symbol_binary_path = symbol_binary_path

        symbol_list = []
        if self.target_os == 'ios' or self.target_os == 'mac':
            symbol_list = self._analyze_apple(base_address, crash_addresses)
        elif self.target_os == 'android':
            symbol_list = self._analyze_android(crash_addresses)
        else:
            print("CrashAnalyzer do not support this platform")

        with open(OUTPUT_TXT_PATH, 'w') as f:
            f.write('===== Crash Analyser Result =====\n\n')
            if self.product_name:
                f.write('{} | {} | {}\n'.format(self.product_name, self.target_os, self.arch))
            if os.environ.get('JENKINS_CONTEXT', ''):
                f.write('Context: {}\n'.format(os.environ.get('JENKINS_CONTEXT')))
            if os.environ.get('BUILD_URL', ''):
                f.write('Jenkins URL: {}\n'.format(os.environ.get('BUILD_URL')))
            if self.symbol_download_url:
                f.write('Symbol URL: {}\n'.format(self.symbol_download_url))
            if self.symbol_binary_path:
                f.write('Symbol binary path: {}\n'.format(self.symbol_binary_path))
            if self.version:
                f.write('SDK Version: {}\n'.format(self.version))
            if self.uuid:
                f.write('UUID: {}\n'.format(self.uuid))
            if base_address:
                f.write('Base address: {}\n'.format(base_address))
            f.write('\n[*] Crash Stack:\n\n')
            f.write('\n'.join(symbol_list))

    def _analyze_apple(self, base_address: str, crash_addresses: List[str]) -> List[str]:
        dest_zip_folder = tempfile.mkdtemp()
        symbol_zip_name = self._download_symbol(dest_zip_folder)
        self._unzip_symbol_file(os.path.join(dest_zip_folder, symbol_zip_name), dest_zip_folder)

        dsym_execute_file_path = self._get_local_symbol_binary_file(dest_zip_folder)
        print("dSYM file: {}".format(dsym_execute_file_path))

        if self.uuid != "":
            match, arch = self._check_uuid_is_same(dsym_execute_file_path, self.uuid)
            if match == False:
                zegoio.delete(dest_zip_folder)
                raise Exception("Cannot match uuid!")

        elif self.arch == None:
            raise Exception("You MUST specific arch!")

        symbol_list = self._get_symbol_apple(dsym_execute_file_path, base_address, crash_addresses)

        self._parse_version_info()

        print("crash stack:\n")
        for symbol in symbol_list:
            print(symbol)

        # remove symbol folder
        zegoio.delete(dest_zip_folder)
        return symbol_list

    def _analyze_android(self, crash_addresses: List[str]) -> List[str]:
        dest_zip_folder = tempfile.mkdtemp()
        symbol_zip_name = self._download_symbol(dest_zip_folder)
        self._unzip_symbol_file(os.path.join(dest_zip_folder, symbol_zip_name), dest_zip_folder)

        framework_so_path = self._get_local_symbol_binary_file(dest_zip_folder)
        print("so file: {}".format(framework_so_path))

        # get addr2line address
        addr2line_file_path = self._get_addr2line_file_path()

        symbol_list = self._get_symbol_android(addr2line_file_path, framework_so_path, crash_addresses)

        self._parse_version_info()

        print("crash stack:\n")
        for symbol in symbol_list:
            print(symbol)

        # remove symbol folder
        zegoio.delete(dest_zip_folder)
        return symbol_list

    def _unzip_symbol_file(self, local_symbol_file_path: str, dest_folder: str):
        zegozip.unzip_file(local_symbol_file_path, dest_folder)

    def _download_symbol(self, dest_zip_folder: str) -> str:
        artifactory = Artifactory()
        artifactory.set_auth('ptp5c8k40vuj', '9bef04b37852e82fb933f27a64fa92c306de51c9')
        artifactory_url = self.symbol_download_url
        artifactory.download(artifact_url=artifactory_url, dst_folder=dest_zip_folder)

        first_index = self.symbol_download_url.rfind('/')
        last_index = self.symbol_download_url.rfind('?')
        if last_index > 0:
            symbol_zip_name = self.symbol_download_url[first_index + 1 : last_index]
        else:
            symbol_zip_name = self.symbol_download_url[first_index + 1: ]

        print("first index: {}, last index: {}".format(first_index, last_index))
        print("cut symbol path: {}".format(symbol_zip_name))

        return symbol_zip_name

    def _get_local_symbol_binary_file(self, src_folder:str) -> str:
        if len(os.listdir(src_folder)) == 0:
            raise Exception("Cannot find symbol path")

        # 若外部指定了二进制的相对路径，则直接使用外部路径。否则按照 ZIM / ZegoEffects 产品的目录去保底解析
        if len(self.symbol_binary_path) > 0:
            return os.path.join(src_folder, self.symbol_binary_path)
        else:
            for folder in os.listdir(src_folder):
                self.symbol_base_folder = os.path.join(src_folder, folder)
                if os.path.isdir(self.symbol_base_folder):
                    break

            if self.target_os == 'ios' or self.target_os == 'mac':
                if self.is_apple_framework:
                    binary_name = self.product_name
                else:
                    binary_name = 'lib%s.dylib' % self.product_name
                return os.path.join(self.symbol_base_folder, self.arch,
                    '%s.dSYM' % binary_name, "Contents", "Resources", "DWARF", binary_name)
            elif self.target_os == 'android':
                return os.path.join(self.symbol_base_folder, self.arch, 'lib{}.so'.format(self.product_name))

        raise Exception("Cannot find symbol base folder")

    def _parse_version_info(self):
        version_txt_path = os.path.join(self.symbol_base_folder, 'VERSION.txt')
        if not os.path.exists(version_txt_path):
            return
        with open(version_txt_path, 'r') as f:
            self.version = f.read().strip()
            print('SDK Version: %s' % self.version)

    def _check_uuid_is_same(self, execute_file, str_uuid) -> Tuple[bool, str]:
        format_uuid = str(uuid.UUID(str_uuid)).upper()
        command = "dwarfdump --uuid {}".format(execute_file)

        ok, result = zegocmd.execute(command)
        print("check uuid result: {}".format(result))
        print("format uuid: {}".format(format_uuid))
        if ok == 0:
            p = re.compile('''UUID: ([^(]*) \(([^)]*)\)''', re.M)
            uuid_list = p.findall(result)
            for uuid_info in uuid_list:
                print ("uuid: {}, arch: {}".format(uuid_info[0], uuid_info[1]))
                if format_uuid == uuid_info[0]:
                    return (True, uuid_info[1])

        return (False, "")

    def _get_android_toolchain_path(self) -> Tuple[str, str, str]:
        os_folder_name = None
        if sys.platform == 'win32':
            os_folder_name = "windows-x86_64"
        elif sys.platform.startswith("linux"):
            os_folder_name = "linux-x86_64"
        elif sys.platform.startswith("darwin"):
            os_folder_name = "darwin-x86_64"
        else:
            raise Exception("unknown system occur when get android toolchain path")

        if self.arch == "armeabi-v7a":
            return ("arm-linux-androideabi-4.9", os_folder_name, "arm-linux-androideabi-addr2line")
        elif self.arch == "arm64-v8a":
            return ("aarch64-linux-android-4.9", os_folder_name, "aarch64-linux-android-addr2line")
        elif self.arch == "x86":
            return ("x86-4.9", os_folder_name, "i686-linux-android-addr2line")
        elif self.arch == "x86_64":
            return ("x86_64-4.9", os_folder_name, "x86_64-linux-android-addr2line")
        else:
            raise Exception("unknown arch: " + self.arch)


    def _get_addr2line_file_path(self) -> str:
        ndk_bundle = os.environ["NDK_HOME"]
        if len(ndk_bundle) == 0:
            raise Exception("Cannot find ndk home path")

        (arch_path, os_folder, addr2line_file) = self._get_android_toolchain_path()
        addr2line_file_path = os.path.join(ndk_bundle, "toolchains", arch_path, "prebuilt", os_folder, "bin",
                                           addr2line_file)

        return addr2line_file_path

    def _get_symbol_android(self, addr2line_path:str, execute_file:str, crash_addresses:List[str]) -> List[str]:
        crash_symbol_list = []
        for str_crash_address in crash_addresses:
            crash_address = int(str_crash_address, 16)

            command = "{} -e {} -f {} -C -i".format(addr2line_path, execute_file, hex(crash_address))
            ok, result = zegocmd.execute(command)
            if ok == 0:
                crash_symbol_list.append("{}\n{}".format(hex(crash_address), result))
            else:
                print("execute failed reason: {}".format(result))

        return crash_symbol_list

    def _get_symbol_apple(self, execute_file:str, str_base_address:str, crash_addresses:List[str]) -> List[str]:
        if str_base_address.startswith("0x"):
            base_address = int(str_base_address, 16)
        else:
            base_address = int(str_base_address)
        base_address = hex(base_address)

        print("base address {}".format(base_address))

        crash_symbol_list = []
        for str_crash_address in crash_addresses:
            if str_crash_address.startswith("0x"):
                crash_address = int(str_crash_address, 16)
            else:
                crash_address = int(str_crash_address)

            command = "atos -o {} -arch {} -l {} {}".format(execute_file, self.arch, base_address, hex(crash_address))
            ok, result = zegocmd.execute(command)
            if ok == 0:
                crash_symbol_list.append("{}\n{}".format(hex(crash_address), result))
            else:
                print("execut failed reason: {}".format(result))

        return crash_symbol_list


def main(argv):
    arguments = __parse_args(argv)
    if arguments.symbol_download_url == "":
        raise Exception("You MUST set the '--symbol-download-url' param")
    if arguments.crash_addresses == "":
        raise Exception("You MUST set the crash addresses")

    print("current platform: {}".format(arguments.ios))
    if arguments.ios:
        analyzer = CrashAnalyzer(arguments.product_name, 'ios', arguments.ios_arch)
        analyzer.set_uuid(arguments.uuid)
        analyzer.is_apple_framework = arguments.is_apple_framework
    elif arguments.mac:
        analyzer = CrashAnalyzer(arguments.product_name, 'mac', arguments.mac_arch)
        analyzer.set_uuid(arguments.uuid)
        analyzer.is_apple_framework = arguments.is_apple_framework
    elif arguments.android:
        analyzer = CrashAnalyzer(arguments.product_name, 'android', arguments.android_arch)

    analyzer.analyze(arguments.symbol_download_url, arguments.symbol_binary_path, arguments.base_address, arguments.crash_addresses)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
