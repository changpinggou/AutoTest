#!/usr/bin/env python -u
# coding: utf-8

import os
import time
import shutil
import tempfile
import subprocess
from enum import Enum
from typing import List

"""
Script for creating XCFramework, it can handle the lipo steps

Support framework / dylib / static archive (.a)
"""

class LibType(Enum):
    FRAMEWORK = 0
    STATIC_ARCHIVE = 1
    SHARED_DYLIB = 2

class PlatformVariant(Enum):
    IOS_DEVICE = 0
    IOS_SIMULATOR = 1
    IOS_MACCATALYST = 2
    MACOS_DEVICE = 3
    WATCHOS_DEVICE = 4
    WATCHOS_SIMULATOR = 5
    TVOS_DEVICE = 6
    TVOS_SIMULATOR = 7

class Arch(Enum):
    ARM64 = 0,
    ARMV7 = 1,
    I386 = 2,
    X86_64 = 3

class Library:
    """
    Modle for a library (Framework / dylib+header / static(.a)+header)
    """
    def __init__(self, lib_type: LibType, arch: Arch, platform: PlatformVariant) -> None:
        self.lib_type: LibType = lib_type
        self.arch: List[Arch] = [arch]
        self.platform: PlatformVariant = platform
        self.lib_path: str = ''
        self.header_path: str = ''

    def set_lib_path(self, path: str):
        self.lib_path = path

    def set_header_path(self, path: str):
        assert self.lib_type != LibType.FRAMEWORK
        self.header_path = path


