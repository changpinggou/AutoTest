#!/usr/bin/env python3 -u
# coding:utf-8

import os
import sys
import tempfile
import uuid
import re
import json
import argparse

from zegopy.common import io as zegoio
from zegopy.common import command as zegocmd
# from zegopy.common.ftputil import SimpleFTP
from zegopy.builder import zip_folder as zegozip
from zegopy.common.argutil import CmdParam
from zegopy.common.jenkinsutil import get_bool, get_string

from os.path import expanduser

if sys.version_info.major == 2:
    from urllib import quote
else:
    from urllib.parse import quote


def get_execute_ios_file_name(framework):
    if framework.lower() == "zegoavkit":
        return "libZegoAVKit2.dylib"

    if framework.lower() == "zegoliveroom":
        return "libZegoLiveRoom.dylib"

    if framework.lower() == "zegoaudioroom":
        return "libZegoAudioRoom.dylib"


def get_execute_mac_file_name(framework):
    if framework.lower() == "zegoavkit":
        return "libZegoAVKit2OSX.dylib"

    if framework.lower() == "zegoliveroom":
        return "libZegoLiveRoomOSX.dylib"

    if framework.lower() == "zegoaudioroom":
        return "libZegoAudioRoomOSX.dylib"


def get_execute_android_file_name(framework):
    if framework.lower() == "zegoavkit":
        return "libzegoavkit.so"

    if framework.lower() == "zegoliveroom":
        return "libzegoliveroom.so"

    if framework.lower() == "zegoaudioroom":
        return "libzegoliveroom.so"


def get_android_toolchain_path(arch):
    os_folder_name = None
    if sys.platform == 'win32':
        os_folder_name = "windows-x86_64"
    elif sys.platform.startswith("linux"):
        os_folder_name = "linux-x86_64"
    elif sys.platform.startswith("darwin"):
        os_folder_name = "darwin-x86_64"
    else:
        raise Exception("unknown system")

    if arch == "armeabi-v7a":
        return ("arm-linux-androideabi-4.9", os_folder_name, "arm-linux-androideabi-addr2line")
    elif arch == "arm64-v8a":
        return ("aarch64-linux-android-4.9", os_folder_name, "aarch64-linux-android-addr2line")
    elif arch == "x86":
        return ("x86-4.9", os_folder_name, "i686-linux-android-addr2line")
    else:
        raise Exception("unknown arch: " + arch)


