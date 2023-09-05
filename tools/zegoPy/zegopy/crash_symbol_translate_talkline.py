#!/usr/bin/env python3 -u
# coding:utf-8

import os
import sys
import tempfile
import uuid
import re
import json

from zegopy.common import io as zegoio 
from zegopy.common import command as zegocmd
from zegopy.builder import zip_folder as zegozip

from os.path import expanduser

# script_path = os.path.dirname(os.path.realpath(__file__))

def get_execute_ios_file_name(framework):
    if framework.lower() == "zegomeetingroom":
        return "libZegoMeetingRoom.dylib"
    
    if framework.lower() == "zegoappdc":
        return "libZegoLiveRoom.dylib"

    if framework.lower() == "zegoeducation":
        return "ZegoEducation"


def get_execute_mac_file_name(framework):
    if framework.lower() == "zegomeetingroom":
        return "libZegoMeetingRoomOSX.dylib"
    
    if framework.lower() == "zegoappdc":
        return "libZegoAppDCOSX.dylib"

    if framework.lower() == "zegoeducation":
        return "libZegoEducationOSX.dylib"


def get_execute_android_file_name(framework):
    if framework.lower() == "zegomeetingroom":
        return "libzegomeetingroom.so"
    
    if framework.lower() == "zegoappdc":
        return "libzegoappdc.so"

    if framework.lower() == "zegoeducation":
        return "libzegoeducation.so"


def get_android_toolchain_path(arch):
    if arch == "armeabi-v7a":
        return ("arm-linux-androideabi-4.9", "arm-linux-androideabi-addr2line")
    
    if arch == "arm64-v8a":
        return ("aarch64-linux-android-4.9", "aarch64-linux-android-addr2line")

    if arch == "x86":
        return ("x86-4.9", "i686-linux-android-addr2line")


def copy_symbol_file(framework, sdk_version, dest_zip_folder, part_symbol_zip_name, platform, develop, deploy):
    print("copy symbol file >>> ")
    print(dest_zip_folder)
    print(part_symbol_zip_name)

    #mount share
    mount_temp = os.path.join(expanduser("~"), "zego_sdk_symbol")

    zegoio.insure_dir_exists(mount_temp)

    server_path = ""
    if framework == "zegoeducation":
        if develop:
            server_path = "//192.168.1.3/share/education/ZegoVideoConferenceTest/{0}".format(platform.lower())
        if deploy:
            server_path = "//192.168.1.3/share/education/ZegoVideoConference/{0}".format(platform.lower())
    else:
        server_path = "//192.168.1.3/share/zego_sdk"
    k_login_info = 'share:share%40zego@'
    src_share_path = '//' + k_login_info + server_path[2:]

    src_share_path_no_login = server_path

    zegocmd.execute('umount -f {0}'.format(mount_temp))

    print("<< going to mount share {0} to {1}".format(src_share_path_no_login, mount_temp))

    ok, result = zegocmd.execute('mount -t smbfs {0} {1}'.format(src_share_path, mount_temp))
    if ok != 0:
        print("mount share failed: {0}".format(result))
        ok, result = zegocmd.execute('mount -t smbfs {0} {1}'.format(src_share_path_no_login, mount_temp))
        if ok != 0:
            print("mount share failed again: {0}".format(result))
            zegocmd.execute('umount -f {0}'.format(mount_temp))
            raise Exception(result)

    found_framework = False 
    symbol_zip_name = ""

    if framework == "zegoeducation":
        app_folder_path = get_symbol_path_from_share(framework, sdk_version, mount_temp)
        if app_folder_path != "":
            print("app_folder_path: {0}".format(app_folder_path))
            (result, symbol_zip_name) = copy_framework_symbol(app_folder_path, part_symbol_zip_name, dest_zip_folder, platform)
            if result:
                found_framework = True

        # ok, result = zegocmd.execute('umount -f {0}'.format(mount_temp))
        # if ok != 0:
        #     raise Exception(result)
    else:
        sdk_framework_folder_path = get_symbol_path_from_share(framework, sdk_version, mount_temp)
        print("sdk_framework_folder_path: {0}".format(sdk_framework_folder_path))
        if sdk_framework_folder_path != "":
            print ("framework: {}".format(sdk_framework_folder_path))
            (result, symbol_zip_name) = copy_framework_symbol(sdk_framework_folder_path, part_symbol_zip_name, dest_zip_folder, platform)
            if result:
                copy_ve_json_file(sdk_framework_folder_path, dest_zip_folder, platform)
                found_framework = True

        ok, result = zegocmd.execute('umount -f {0}'.format(mount_temp))
        if ok != 0:
            raise Exception(result)

    return (found_framework, symbol_zip_name)