class XCFrameworkCreator:
    """
    Create the XCFramework by framework or dylib or static(.a)
    For usage info, please see the "main" function in this script
    """
    def __init__(self, lib_type: LibType, output_path: str) -> None:
        self.lib_type: LibType = lib_type
        self.lib_list: List[Library] = []
        self.output_path = output_path
        assert self.output_path.endswith('.xcframework')
        self.mac_framework_version = 'A'
        self.cache_dir = os.path.join(tempfile.gettempdir(), 'XCFrameworkCreator', str(time.time()))

    def override_default_mac_framework_version_string(self, version: str):
        # Default is "A", you can override it to your actual version
        self.mac_framework_version = version

    def _lipo_combine_binary(self, input_left: Library, input_right: Library) -> str:
        """
        Use lipo to combine 'input_left' binary and 'input_right' binary.
        output will be generated to /tmp/.../
        """
        base_name = input_left.lib_path.split('/')[-1]
        output_dir = os.path.join(self.cache_dir, str(time.time()))
        os.makedirs(output_dir)
        output_path = os.path.join(output_dir, base_name)
        lipo_create_cmd = ['xcrun', 'lipo', '-create']

        if self.lib_type == LibType.FRAMEWORK and \
            (input_left.platform == PlatformVariant.MACOS_DEVICE or \
            input_left.platform == PlatformVariant.IOS_MACCATALYST):
            shutil.copytree(input_right.lib_path, output_path, symlinks=True)
            target_name = base_name[:-len('.framework')]
            lipo_create_cmd.extend([
                '{0}/Versions/{1}/{2}'.format(input_left.lib_path, self.mac_framework_version, target_name),
                '{0}/Versions/{1}/{2}'.format(output_path, self.mac_framework_version, target_name),
                '-output',
                '{0}/Versions/{1}/{2}'.format(output_path, self.mac_framework_version, target_name)])
        elif self.lib_type == LibType.FRAMEWORK:
            shutil.copytree(input_right.lib_path, output_path, symlinks=True)
            target_name = base_name[:-len('.framework')]
            lipo_create_cmd.extend([
                '{}/{}'.format(input_left.lib_path, target_name),
                '{}/{}'.format(output_path, target_name), '-output',
                '{}/{}'.format(output_path, target_name)])
        else:
            lipo_create_cmd.extend([
                input_left.lib_path, input_right.lib_path,
                '-output', output_path])

        print('\n[*] Execute command: {}'.format(' '.join(lipo_create_cmd)))
        subprocess.check_call(lipo_create_cmd)
        return output_path

    def add_framework(self, framework_path: str, arch: Arch, platform_variant: PlatformVariant):
        """Add a single arch framework (support static or shared framework)
        """
        assert self.lib_type == LibType.FRAMEWORK
        new_lib = Library(self.lib_type, arch, platform_variant)
        new_lib.set_lib_path(framework_path)
        match = False
        for lib in self.lib_list:
            if new_lib.platform == lib.platform:
                if new_lib.arch[0] in lib.arch:
                    print('[XCFrameworkCreator] [ERROR] Duplicate arch for same platform variant: "{}", skip'.format(new_lib.lib_path))
                else:
                    fat_lib_path = self._lipo_combine_binary(lib, new_lib)
                    self.lib_list.remove(lib)

                    fat_lib = Library(self.lib_type, lib.arch + new_lib.arch, lib.platform)
                    fat_lib.set_lib_path(fat_lib_path)
                    self.lib_list.append(fat_lib)
                    match = True
                    break
        if not match:
            self.lib_list.append(new_lib)

    def add_fat_framework(self, framework_path: str, platform_variant: PlatformVariant):
        """Add a FAT framework, means a framework contains multiple archs
        Note: Only support the same variant in a FAT framwork,
            e.g. A framework contains arm64(deivce) + x64(simulator) is NOT SUPPORTED!
            e.g. A framework contains arm64(device) + armv7(device) is OK!
        """
        assert self.lib_type == LibType.FRAMEWORK
        new_lib = Library(self.lib_type, None, platform_variant)
        new_lib.set_lib_path(framework_path)
        self.lib_list.append(new_lib)

    def add_static_archive(self, lib_path: str, header_path: str, arch: Arch, platform_variant: PlatformVariant):
        """Add a single arch static library (.a) with headers
        """
        assert self.lib_type == LibType.STATIC_ARCHIVE
        new_lib = Library(self.lib_type, arch, platform_variant)
        new_lib.set_lib_path(lib_path)
        new_lib.set_header_path(header_path)
        match = False
        for lib in self.lib_list:
            if new_lib.platform == lib.platform:
                if new_lib.arch[0] in lib.arch:
                    print('[XCFrameworkCreator] [ERROR] Duplicate arch for same platform variant: "{}", skip'.format(new_lib.lib_path))
                else:
                    fat_lib_path = self._lipo_combine_binary(lib, new_lib)
                    self.lib_list.remove(lib)

                    fat_lib = Library(self.lib_type, lib.arch + new_lib.arch, lib.platform)
                    fat_lib.set_lib_path(fat_lib_path)
                    fat_lib.set_header_path(header_path)
                    self.lib_list.append(fat_lib)
                    match = True
                    break
        if not match:
            self.lib_list.append(new_lib)

    def add_fat_static_archive(self, lib_path: str, header_path: str, platform_variant: PlatformVariant):
        """Add a FAT static library with headers
        Note: Only support the same variant in a FAT library
        """
        assert self.lib_type == LibType.STATIC_ARCHIVE
        new_lib = Library(self.lib_type, None, platform_variant)
        new_lib.set_lib_path(lib_path)
        new_lib.set_header_path(header_path)
        self.lib_list.append(new_lib)

    def add_shared_dylib(self, lib_path: str, header_path: str, arch: Arch, platform_variant: PlatformVariant):
        """Add a single arch shared dylib with headers
        """
        assert self.lib_type == LibType.SHARED_DYLIB
        new_lib = Library(self.lib_type, arch, platform_variant)
        new_lib.set_lib_path(lib_path)
        new_lib.set_header_path(header_path)
        match = False
        for lib in self.lib_list:
            if new_lib.platform == lib.platform:
                if new_lib.arch[0] in lib.arch:
                    print('[XCFrameworkCreator] [ERROR] Duplicate arch for same platform variant: "{}", skip'.format(new_lib.lib_path))
                else:
                    fat_lib_path = self._lipo_combine_binary(lib, new_lib)
                    self.lib_list.remove(lib)

                    fat_lib = Library(self.lib_type, lib.arch + new_lib.arch, lib.platform)
                    fat_lib.set_lib_path(fat_lib_path)
                    fat_lib.set_header_path(header_path)
                    self.lib_list.append(fat_lib)
                    match = True
                    break
        if not match:
            self.lib_list.append(new_lib)

    def add_fat_shared_dylib(self, lib_path: str, header_path: str, platform_variant: PlatformVariant):
        """Add a FAT shared dylib with headers
        Note: Only support the same variant in a FAT library
        """
        assert self.lib_type == LibType.SHARED_DYLIB
        new_lib = Library(self.lib_type, None, platform_variant)
        new_lib.set_lib_path(lib_path)
        new_lib.set_header_path(header_path)
        self.lib_list.append(new_lib)

    def generate(self, clear_cache=True):
        """Do the actual xcodebuild command with all libraries
        Args:
            clear_cache (bool, optional): Whether to clear cache files. Defaults to True.
        """
        xcframework_cmd = ['xcrun', 'xcodebuild', '-create-xcframework']
        for lib in self.lib_list:
            if self.lib_type == LibType.FRAMEWORK:
                xcframework_cmd.extend(['-framework', lib.lib_path])
            elif self.lib_type == LibType.SHARED_DYLIB or self.lib_type == LibType.STATIC_ARCHIVE:
                xcframework_cmd.extend(['-library', lib.lib_path, '-headers', lib.header_path])
        xcframework_cmd.extend(['-output', self.output_path])
        print('\n[*] Execute command: {}'.format(' '.join(xcframework_cmd)))
        subprocess.check_call(xcframework_cmd)
        if clear_cache:
            shutil.rmtree(self.cache_dir, ignore_errors=True)


