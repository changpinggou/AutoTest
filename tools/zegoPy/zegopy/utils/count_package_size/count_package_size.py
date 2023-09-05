import os
import sys
import json
import time
import argparse
import platform
import tempfile
import subprocess
from abc import ABCMeta,abstractmethod
from enum import Enum
from typing import Dict

from zegopy.common import io
from zegopy.common import ziputil
from zegopy.builder import jenkins_keychain_util
from zegopy.builder.downloader import SimpleDownloader
from zegopy.builder.zego_artifactory import ZegoArtifactory

THIS_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

class ZegoPlatformType(Enum):
    Android = 0
    iOS = 1
    macOS = 2
    Windows = 3
    Linux = 4

class Arch(Enum):
    ARM64 = 0,
    ARMV7 = 1,
    X86 = 2,
    X64 = 3

def count_package_size(platform: ZegoPlatformType, sdk_path: str, lib_path: str, arch: Arch) -> Dict:
    """统计 SDK 包大小 （只支持动态库，因为静态库无法计算增量）
    增量大小结果:
        Android/iOS: 集成 SDK 后的最简单的空项目 Demo 编译后二进制的大小 - 空项目直接编译的二进制的大小)
        桌面端: 整个动态库的大小

    Args:
        platform (ZegoPlatformType): 要测试的平台类型
        sdk_path (str): 待统计的 SDK 压缩包的路径, 支持 smb 或 http
        lib_path (str): 待统计的实际动态库 (framework/dylib/dll/so/jar) 在 zip 包中的相对路径
            例:
            1. iOS: "SDK/ZegoEffects.xcframework/ios-arm64_armv7/ZegoEffects.framework"
            2. Android: "ZegoExpressEngine-video-android-java"
            3. macOS: "product/ZegoLiveRoom/Release/ZegoLiveRoomOSX.framework"
            4. Win: "libs/x64"
        arch (Arch): 要测试的架构类型 (iOS 仅支持 arm64 / macOS 仅支持 x64)

    Returns:
        Dict: key: 架构名称, value: SDK 增量大小 (Byte) (possible key: armv7/arm64/x86/x64) example: {'arm64': 13111417}
    """

    counter = None
    if platform == ZegoPlatformType.Android:
        counter = CountAndroidPackageSize(arch)
    elif platform == ZegoPlatformType.iOS:
        counter = CountIOSPackageSize(arch)
    elif platform == ZegoPlatformType.macOS:
        counter = CountMacOSPackageSize(arch)
    elif platform == ZegoPlatformType.Windows:
        counter = CountWindowsPackageSize(arch)
    elif platform == ZegoPlatformType.Linux:
        counter = CountLinuxPackageSize(arch)
    else:
        raise Exception('[count_package_size] Unknown platform type: {}'.format(platform))

    result_map = counter.count_package_size(sdk_path, lib_path)

    print('[*] [CountPackageSize] Platform: {0}, Result: {1}'.format(platform, result_map))

    return result_map

class CountPackageSize(metaclass=ABCMeta):
    def __init__(self, arch: Arch) -> None:
        self.tmp_path = os.path.join(tempfile.gettempdir(), 'CountPackageSize', str(time.time()))
        os.makedirs(self.tmp_path)

    def download_sdk(self, artifact_url: str):
        if artifact_url.startswith('smb'):
            downloader = SimpleDownloader()
            artifact_path = downloader.download(artifact_url, self.tmp_path)
        elif artifact_url.startswith('http'):
            artifactory = ZegoArtifactory()
            artifact_path = artifactory.download(artifact_url, self.tmp_path)
        else:
            # 取本地路径的 zip
            if os.path.exists(artifact_url):
                artifact_path = artifact_url
            else:
                raise Exception('Illegal URL, or can not find it on local disk')
        ziputil.unzip_file(artifact_path, self.tmp_path)
        # zip_file_bare_name = os.path.split(artifact_url.split('?')[0])[-1][:-4]

    @abstractmethod
    def count_package_size(self, sdk_path: str, lib_path: str):
        pass