def get_symbol_path_from_share(framework, sdk_version, local_mount_path):
    framework_folder_list = os.listdir(local_mount_path)
    # print("framework_foler_list: {0}".format(framework_folder_list))

    if framework == "zegoeducation": 
        for app_folder in framework_folder_list:
            if not os.path.isdir(os.path.join(local_mount_path, app_folder)):
                continue
            
            if app_folder != sdk_version:
                continue
            
            return os.path.join(local_mount_path, app_folder, "ZegoEducation.app.dSYM")
    else:
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
                
                if sdk_version in sdk_framework_folder:
                    return os.path.join(sdk_framework_folder_path, sdk_framework_folder)
        
    return ""


def copy_framework_symbol(src_framework_folder, part_symbol_zip_name, dest_framework_folder, platform):
    # print ("src_framework_folder: {0}, part_symbol_zip_name: {1}, dest_framework_folder: {2}, platform: {3}".format(src_framework_folder, part_symbol_zip_name, dest_framework_folder,platform ))

    if part_symbol_zip_name == "ZegoEducation.app.dSYM":
        symbol_file_path = src_framework_folder
        if os.path.exists(symbol_file_path):
            result = zegoio.copy(symbol_file_path, dest_framework_folder)
            if result == 0:
                print("copy_framework_symbol succceed, copy {} -> {}".format(symbol_file_path, dest_framework_folder))
                return (True, src_framework_folder)
            else:
                print("copy_framework_symbol failed, copy {} -> {}".format(symbol_file_path, dest_framework_folder))
                return (False, src_framework_folder)
    else :
        platform_folder_path = os.path.join(src_framework_folder, platform)
        platform_folder_list = os.listdir(platform_folder_path) 
        print ("symbol_zip_name: {}".format(part_symbol_zip_name))

        for platform_folder_file in platform_folder_list:
            if part_symbol_zip_name in platform_folder_file:
                symbol_file_path = os.path.join(platform_folder_path, platform_folder_file)
                print("copy {} -> {}".format(symbol_file_path, dest_framework_folder))
                if os.path.exists(symbol_file_path):
                    zegoio.copy(symbol_file_path, dest_framework_folder)
                    return (True, platform_folder_file)

    return (False, "")

def copy_ve_json_file(src_framework_folder, dest_framework_folder, platform):
    ve_json_file_path = os.path.join(src_framework_folder, platform, "construct.json")

    print("copy {} -> {}".format(ve_json_file_path, dest_framework_folder))

    zegoio.copy(ve_json_file_path, dest_framework_folder)


def unzip_symbol_file(symbol_file_path, dest_folder):
    zegozip.unzip_file(symbol_file_path, dest_folder)


def get_dSYM_file_path_ios(dest_folder):
    dest_sym_folder = os.path.join(dest_folder, "iphoneos")
    dest_sym_file_list = os.listdir(dest_sym_folder)

    for dest_sym_file in dest_sym_file_list:
        if dest_sym_file.endswith(".dSYM"):
            return os.path.join(dest_sym_folder, dest_sym_file)

    return ""


def get_dSYM_file_path_mac(dest_folder, framework):
    dest_sym_folder = os.path.join(dest_folder, "product", framework, "symbol")
    dest_sym_file_list = os.listdir(dest_sym_folder)

    for dest_sym_file in dest_sym_file_list:
        if dest_sym_file.endswith(".dSYM"):
            return os.path.join(dest_sym_folder, dest_sym_file)

    return ""


def check_uuid_is_same(execute_file, str_uuid):

    format_uuid = str(uuid.UUID(str_uuid)).upper()
    command = "dwarfdump --uuid {}".format(execute_file)

    ok, result = zegocmd.execute(command)
    if ok == 0:
        p = re.compile('''UUID: ([^(]*) \(([^)]*)\)''', re.M)
        uuid_list = p.findall(result.encode('utf-8'))
        print (uuid_list)
        for uuid_info in uuid_list:
            print ("uuid: {}, arch: {}".format(uuid_info[0], uuid_info[1]))
            if format_uuid == uuid_info[0]:
                return (True, uuid_info[1])
    else:
        print("execute command failed: {0}".format(command))

    return (False, "")


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
            crash_symbol_list.append("{}\n{}".format(hex(crash_address), result.encode('utf-8')))
        else:
            print ("execut failed reason: {}".format(result.encode('utf-8')))

    return crash_symbol_list


