#!/usr/bin/env python -u
# coding:utf-8

"""
使用 polly 编译项目
"""
import os
from os.path import join as pjoin
from multiprocessing import cpu_count
from typing import Dict
from zegopy.builder import zego_helper
from zegopy.builder import jenkins_keychain_util
from zegopy.builder.build_env_config import *


__LINUX_TOOLCHAIN_CONFIG = {
    "linux": {
        "support_product": LINUX.ARCH_TOOLCHAIN_TABLE,
        "env": []
    },
    "hisi": {
        "support_product": EMBEDDED._HISI_TOOLCHAIN_TABLE,
        "env": [
            {
                "key": "PATH",
                "value": lambda product: "" if product is None else (pjoin(os.environ.get("HISI_HOME"), "arm-{}".format(EMBEDDED._HISI_TOOLCHAIN_TABLE[product]), "bin") if EMBEDDED._HISI_TOOLCHAIN_TABLE[product].startswith("hisi-himix") else pjoin(os.environ.get("HISI_HOME"), "arm-{}-linux".format(EMBEDDED._HISI_TOOLCHAIN_TABLE[product].replace('-', '')), "target/bin")),
            },
            {
                "key": "LC_ALL",
                "value": lambda product: "C" if EMBEDDED._HISI_TOOLCHAIN_TABLE[product].startswith("hisi-himix") else ""
            }
        ]
    },
    "rockchip": {
        "support_product": EMBEDDED._ROCKCHIP_TOOLCHAIN_TABLE,
        "env": [
            {
                "key": "PATH",
                "value": lambda product: "" if (product is None or product != "px3se") else pjoin(os.environ.get("ROCKCHIP_HOME"), product, "usr/bin")
            },
            {
                "key": "LD_LIBRARY_PATH",
                "value": lambda product: "" if product is None else pjoin(os.environ.get("ROCKCHIP_HOME"), product, "usr/lib" if product == "px3se" else "lib")
            }
        ]
    },
    "allwinner": {
        "support_product": EMBEDDED._ALLWINNER_TOOLCHAIN_TABLE,
        "env": [
            {
                "key": "PATH",
                "value": lambda product: "" if product is None else pjoin(os.environ.get("ALLWINNER_HOME"), product, "bin") + ":" + os.environ['PATH']
            },
            {
                "key": "STAGING_DIR",
                "value": lambda product: "" if product is None else pjoin(os.environ.get("ALLWINNER_HOME"), product)
            }
        ]
    },
    "gokeic": {
        "support_product": EMBEDDED._GOKEIC_TOOLCHAIN_TABLE,
        "env": [
            {
                "key": "LD_LIBRARY_PATH",
                "value": lambda product: "" if product is None else pjoin(os.environ.get("GOKEIC_HOME"), product, "arm-linux-gcc-4.8.5/lib")
            }
        ]
    },
    "ingenic": {
        "support_product": EMBEDDED._INGENIC_TOOLCHAIN_TABLE,
        "env": []
    },
    "raspberrypi": {
        "support_product": EMBEDDED._RASPBERRYPI_TOOLCHAIN_TABLE,
        "env": []
    },
    "neoway": {
        "support_product": EMBEDDED._NEOWAY_TOOLCHAIN_TABLE,
        "env": [
            {
                "key": "PATH",
                "value": lambda product: pjoin(os.environ.get("NEOWAY_HOME"), 'arm-oe/sysroots/x86_64-oesdk-linux/usr/bin/arm-oe-linux-gnueabi')
            }
        ]
    },
    "novatek": {
        "support_product": EMBEDDED._NOVATEK_TOOLCHAIN_TABLE,
        "env": [
            {
                "key": "LD_LIBRARY_PATH",
                "value": lambda product: "" if product is None else pjoin(os.environ.get("NOVATEK_HOME"), "mipsel-{}".format(product), "usr/lib")
            }
        ]
    },
    "linaro": {
        "support_product": EMBEDDED._LINARO_TOOLCHAIN_TABLE,
        "env": []
    },
    "alios": {
        "support_product": EMBEDDED._ALIOS_TOOLCHAIN_TABLE,
        "env": []
    },
    "myir": {
        "support_product": EMBEDDED._MYIR_TOOLCHAIN_TABLE,
        "env": [
            {
                "key": "LD_LIBRARY_PATH",
                "value": lambda product: "" if product is None else pjoin(os.environ.get("MYIR_HOME"), product, "usr/lib")
            }
        ]
    },
    "arm_linux": {
        "support_product": EMBEDDED._STANDARD_ARM_TOOLCHAIN_TABLE,
        "env": []
    }
}