class CountAndroidPackageSize(CountPackageSize):
    def __init__(self, arch: Arch) -> None:
        super(CountAndroidPackageSize, self).__init__(arch)
        self.arch = arch
        self.android_project_path = os.path.join(THIS_SCRIPT_PATH, 'android', 'CountPackageSize')
        self.lib_folder_path = os.path.join(self.android_project_path, 'app', 'libs')
        self.gradle_path = os.path.join(self.android_project_path, 'app', 'build.gradle')
        self.apk_product_path = os.path.join(self.android_project_path, 'app/build/outputs/apk/release/app-release.apk')

    def count_package_size(self, sdk_path: str, lib_path: str):
        """统计 Android SDK 包大小（集成 APK 后相对于空项目的增量大小, 计算 arm64 + armv7）"""

        # 编译并获取未集成 SDK 的 APK 大小
        io.delete(self.lib_folder_path)
        self._build_apk()
        empty_apk_size = os.path.getsize(self.apk_product_path)
        print('\n[*] Empty apk size: {} MB\n'.format(round(empty_apk_size/1024/1024, 3)))

        # 拷贝 SDK 到目录中
        self._copy_sdk_and_move_to_test_project(sdk_path, lib_path)

        # 编译并获取集成指定架构 SDK 后的 APK 大小
        self._convert_build_gradle_arch(self.arch)
        self._build_apk()
        integrated_apk_size = os.path.getsize(self.apk_product_path)
        print('\n[*] Intergrated apk size: {} MB\n'.format(round(integrated_apk_size/1024/1024, 3)))

        # 恢复 build gradle
        self._convert_build_gradle_arch(Arch.ARM64)

        apk_increment_size = integrated_apk_size - empty_apk_size

        print('[*] [Count Android Package Size] [{}] APK Product Size: {} MB, SDK Increment Size: {} MB'.format(
            self.arch,
            round(integrated_apk_size/1024/1024, 3),
            round(apk_increment_size/1024/1024, 3)
        ))

        return {self.arch.name.lower(): apk_increment_size}

    def _copy_sdk_and_move_to_test_project(self, sdk_path: str, lib_path: str):
        """拷贝 SDK 并放置于 Android 测试工程的指定目录下"""

        self.download_sdk(sdk_path)
        io.copy_folder(os.path.join(self.tmp_path, lib_path), self.lib_folder_path, overwrite=True, symlinks=True)

    def _build_apk(self):
        """编译 Android 工程"""
        os.chdir(self.android_project_path)
        subprocess.check_call(['sh', 'gradlew', 'clean', 'assemblerelease'])

    def _convert_build_gradle_arch(self, arch: Arch):
        """重写覆盖 build.gradle 的 ndk abiFilters 架构类型
        Args: arch (str): 'arm64-v8a' or 'armeabi-v7a'
        """
        with open(self.gradle_path, 'r') as fr:
            content = fr.readlines()

        if arch == Arch.ARM64: arch_abi = 'arm64-v8a'
        elif arch == Arch.ARMV7: arch_abi = 'armeabi-v7a'
        elif arch == Arch.X86: arch_abi = 'x86'
        elif arch == Arch.X64: arch_abi = 'x86_64'
        else: raise Exception('Unknown android arch')

        with open(self.gradle_path, 'w') as fw:
            for line in content:
                if 'abiFilters' in line:
                    line = '        ndk {{ abiFilters \'{0}\' }}\n'.format(arch_abi)
                fw.write(line)


