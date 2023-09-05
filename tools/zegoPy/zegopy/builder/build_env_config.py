#!/usr/bin/env python -u
# coding: utf-8

import os
import sys

from zegopy.common import osutil


class ANDROID(object):
    BOOT_CLASSPATH = "~/Library/Android/sdk/platforms/android-23/android.jar"

    NDK_PATH = os.environ["NDK_HOME"] if "NDK_HOME" in os.environ else ""
    #if not NDK_PATH:
    #    print ("* Warning * No NDK_HOME be setting in os environment. Ignore this if not build Android")

    __ABI_ARMEABI_V7A = "armeabi-v7a"
    __ABI_ARMEABI = "armeabi"
    __ABI_ARM64_V8A = "arm64-v8a"
    __ABI_X86 = "x86"
    __ABI_X86_64 = "x86_64"

    __ABI_ARMEABI_V7A_CXX14_NDK16B = "armeabi-v7a-cxx14-ndk16b"
    __ABI_ARMEABI_V7A_CXX14 = "armeabi-v7a-cxx14"
    __ABI_ARMEABI_CXX14 = "armeabi-cxx14"
    __ABI_ARM64_V8A_CXX14_NDK16B = "arm64-v8a-cxx14-ndk16b"
    __ABI_ARM64_V8A_CXX14 = "arm64-v8a-cxx14"
    __ABI_X86_CXX14 = "x86-cxx14"
    __ABI_X86_64_CXX14 = "x86_64-cxx14"

    ABI_TOOLCHAIN_TABLE = {
        __ABI_ARMEABI_V7A: "android-ndk-r13b-api-15-armeabi-v7a-neon",
        __ABI_ARMEABI: "android-ndk-r13b-api-15-armeabi",
        __ABI_ARM64_V8A:   "android-ndk-r13b-api-21-arm64-v8a",
        __ABI_X86: "android-ndk-r13b-api-15-x86",
        __ABI_X86_64: "android-ndk-r13b-api-21-x86-64",
        __ABI_ARMEABI_V7A_CXX14_NDK16B: "android-ndk-r16b-api-21-armeabi-v7a-neon-clang-libcxx14",
        __ABI_ARMEABI_V7A_CXX14: "android-ndk-r13b-api-15-armeabi-v7a-neon-cxx14",
        __ABI_ARMEABI_CXX14: "android-ndk-r13b-api-15-armeabi-cxx14",
        __ABI_ARM64_V8A_CXX14_NDK16B: "android-ndk-r16b-api-21-arm64-v8a-neon-clang-libcxx14",
        __ABI_ARM64_V8A_CXX14:   "android-ndk-r13b-api-21-arm64-v8a-cxx14",
        __ABI_X86_CXX14: "android-ndk-r13b-api-15-x86-cxx14",
        __ABI_X86_64_CXX14: "android-ndk-r13b-api-21-x86-64-cxx14",
    }

    # 要支持 Address Sanitizer，NDK 版本不能太低，但目前我们 SDK 编译使用的是 r13b，待 SDK 编译升级 NDK 为 >= r16b 时，可以不用此变量
    ABI_TOOLCHAIN_TABLE_WITH_r16b = {
        __ABI_ARMEABI_V7A: "android-ndk-r16b-api-21-armeabi-v7a-neon-clang-libcxx",
        __ABI_ARMEABI: "android-ndk-r16b-api-21-armeabi-clang-libcxx",
        __ABI_ARM64_V8A: "android-ndk-r16b-api-21-arm64-v8a-neon-clang-libcxx",
        __ABI_X86: "android-ndk-r16b-api-21-x86-clang-libcxx",
        __ABI_X86_64: "android-ndk-r16b-api-21-x86-64-clang-libcxx"
    }

    ABI_TOOLCHAIN_TABLE_WITH_r21d = {
        __ABI_ARMEABI_V7A: "android-ndk-r21d-api-19-armeabi-v7a-neon-clang",
        __ABI_ARM64_V8A: "android-ndk-r21d-api-21-arm64-v8a-clang",
        __ABI_X86: "android-ndk-r21d-api-19-x86-clang",
        __ABI_X86_64: "android-ndk-r21d-api-21-x86-64-clang"
    }

    BIN_TRIP_TABLE = {
        __ABI_ARMEABI_V7A_CXX14_NDK16B: "{}/toolchains/arm-linux-androideabi-4.9/prebuilt/{}-x86_64/bin/arm-linux-androideabi-strip --strip-unneeded ".format(NDK_PATH, osutil.get_current_os_name().lower()),
        __ABI_ARMEABI_V7A: "{}/toolchains/arm-linux-androideabi-4.9/prebuilt/{}-x86_64/bin/arm-linux-androideabi-strip --strip-unneeded ".format(NDK_PATH, osutil.get_current_os_name().lower()),
        __ABI_ARMEABI: "{}/toolchains/arm-linux-androideabi-4.9/prebuilt/{}-x86_64/bin/arm-linux-androideabi-strip --strip-unneeded ".format(NDK_PATH, osutil.get_current_os_name().lower()),
        __ABI_ARM64_V8A: "{}/toolchains/aarch64-linux-android-4.9/prebuilt/{}-x86_64/bin/aarch64-linux-android-strip --strip-unneeded ".format(NDK_PATH, osutil.get_current_os_name().lower()),
        __ABI_ARM64_V8A_CXX14_NDK16B:"{}/toolchains/aarch64-linux-android-4.9/prebuilt/{}-x86_64/bin/aarch64-linux-android-strip --strip-unneeded ".format(NDK_PATH, osutil.get_current_os_name().lower()),
        __ABI_X86: "{}/toolchains/x86-4.9/prebuilt/{}-x86_64/bin/i686-linux-android-strip --strip-unneeded".format(NDK_PATH, osutil.get_current_os_name().lower()),
        __ABI_X86_64: "{}/toolchains/x86_64-4.9/prebuilt/{}-x86_64/bin/x86_64-linux-android-strip --strip-unneeded".format(NDK_PATH, osutil.get_current_os_name().lower())
    }


