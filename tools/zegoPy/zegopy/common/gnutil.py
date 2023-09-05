#!/usr/bin/env python3
# coding: utf-8

"""
This script contains some useful functions for GN (Generate Ninja) build script
"""

import os
import shutil
import sys
import argparse
import subprocess
from zegopy.common import osutil
from typing import Dict, List, Tuple


def get_build_target_dir(root_path: str, target_os: str, lib_type: str, build_lang: str) -> str:
    """Get GN output target dir (intermediate dir),
        needs to append "build_type" and "cpu" to this return value

        Note: Our purpose of putting this function in this public
            repo is to unify the output directory path of each project

    Args:
        root_path (str): Project root path
        target_os (str): android/ios/mac/win/...
        lib_type (str): "shared" or "static"
        build_lang (str): c/cpp/objc/java/...

    Returns:
        str: The intermediate target output dir path
    """
    return os.path.join(root_path, '_out',
        '{0}-{1}-{2}'.format(target_os, lib_type, build_lang))


def get_abi_from_cpu(target_os: str, cpu: str, short=False) -> str:
    """Get the platform-specific abi naming of the cpu architecture

    Args:
        target_os (str): android/ios/mac/win/...
        cpu (str): arm/arm64/x86/x64/arm64-simulator/x64-catalyst...
        short (bool): Param for arch variant, e.g. iOS x64-simulator,
            True: return 'x86_64', False: return 'x86_64-simulator'

    Returns:
        str: The platform-specific abi naming of the cpu architecture
    """
    if cpu == 'arm':
        if target_os == 'ios' or target_os == 'mac':
            return 'armv7'
        elif target_os == 'android':
            return 'armeabi-v7a'
        elif target_os == 'win':
            return 'arm'
        elif target_os == 'linux':
            return 'armv7'
        else:
            return cpu

    elif cpu == 'arm64':
        if target_os == 'ios' or target_os == 'mac':
            return 'arm64'
        elif target_os == 'android':
            return 'arm64-v8a'
        elif target_os == 'win':
            return 'arm64'
        elif target_os == 'linux':
            return 'arm64'
        else:
            return cpu

    elif cpu == 'x86':
        if target_os == 'ios' or target_os == 'mac':
            return 'i386'
        elif target_os == 'android':
            return 'x86'
        elif target_os == 'win':
            return 'x86'
        elif target_os == 'linux':
            return 'x86'
        else:
            return cpu

    elif cpu == 'x64':
        if target_os == 'ios' or target_os == 'mac':
            return 'x86_64'
        elif target_os == 'android':
            return 'x86_64'
        elif target_os == 'win':
            return 'x64'
        elif target_os == 'linux':
            return 'x86_64'
        else:
            return cpu

    elif cpu.endswith('-simulator'):
        suffix = '-simulator' if not short else ''
        return get_abi_from_cpu(target_os, cpu[:-len('-simulator')]) + suffix

    elif cpu.endswith('-catalyst'):
        suffix = '-catalyst' if not short else ''
        return get_abi_from_cpu(target_os, cpu[:-len('-catalyst')]) + suffix

    else: # Unknown cpu
        return cpu


def get_cpu_from_abi(target_os: str, abi: str) -> str:
    """Get the common cpu architecture of the platform-specific abi naming

    Args:
        target_os (str): android/ios/mac/win/...
        abi (str): armeabi-v7a/arm64-v8a/arm64/x86_64/...

    Returns:
        str: The cpu architecture naming
    """
    android_map = {
        'armeabi': 'arm',
        'armeabi-v7a': 'arm',
        'arm64-v8a': 'arm64',
        'x86': 'x86',
        'x86_64': 'x64',
    }

    apple_map = {
        'armv7': 'arm',
        'armv7s': 'arm',
        'arm64': 'arm64',
        'arm64e': 'arm64',
        'i386': 'x86',
        'x86_64': 'x64',
    }

    if target_os == 'android':
        return android_map[abi]
    elif target_os == 'ios' or target_os == 'mac':
        return apple_map[abi]
    elif target_os == 'win':
        return abi # The Windows ABI is the same as cpu arch
    else:
        return abi # TODO: Process other platform