class CountIOSPackageSize(CountPackageSize):
    def __init__(self, arch: Arch) -> None:
        super(CountIOSPackageSize, self).__init__(arch)
        self.arch = arch
        if arch != Arch.ARM64:
            raise Exception('iOS only support arm64')
        self.xcode_project_path = os.path.join(THIS_SCRIPT_PATH, 'ios', 'CountPackageSize.xcodeproj')
        self.xcode_pbxproj_path = os.path.join(self.xcode_project_path, 'project.pbxproj')
        self.lib_folder_path = os.path.join(THIS_SCRIPT_PATH, 'ios', 'Libs')
        self.export_options_path = os.path.join(THIS_SCRIPT_PATH, 'ios', 'archive-export-options.plist')
        self.cache_xcarchive_path = os.path.join(self.tmp_path, 'cache', 'ios', 'CountPackageSize.xcarchive')
        self.exported_folder_path = os.path.join(self.tmp_path, 'bin', 'ios')
        self.exported_ipa_path = os.path.join(self.exported_folder_path, 'CountPackageSize.ipa')

    def count_package_size(self, sdk_path: str, lib_path: str):
        """统计 iOS SDK 包大小（集成 IPA 后相对于空项目的增量大小, 仅计算 arm64）"""

        if not lib_path.endswith('.framework'):
            raise Exception('iOS only support normal .framework')

        # 先构建空项目，计算包大小
        empty_ipa_path = self._build_ipa()
        empty_ipa_size = os.path.getsize(empty_ipa_path)
        print('\n[*] Empty ipa size: {} MB\n'.format(round(empty_ipa_size/1024/1024, 3)))

        # 计算待测试的 SDK 集成到 App 后的包大小
        framework_name = lib_path.split('/')[-1]
        self._copy_sdk_and_move_to_test_project(sdk_path, lib_path)
        self._change_xcodeproj_embeded_framework('EmptyTestLib.framework', framework_name)
        ipa_path = self._build_ipa()
        ipa_size = os.path.getsize(ipa_path)
        print('\n[*] Intergrated ipa size: {} MB\n'.format(round(ipa_size/1024/1024, 3)))

        ipa_increment_size = ipa_size - empty_ipa_size

        print('[*] [Count iOS Package Size] [{}] IPA Product Size: {} MB, SDK Increment Size: {} MB'.format(
            self.arch,
            round(ipa_size/1024/1024, 3),
            round(ipa_increment_size/1024/1024, 3)
        ))

        # Restore file
        self._change_xcodeproj_embeded_framework(framework_name, 'EmptyTestLib.framework')

        return {self.arch.name.lower(): ipa_increment_size}

    def _copy_sdk_and_move_to_test_project(self, sdk_path: str, lib_path: str):
        """拷贝 SDK 并放置于 Xcode 测试工程的指定目录下"""
        self.download_sdk(sdk_path)
        io.copy(os.path.join(self.tmp_path, lib_path), self.lib_folder_path, overwrite=True, symlinks=True)

    def _change_xcodeproj_embeded_framework(self, old_name: str, new_name: str):
        with open(self.xcode_pbxproj_path, 'r') as fr:
            lines = fr.readlines()
        with open(self.xcode_pbxproj_path, 'w') as fw:
            for line in lines:
                line = line.replace(old_name, new_name)
                fw.write(line)

    def _build_ipa(self):
        """编译 Xcode 工程"""
        # 在 Slave 编译机上运行时需要解锁 Keychain
        jenkins_keychain_util.unlock_keychain_if_need()

        # Archive
        archive_cmd = ['arch', '-arm64'] if 'arm64' in platform.machine() else []
        archive_cmd.extend(['xcrun', 'xcodebuild', 'archive', '-allowProvisioningUpdates',
            '-destination', 'generic/platform=iOS', '-project', self.xcode_project_path,
            '-scheme', 'CountPackageSize', '-archivePath', self.cache_xcarchive_path])
        print('\n[*] Execute command: {}'.format(archive_cmd))
        subprocess.check_call(archive_cmd)

        # Export
        export_cmd = ['arch', '-arm64']if 'arm64' in platform.machine() else []
        export_cmd.extend(['xcrun', 'xcodebuild', '-exportArchive', '-allowProvisioningUpdates',
            '-archivePath', self.cache_xcarchive_path, '-exportPath', self.exported_folder_path,
            '-exportOptionsPlist', self.export_options_path])
        print('\n[*] Execute command: {}'.format(export_cmd))
        subprocess.check_call(export_cmd)

        return self.exported_ipa_path


