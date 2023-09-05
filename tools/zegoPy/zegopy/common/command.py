#!/usr/bin/env python -u
# coding:utf-8

"""
    封装一些调用 shell 的方法集
"""

import sys
import subprocess
try:
    import chardet
except ImportError as e:
    import os
    os.system("pip3 install chardet")
    os.system("pip install chardet")
    import chardet


def __tag_print(msg, newline=False):
    print("{}[zegocmd] {}".format("\r\n" if newline else "", msg))


def __safe_stdout_write(_text):
    """
    仅过滤掉编码异常的字符，其它内容正常输出
    """
    for _ch in _text:
        try:
            sys.stdout.write(_ch)
        except UnicodeError:
            sys.stdout.write('?')


def __fix_cmd(raw_cmd):
    """
    fix the command for windows platform
    :param raw_cmd: 原始待执行 Shell 命令
    """
    mswindows = (sys.platform == 'win32')

    if not mswindows:
        raw_cmd = '{ ' + raw_cmd + '; }'
    return raw_cmd + " 2>&1"


def execute(raw_cmd, is_print=False):
    """
    execute command.
    :param raw_cmd: command line;
    :param is_print: whether print console message, default False;
    :return (state, text): execute failed when state not equals zero.
    """
    # noinspection PyBroadException
    try:
        __tag_print("Execute: [{}]".format(raw_cmd))
    except Exception:
        __tag_print('Execute: PRINT RAW CMD ERROR')

    _cmd = __fix_cmd(raw_cmd)
    process = subprocess.Popen(_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return_code = process.wait()

    stderr_encoding = chardet.detect(stderr)['encoding']
    stdout_encoding = chardet.detect(stdout)['encoding']

    if return_code != 0:
        state = return_code

        try: text = stderr.decode(stderr_encoding, errors='replace')
        except: text = stderr.decode('utf8', errors='replace')

        if len(text) == 0:

            try: text = stdout.decode(stdout_encoding, errors='replace')
            except: text = stdout.decode('utf8', errors='replace')

        if is_print:
            __tag_print("error: " + text)
    else:
        state = 0
        try: text = stdout.decode(stdout_encoding, errors='replace')
        except: text = stdout.decode('utf8', errors='replace')
        if is_print:
            __tag_print("result: " + text)

    return state, text


def execute_async(raw_cmd):
    """
        must use for...in async_execute, otherwise can't run command line
        :param raw_cmd: command line;
        :return: 每次返回部分输出信息，当返回的结果类型为 int 时，表示运行结束，且该值为执行命令结果，仅在不为 0 时，才表示执行成功。
    """
    __tag_print("Async Execute: [" + raw_cmd + "]")
    _cmd = __fix_cmd(raw_cmd)
    # subprocess.Popen's stdout default return a readable stream object,
    # If the universal_newlines argument was True or text or encoding or errors be set, the stream is a text stream,
    # otherwise it is a byte stream.
    # but param encoding and errors be support python v3.6
    # param text be support by python v3.7
    p = subprocess.Popen(_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True, universal_newlines=False, bufsize=512)

    while p.poll() is None:
        bytes_data = p.stdout.read(256)
        encoding = chardet.detect(bytes_data)['encoding']
        try: yield bytes_data.decode(encoding=encoding, errors='replace')
        except: yield bytes_data.decode(encoding='utf8', errors='replace')

    exit_code = p.returncode
    p.kill()

    yield  exit_code


def execute_and_print(raw_cmd):
    """
        like execute, default print output message
        :param raw_cmd: command line;
        :return 0 is success, otherwise not equals zero.
    """
    exit_code = 0
    for _text in execute_async(raw_cmd):
        if type(_text) == int:
            exit_code = _text
        else:
            try:
                sys.stdout.write(str(_text))
            except UnicodeError:
                __safe_stdout_write(_text)

    return exit_code


def execute_rollback(raw_cmd, stop_func):
    """
    execute the shell command that never stop. eg: top or adb logcat ...
    :param raw_cmd: not fix shell command
    :param stop_func: function delegate, exit async_execute_rollback when return True
    :return (state, text): execute failed when state not equals zero.
    """

    __tag_print("Execute rollback: [" + raw_cmd + "]")
    _cmd = __fix_cmd(raw_cmd)
    # subprocess.Popen's stdout default return a readable stream object,
    # If the universal_newlines argument was True or text or encoding or errors be set, the stream is a text stream,
    # otherwise it is a byte stream.
    # but param encoding and errors be support python v3.6
    # param text be support by python v3.7
    p = subprocess.Popen(_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True, universal_newlines=False, bufsize=512)

    state = 0
    text = ""
    while p.poll() is None:
        if stop_func():
            __tag_print("Execute Interrupt by user", True)
            state = -1
            break

        bytedata = p.stdout.read(256)
        encoding = chardet.detect(bytedata)['encoding']
        try: _text = bytedata.decode(encoding, errors='replace')
        except: _text = bytedata.decode('utf8', errors='replace')

        try:
            sys.stdout.write(_text)
        except UnicodeError:
            __safe_stdout_write(_text)

        text += _text

    if state == 0:
        state = p.returncode

    p.kill()

    return state, text


def call(*popenargs, **kwargs):
    """
    call subprocess.call to execute command.
    eg: check_call(['ls', '-l', '-a']).

    主要用于启动命令中含有空格等特殊字符时，如 Windows 上的  C:\\Program Files\\xxx，使用 execute 会执行失败
    :param popenargs:
    :param kwargs:
    :return the returncode attribute.
    """
    return subprocess.call(*popenargs, **kwargs)


def check_call(*popenargs, **kwargs):
    """
    call subprocess.check_call to execute command, raise Exception when failed.
    eg: check_call(['ls', '-l', '-a']).

    主要用于启动命令中含有空格等特殊字符时，如 Windows 上的  C:\\Program Files\\xxx，使用 execute 会执行失败
    :param popenargs:
    :param kwargs:
    :return code in the returncode attribute.
    """
    return subprocess.check_call(*popenargs, **kwargs)


def list2cmdline(seq):
    """
    convert list arguments to cmd string
    :param seq:
    :return string cmd
    """
    return subprocess.list2cmdline(seq)


if __name__ == "__main__":
    execute("ls -l")
    execute_and_print("ls -l")

    i = 0

    def need_stop_func():
        global i
        i += 1
        if i > 10:
            return True

        return False

    execute_rollback("top", need_stop_func)
