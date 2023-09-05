#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import importlib.util
import locale

_g_sys_path = sys.path.copy()

_g_env_table = {}
for _key, _value in os.environ.items():
    _g_env_table[_key] = _value


def reset_environ():
    """
    将 os.environ & sys.path 重围到导入此模块时的状态
    """
    tmp_keys = [k for k in os.environ.keys()]   # 不能直接使用 os.environ.keys()，它是一个类似于地址引用，可能会导致 “RuntimeError: dictionary changed size during iteration”
    for _key in tmp_keys:
        if _key in _g_env_table:
            os.environ[_key] = _g_env_table[_key]
        else:
            os.environ.pop(_key)

    sys_path = sys.path.copy()
    for _p in sys_path:
        if _p not in _g_sys_path:
            sys.path.remove(_p)


def set_utf8_locale():
    """
    强制将当前环境设置为 UTF-8 编码，以解决在某些操作系统（如 Windows）上可能出现：
        UnicodeDecodeError: 'gbk' codec can't decode byte 0x93 in position 26: illegal multibyte sequence
    :return True if set success, else failed
    """
    utf8_list = ("zh_CN.UTF-8", "en_US.UTF-8", "C.UTF-8")
    for _u in utf8_list:
        try:
            locale.setlocale(locale.LC_ALL, _u)
            return True
        except locale.Error as e:
            print("try setlocale {} failed: {}".format(_u, e))

    print("* set utf-8 local failed *")

    return False


def reset_locale():
    """
    Sets the locale for category to the default setting
    """
    try:
        locale.resetlocale()
        return True
    except locale.Error as e:
        print("reset_locale failed: {}".format(e))

    return False


def load_py_script(script_path) -> object:
    """
    加载一个 python 脚本
    :param script_path python 脚本路径
    :return <class 'module'>
    """
    script_name = os.path.basename(script_path)
    mod_name = '.' + os.path.splitext(script_name)[0]

    module_spec = importlib.util.spec_from_file_location(mod_name, script_path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    return module