if __name__ == "__main__":

    # 调用示例

    # 示例一： 通过静态库创建 XCFramework （都是单架构的 .a）
    out = './tomcrypt.xcframework'
    creator = XCFrameworkCreator(LibType.STATIC_ARCHIVE, out)
    creator.add_static_archive(
        './arm/libtomcrypt.a', './arm/include',
        Arch.ARMV7, PlatformVariant.IOS_DEVICE)
    creator.add_static_archive(
        './arm64/libtomcrypt.a', './arm64/include',
        Arch.ARM64, PlatformVariant.IOS_DEVICE)
    creator.add_static_archive(
        './arm64-simulator/libtomcrypt.a', './arm64-simulator/include',
        Arch.ARM64, PlatformVariant.IOS_SIMULATOR)
    creator.add_static_archive(
        './x64-simulator/libtomcrypt.a', './x64-simulator/include',
        Arch.X86_64, PlatformVariant.IOS_SIMULATOR)
    creator.add_static_archive(
        './arm64-catalyst/libtomcrypt.a', './arm64-catalyst/include',
        Arch.ARM64, PlatformVariant.IOS_MACCATALYST)
    creator.add_static_archive(
        './x64-catalyst/libtomcrypt.a', './x64-catalyst/include',
        Arch.X86_64, PlatformVariant.IOS_MACCATALYST)
    creator.generate()

    # 示例二： 通过 FAT 静态库创建 XCFramework (确保单个 FAT 静态库仅包含一种变种，例如 真机 armv7+arm64 双架构的库，不允许真机+模拟器架构合并的库)
    out = './tomcrypt.xcframework'
    creator = XCFrameworkCreator(LibType.STATIC_ARCHIVE, out)
    creator.add_fat_static_archive('./arm64_armv7-device/libtomcrypt.a', './arm64_armv7-device/include', PlatformVariant.IOS_DEVICE)
    creator.add_fat_static_archive('./x64_x86_arm64-simulator/libtomcrypt.a', './x64_x86_arm64-simulator/include', PlatformVariant.IOS_SIMULATOR)
    creator.add_fat_static_archive('./x64_arm64-catalyst/libtomcrypt.a', './x64_arm64-catalyst/include', PlatformVariant.IOS_SIMULATOR)
    creator.generate()

    # 示例三： 通过单架构 dylib 动态库创建 XCFramework
    out = './ZegoEffects.xcframework'
    creator = XCFrameworkCreator(LibType.SHARED_DYLIB, out)
    creator.add_shared_dylib('./arm64/libZegoEffects.dylib', './arm64/include', Arch.ARM64, PlatformVariant.MACOS_DEVICE)
    creator.add_shared_dylib('./x64/libZegoEffects.dylib', './x64/include', Arch.X86_64, PlatformVariant.MACOS_DEVICE)
    creator.generate(clear_cache=False)

    # 示例四： 通过 FAT dylib 动态库创建 XCFramework (确保单个 FAT 静态库仅包含一种变种，例如 真机 armv7+arm64 双架构的库，不允许真机+模拟器架构合并的库)
    out = './ZegoEffects.xcframework'
    creator = XCFrameworkCreator(LibType.SHARED_DYLIB, out)
    creator.add_fat_shared_dylib('./arm64_x64/libZegoEffects.dylib', './arm64/include', PlatformVariant.MACOS_DEVICE)
    creator.generate(clear_cache=False)

    # 示例五： 通过单架构 Framework 创建 XCFramework
    out = './ZegoEffects.xcframework'
    creator = XCFrameworkCreator(LibType.FRAMEWORK, out)
    # 如果你的 macOS Framework 的 Version 字段不是 A，调用此方法修改
    creator.override_default_mac_framework_version_string('A')
    creator.add_framework('./arm64/ZegoEffects.framework', Arch.ARM64, PlatformVariant.MACOS_DEVICE)
    creator.add_framework('./x64/ZegoEffects.framework', Arch.X86_64, PlatformVariant.MACOS_DEVICE)
    creator.generate()

    # 示例六： 通过 FAT Framework 创建 XCFramework (确保单个 FAT 静态库仅包含一种变种，例如 真机 armv7+arm64 双架构的库，不允许真机+模拟器架构合并的库)
    out = './ZegoEffects.xcframework'
    creator = XCFrameworkCreator(LibType.FRAMEWORK, out)
    # 如果你的 macOS Framework 的 Version 字段不是 A，调用此方法修改
    creator.override_default_mac_framework_version_string('A')
    creator.add_fat_framework('./arm64_x64/ZegoEffects.framework', PlatformVariant.MACOS_DEVICE)
    creator.generate()