# def copy_symbol_file_from_ftp(framework, sdk_version, dst_zip_folder, part_symbol_zip_name, platform, cplusplus=False):
#     def _found_symbol_folder(_framework, _platform, _sdk_version, _ftp):
#         # 此方法可以根据目录组织结构进行优化，而不是全局遍历（效率太低）
#         top_folder = _framework
#         found = False
#
#         for top, folders, files in _ftp.walk(top_folder):
#             if not top.endswith(_platform):
#                 continue
#
#             for folder_name in folders:
#                 if folder_name.find(_sdk_version) >= 0:
#                     top_folder = os.path.join(top, folder_name)
#                     found = True
#                     break
#
#             if found:
#                 break
#
#         return top_folder if found else None
#
#     def _get_symbol_file(_symbol_folder, _part_symbol_file_name, _platform, _cplusplus, _ftp):
#         if _platform == 'osx':
#             _part_symbol_file_name = "-symbol"
#             if _cplusplus:
#                 _part_symbol_file_name += "_plus"
#             _part_symbol_file_name += ".zip"
#
#         full_symbol_file_name = None
#         for file_info_list in _ftp.list_dir(_symbol_folder):
#             file_name = file_info_list[0]
#             if file_name.find(_part_symbol_file_name) >= 0 and file_name.endswith('.zip'):
#                 full_symbol_file_name = file_name
#                 break
#
#         return full_symbol_file_name
#
#     ftp = SimpleFTP("192.168.100.36")
#     ftp.login("reader", "hiVX62pzSI53maEC")
#
#     framework = framework.lower()
#     platform = platform.lower()
#
#     symbol_folder = _found_symbol_folder(framework, platform, sdk_version, ftp)
#     if not symbol_folder:
#         return False, None
#
#     symbol_file_name = _get_symbol_file(symbol_folder, part_symbol_zip_name, platform, cplusplus, ftp)
#     if not symbol_file_name:
#         return False, None
#
#     success = ftp.download(os.path.join(symbol_folder, symbol_file_name), dst_zip_folder)
#     if success and os.path.exists(os.path.join(dst_zip_folder, symbol_file_name)):
#         return True, symbol_file_name
#
#     return False, None
#
#
def copy_symbol_file_from_share(framework, sdk_version, dst_zip_folder, part_symbol_zip_name, platform,
                                cplusplus=False):
    def _copy_symbol_file(server_path, username, password):
        # mount share
        mount_temp = os.path.join(expanduser("~"), "zego_sdk_symbol")
        zegoio.insure_dir_exists(mount_temp)

        src_share_path = '//{}:{}@{}'.format(username, quote(password), server_path[2:])

        zegocmd.execute('umount -f {0}'.format(mount_temp))

        print("<< going to mount share {0} to {1}".format(server_path, mount_temp))

        ok, result = zegocmd.execute('mount -t smbfs {0} {1}'.format(src_share_path, mount_temp))
        if ok != 0:
            print(result)
            ok, result = zegocmd.execute('mount -t cifs -o username="{}",password="{}" {} {}'.format(
                username, password, server_path, mount_temp))
            if ok != 0:
                zegocmd.execute('umount -f {0}'.format(mount_temp))
                raise Exception(result)

        found_framework = False
        symbol_zip_name = ""
        sdk_framework_folder_path = get_symbol_path_from_share(framework, sdk_version, mount_temp)
        if sdk_framework_folder_path != "":
            print("framework: {}".format(sdk_framework_folder_path))
            (result, symbol_zip_name) = copy_framework_symbol(sdk_framework_folder_path, part_symbol_zip_name,
                                                              dst_zip_folder, platform, cplusplus)
            if result:
                copy_ve_json_file(sdk_framework_folder_path, dst_zip_folder, platform)
                found_framework = True

        ok, result = zegocmd.execute('umount -f {0}'.format(mount_temp))
        if ok != 0:
            raise Exception(result)

        return found_framework, symbol_zip_name

    share_server1 = "//192.168.1.3/share/zego_sdk"
    share_server2 = "//192.168.1.3/share02/product/zego_sdk"
    share_server3 = "//192.168.1.3/share03/zego_sdk"
    k_login_info_username = "share"
    k_login_info_password = "share@zego"

    found, symbol_path = _copy_symbol_file(share_server1, k_login_info_username, k_login_info_password)
    if not found:
        found, symbol_path = _copy_symbol_file(share_server2, k_login_info_username, k_login_info_password)
    if not found:
        found, symbol_path = _copy_symbol_file(share_server3, k_login_info_username, k_login_info_password)

    return found, symbol_path


def get_symbol_path_from_share(framework, sdk_version, local_mount_path):
    framework_folder_list = os.listdir(local_mount_path)

    for framework_folder in framework_folder_list:
        if not os.path.isdir(os.path.join(local_mount_path, framework_folder)):
            continue

        if not framework_folder.startswith(framework.lower()):
            continue

        sdk_framework_folder_path = os.path.join(local_mount_path, framework_folder)
        sdk_framework_folder_list = os.listdir(sdk_framework_folder_path)
        for sdk_framework_folder in sdk_framework_folder_list:
            if not os.path.isdir(os.path.join(sdk_framework_folder_path, sdk_framework_folder)):
                continue

            if sdk_version in sdk_framework_folder \
                    and not sdk_framework_folder.endswith("_win"):   # 排除 _win 结尾的文件夹
                return os.path.join(sdk_framework_folder_path, sdk_framework_folder)

    return ""