class CountMacOSPackageSize(CountPackageSize):
    # 暂时直接统计将 Framework 打包到 DMG 后的大小
    # 因为构建 App 时不会压缩 Framework ，而是仅仅干掉了头文件，可以忽略不计
    def __init__(self, arch: Arch) -> None:
        super(CountMacOSPackageSize, self).__init__(arch)
        self.arch = arch
        if arch != Arch.X64:
            raise Exception('macOS only support x86_64')
        self.xcode_project_path = os.path.join(THIS_SCRIPT_PATH, 'macos', 'CountPackageSize.xcodeproj')
        self.xcode_pbxproj_path = os.path.join(self.xcode_project_path, 'project.pbxproj')
        self.lib_folder_path = os.path.join(THIS_SCRIPT_PATH, 'macos', 'Libs')
        self.export_options_path = os.path.join(THIS_SCRIPT_PATH, 'macos', 'archive-export-options.plist')
        self.cache_xcarchive_path = os.path.join(self.tmp_path, 'cache', 'macos', 'CountPackageSize.xcarchive')
        self.exported_folder_path = os.path.join(self.tmp_path, 'bin', 'macos')
        self.exported_app_path = os.path.join(self.exported_folder_path, 'CountPackageSize.app')
        self.dmg_path = os.path.join(self.exported_folder_path, 'CountPackageSize.dmg')

    def count_package_size(self, sdk_path: str, lib_path: str):
        """统计 macOS SDK 包大小（集成 app 后相对于空项目的增量大小, 仅计算 x86_64）"""

        if not lib_path.endswith('.framework'):
            raise Exception('macOS only support normal .framework')

        # 先构建空项目，计算包大小
        self._build_dmg()
        empty_dmg_size = os.path.getsize(self.dmg_path)
        print('\n[*] Empty dmg size: {} MB\n'.format(round(empty_dmg_size/1024/1024, 3)))

        # 计算待测试的 SDK 集成到 App 后的包大小
        framework_name = lib_path.split('/')[-1]
        self._copy_sdk_and_move_to_test_project(sdk_path, lib_path)
        self._change_xcodeproj_embeded_framework('EmptyTestLib.framework', framework_name)
        self._strip_framework_archs(os.path.join(self.lib_folder_path, framework_name))
        self._build_dmg()
        dmg_size = os.path.getsize(self.dmg_path)
        print('\n[*] Intergrated dmg size: {} MB\n'.format(round(dmg_size/1024/1024, 3)))

        dmg_increment_size = dmg_size - empty_dmg_size

        print('[*] [Count macOS Package Size] [{}] DMG Product Size: {} MB, SDK Increment Size: {} MB'.format(
            self.arch,
            round(dmg_size/1024/1024, 3),
            round(dmg_increment_size/1024/1024, 3)
        ))

        # Restore file
        self._change_xcodeproj_embeded_framework(framework_name, 'EmptyTestLib.framework')

        return {self.arch.name.lower(): dmg_increment_size}

    def _copy_sdk_and_move_to_test_project(self, sdk_path: str, lib_path: str):
        """拷贝 SDK 并放置于 Xcode 测试工程的指定目录下"""
        self.download_sdk(sdk_path)
        io.copy(os.path.join(self.tmp_path, lib_path), self.lib_folder_path, overwrite=True, symlinks=True)

    def _strip_framework_archs(self, framework_path: str):
        # 移除可能存在的 arm64 架构，仅需要 x86_64
        framework_name = framework_path.split('/')[-1][:-len('.framework')]
        framework_bin_path = os.path.join(framework_path, 'Versions', 'A', framework_name)
        subprocess.check_call(['lipo', '-remove', 'arm64', '-output', framework_bin_path, framework_bin_path])

    def _change_xcodeproj_embeded_framework(self, old_name: str, new_name: str):
        with open(self.xcode_pbxproj_path, 'r') as fr:
            lines = fr.readlines()
        with open(self.xcode_pbxproj_path, 'w') as fw:
            for line in lines:
                line = line.replace(old_name, new_name)
                fw.write(line)

    def _build_dmg(self):
        """编译 Xcode 工程"""
        # 在 Slave 编译机上运行时需要解锁 Keychain
        jenkins_keychain_util.unlock_keychain_if_need()

        # Archive
        archive_cmd = ['arch', '-arm64'] if 'arm64' in platform.machine() else []
        archive_cmd.extend(['xcrun', 'xcodebuild', 'archive', '-allowProvisioningUpdates',
            '-destination', 'generic/platform=macOS', '-project', self.xcode_project_path,
            '-scheme', 'CountPackageSize', '-archivePath', self.cache_xcarchive_path])
        print('\n[*] Execute command: {}'.format(archive_cmd))
        subprocess.check_call(archive_cmd)

        # Export
        export_cmd = ['arch', '-arm64'] if 'arm64' in platform.machine() else []
        export_cmd.extend(['xcrun', 'xcodebuild', '-exportArchive', '-allowProvisioningUpdates',
            '-archivePath', self.cache_xcarchive_path, '-exportPath', self.exported_folder_path,
            '-exportOptionsPlist', self.export_options_path])
        print('\n[*] Execute command: {}'.format(export_cmd))
        subprocess.check_call(export_cmd)

        io.delete(self.dmg_path)
        create_dmg_cmd = ['create-dmg', '--no-internet-enable', '--hdiutil-quiet', '--sandbox-safe', self.dmg_path, self.exported_app_path]
        subprocess.check_call(create_dmg_cmd)

        return self.dmg_path

    def _copy_sdk_and_move_to_test_project(self, sdk_path: str, lib_path: str):
        """拷贝 SDK Framework 并放置于 macOS 目录下"""
        self.download_sdk(sdk_path)
        io.copy(os.path.join(self.tmp_path, lib_path), self.lib_folder_path, overwrite=True, symlinks=True)


