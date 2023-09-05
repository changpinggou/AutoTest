from setuptools import setup, find_packages
from zegopy.common import version_generator
import os, sys, subprocess

ROOT_PATH = os.path.dirname(__file__)
TEMP_VERSION_PATH = os.path.join(ROOT_PATH, 'zegopy', 'VERSION')

# 卸载老 zegopy，避免与新 zegopy 冲突
def uninstall_legacy_zegopy():
    from distutils.sysconfig import get_python_lib # get site-packages
    old_pyscripts_pth_file = os.path.join(get_python_lib(), 'ZegoPy.pth')
    if os.path.exists(old_pyscripts_pth_file):
        print('[WARNING] Find the legacy "zegopy" in your python3 site-package "%s", uninstall it!' % old_pyscripts_pth_file)
        os.remove(old_pyscripts_pth_file)

# For compatibility with old build scripts
if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == '-f'):
    print('[WARNING] You should use "python3 setup.py develop" to upgrade/install pyscripts!')
    uninstall_legacy_zegopy()
    subprocess.check_call('"{}" "{}" develop'.format(sys.executable, __file__), shell=True)
    sys.exit()

version = ''
if sys.argv[1] in ['install', 'sdist', 'build', 'develop'] :
    # 这个分支是给本地运行 'python3 setup.py install' 或者 Jenkins 打包时执行的
    print('[*] Generate version')
    version = version_generator.get_long_semver(ROOT_PATH).split('-')[0]
    with open(TEMP_VERSION_PATH, 'w') as fw:
        fw.write(version)
elif os.path.exists(TEMP_VERSION_PATH):
    # 这个分支是给终端用户使用 "pip3 install zegopy" 时，pip 自动调用此 setup.py 脚本时执行的
    print('[*] Find temporary VERSION file in "%s"' % TEMP_VERSION_PATH)
    with open(TEMP_VERSION_PATH, 'r') as fr:
        version = fr.read().strip()
else:
    error_message = '[ERROR] Can not find VERSION file, install zegopy failed!'
    print(error_message)
    raise Exception(error_message)

print('==== Version: %s ====' % version)

setup(
    name='zegopy',
    version=version,
    packages=find_packages(),
    package_data={'': ['*']},
    include_package_data=True,
    description='pyscripts 打包成 pypi 库供各编译机、开发机使用 pip 安装使用',
    author='zegopy',
    url='http://dev.coding.zego.cloud/p/common_utils/artifacts/156/pypi/packages',
    author_email='zegopy@zego.im',
    keywords='zegopy'
)