def android_build(project_root, abi, build_type, fwd_configs, only_config=False, use_ndk_r21d=False):
    """
    调用 polly 编译 Android 项目
    :param project_root: 项目根路径
    :param abi: 平台类型，取值范围 ['armeabi', 'armeabi-v7a', 'arm64-v8a', 'x86']
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :param use_ndk_r21d: 如果指定 use_ndk_r21d，则使用 NDK r21d 编译 C/C++ 代码，否则使用 r13b toolchain 进行编译
    """
    _toolchain = None
    if use_ndk_r21d:
        os.environ["ANDROID_NDK_r21d"] = os.environ["ANDROID_NDK_HOME_r21d"]
        _toolchain = ANDROID.ABI_TOOLCHAIN_TABLE_WITH_r21d[abi]
    else:
        os.environ["ANDROID_NDK_r13b"] = os.environ["NDK_HOME"]
        _toolchain = ANDROID.ABI_TOOLCHAIN_TABLE[abi]

    from multiprocessing import cpu_count
    command_arguments = ['--verbose', '--clear', '--toolchain', _toolchain,
                         '--config', build_type.capitalize(), '--home', project_root,
                         '--jobs', str(cpu_count())]

    if only_config:
        command_arguments.append('--nobuild')

    # 添加 Android 特有的配置项
    fwd_configs["CMAKE_ANDROID_NDK_TOOLCHAIN_VERSION"] = "clang"

    if "CMAKE_ANDROID_STL_TYPE" not in fwd_configs:
        fwd_configs["CMAKE_ANDROID_STL_TYPE"] = "c++_static"

    _append_fwd_params(command_arguments, fwd_configs)

    _build(command_arguments)


def android_build2(project_root, abi, build_type, fwd_configs, only_config=False, use_ndk_r21d=False):
    """
    调用 polly 编译 Android 项目
    :param project_root: 项目根路径
    :param abi: 平台类型，取值范围 ['armeabi', 'armeabi-v7a', 'arm64-v8a', 'x86']
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :param use_ndk_r21d: 如果指定 use_ndk_r21d，则使用 NDK r21d 编译 C/C++ 代码，否则使用 r13b toolchain 进行编译
    """

    _toolchain = None
    if use_ndk_r21d:
        os.environ["ANDROID_NDK_r21d"] = os.environ["ANDROID_NDK_HOME_r21d"]
        _toolchain = ANDROID.ABI_TOOLCHAIN_TABLE_WITH_r21d[abi]
    else:
        os.environ["ANDROID_NDK_r13b"] = os.environ["NDK_HOME"]
        _toolchain = ANDROID.ABI_TOOLCHAIN_TABLE[abi]

    from multiprocessing import cpu_count
    command_arguments = ['--verbose', '--clear', '--install', '--toolchain', _toolchain,
                         '--config', build_type.capitalize(), '--home', project_root,
                         '--jobs', str(cpu_count())]

    if only_config:
        command_arguments.append('--nobuild')

    # 添加 Android 特有的配置项
    fwd_configs["CMAKE_ANDROID_NDK_TOOLCHAIN_VERSION"] = "clang"
    if "CMAKE_ANDROID_STL_TYPE" not in fwd_configs:
        fwd_configs["CMAKE_ANDROID_STL_TYPE"] = "c++_static"

    _append_fwd_params(command_arguments, fwd_configs)

    _build(command_arguments)