def copy_framework_symbol(src_framework_folder, part_symbol_zip_name, dest_framework_folder, platform, cplusplus):
    platform_folder_path = os.path.join(src_framework_folder, platform)
    platform_folder_list = os.listdir(platform_folder_path)

    if platform == "Mac" or platform == "osx":
        part_symbol_zip_name = "{}-symbol".format(os.path.basename(src_framework_folder))
        if cplusplus:
            part_symbol_zip_name = "{}_plus".format(part_symbol_zip_name)

    print("symbol_zip_name: {}".format(part_symbol_zip_name))

    for platform_folder_file in platform_folder_list:
        if part_symbol_zip_name in platform_folder_file:
            symbol_file_path = os.path.join(platform_folder_path, platform_folder_file)
            print("copy {} -> {}".format(symbol_file_path, dest_framework_folder))
            if os.path.exists(symbol_file_path):
                zegoio.copy(symbol_file_path, dest_framework_folder)
                return True, platform_folder_file

    return False, ""


def copy_ve_json_file(src_framework_folder, dest_framework_folder, platform):
    ve_json_file_path = os.path.join(src_framework_folder, platform, "construct.json")

    print("copy {} -> {}".format(ve_json_file_path, dest_framework_folder))

    zegoio.copy(ve_json_file_path, dest_framework_folder)


def unzip_symbol_file(symbol_file_path, dst_folder):
    zegozip.unzip_file(symbol_file_path, dst_folder)


def get_dSYM_file_path_ios(dst_folder, arch):
    dst_sym_folder = os.path.join(dst_folder, "iPhoneos")
    if arch == "x86_64":
        dst_sym_folder = os.path.join(dst_folder, "iphonesimulator")
    dst_sym_file_list = os.listdir(dst_sym_folder)

    for dst_sym_file in dst_sym_file_list:
        if dst_sym_file.endswith(".dSYM"):
            return os.path.join(dst_sym_folder, dst_sym_file)

    return ""


def get_dSYM_file_path_mac(dst_folder, framework, cplusplus):
    dst_sym_folder = os.path.join(dst_folder, "product", framework)
    if not os.path.exists(dst_sym_folder):
        dst_sym_folder = os.path.join(dst_folder, "product")

    if cplusplus:
        dst_sym_folder = os.path.join(dst_sym_folder, "symbol_plus")
    else:
        dst_sym_folder = os.path.join(dst_sym_folder, "symbol")

    dst_sym_file_list = os.listdir(dst_sym_folder)

    for dst_sym_file in dst_sym_file_list:
        if dst_sym_file.endswith(".dSYM"):
            return os.path.join(dst_sym_folder, dst_sym_file)

    return ""


def check_uuid_is_same(execute_file, str_uuid):
    format_uuid = str(uuid.UUID(str_uuid)).upper()
    command = "dwarfdump --uuid {}".format(execute_file)

    ok, result = zegocmd.execute(command)
    if ok == 0:
        p = re.compile('''UUID: ([^(]*) \(([^)]*)\)''', re.M)
        uuid_list = p.findall(result)
        for uuid_info in uuid_list:
            # print ("uuid: {}, arch: {}".format(uuid_info[0], uuid_info[1]))
            if format_uuid == uuid_info[0]:
                return True, uuid_info[1]

    return False, ""


def get_symbol_ios(execute_file, str_base_address, arch, crash_addresses):
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

        command = "atos -o {} -arch {} -l {} {}".format(execute_file, arch, base_address, hex(crash_address))
        ok, result = zegocmd.execute(command)
        if ok == 0:
            crash_symbol_list.append("{}\n{}".format(hex(crash_address), result))
        else:
            print("execute failed reason: {}".format(result))

    return crash_symbol_list


def get_symbol_android(addr2line_path, execute_file, crash_addresses):
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


def get_ve_version(dst_folder):
    ve_file_path = os.path.join(dst_folder, "construct.json")
    if not os.path.exists(ve_file_path):
        print("don't have construct.json")
        return ""

    with open(ve_file_path) as file_config:
        json_config = json.loads(file_config.read())
        return json_config["version"]

    return ""


def get_framework_so_path(dst_zip_folder, arch, framework):
    return os.path.join(dst_zip_folder, "symbols", arch, get_execute_android_file_name(framework))


def get_addr2line_file_path(arch):
    ndk_bundle = os.environ["NDK_HOME"]
    if len(ndk_bundle) == 0:
        raise Exception("Cannot find ndk home path")

    (arch_path, os_folder, addr2line_file) = get_android_toolchain_path(arch)
    addr2line_file_path = os.path.join(ndk_bundle, "toolchains", arch_path, "prebuilt", os_folder, "bin",
                                       addr2line_file)

    return addr2line_file_path