def get_cpu_list_and_build_lang(args) -> Tuple[List[str], str]:
    """Parse argument object to get cpu list and build lang
    Args:
        args (argparse.NameSpace): Arguments object
    Returns:
        Tuple[List[str], str]: (cpu_list, build_lang)
    """
    cpu_list, lang = [], ''
    try:
        target_os = getattr(args, 'target_os')
        cpu_list = getattr(args, '%s_cpu' % target_os)
        lang = getattr(args, '%s_lang' % target_os)
    except Exception as e:
        raise Exception("[ERROR] Unknown args: %s" % e)
    return (cpu_list, lang)


def get_os_name(target_os: str) -> str:
    """Get a standard OS name by GN "target_os" value
    """
    if target_os == 'android':
        return 'Android'
    elif target_os == 'ios':
        return 'iOS'
    elif target_os == 'mac':
        return 'macOS'
    elif target_os == 'win':
        return 'Windows'
    elif target_os == 'linux':
        return 'Linux'
    raise Exception('Unknown "target_os": %s' % target_os)


def gn_args_to_command_line_args(gn_args: Dict) -> List[str]:
    def merge(key, value):
        if type(value) is int:
            return '%s=%s' % (key, value)
        if type(value) is bool:
            return '%s=%s' % (key, 'true' if value else 'false')
        if type(value) is list:
            return '%s=[%s]' % (key, ','.join('"%s"' % v for v in value))
        if type(value) is str and (value.lower()=='true' or value.lower()=='false'):
            return '%s=%s' % (key, value.lower())
        return '%s="%s"' % (key, value)
    return [merge(x, y) for x, y in gn_args.items()]

################################
### GN Runner Implementation ###
################################

def get_default_gn_args(build_type: str, cpu: str, target_os: str, target_os_variant: str) -> Dict:
    """Configure the default gn args for invoking the 'gn gen'
    This function only handle the common situation,
    so you have to configure other gn args you need,
    such as iOS/macOS deployment target, whether to enable iOS bitcode,
    whether to disable 'treat_warnings_as_errors' and so on.

    Args:
        build_type (str): ['release', 'debug']
        cpu (str): The target_cpu, if iOS, it needs variant suffix
        target_os (str): ['android', 'ios', 'mac', 'win', 'linux']
        target_os_variant (str): If linux, need to set

    Returns:
        Dict: The gn args map
    """
    gn_args = {}
    gn_args['is_official_build'] = build_type == 'release'
    gn_args['target_os'] = target_os
    gn_args['target_cpu'] = cpu.split('-')[0]
    gn_args['is_msan'] = False
    gn_args['is_asan'] = False
    gn_args['is_tsan'] = False
    gn_args['is_lsan'] = False
    gn_args['is_ubsan'] = False

    if target_os == 'android':
        gn_args['android32_ndk_api_level'] = 19 # aka Android 4.4
        gn_args['android_ndk_root'] = os.environ.get('ANDROID_NDK_HOME_r21d', '')
        gn_args['android_ndk_version'] = 'r21d'
        if build_type == 'debug':
            # Fix the issue that Android native code cannot be debugged.
            # Force set symbol_level to 2 (rich symbol), to makesure
            # the final ELF product contains enough debug information.
            #
            # Because the chromium product ELF size is too large (over 4GB)
            # and reach the 32bit system's limitation, although build for debug,
            # they also reduce the symbol_level ('-g1') then we cannot debug the code
            # So we force set symbol_level to 2 ('-g2') when building debug ELF
            gn_args['symbol_level'] = 2
            gn_args['ignore_elf32_limitations'] = True
            gn_args['android_full_debug'] = True

    elif target_os == 'ios':
        gn_args['ios_deployment_target'] = '9.0'
        gn_args['ios_app_bundle_id_prefix'] = 'im.zego'
        gn_args['ios_code_signing_identity_team_name'] = 'Zego'
        gn_args['ios_enable_code_signing'] = False
        gn_args['enable_dsyms'] = True # Always generating dsyms even debug
        if 'catalyst' in cpu:
            gn_args['target_environment'] = 'catalyst'
            gn_args['ios_deployment_target'] = '14.0' # We support MacCatalyst since macOS 11.0 (aka iOS 14.0)
        elif 'simulator' in cpu:
            gn_args['target_environment'] = 'simulator'
        else:
            gn_args['target_environment'] = 'device'

    elif target_os == 'mac':
        gn_args['mac_deployment_target'] = '10.11.0'
        gn_args['mac_app_bundle_id_prefix'] = 'im.zego'
        gn_args['enable_dsyms'] = True # Always generating dsyms even debug

    elif target_os == 'win':
        gn_args['is_clang'] = False # Use MSVC
        gn_args['enable_iterator_debugging'] = build_type == 'debug'
        gn_args['no_show_includes'] = True # Do not print huge useless log of "Include xxx"

    elif target_os == 'linux':
        gn_args['is_clang'] = False
        gn_args['is_cfi'] = False
        gn_args['use_glib'] = False
        gn_args['use_cxx11'] = True # Some embedded toolchain does not support c++14
        gn_args['linux_variant'] = target_os_variant
        if target_os_variant in ['ubuntu', 'centos']:
            gn_args['custom_toolchain'] = '//build/toolchain/linux:{}'.format(cpu)
            gn_args['use_sysroot'] = False # Do not use sysroot for native linux build
        else:
            gn_args['custom_toolchain'] = '//build/toolchain/linux/embedded/{}:{}'.format(target_os_variant, cpu)
            gn_args['host_toolchain'] = gn_args['custom_toolchain']
        if build_type == 'debug':
            gn_args['symbol_level'] = 2
            gn_args['ignore_elf32_limitations'] = True
    return gn_args