class CountWindowsPackageSize(CountPackageSize):
    def __init__(self, arch: Arch) -> None:
        super(CountWindowsPackageSize, self).__init__(arch)
        self.arch = arch
        self.lib_folder_path = os.path.join(self.tmp_path, 'windows', 'lib')
        os.makedirs(self.lib_folder_path)

    def count_package_size(self, sdk_path: str, lib_path: str):
        """统计 Windows SDK 包大小（直接计算 .dll 和 .lib 的大小）"""

        self._copy_sdk_and_move_to_test_project(sdk_path, lib_path)

        dll_path = ''
        lib_path = ''
        for file_name in os.listdir(self.lib_folder_path):
            if file_name.endswith('.dll'):
                dll_path = os.path.join(self.lib_folder_path, file_name)
            if file_name.endswith('.lib'):
                lib_path = os.path.join(self.lib_folder_path, file_name)

        if not dll_path:
            raise Exception('Can not find any .dll file under %s' % self.lib_folder_path)
        if not lib_path:
            raise Exception('Can not find any .lib file under %s' % self.lib_folder_path)

        print('\n[*] DLL: {}, LIB: {}'.format(dll_path, lib_path))

        dll_size = os.path.getsize(dll_path)
        lib_size = os.path.getsize(lib_path)

        print('[*] [Count Windows Package Size] [{}] DLL Size: {} MB, LIB Size: {} MB, All Size: {} MB'.format(
            self.arch,
            round(dll_size/1024/1024, 3),
            round(lib_size/1024/1024, 3),
            round((dll_size+lib_size)/1024/1024, 3),
        ))
        return {self.arch.name.lower(): (dll_size+lib_size)}

    def _copy_sdk_and_move_to_test_project(self, sdk_path: str, lib_path: str):
        """拷贝 SDK 并放置于 Windows 目录下"""
        self.download_sdk(sdk_path)
        io.copy_folder(os.path.join(self.tmp_path, lib_path), self.lib_folder_path, overwrite=True, symlinks=True)


class CountLinuxPackageSize(CountPackageSize):
    def __init__(self, arch: Arch) -> None:
        super(CountLinuxPackageSize, self).__init__(arch)
        self.arch = arch
        self.lib_folder_path = os.path.join(self.tmp_path, 'linux', 'lib')
        os.makedirs(self.lib_folder_path)

    def count_package_size(self, sdk_path: str, lib_path: str):
        """统计 Linux SDK 包大小（直接计算 .so 的大小）"""

        self._copy_sdk_and_move_to_test_project(sdk_path, lib_path)

        so_path = ''
        for file_name in os.listdir(self.lib_folder_path):
            if file_name.endswith('.so'):
                so_path = os.path.join(self.lib_folder_path, file_name)

        if not so_path:
            raise Exception('Can not find any .so file under %s' % self.lib_folder_path)
        print('\n[*] .SO: %s' % so_path)
        so_size = os.path.getsize(so_path)

        print('[*] [Count Linux Package Size] [{}] SO Size: {} MB'.format(
            self.arch,
            round(so_size/1024/1024, 3),
        ))
        return {self.arch.name.lower(): so_size}

    def _copy_sdk_and_move_to_test_project(self, sdk_path: str, lib_path: str):
        """拷贝 SDK (.so 本体) 并放置于 Linux 目录下"""
        self.download_sdk(sdk_path)
        io.copy(os.path.join(self.tmp_path, lib_path), self.lib_folder_path, overwrite=True, symlinks=True)