def get_symbol_android(addr2line_path, execute_file, crash_addresses):

    crash_symbol_list = []
    for str_crash_address in crash_addresses:
        crash_address = int(str_crash_address, 16)

        command = "{} -e {} -f -C {}".format(addr2line_path, execute_file, hex(crash_address))
        ok, result = zegocmd.execute(command)
        if ok == 0:
            crash_symbol_list.append("{}\n{}".format(hex(crash_address), result.encode('utf-8')))
        else:
            print ("execut failed reason: {}".format(result.encode('utf-8')))

    return crash_symbol_list


def get_ve_version(dest_folder):
    ve_file_path = os.path.join(dest_folder, "construct.json")
    if not os.path.exists(ve_file_path):
        print ("don't have construct.json")
        return ""
        
    with open(ve_file_path) as file_config:
        json_config = json.loads(file_config.read())
        return json_config["version"]

    return ""


def get_framework_so_path(dest_zip_folder, arch, framework):
    return os.path.join(dest_zip_folder, "symbols", arch, get_execute_android_file_name(framework))


def get_addr2line_file_path(arch):
    ndk_bundle = os.environ["NDK_HOME"]
    if len(ndk_bundle) == 0:
        raise Exception("Cannot find ndk home path")

    (arch_path, addr2line_file) = get_android_toolchain_path(arch)
    addr2line_file_path = os.path.join(ndk_bundle, "toolchains", arch_path, "prebuilt", "darwin-x86_64", "bin", addr2line_file)

    return addr2line_file_path


def run_ios(framework, sdk_version, uuid, arch, base_address, crash_addresses, develop, deploy):
    if sdk_version == "":
        return

    if len(crash_addresses) == 0:
        print("no crash stack!")
        return

    # dest_zip_folder = os.path.join(tempfile.mkdtemp(), "symbol_ios")
    dest_zip_folder = os.path.join(expanduser("~/crash"), "symbol_ios")

    part_symbol_zip_name = ""
    if framework.lower() == "zegoeducation":
        part_symbol_zip_name = "ZegoEducation.app.dSYM"
    else:
        part_symbol_zip_name = "symbol_{}".format(framework.lower())

    (found_framework, symbol_zip_name) = copy_symbol_file(framework, sdk_version, dest_zip_folder, part_symbol_zip_name, "iOS", develop, deploy)
    if found_framework == False:
        print("cannot find framewrok, check sdk_version {}!".format(sdk_version))
        return 

    dsym_file_path = ""
    if framework == "zegoeducation":
        dsym_file_path = symbol_zip_name
    else:
        unzip_symbol_file(os.path.join(dest_zip_folder, symbol_zip_name), dest_zip_folder)
        dsym_file_path = get_dSYM_file_path_ios(dest_zip_folder)
        if dsym_file_path == "":
            print("cannot find dsym file!")
            return 

    print("dSYM file: {}".format(dsym_file_path))
    execute_file = os.path.join(dsym_file_path, "Contents", "Resources", "DWARF", get_execute_ios_file_name(framework))

    if uuid != "":
        match, arch = check_uuid_is_same(execute_file, uuid)
        if match == False:
            print("cannot match uuid!")
            zegoio.delete(dest_zip_folder)
            return

        print("arch: {}".format(arch))
    elif arch == None:
        print("must specific arch")
        return

    symbol_list = get_symbol_ios(execute_file, base_address, arch, crash_addresses)

    #get VE version
    ve_version = get_ve_version(dest_zip_folder)

    print(">>")
    print("ve version: {}".format(ve_version))

    print("crash stack:\n")
    for symbol in symbol_list:
        print (symbol)

    #remove symbol folder
    zegoio.delete(dest_zip_folder)