def android_build_enable_asan(project_root, abi, build_type, fwd_configs):
    """
    编译带 asan 特性的 Android 项目
    :param project_root:
    :param abi:
    :param build_type:
    :param fwd_configs:
    :return:
    """
    if abi not in ANDROID.ABI_TOOLCHAIN_TABLE_WITH_r16b:
        raise Exception("Not support the abi: {} for asan".format(abi))

    os.environ["ANDROID_NDK_r16b"] = os.path.join(os.environ["ANDROID_HOME"], "ndks", "ndk-r16b")

    from multiprocessing import cpu_count
    command_arguments = ['--verbose', '--clear', '--toolchain', ANDROID.ABI_TOOLCHAIN_TABLE_WITH_r16b[abi],
                         '--config', build_type.capitalize(), '--home', project_root,
                         '--jobs', str(cpu_count())]

    # 添加 Android 特有的配置项
    fwd_configs["CMAKE_ANDROID_NDK_TOOLCHAIN_VERSION"] = "clang"
    fwd_configs["ENABLE_ASAN"] = True   # 开启 Address Sanitizer 特性

    _append_fwd_params(command_arguments, fwd_configs)

    _build(command_arguments)



def ios_build_new(project_root:str, toolchain_file:str, build_type:str, fwd_configs:Dict, ios_variant:str, install_framework:bool, only_config=False, plist_path='', certificate_name='', clear_cache=True, force_legacy=False):
    """
    为了兼容 XCFramework ，请优先使用此方法构建 iOS 库
    支持构建 .a / .dylib / .framework
    若需要生成 Framework 请指定 install_framework 参数为 True
    注意：必须指定 "ios_variant" 参数，目前支持 "device" / "simulator" / "maccatalyst" 三种类型
    意味着一次调用只能构建出一种设备类型，若需要同时构建真机、模拟器、MacCatalyst，请调用三次此方法
    当使用此方式构建时，可以在 CMakeLists 中通过 ${IOS_VARIANT} 获取当前正在构建的变种，
    可用于链接时区分到底要链接 iOS XCFramework 内哪个二进制（ XCFramework 中，不同变种的架构分在不同的文件夹内 ）
    CMake 中的 ${IOS_VARIANT} 变量的取值为 ["DEVICE", "SIMULATOR", "MACCATALYST"]

    注意使用此函数构建后，产物的 _builds, _install, _framework 目录下都会多一层 [ios_variant] 目录

    Args:
        project_root (str): 项目根路径
        toolchain_file (str): iOS toolchain file
        build_type (str): 编译类型，取值范围 ['Release', 'Debug']
        fwd_configs (Dict): 透传给 CMakeLists.txt 的自定义参数
        ios_variant (str): iOS 设备变种，请指定 "device" / "simulator" / "maccatalyst" 之一
        install_framework (bool): 是否生成 "_framework/[toolchain]/[ios_variant]/xxxxx.framework" 产物
        only_config (bool, optional): 是否仅生成 CMake 工程而不编译. Defaults to False.
        plist_path (str, optional): 当 install_framework==True 时需要指定 plist 文件路径. Defaults to ''.
        certificate_name (str, optional): 当 install_framework==True 且 时需要指定, 签名用. Defaults to ''.
        clear_cache (str, optional): 是否清理上一次构建缓存
        force_legacy (bool, optional): [description]. Defaults to False.
    """

    command_arguments = ['--verbose', '--ios-multiarch',
                         '--ios-variant', ios_variant,
                         '--toolchain', toolchain_file,
                         '--identity', certificate_name,
                         '--config', build_type.capitalize(),
                         '--home', project_root,
                         '--plist', plist_path]

    if install_framework:
        command_arguments.append('--framework')
        command_arguments.append('--framework-support-multi-variant')

    if only_config:
        command_arguments.append('--nobuild')

    if clear_cache:
        command_arguments.append('--clear')
    else:
        command_arguments.append('--reconfig')

    if force_legacy:
        _, cmake_ver = zego_helper.get_cmake_version()
        if cmake_ver[0] >= 3 and cmake_ver[1] >= 19:
            # 此参数仅在 CMake 3.19 版本以上才能设置，低于此版本的 CMake 设置后会抛出未知参数异常
            command_arguments.append('--force-use-xcode-legacy')

    _append_fwd_params(command_arguments, fwd_configs)

    jenkins_keychain_util.unlock_keychain_if_need()  # 当 jenkins 任务在 slave 上启动时， 因 xcode 签名 Bug，会出现 errSecInternalComponent 异常
    _build(command_arguments)