class IOS(object):
    BUILD_TYPE_TABLE_NO_PLUS = {'dynamic': "dynamic framework",
                                  'static': "static framework",
                                  'no_ffmpeg': "no ffmpeg static framework"
                                }

    BUILD_TYPE_TABLE_WITH_PLUS = BUILD_TYPE_TABLE_NO_PLUS.copy()
    BUILD_TYPE_TABLE_WITH_PLUS['plus'] = "c++ interface dynamic framework"
    BUILD_TYPE_TABLE_WITH_PLUS['plus_static'] = "c++ interface static framework"


class WINDOWS(object):
    __ARCH_X86 = "x86"
    __ARCH_X64 = "x64"
    __ARCH_X86_XP = "x86_xp"
    __ARCH_X64_XP = "x64_xp"
    __ARCH_X86_CXX14 = "x86-cxx14"
    __ARCH_X64_CXX14 = "x64-cxx14"
    __ARCH_X86_V142 = "x86-v142"
    __ARCH_X64_V142 = "x64-v142"
    __ARCH_X86_XP_V142 = "x86_xp-v142"
    __ARCH_X64_XP_V142 = "x64_xp-v142"
    __ARCH_X64_VS14_LLVM = "x64-vs14-llvm"

    ARCH_TOOLCHAIN_TABLE = {
        __ARCH_X86: "vs-14-2015",
        __ARCH_X64: "vs-14-2015-win64",
        __ARCH_X86_XP: "vs-14-2015-xp",
        __ARCH_X64_XP: "vs-14-2015-win64-xp",
        __ARCH_X86_CXX14: "vs-15-2017",
        __ARCH_X64_CXX14: "vs-15-2017-win64",
        __ARCH_X86_V142: "vs-16-2019",
        __ARCH_X64_V142: "vs-16-2019-win64",
        __ARCH_X86_XP_V142: "vs-16-2019-xp",
        __ARCH_X64_XP_V142: "vs-16-2019-win64-xp",
        __ARCH_X64_VS14_LLVM: "vs-14-2015-win64-llvm-vs2014"
    }


