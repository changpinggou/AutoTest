#!/usr/bin/env python3
#coding: utf-8


'''
用于解密 ZEGO SDK 生成的日志文件，用法：python3 -m zegopy.DecryptLog [log_file_name]
'''


import os
import sys


KPass = b"ljc"
LINE_SEP = ord('\n')

IS_PYTHON2 = sys.version_info.major == 2

def should_decrypt(c):
    if isinstance(c, str):
        c = ord(c)

    if c == 0 or c == LINE_SEP:
        return False

    return True


def decrypt_str(s):
    i = -1
    _s = bytearray(s)
    for c in s:
        i += 1
        if should_decrypt(c):
            if IS_PYTHON2:
                _c = ord(c) ^ ord(KPass[i % 3])
            else:
                _c = c ^ KPass[i % 3]
            
            if should_decrypt(_c):
                _s[i] = _c
            else:
                _s[i] = c
        else:
            _s[i] = c

    return _s


def get_decrypt_file_name(src_file_name):
    fpath, ext = os.path.splitext(src_file_name)
    return "{}_decrypt{}".format(fpath, ext)


def decrypt_file(fname):
    decrypt_file_name = get_decrypt_file_name(fname)
    fr = open(fname, "rb")
    fw = open(decrypt_file_name, "wb")
    while True:
        line = fr.readline()
        if line is None or len(line) == 0:
            break

        fw.write(decrypt_str(line))

    fw.flush()
    fw.close()
    fr.close()

    return decrypt_file_name


def decrypt():
    src_file = None
    if len(sys.argv) == 1:
        src_file = os.path.realpath("zegoavlog1.txt")
    elif len(sys.argv) == 2:
        src_file = os.path.realpath(sys.argv[1])
    else:
        raise Exception("*** Arguments Error ***")

    if not os.path.exists(src_file):
        raise Exception("File : {} not exists.".format(src_file))

    print ("Src encrypt file is: {}".format(src_file))
    print ("Begin decrypt...")
    decrypt_file_name = decrypt_file(src_file)
    print ("The target file is: {}".format(decrypt_file_name))
    print ("Finish.")


if __name__ == "__main__":
    decrypt()