def ios_build(project_root, plist_path, toolchain_file, build_type, fwd_configs, certificate_name, only_config=False, with_simulator=True, force_legacy=False):
    """
    调用 polly 编译 iOS 项目
    :param project_root: 项目根路径
    :param plist_path: Info.plist 文件全路径
    :param toolchain_file: iOS toolchain file
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :param with_simulator: 是否编译并合并 iOS 模拟器架构
    :param force_legacy: CMake 3.19 及以上版本在 Xcode 12 上默认使用 New Build System，若需强制继续使用 Legacy Build System，设此值为 True
    """
    command_arguments = ['--verbose', '--clear', '--framework',
                         '--toolchain', toolchain_file,
                         '--identity', certificate_name,
                         '--config', build_type.capitalize(),
                         '--home', project_root,
                         '--plist', plist_path]

    if only_config:
        command_arguments.append('--nobuild')

    if with_simulator:
        command_arguments.append('--ios-combined')

    if force_legacy:
        _, cmake_ver = zego_helper.get_cmake_version()
        if cmake_ver[0] >= 3 and cmake_ver[1] >= 19:
            # 此参数仅在 CMake 3.19 版本以上才能设置，低于此版本的 CMake 设置后会抛出未知参数异常
            command_arguments.append('--force-use-xcode-legacy')

    _append_fwd_params(command_arguments, fwd_configs)

    jenkins_keychain_util.unlock_keychain_if_need()  # 当 jenkins 任务在 slave 上启动时， 因 xcode 签名 Bug，会出现 errSecInternalComponent 异常
    _build(command_arguments)


