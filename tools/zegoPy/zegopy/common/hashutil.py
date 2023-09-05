#!/usr/bin/env python3
# coding: utf-8


import os
import hashlib


def has_string(s):
    md5 = hashlib.md5(s)
    return md5.hexdigest()


def _hash_file_no_check(m, file_path):
    fr = open(file_path, "rb")
    try:
        while True:
            block = fr.read(4096)
            if len(block) == 0:
                break

            m.update(block)
    finally:
        if fr:
            fr.close()

    return m


def hash_file(file_path):
    if not os.path.exists(file_path):
        print("%s not exist, hash failed".format(file_path))
        return None

    md5 = hashlib.md5()
    _hash_file_no_check(md5, file_path)
    return md5.hexdigest()


def hash_folder(dir_root):
    if not os.path.exists(dir_root):
        print("%s not exist, hash failed".format(dir_root))
        return None

    md5 = hashlib.md5()
    for root, folders, files in os.walk(dir_root):
        folders.sort()
        files.sort()
        for fname in files:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, dir_root)
            unix_style_path = rel_path.replace('\\', '/')   # 确保不同平台生成的 hash 一样
            md5.update(unix_style_path.encode('utf-8'))

            _hash_file_no_check(md5, full_path)

    return md5.hexdigest()