def run_android(framework, sdk_version, arch, crash_addresses, develop, deploy):
    if sdk_version == "":
        return

    if len(crash_addresses) == 0:
        print("no crash stack")
        return
        
    dest_zip_folder = os.path.join(tempfile.mkdtemp(), "symbol_android")
    part_symbol_zip_name = sdk_version

    (found_framework, symbol_zip_name) = copy_symbol_file(framework, sdk_version, dest_zip_folder, part_symbol_zip_name, "android", develop, deploy)
    if found_framework == False:
        print("cannot find framewrok")
        return 

    unzip_symbol_file(os.path.join(dest_zip_folder, symbol_zip_name), dest_zip_folder)

    framework_so_path = get_framework_so_path(dest_zip_folder, arch, framework)

    #get addr2line address
    addr2line_file_path = get_addr2line_file_path(arch)

    symbol_list = get_symbol_android(addr2line_file_path, framework_so_path, crash_addresses)

    #get VE version
    ve_version = get_ve_version(dest_zip_folder)
    print(">>")
    print("ve version: {}".format(ve_version))

    print("crash stack:\n")
    for symbol in symbol_list:
        print (symbol)

    #remove symbol folder
    zegoio.delete(dest_zip_folder)


def run_mac(framework, sdk_version, uuid, arch, base_address, crash_addresses, develop, deploy):
    if sdk_version == "":
        return

    if len(crash_addresses) == 0:
        print("no crash stack!")
        return

    dest_zip_folder = os.path.join(tempfile.mkdtemp(), "symbol_mac")
    part_symbol_zip_name = "{}-symbol".format(sdk_version.lower())

    (found_framework, symbol_zip_name) = copy_symbol_file(framework, sdk_version, dest_zip_folder, part_symbol_zip_name, "Mac", develop, deploy)
    if found_framework == False:
        print("cannot find framewrok, check sdk_version {}!".format(sdk_version))
        return 

    unzip_symbol_file(os.path.join(dest_zip_folder, symbol_zip_name), dest_zip_folder)

    dsym_file_path = get_dSYM_file_path_mac(dest_zip_folder, framework)
    if dsym_file_path == "":
        print("cannot find dsym file!")
        return 

    print("dSYM file: {}".format(dsym_file_path))
    execute_file = os.path.join(dsym_file_path, "Contents", "Resources", "DWARF", get_execute_mac_file_name(framework))

    if uuid != "":
        match, arch = check_uuid_is_same(execute_file, uuid)
        if match == False:
            print("cannot match uuid!")
            zegoio.delete(dest_zip_folder)
            return

        print("arch: {}".format(arch))
    elif arch == None:
        arch = "x86_64"

    symbol_list = get_symbol_ios(execute_file, base_address, arch, crash_addresses)

    #get VE version
    ve_version = get_ve_version(dest_zip_folder)

    print(">>")
    print("ve version: {}".format(ve_version))

    print("crash stack:\n")
    for symbol in symbol_list:
        print (symbol)

    #remove symbol folder
    zegoio.delete(dest_zip_folder)


if __name__ == "__main__":
    import argparse

    parse = argparse.ArgumentParser()

    parse.add_argument("--iOS", action='store_true', default=False, help="ios")
    parse.add_argument("--Android", action='store_true', default=False, help="Android")
    parse.add_argument("--Mac", action='store_true', default=False, help="Mac")
    parse.add_argument('--framework', action='store', type=str, help="framework")
    parse.add_argument('--develop', action='store_true', default=False)
    parse.add_argument('--deploy', action='store_true', default=False)
    parse.add_argument('--sdk_version', action='store', type=str, help="specific sdk version")
    parse.add_argument('--uuid', action='store', type=str, default='', help="specific uuid")
    parse.add_argument('--arch', action='store', type=str, help="cpu arch")
    parse.add_argument("--base_address", action='store', type=str, default='0', help="base address")
    parse.add_argument("--crash_addresses", action='store', type=str, nargs='+', help="crash addresses")

    arguments = parse.parse_args()

    if arguments.iOS:
        arch = arguments.arch 
        if arguments.uuid != "":
            arch = ""

        run_ios(arguments.framework, arguments.sdk_version, arguments.uuid, arch, arguments.base_address, arguments.crash_addresses, arguments.develop, arguments.deploy)
    elif arguments.Android:
        run_android(arguments.framework, arguments.sdk_version, arguments.arch, arguments.crash_addresses, arguments.develop, arguments.deploy)
    elif arguments.Mac:
        run_mac(arguments.framework, arguments.sdk_version, arguments.uuid, "x86_64", arguments.base_address, arguments.crash_addresses, arguments.develop, arguments.deploy)