def invoke_gn_gen(proj_root: str, proj_name: str, target_os: str, out_dir: str, gn_build_dir: str, gn_args: Dict, gn_bin: str, ninja_bin: str, ide='default') -> int:
    """Run gn gen command to generate ninja build files

    Args:
        proj_root (str): Your project root directory path
        proj_name (str): Your project name, e.g. "ZIM" / "ZegoLiveRoom"
        target_os (str): The build destination target os ['android', 'ios, 'mac', 'win', 'linux']
        out_dir (str): The "out" build directory
        gn_build_dir (str): The gn "build" (contains gn toolchains and configs) directory
        gn_args (Dict): The key-value map pass to the "gn --args"
        gn_bin (str): The "gn" binary executable full path
        ninja_bin (str): The "ninja" binary executable full path
        ide (str, optional): What type of IDE shell project needs to be generated. Defaults to "default"
            supported value is ["default", "cmake", "qt"]
            "default": Xcode project for iOS/macOS, Visual Studio project for Windows, CMakeLists for others

    Returns:
        int: Execute result status code, 0 == success
    """
    gn_cmd = [gn_bin, 'gen', out_dir, '--check', '-v']
    gn_cmd.append('--ninja-executable=%s' % ninja_bin)
    if ide == 'default' and target_os in ['ios', 'mac']:
        # Generate an Xcode project for Darwin.
        gn_cmd.append('--ide=xcode')
        gn_cmd.append('--xcode-project=%s' % proj_name)
        gn_cmd.append('--xcode-build-system=new')
    elif ide == 'default' and target_os == 'win':
        # Generate a Visual Studio project for Windows.
        gn_cmd.append('--ide=vs')
        gn_cmd.append('--sln=%s' % proj_name)
    elif ide == 'qt':
        # Generate QtCreator project.
        gn_cmd.append('--ide=qtcreator')
    else:
        # Generate a CMakeLists.txt for Android Studio Gradle or other IDE.
        gn_cmd.append('--ide=json')
        gn_cmd.append('--json-ide-script=%s/android/gradle/gn_to_cmake.py' % gn_build_dir)

    cmd_gn_args = gn_args_to_command_line_args(gn_args)
    gn_cmd.append('--args=%s' % ' '.join(cmd_gn_args))

    print('\n[*] Generating GN files in: {}'.format(out_dir))
    print('\n[*] GN command: {}\n'.format(' '.join(gn_cmd)))
    try:
        gn_call_result = subprocess.call(gn_cmd, cwd=proj_root)
    except Exception as e:
        print('[*] Failed to generate gn files: ', e)
        sys.exit(1)
    return gn_call_result