class LINUX(object):
    ARCH_X86 = "x86"
    ARCH_X86_64 = "x86_64"
    ARCH_X86_CXX14 = "x86-cxx14"
    ARCH_X86_64_CXX14 = "x86_64-cxx14"

    ARCH_TOOLCHAIN_TABLE = {
        ARCH_X86: "gcc-linux",
        ARCH_X86_64: "gcc-linux",
        ARCH_X86_CXX14: "gcc-linux-cxx14",
        ARCH_X86_64_CXX14: "gcc-linux-cxx14",

    }

class OHOS(object):
    __ABI_ARMEABI_V7A = "armeabi-v7a"
    __ABI_ARM64_V8A = "arm64-v8a"
    __ABI_X86_64 = "x86_64"

    ABI_TOOLCHAIN_TABLE = {
        __ABI_ARMEABI_V7A: "ohos-sdk-native-armeabi-v7a",
        __ABI_ARM64_V8A:   "ohos-sdk-native-arm64-v8a",
        __ABI_X86_64:      "ohos-sdk-native-x86-64",
    }

class _InnerEmbedded(object):
    """
    将 PRODUCT_TOOLCHAIN_TABLE 直接定义在 EMBEDDED 类中通过 _register_toolchain 访问会产生：
     TypeError: 'staticmethod' object is not callable 错误，
    所以采用这种迂回方式来实现
    """
    PRODUCT_TOOLCHAIN_TABLE = {}

    @staticmethod
    def _register_toolchain(toolchain_table):
        for (key, value) in toolchain_table.items():
            _InnerEmbedded.PRODUCT_TOOLCHAIN_TABLE[key] = value