def ios_build_lib(project_root, toolchain_file, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 iOS 项目
    :param project_root: 项目根路径
    :param toolchain_file: iOS toolchain file
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    """
    command_arguments = ['--verbose', '--clear', '--iossim', '--ios-multiarch',
                         '--toolchain', toolchain_file,
                         '--config', build_type.capitalize(),
                         '--home', project_root]

    if only_config:
        command_arguments.append('--nobuild')

    _append_fwd_params(command_arguments, fwd_configs)

    jenkins_keychain_util.unlock_keychain_if_need()  # 当 jenkins 任务在 slave 上启动时， 因 xcode 签名 Bug，会出现 errSecInternalComponent 异常
    _build(command_arguments)

    command_arguments = ['--verbose', '--reconfig', '--ios-multiarch',
                         '--toolchain', toolchain_file,
                         '--config', build_type.capitalize(),
                         '--home', project_root]
    if only_config:
        command_arguments.append('--nobuild')

    _append_fwd_params(command_arguments, fwd_configs)

    _build(command_arguments)


def ios_build_lib2(project_root, toolchain_file, build_type, fwd_configs, only_config=False, force_legacy=False):
    """
    调用 polly 编译 iOS 项目
    :param project_root: 项目根路径
    :param toolchain_file: iOS toolchain file
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    """
    command_arguments = ['--verbose', '--clear', '--ios-multiarch', '--install', '--ios-combined',
                         '--toolchain', toolchain_file,
                         '--config', build_type.capitalize(),
                         '--home', project_root]

    if only_config:
        command_arguments.append('--nobuild')

    if force_legacy:
        _, cmake_ver = zego_helper.get_cmake_version()
        if cmake_ver[0] >= 3 and cmake_ver[1] >= 19:
            # 此参数仅在 CMake 3.19 版本以上才能设置，低于此版本的 CMake 设置后会抛出未知参数异常
            command_arguments.append('--force-use-xcode-legacy')

    _append_fwd_params(command_arguments, fwd_configs)

    jenkins_keychain_util.unlock_keychain_if_need()  # 当 jenkins 任务在 slave 上启动时， 因 xcode 签名 Bug，会出现 errSecInternalComponent 异常
    _build(command_arguments)


def ios_build_lib3(project_root, toolchain_file, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 iOS 项目
    :param project_root: 项目根路径
    :param toolchain_file: iOS toolchain file
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    """
    command_arguments = ['--verbose', '--clear', '--ios-multiarch',
                         '--toolchain', toolchain_file,
                         '--config', build_type.capitalize(),
                         '--home', project_root]

    if only_config:
        command_arguments.append('--nobuild')

    _append_fwd_params(command_arguments, fwd_configs)

    jenkins_keychain_util.unlock_keychain_if_need()  # 当 jenkins 任务在 slave 上启动时， 因 xcode 签名 Bug，会出现 errSecInternalComponent 异常
    _build(command_arguments)


def mac_build(project_root, plist_path, toolchain_file, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 Mac 项目
    :param project_root: 项目根路径
    :param plist_path: Info.plist 文件全路径
    :param toolchain_file: mac toolchain file
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    command_arguments = ['--verbose', '--clear', '--framework', '--toolchain', toolchain_file,
                         '--config', build_type.capitalize(), '--home', project_root, '--plist', plist_path]

    if only_config:
        command_arguments.append('--nobuild')

    _append_fwd_params(command_arguments, fwd_configs)

    jenkins_keychain_util.unlock_keychain_if_need()  # 当 jenkins 任务在 slave 上启动时， 因 xcode 签名 Bug，会出现 errSecInternalComponent 异常
    _build(command_arguments)


def mac_build_lib(project_root, toolchain_file, build_type, fwd_configs, only_config=False, force_legacy=False):
    """
    调用 polly 编译 Mac 项目
    :param project_root: 项目根路径
    :param toolchain_file: mac toolchain file
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    command_arguments = ['--verbose', '--clear', '--toolchain', toolchain_file,
                         '--config', build_type.capitalize(), '--home', project_root]

    if only_config:
        command_arguments.append('--nobuild')

    if force_legacy:
        _, cmake_ver = zego_helper.get_cmake_version()
        if cmake_ver[0] >= 3 and cmake_ver[1] >= 19:
            # 此参数仅在 CMake 3.19 版本以上才能设置，低于此版本的 CMake 设置后会抛出未知参数异常
            command_arguments.append('--force-use-xcode-legacy')

    _append_fwd_params(command_arguments, fwd_configs)

    jenkins_keychain_util.unlock_keychain_if_need()  # 当 jenkins 任务在 slave 上启动时， 因 xcode 签名 Bug，会出现 errSecInternalComponent 异常
    _build(command_arguments)


def mac_build_lib2(project_root, toolchain_file, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 Mac 项目
    :param project_root: 项目根路径
    :param toolchain_file: mac toolchain file
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    command_arguments = ['--verbose', '--clear', '--install', '--toolchain', toolchain_file,
                         '--config', build_type.capitalize(), '--home', project_root]

    if only_config:
        command_arguments.append('--nobuild')

    _append_fwd_params(command_arguments, fwd_configs)

    jenkins_keychain_util.unlock_keychain_if_need()  # 当 jenkins 任务在 slave 上启动时， 因 xcode 签名 Bug，会出现 errSecInternalComponent 异常
    _build(command_arguments)


def windows_build(project_root, arch_type, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 Windows 项目
    :param project_root: 项目根路径
    :param arch_type: arch 类型，取值范围 ['x86', 'x64']
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    command_arguments = ['--verbose', '--clear', '--config', build_type.capitalize(),
                         '--toolchain', WINDOWS.ARCH_TOOLCHAIN_TABLE[arch_type], '--home', project_root,
                         '--jobs', str(cpu_count()), ]

    if only_config:
        command_arguments.append('--nobuild')

    _append_fwd_params(command_arguments, fwd_configs)

    _build(command_arguments)


def linux_build(project_root, cpu_type, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 Linux 项目
    :param project_root: 项目根路径
    :param cpu_type CPU 类型，一般为 x86_64
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "linux", cpu_type, build_type, fwd_configs, only_config)

def arm_linux_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 arm_linux 项目
    :param project_root: 项目根路径
    :param product allwinner 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "arm_linux", product, build_type, fwd_configs, only_config)

def allwinner_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 allwinner 项目
    :param project_root: 项目根路径
    :param product allwinner 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "allwinner", product, build_type, fwd_configs, only_config)


def hisi_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 hisi 项目
    :param project_root: 项目根路径
    :param product hisi 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "hisi", product, build_type, fwd_configs, only_config)


def rockchip_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 rockchip 项目
    :param project_root: 项目根路径
    :param product rockchip 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "rockchip", product, build_type, fwd_configs, only_config)


def novatek_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 ovatek 项目
    :param project_root: 项目根路径
    :param product ovatek 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "novatek", product, build_type, fwd_configs, only_config)


def ingenic_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 ingenic 项目
    :param project_root: 项目根路径
    :param product ingenic 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "ingenic", product, build_type, fwd_configs, only_config)


def raspberrypi_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 raspberrypi 项目
    :param project_root: 项目根路径
    :param product raspberrypi 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "raspberrypi", product, build_type, fwd_configs, only_config)


def neoway_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 neoway 项目
    :param project_root: 项目根路径
    :param product neoway 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "neoway", product, build_type, fwd_configs, only_config)


def linaro_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 linaro 项目
    :param project_root: 项目根路径
    :param product linaro 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "linaro", product, build_type, fwd_configs, only_config)


def gokeic_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 gokeic 项目
    :param project_root: 项目根路径
    :param product gokeic 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "gokeic", product, build_type, fwd_configs, only_config)

def alios_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 alios 项目
    :param project_root: 项目根路径
    :param product gokeic 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "alios", product, build_type, fwd_configs, only_config)

def myir_build(project_root, product, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 myir 项目
    :param project_root: 项目根路径
    :param product gokeic 提供的产品类型
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    unix_like_build(project_root, "myir", product, build_type, fwd_configs, only_config)

def ohos_build(project_root, abi, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 HarmonyOS 项目
    :param project_root: 项目根路径
    :param abi: 平台类型，取值范围 ['armeabi-v7a', 'arm64-v8a', 'x86_64']
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    """
    _native_root = os.environ["OHOS_NATIVE_HOME"]
    _toolchain = OHOS.ABI_TOOLCHAIN_TABLE[abi]

    from multiprocessing import cpu_count
    command_arguments = ['--verbose', '--clear', '--toolchain', _toolchain,
                         '--config', build_type.capitalize(), '--home', project_root,
                         '--jobs', str(cpu_count())]

    if only_config:
        command_arguments.append('--nobuild')

    # 添加 ohos 特有的配置项
    fwd_configs["OHOS_ARCH"] = abi
    fwd_configs["OHOS_SDK_NATIVE"] = _native_root
    fwd_configs["CMAKE_SYSTEM_NAME"] = "OHOS"
    fwd_configs["CMAKE_OHOS_ARCH_ABI"] = abi
    fwd_configs["CMAKE_EXPORT_COMPILE_COMMANDS"] = "ON"
    # fwd_configs["CMAKE_TOOLCHAIN_FILE"] = "{0}/build/cmake/ohos.toolchain.cmake".format(_native_root)
    # fwd_configs["CMAKE_MAKE_PROGRAM"] = "{0}/build-tools/cmake/bin/ninja".format(_native_root)

    _append_fwd_params(command_arguments, fwd_configs)

    _build(command_arguments)

def normal_build(project_root, toolchain_file, build_type, advance_arguments=[]):
    """
    使用 Polly 构建普通应用
    :param project_root
    :param toolchain_file
    :param build_type
    :param advance_arguments
    :return
    """
    command_arguments = ['--home', project_root, '--toolchain', toolchain_file, '--config', build_type.capitalize()]
    _append_fwd_params(command_arguments, advance_arguments)
    _build(command_arguments)


def unix_like_build(project_root, manufacturer, soc_name, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 类 Unix 项目
    :param project_root: 项目根路径
    :param manufacturer: 厂商名，支持列表见 __LINUX_TOOLCHAIN_CONFIG 定义
    :param soc_name 芯片型号/名，当为标准 Linux 时，为 CPU 构架
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    _inner_unix_like_build(project_root, manufacturer, soc_name, build_type, fwd_configs, enable_install=False, only_config=only_config)


def unix_like_build_with_install(project_root, manufacturer, soc_name, build_type, fwd_configs, only_config=False):
    """
    调用 polly 编译 类 Unix 项目（带 --install 参数）
    :param project_root: 项目根路径
    :param manufacturer: 厂商名，支持列表见 __LINUX_TOOLCHAIN_CONFIG 定义
    :param soc_name 芯片型号/名，当为标准 Linux 时，为 CPU 构架
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    _inner_unix_like_build(project_root, manufacturer, soc_name, build_type, fwd_configs, enable_install=True, only_config=only_config)


def _inner_unix_like_build(project_root, manufacturer, soc_name, build_type, fwd_configs, enable_install=False, only_config=False):
    """
    调用 polly 编译 类 Unix 项目
    :param project_root: 项目根路径
    :param manufacturer: 厂商名，支持列表见 __EMBEDDED_TOOLCHAIN_CONFIG 定义
    :param soc_name 芯片型号/名
    :param build_type: 编译类型，取值范围 ['Release', 'Debug']
    :param fwd_configs: 透传给 CMakeLists.txt 的自定义参数
    :param enable_install: 编译参数是否需要带 --install
    :param only_config: 如果指定 only_config，则只执行 make config, 而不会 build 项目
    :return:
    """
    def _setup_environment(env_config, product):
        for item in env_config:
            key, value_func = item["key"], item["value"]
            value = value_func(product)
            if value:
                if key == "PATH":
                    os.environ[key] = os.environ[key] + ":" + value
                else:
                    os.environ[key] = value
            else:
                print("invalid environ value: {} for key: {}".format(value, key))

    if manufacturer not in __LINUX_TOOLCHAIN_CONFIG:
        raise Exception("not support manufacturer: {}, must in [{}]".format(manufacturer, ", ".join(__LINUX_TOOLCHAIN_CONFIG.keys())))

    support_products = __LINUX_TOOLCHAIN_CONFIG[manufacturer]["support_product"]
    if soc_name not in support_products:
        raise Exception("not support soc: {}, must in: [{}]".format(soc_name, ", ".join(support_products.keys())))

    _setup_environment(__LINUX_TOOLCHAIN_CONFIG[manufacturer]["env"], soc_name)

    toolchain_file = support_products[soc_name]
    command_arguments = ['--verbose', '--clear', '--config', build_type.capitalize(),
                         '--toolchain', toolchain_file, '--home', project_root, '--jobs', str(int(cpu_count() / 2))]

    if only_config:
        command_arguments.append('--nobuild')

    if enable_install:
        command_arguments.append('--install')

    _append_fwd_params(command_arguments, fwd_configs)

    _build(command_arguments)


def _append_fwd_params(command_arguments, fwd_configs):
    command_arguments.append('--fwd')
    for (key, value) in fwd_configs.items():
        command_arguments.append("{}={}".format(key, value))

    return command_arguments


def _build(command_arguments):
    """
    调用 polly 编译 Android/iOS 项目
    :param command_arguments: 参数列表
    """

    import sys
    from subprocess import call
    from os.path import abspath, dirname, join
    polly_build_path = abspath(join(dirname(abspath(__file__)), '../polly/bin/', 'build.py'))

    new_command_arguments = [sys.executable, '-u', polly_build_path]
    new_command_arguments.extend(command_arguments)

    print("{} Execute command {}".format("***" * 5, "***" * 5))
    is_executable = True # first argument is executable
    for _item in new_command_arguments:
        if is_executable:
            print("  " + str(_item))
            is_executable = False
        else:
            print("    " + str(_item))
    print("*******" * 6)

    state = call(new_command_arguments)  # shell=True
    if state != 0:
        raise Exception("[*] Execute {} failed.".format(' '.join(new_command_arguments)))