def invoke_ninja_compdb(proj_root: str, out_dir: str, ninja_bin: str):
    """
    Generate/Replace the compile commands database in out.
    It does not run a actual ninja build command,
    but just generate a full ninja compile commands.

    Args:
        proj_root (str): Your project root directory path
        out_dir (str): The "out" build directory
        ninja_bin (str): The "ninja" binary full path
            e.g. '/Users/zego/path/to/ninja' or 'C:\\path\\to\\ninja.exe'
    """
    ninja_compdb_cmd = ['arch', '-arm64'] if osutil.is_arm64_mac() else []
    ninja_compdb_cmd.extend([
        ninja_bin, '-C', out_dir, '-t', 'compdb',
        'cc', 'cxx', 'objc', 'objcxx', 'asm'])

    print('\n[*] Run ninja -t compdb command: {}'.format(' '.join(ninja_compdb_cmd)))
    try:
        contents = subprocess.check_output(ninja_compdb_cmd, cwd=proj_root)
        with open(os.path.join(out_dir, 'compile_commands.json'), 'wb') as fw:
            fw.write(contents)
    except subprocess.CalledProcessError as exc:
        print('[*] Failed to run ninja -t compdb: ', exc.returncode, exc.output)
        sys.exit(1)


def invoke_ninja_graph(proj_root: str, out_dir: str, ninja_bin: str, generate_svg=False):
    """
    Generate a file in the syntax used by graphviz,
    then use dot to generates a graph.sv

    Args:
        proj_root (str): Your project root directory path
        out_dir (str): The "out" build directory
        ninja_bin (str): The "ninja" binary full path
            e.g. '/Users/zego/path/to/ninja' or 'C:\\path\\to\\ninja.exe'
        generate_svg (bool, optional): Whether to generate SVG with "dot" tool, default to False.
    """
    ninja_graph_cmd = ['arch', '-arm64'] if osutil.is_arm64_mac() else []
    ninja_graph_cmd.extend([ninja_bin, '-C', out_dir, '-t', 'graph'])

    print('\n[*] Run ninja -t graph command: {}'.format(' '.join(ninja_graph_cmd)))
    try:
        graph = subprocess.check_output(ninja_graph_cmd, cwd=proj_root)
        with open(os.path.join(out_dir, 'graph.gv'), 'w') as f:
            f.write(graph.decode('utf-8'))
    except Exception as e: print('[*] Failed to run ninja -t graph: ', e)

    if not generate_svg:
        return

    # Generate SVG only when 'dot' has been installed
    if shutil.which('dot'):
        dot_cmd = ['dot', '-Tsvg', '-o{}/graph.svg'.format(out_dir), os.path.join(out_dir, 'graph.gv')]
        print('\n[*] Run dot command: {}'.format(' '.join(dot_cmd)))
        try: subprocess.check_call(dot_cmd)
        except Exception as e: print('[*] Failed to run dot: ', e)
    else:
        print('[ERROR] "dot" tool has not been installed, skip the step of generate SVG from "graph.gv", you can install it with `brew install graphviz` on macOS!')


def invoke_ninja_build(proj_root: str, out_dir: str, ninja_bin: str, parallel_jobs=0) -> int:
    """Run ninja build command to compile.

    Args:
        proj_root (str): Your project root directory path
        out_dir (str): The "out" build directory
        ninja_bin (str): The "ninja" binary full path
            e.g. '/Users/zego/path/to/ninja' or 'C:\\path\\to\\ninja.exe'
        parallel_jobs (int): Run N jobs in parallel (0 means default)

    Returns:
        int: Execute result status code, 0 == success
    """
    ninja_build_cmd = ['arch', '-arm64'] if osutil.is_arm64_mac() else []
    ninja_build_cmd.extend([
        ninja_bin, '-C', out_dir, '-v',
        '-d', 'keeprsp', '-d', 'keepdepfile'])
    if parallel_jobs > 0:
        ninja_build_cmd.extend(['-j', str(parallel_jobs)])

    print('\n[*] Run ninja build command: {}\n'.format(' '.join(ninja_build_cmd)))
    status = 0
    try:
        status = subprocess.check_call(ninja_build_cmd, cwd=proj_root)
    except subprocess.CalledProcessError as exc:
        print('[*] Failed to run ninja build, status:', exc.returncode, 'output:', exc.output)
        status = exc.returncode

    # Convert ninja log into trace json
    # You can open https://ui.perfetto.dev and drag the json into it
    subprocess.call([sys.executable,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ninjatracing.py'),
        '-o', os.path.join(out_dir, '.ninja_trace.json'),
        os.path.join(out_dir, '.ninja_log')])
    return status