def run_ios(framework, sdk_version, uuid, arch, base_address, crash_addresses):
    if sdk_version == "":
        return

    if len(crash_addresses) == 0:
        print("no crash stack!")
        return

    dst_zip_folder = os.path.join(tempfile.mkdtemp(), "symbol_ios")
    part_symbol_zip_name = "symbol_{}".format(framework.lower())

    found_framework, symbol_zip_name = copy_symbol_file_from_share(framework, sdk_version, dst_zip_folder,
                                                                   part_symbol_zip_name, "iOS")
    # if not found_framework:
    #     print("search symbol file from ftp server")
    #     found_framework, symbol_zip_name = copy_symbol_file_from_ftp(framework, sdk_version, dest_zip_folder, part_symbol_zip_name, "ios")

    if not found_framework:
        print("cannot find framework, check sdk_version {}!".format(sdk_version))
        return

    unzip_symbol_file(os.path.join(dst_zip_folder, symbol_zip_name), dst_zip_folder)

    dsym_file_path = get_dSYM_file_path_ios(dst_zip_folder, arch)
    if dsym_file_path == "":
        print("cannot find dsym file!")
        return

    print("dSYM file: {}".format(dsym_file_path))
    execute_file = os.path.join(dsym_file_path, "Contents", "Resources", "DWARF", get_execute_ios_file_name(framework))

    if uuid != "":
        match, arch = check_uuid_is_same(execute_file, uuid)
        if not match:
            print("cannot match uuid!")
            zegoio.delete(dst_zip_folder)
            return

        print("arch: {}".format(arch))
    elif arch is None:
        print("must specific arch")
        return

    symbol_list = get_symbol_ios(execute_file, base_address, arch, crash_addresses)

    # get VE version
    ve_version = get_ve_version(dst_zip_folder)

    print(">>")
    print("ve version: {}".format(ve_version))

    print("crash stack:\n")
    for symbol in symbol_list:
        print(symbol)

    # remove symbol folder
    zegoio.delete(dst_zip_folder)


def run_android(framework, sdk_version, arch, crash_addresses):
    if sdk_version == "":
        return

    if len(crash_addresses) == 0:
        print("no crash stack")
        return

    dst_zip_folder = os.path.join(tempfile.mkdtemp(), "symbol_android")
    part_symbol_zip_name = sdk_version

    found_framework, symbol_zip_name = copy_symbol_file_from_share(framework, sdk_version, dst_zip_folder,
                                                                   part_symbol_zip_name, "android")
    # if not found_framework:
    #     print("search symbol file from ftp server")
    #     found_framework, symbol_zip_name = copy_symbol_file_from_ftp(framework, sdk_version, dest_zip_folder, part_symbol_zip_name, "android")

    if not found_framework:
        print("cannot find framework")
        return

    unzip_symbol_file(os.path.join(dst_zip_folder, symbol_zip_name), dst_zip_folder)

    framework_so_path = get_framework_so_path(dst_zip_folder, arch, framework)

    # get addr2line address
    addr2line_file_path = get_addr2line_file_path(arch)

    symbol_list = get_symbol_android(addr2line_file_path, framework_so_path, crash_addresses)

    # get VE version
    ve_version = get_ve_version(dst_zip_folder)
    print(">>")
    print("ve version: {}".format(ve_version))

    print("crash stack:\n")
    for symbol in symbol_list:
        print(symbol)

    # remove symbol folder
    zegoio.delete(dst_zip_folder)