class EMBEDDED(_InnerEmbedded):
    _ALLWINNER_TOOLCHAIN_TABLE = {"r16": "allwinner-r16", "r328": "allwinner-r328"}
    _InnerEmbedded._register_toolchain(_ALLWINNER_TOOLCHAIN_TABLE)

    _HISI_TOOLCHAIN_TABLE = {"hi3531a_c01": "hisi-v300", "hi3531d_c01": "hisi-v500", "hi3531d_c02": "hisi-v600",
                             "hi3536": "hisi-v300", "hi3516d": "hisi-himix200", "hi3559v200": "hisi-himix100",
                             "hi3561a": "hisi-v610"}
    _InnerEmbedded._register_toolchain(_HISI_TOOLCHAIN_TABLE)

    _ROCKCHIP_TOOLCHAIN_TABLE = {"px3se": "rockchip-px3se", "rk356x": "rockchip-rk356x", "rk3399k": "rockchip-rk3399k", "rv1126_rv1109": "rockchip-rv1126_rv1109"}
    _InnerEmbedded._register_toolchain(_ROCKCHIP_TOOLCHAIN_TABLE)

    _NOVATEK_TOOLCHAIN_TABLE = {"24kec": "novatek-24kec"}
    _InnerEmbedded._register_toolchain(_NOVATEK_TOOLCHAIN_TABLE)

    _INGENIC_TOOLCHAIN_TABLE = {"camera": "ingenic-camera"}
    _InnerEmbedded._register_toolchain(_INGENIC_TOOLCHAIN_TABLE)

    # 目前树莓派所有型号的 soc 都是使用的同一份交叉编译工具链
    _RASPBERRYPI_TOOLCHAIN_TABLE = {"bcm2837": "raspberrypi-bcm2837","rpi32": "linux-gcc-armhf", "rpi3b64bit": "linux-gcc-aarch64-lp64"}
    _InnerEmbedded._register_toolchain(_RASPBERRYPI_TOOLCHAIN_TABLE)

    _NEOWAY_TOOLCHAIN_TABLE = {"mdm9607": "neoway-mdm9607"}
    _InnerEmbedded._register_toolchain(_NEOWAY_TOOLCHAIN_TABLE)

    # v7.3.1 是给上汽的；v5.5.0 是给君和睿通、全视通及赛赛的; v4.9.4 是给北京特微智能科技的
    _LINARO_TOOLCHAIN_TABLE = {
        "v4.9.4": "linaro-v4-9-4-arm", "v4.9.4-armhf": "linaro-v4-9-4-armhf",
        "v5.5.0": "linaro-v5-5-0-arm", "v5.5.0-armhf": "linaro-v5-5-0-armhf", "v5.5.0-aarch64": "linaro-v5-5-0-aarch64-linux-gnu",
        "v7.3.1": "linaro-v7-3-1-arm", "v7.3.1-armhf": "linaro-v7-3-1-armhf", "v7.3.1-aarch64": "linaro-v7-3-1-aarch64-linux-gnu"
        }
    _InnerEmbedded._register_toolchain(_LINARO_TOOLCHAIN_TABLE)

    _GOKEIC_TOOLCHAIN_TABLE = {"sgks6802": "gokeic-sgks6802"}
    _InnerEmbedded._register_toolchain(_GOKEIC_TOOLCHAIN_TABLE)

    # 上汽
    _ALIOS_TOOLCHAIN_TABLE = {"alios4_armhf": "alios-api-4-armhf", "alios4_arm64": "alios-api-4-arm64", "alios4_x86_64": "alios-api-4-x86_64"}
    _InnerEmbedded._register_toolchain(_ALIOS_TOOLCHAIN_TABLE)

    # 赛赛
    _MYIR_TOOLCHAIN_TABLE = {"am335x": "myir-am335x"}
    _InnerEmbedded._register_toolchain(_MYIR_TOOLCHAIN_TABLE)

    '''
    基于 Ubuntu 内置的 xxx-linux-gnu-g++，具体是 gcc-5.4.0 还是 gcc-9.3.0 还是其它版本，取决于安装的交叉编译工具链版本。
    其中 5.4.0 一般在 Ubuntu 16.xx 中安装，9.3.0 在 Ubuntu 20.04 中安装
    in Ubuntu 16.04
    apt install gcc-5-arm-linux-gnueabi g++-5-arm-linux-gnueabi \
        gcc-5-arm-linux-gnueabihf  g++-5-arm-linux-gnueabihf \
        gcc-5-aarch64-linux-gnu g++-5-aarch64-linux-gnu
    或 in Ubuntu 20.04
    apt install gcc-9-arm-linux-gnueabi g++-9-arm-linux-gnueabi \
        gcc-9-arm-linux-gnueabihf  g++-9-arm-linux-gnueabihf \
        gcc-9-aarch64-linux-gnu g++-9-aarch64-linux-gnu
    也可以不指定版本，让 apt 根据系统版本自动选择最优的（且必须安装）：
    apt install gcc-arm-linux-gnueabi g++-arm-linux-gnueabi \
        gcc-arm-linux-gnueabihf  g++-arm-linux-gnueabihf \
        gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

    必须安装 (pkg-config-xxx），否则 curl 编不过
    apt install pkg-config-aarch64-linux-gnu pkg-config-arm-linux-gnueabihf pkg-config-arm-linux-gnueabi
    '''
    _STANDARD_ARM_TOOLCHAIN_TABLE = {
        "standard_aarch64_linux_gnu": "linux-gcc-aarch64-lp64",
        "standard_arm_linux_gnueabihf": "linux-gcc-armhf",
        # "standard_arm_linux_gnueabi": "linux-gcc-arm"
    }
    _InnerEmbedded._register_toolchain(_STANDARD_ARM_TOOLCHAIN_TABLE)