###################
### Apple Utils ###
###################

def insert_organization_name_to_generated_xcode_project(pbxproj_path: str, organization: str):
    """
    The dummy Xcode project generated by GN is lack of ORGANIZATIONNAME,
    so we manually add for it
    """

    if not os.path.exists(pbxproj_path):
        print('[WARNING] The dummy Xcode project "%s" does not exist!' % pbxproj_path)
        return

    flag = '\t\t\t\tORGANIZATIONNAME = {};\n'.format(organization)

    with open(pbxproj_path, 'r') as fr:
        content = fr.readlines()
    with open(pbxproj_path, 'w') as fw:
        for line in content:
            fw.write(line)
            # The flag should be inserted into "attributes"
            if 'attributes = {' in line:
                fw.write(flag)


def insert_other_cpp_flags_to_generated_xcode_project(pbxproj_path: str, stdcpp_ver=17):
    """
    The dummy Xcode project generated by GN is lack of C++ flag,
    so we manually add a `-std=c++17` flag for it
    """

    if not os.path.exists(pbxproj_path):
        print('[WARNING] The dummy Xcode project "%s" does not exist!' % pbxproj_path)
        return

    flag = '\t\t\t\tOTHER_CPLUSPLUSFLAGS = "-std=c++{}";\n'.format(stdcpp_ver)

    with open(pbxproj_path, 'r') as fr:
        content = fr.readlines()
    with open(pbxproj_path, 'w') as fw:
        for line in content:
            fw.write(line)
            # The flag should be inserted under the header search path
            if 'HEADER_SEARCH_PATHS' in line:
                fw.write(flag)


def expand_header_search_path_of_generated_xcode_project(pbxproj_path: str):
    """
    The dummy Xcode project generated by GN is hardcode "HEADER_SEARCH_PATHS" as only one root source path
    so we manually expand wildcard to it, to make it search all sub folder recursively
    """

    if not os.path.exists(pbxproj_path):
        print('[WARNING] The dummy Xcode project "%s" does not exist!' % pbxproj_path)
        return

    with open(pbxproj_path, 'r') as fr:
        content = fr.readlines()
    with open(pbxproj_path, 'w') as fw:
        for line in content:
            if 'HEADER_SEARCH_PATHS' in line:
                line = line.replace('= ', '= "').replace(';\n', '**";\n')
            fw.write(line)


def create_xcode_scheme(xcodeproj_path: str, scheme_name: str):
    os.environ['GEM_HOME'] = os.path.join(os.path.expanduser('~'), '.gem')
    if 'xcodeproj' not in subprocess.check_output(['gem', 'list']).decode('utf8'):
        subprocess.call(['gem', 'install', 'xcodeproj'])
    subprocess.call(['ruby', os.path.join(os.path.dirname(__file__),
        'create_xcode_scheme.rb'), xcodeproj_path, scheme_name])


#####################
### Android Utils ###
#####################

def change_generated_android_cmakelist_library_target_name(cmakelist_path: str, origin_target: str, new_target: str):
    """
    The dummy cmakelist generated by GN and (gn_to_cmake.py),
    is using GN target name to naming the product output lib name,
    but not the 'output_name', so we need to change it manually

    Args:
        cmakelist_path (str): The CMakeList file which we want to change
        origin_target (str): The origin target name, e.g. "src__main_zef_android_jni_shared_library"
        new_target (str): The expected new target name, e.g. "ZegoEffects"
    """

    if not os.path.exists(cmakelist_path):
        print('[WARNING] The dummy CMakeLists "%s" does not exist!' % cmakelist_path)
        return

    with open(cmakelist_path, 'r') as fr:
        content = fr.readlines()
    with open(cmakelist_path, 'w') as fw:
        for line in content:
            if origin_target in line:
                line = line.replace(origin_target, new_target).rstrip()
                line += ' # ZEGO: We have replaced the target name from "%s", to make the output library name correct.\n' % origin_target
            fw.write(line)