def run_mac(framework, sdk_version, uuid, arch, base_address, crash_addresses, cplusplus):
    if sdk_version == "":
        return

    if len(crash_addresses) == 0:
        print("no crash stack!")
        return

    dst_zip_folder = os.path.join(tempfile.mkdtemp(), "symbol_mac")
    part_symbol_zip_name = sdk_version.lower()

    found_framework, symbol_zip_name = copy_symbol_file_from_share(framework, sdk_version, dst_zip_folder,
                                                                   part_symbol_zip_name, "osx", cplusplus)

    if not found_framework:
        found_framework, symbol_zip_name = copy_symbol_file_from_share(framework, sdk_version, dst_zip_folder,
                                                                       part_symbol_zip_name, "Mac", cplusplus)
    # if not found_framework:
    #     print("search symbol file from ftp server")
    #     found_framework, symbol_zip_name = copy_symbol_file_from_ftp(framework, sdk_version, dest_zip_folder, part_symbol_zip_name, "osx")

    if not found_framework:
        print("cannot find framework, check sdk_version {}!".format(sdk_version))
        return

    unzip_symbol_file(os.path.join(dst_zip_folder, symbol_zip_name), dst_zip_folder)

    dsym_file_path = get_dSYM_file_path_mac(dst_zip_folder, framework, cplusplus)
    if dsym_file_path == "":
        print("cannot find dsym file!")
        return

    print("dSYM file: {}".format(dsym_file_path))
    execute_file = os.path.join(dsym_file_path, "Contents", "Resources", "DWARF", get_execute_mac_file_name(framework))

    if uuid != "":
        match, arch = check_uuid_is_same(execute_file, uuid)
        if not match:
            print("cannot match uuid!")
            zegoio.delete(dst_zip_folder)
            return

        print("arch: {}".format(arch))
    elif arch is None:
        arch = "x86_64"

    symbol_list = get_symbol_ios(execute_file, base_address, arch, crash_addresses)

    # get VE version
    ve_version = get_ve_version(dst_zip_folder)

    print(">>")
    print("ve version: {}".format(ve_version))

    print("crash stack:\n")
    for symbol in symbol_list:
        print(symbol)

    # remove symbol folder
    zegoio.delete(dst_zip_folder)


def run(jenkins_args):
    parse = argparse.ArgumentParser()

    parse.add_argument("--iOS", action='store_true', default=False, help="ios")
    parse.add_argument("--Android", action='store_true', default=False, help="Android")
    parse.add_argument("--Mac", action='store_true', default=False, help="Mac")
    parse.add_argument('--framework', action='store', type=str, help="framework")
    parse.add_argument('--sdk_version', action='store', type=str, help="specific sdk version")
    parse.add_argument('--uuid', action='store', type=str, default='', help="specific uuid")
    parse.add_argument('--arch', action='store', type=str, help="cpu arch")
    parse.add_argument("--base_address", action='store', type=str, default='0', help="base address")
    parse.add_argument("--crash_addresses", action='store', type=str, nargs='+', help="crash addresses")
    parse.add_argument("--cplusplus", action='store_true', default=False, help="c++ interface")
    arguments = parse.parse_args(jenkins_args)

    if arguments.iOS:
        arch = arguments.arch
        if arguments.uuid != "":
            arch = ""

        run_ios(arguments.framework, arguments.sdk_version, arguments.uuid, arch, arguments.base_address,
                arguments.crash_addresses)
    elif arguments.Android:
        run_android(arguments.framework, arguments.sdk_version, arguments.arch, arguments.crash_addresses)
    elif arguments.Mac:
        run_mac(arguments.framework, arguments.sdk_version, arguments.uuid, "x86_64", arguments.base_address,
                arguments.crash_addresses, arguments.cplusplus)
    else:
        print("*** must specify a platform, eg: --iOS or --Mac or --Android ***")


def run_on_jenkins():
    args = CmdParam()
    if get_bool("iOS"):
        args.append('--iOS')
    if get_bool('Android'):
        args.append('--Android')
    if get_bool('Mac'):
        args.append('--Mac')

    if get_string('framework'):
        args.append('--framework', get_string('framework'))
    if get_string('sdk_version'):
        args.append('--sdk_version', get_string('sdk_version'))
    if get_string('uuid'):
        args.append('--uuid', get_string('uuid'))
    if get_string('arch'):
        args.append('--arch', get_string('arch'))
    if get_string('base_address'):
        args.append('--base_address', get_string('base_address'))
    if get_string('crash_addresses'):
        args.append('--crash_addresses', *get_string('crash_addresses').splitlines())
    if get_bool('cplusplus'):
        args.append('--cplusplus')

    run(args.get_all())


if __name__ == "__main__":
    run_on_jenkins()