def main(argv):
    parser = argparse.ArgumentParser(description='The root build script.')
    parser.add_argument('os', type=str, choices=['android', 'ios', 'mac', 'win', 'linux'])
    parser.add_argument('sdk_path', type=str, help='SDK zip path, smb or http or local path')
    parser.add_argument('lib_path', type=str, help='Target library related path in the zip, e.g. "release/x64"')
    parser.add_argument('arch', type=str, choices=['armv7', 'arm64', 'x86', 'x64'])
    args = parser.parse_args(argv[1:])

    if args.os == 'android': platform = ZegoPlatformType.Android
    elif args.os == 'ios': platform = ZegoPlatformType.iOS
    elif args.os == 'mac': platform = ZegoPlatformType.macOS
    elif args.os == 'win': platform = ZegoPlatformType.Windows
    elif args.os == 'linux': platform = ZegoPlatformType.Linux

    if args.arch =='armv7': arch = Arch.ARMV7
    elif args.arch =='arm64': arch = Arch.ARM64
    elif args.arch =='x86': arch = Arch.X86
    elif args.arch =='x64': arch = Arch.X64

    size_result = count_package_size(platform, args.sdk_path, args.lib_path, arch)
    with open(os.path.join(THIS_SCRIPT_PATH, '_output.json'), 'w') as f:
        json.dump({'key': args.sdk_path, 'value': size_result}, f, indent=4)
    print('\n[*] Success! ^_^')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

    # 使用方式：在你自己的脚本中引用 count_package_size 函数，或使用 Jenkins 任务
    # http://ci.zego.cloud/job/native_common/job/count_package_size/

    # 调用示例

    # Android
    # count_package_size(ZegoPlatformType.Android, 'https://artifact-master.zego.cloud/generic/express/public/express_native/stable/video/android-java/ZegoExpressEngine-video-android-java.zip?version=2.9.4.2209', 'ZegoExpressEngine-video-android-java', Arch.ARM64)

    # iOS
    # count_package_size(ZegoPlatformType.iOS, 'smb://192.168.1.3/share/zego_sdk/zegoliveroom_release_new/zegoliveroom_210723_212634_release-new-0-gcbdb20077f_bn4256_12_video_mediaplayer/ios/zegoliveroom_210723_212634_release-new-0-gcbdb20077f_bn4256_12_video_mediaplayer_ios.zip', 'Release/iphoneos/ZegoLiveRoom.framework', Arch.ARM64)

    #macOS
    # count_package_size(ZegoPlatformType.macOS, 'https://artifact-master.zego.cloud/generic/express/public/express_native/stable/video/mac-objc/ZegoExpressEngine-video-mac-objc.zip?version=2.9.4.2141', 'ZegoExpressEngine-video-mac-objc/ZegoExpressEngine.xcframework/macos-arm64_x86_64/ZegoExpressEngine.framework', Arch.X64)

    # Windows
    # count_package_size(ZegoPlatformType.Windows, 'smb://192.168.1.3/share/zego_sdk/zegoliveroom_release_new/zegoliveroom_210722_170238_release-new-0-gcbdb20077f_bn4232_12_video_mediaplayer_win/windows/zegoliveroom_210722_170238_release-new-0-gcbdb20077f_bn4232_12_video_mediaplayer_win_dynamic.zip', 'libs/x86', Arch.X86)

    # Linux
    # count_package_size(ZegoPlatformType.Linux, 'https://artifact-master.zego.cloud/generic/express/public/express_native/stable/video/centos-cpp/ZegoExpressEngine-video-centos-cpp.zip?version=2.9.4.2141', 'ZegoExpressEngine-video-centos-cpp/x86_64/libZegoExpressEngine.so', Arch.X64)
