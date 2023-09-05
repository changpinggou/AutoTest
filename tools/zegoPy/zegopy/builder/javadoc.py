#!/usr/bin/env python -u
# coding: utf-8

from os.path import curdir, join, realpath

from zegopy.common import command as zegocmd
from zegopy.common.argutil import CmdParam


class JavaDoc(object):
    SCOPE_LIST = ('public', 'protected', 'package', 'private')

    def __init__(self):
        default_args = ['-encoding', 'utf-8', '-docencoding', 'utf-8',
                        '-docfilessubdirs', '-notimestamp']
        self._params = CmdParam(args=default_args)
        default_target_path = join(realpath(curdir), '_javadoc')
        self._params.append('-d', default_target_path)

        self._scope = '-public'
        self._source_ref_file = ''
        self._source_path = []
        self._boot_classpath = []
        self._classpath = []
        self._sub_packages = []
        self._package_names = []
        self._exclude_files = []

    def set_title(self, title):
        self._params.update('-windowtitle', title)
        self._params.update('-doctitle', title)
        return self

    def set_footer(self, footer):
        self._params.update('-footer', footer)
        return self

    def set_target_path(self, target_path):
        self._params.update('-d', target_path)
        return self

    def set_doc_encoding(self, encoding='utf-8'):
        self._params.update('-encoding', encoding)
        self._params.update('-docencoding', encoding)
        return self

    def set_charset(self, charset='UTF-8'):
        self._params.update('-charset', charset)
        return self

    def set_source_ref_file(self, ref_file_path):
        self._source_ref_file = ref_file_path
        return self

    def add_source_path(self, source_path):
        if source_path not in self._source_path:
            self._source_path.append(source_path)
        return self

    # Note: option "--boot-class-path" not allowed with target 11
    # You should use "--class-path" instead!
    def add_boot_classpath(self, boot_classpath):
        if boot_classpath not in self._boot_classpath:
            self._boot_classpath.append(boot_classpath)
        return self

    def add_classpath(self, classpath):
        if classpath not in self._classpath:
            self._classpath.append(classpath)
        return self

    def add_sub_package(self, sub_package):
        if sub_package not in self._sub_packages:
            self._sub_packages.append(sub_package)
        return self

    def add_package_name(self, package_name):
        if package_name not in self._package_names:
            self._package_names.append(package_name)
        return self

    '''
    This method not workable just now !!!
    '''
    def add_exclude_file(self, *exclude_files):
        for _item in exclude_files:
            if _item not in self._exclude_files:
                self._exclude_files.append(_item)
        return self

    def set_scope(self, scope):
        if scope not in JavaDoc.SCOPE_LIST:
            raise Exception('[*] unknown scope category, must in %s'.format(scope_table))

        self._scope = '-{}'.format(scope)
        return self

    def set_params(self, *params, **kwparams):
        for p in params:
            self._params.update(p)

        for key in kwparams:
            self._params.update(key, kwparams[key])

        return self

    def generate(self):
        def _update_list_param(key, lvalue):
            if self._params.has(key):
                lvalue.extend(self._params.remove(key))

            if lvalue:
                self._params.append(key, *lvalue)

        if not self._source_ref_file and not self._source_path:
            raise Exception("[*] Must specify at least one source path or source_reference_file")

        if self._package_names:
            self._params.append(*self._package_names)

        _update_list_param('-sourcepath', self._source_path)
        _update_list_param('-subpackages', self._sub_packages)

        self._params.append(self._scope)
        if self._exclude_files:
            self._params.append('-excludedocfilessubdir', ':'.join(self._exclude_files))

        if self._boot_classpath:
            self._params.append('-bootclasspath', ':'.join(self._boot_classpath))

        if self._classpath:
            self._params.append('-classpath', ':'.join(self._classpath))

        if self._source_ref_file:
            self._params.append('@{}'.format(self._source_ref_file))

        self._params.insert(0, 'javadoc')
        self._params.append('-Xdoclint:none')
        state, text = zegocmd.execute(zegocmd.list2cmdline(self._params.get_all()))
        if state != 0:
            print(text)
            raise Exception("[*] Generate Failed")


if __name__ == "__main__":
    import os
    jd = JavaDoc()
    jd.set_title("ZegoAVKit")
    jd.add_source_path("/Users/realuei/data/zego/code/zegoavkit/builds/android/_builds/android-ndk-r13b-api-15-armeabi-v7a-neon-Release/java-source")
    android_jar_path = realpath(join(os.environ['ANDROID_HOME'], 'platforms/android-25/android.jar'))
    jd.add_boot_classpath(android_jar_path)
    jd.add_package_name("com.zego.zegoavkit2")
    jd.generate()