def temporary_change_android_gradle_external_build(gradle_path: str, enable: bool):
    """
    Modify Android gradle file, bacause it refer the debug's CMakeLists,
    it just used for debug with android studio,
    so when build with GN/Ninja, we should comment it

    Args:
        gradle_path (str): The android gradle path
        enable (bool): Whether to restore it or comment it
    """
    if not os.path.exists(gradle_path):
        print('[WARNING] The gradle file "%s" does not exist!' % gradle_path)
        return

    with open(gradle_path, 'r') as fr:
        all_lines = fr.readlines()
    with open(gradle_path, 'w') as fw:
        for line in all_lines:
            if 'CMakeLists.txt' in line:
                if not enable and not line.startswith('//'):
                    line = '//' + line
                elif enable and line.startswith('//'):
                    line = line[2:]
            fw.write(line)


def generate_android_build_config_properties(build_config_properties_file_path: str, javasrc_dirs: List[str], fwd: List[str]):
    """Generate the "build_config.properties" file for android gradle project
    You need to collect(copy) all java source folders to "javasrc_dir_path"

    If you use GN's "collect_javasrc" template,
    the "javasrc_dirs" should be ["${out_dir_path}/javasrc"]

    Args:
        build_config_properties_file_path (str): The path of "build_config.properties" file to be generated
        javasrc_dirs (List[str]): A path list of folders which contains java source file to be compile by gradle
        fwd (List[str]): Some other forward define, forward them to gradle
    """
    if not javasrc_dirs:
        raise Exception('Empty list of "javasrc_dirs"')
    with open(build_config_properties_file_path, 'w') as fw:
        fw.write('MAIN_JAVA_SRC_DIRS=%s\n' % ','.join(javasrc_dirs))
        for define in fwd:
            fw.write('%s\n' % define)

###################
### Linux Utils ###
###################

def load_gn_embedded_toolchains_for_argparse(gn_build_toolchain_dir: str, parser: argparse.ArgumentParser, linux_variant: argparse.Action):
    """Load embedded toolchains from GN "build" folder,
    and transfer them to argparse's argument.

    Args:
        gn_build_toolchain_dir (str): The GN "build" folder path of your project, e.g.
            "/Users/patrickfu/zim_sdk/build"

        parser (argparse.ArgumentParser): The ArgumentParser object, e.g.
            parser = argparse.ArgumentParser(description='The root build script.')

        linux_variant (argparse.Action): An argument of "--linux-variant", e.g.
            linux_variant_action = parser.add_argument('--linux-variant', type=str, choices=['ubuntu', 'centos'])

    Example:
        def __parse_args(args):
            args = args[1:]
            parser = argparse.ArgumentParser(description='The root build script.')
            parser.add_argument('--linux', dest='target_os', action='store_const', const='linux')
            parser.add_argument('--linux-cpu', action='store', type=str, nargs='+', choices=['arm64', 'arm64', 'x86', 'x64'], default=['x64'])

            linux_variant_action = parser.add_argument('--linux-variant', type=str, choices=['ubuntu', 'centos'])

            load_gn_embedded_toolchains_for_argparse(parser, linux_variant_action)

            return parser.parse_args(args)

    """
    if not os.path.exists(gn_build_toolchain_dir):
        print('\n[ERROR] The GN build toolchain dir "%s" is empty!' % gn_build_toolchain_dir)
        print('It may be that the "build" submodule of your git repo has not been checked out.\n')
        sys.exit(1)
    embedded_toolchain_root = os.path.join(gn_build_toolchain_dir, 'toolchain', 'linux', 'embedded')
    embedded_toolchains = {}
    for manufacturer in os.listdir(embedded_toolchain_root):
        if not os.path.isdir(os.path.join(embedded_toolchain_root, manufacturer)):
            continue
        embedded_toolchains[manufacturer] = []
        with open(os.path.join(embedded_toolchain_root, manufacturer, 'BUILD.gn'), 'r') as fr:
            for line in fr.readlines():
                if 'gcc_toolchain(' in line:
                    embedded_toolchains[manufacturer].append(line[line.find('(')+2:line.find(')')-1])
        linux_variant.choices.append(manufacturer)
        parser.add_argument('--{}-toolchains'.format(manufacturer), action='store', type=str, nargs='+',
            choices=embedded_toolchains[manufacturer], default=embedded_toolchains[manufacturer])
