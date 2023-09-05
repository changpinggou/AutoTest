#!/usr/bin/env python -u
# coding:utf-8

"""
    封装一些 I/O 相关的方法，主要是文件及文件夹的创建、删除等操作
"""

import os
import shutil


def delete(path):
    """
    删除一个文件/文件夹
    :param path: 待删除的文件路径
    :return:
    """
    if not os.path.exists(path):
        print("[*] {} not exists".format(path))
        return

    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
    elif os.path.islink(path):
        os.remove(path)
    else:
        print("[*] unknown type for: " + path)


def insure_dir_exists(dir_path):
    """
    确保文件夹存在
    :param dir_path: 待检查的文件夹路径
    :return:
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def insure_empty_dir(dir_path):
    """
    确保为一个空文件夹；如果不存在，则创建；
    如果已经存在，存清除文件中的任何已有文件和文件夹
    :param dir_path: 待检查的文件夹路径
    :return:
    """
    if os.path.exists(dir_path):
        clean_folder(dir_path)
    else:
        os.makedirs(dir_path)


def clean_folder(folder):
    """
    删除文件夹下的所有内容
    :param folder: 待处理的文件夹路径
    :return:
    """
    if not os.path.isdir(folder):
        print("[*] {} not dir or not exists".format(folder))
        return

    for name in os.listdir(folder):
        delete(os.path.join(folder, name))


def __copy_folder(_src, _dst, _overwrite, symlinks):
    error_code = 0
    basename = os.path.basename(_src)
    target_path = os.path.join(_dst, basename)
    if not os.path.exists(target_path):
        shutil.copytree(_src, target_path, symlinks=symlinks)
    elif _overwrite:
        delete(target_path)
        shutil.copytree(_src, target_path, symlinks=symlinks)
    else:
        print("[*] dst: {} has exists".format(target_path))
        error_code = -2

    return error_code


def copy(src, dst, overwrite=False, symlinks=False):
    """
    拷贝文件/文件夹至目标。
    当 src 为文件：
        dst 存在：dst 为目录，直接将 src 拷贝至 dst 目录中，若 dst 为文件，则由 overwrite 决定是否覆盖或者什么都不做
        dst 不存在：新建 dst 目录，并将 src 拷贝至新建目录中
    当 src 为目录：
        dst 存在：由 overwrite 决定是否覆盖或者什么都不做
        dst 不存在：等同于 shutil.copytree
    :param src: 源文件/文件夹
    :param dst: 目标目录
    :param overwrite: 当目标文件存在时，是否覆盖目标文件。True 时覆盖，否则不覆盖。默认为 False
    :param symlinks: 仅在源为文件夹时有效。== True，如果源文件夹中含有软链接，则目标目录中也是软链接；否则目标文件夹中为软链接指向的内容。默认为 False
    :return: 成功返回 0；否则返回非 0
    """
    def _copy_file(_src, _dst, _overwrite):
        error_code = 0
        if not os.path.exists(_dst):
            os.makedirs(_dst)
            shutil.copy(_src, _dst)
        elif os.path.isdir(_dst):
            shutil.copy(_src, _dst)
        else:
            if _overwrite:
                shutil.copyfile(_src, _dst)
            else:
                print("[*] dst: {} has exists".format(_dst))
                error_code = -2

        return error_code

    if not os.path.exists(src):
        print("[*] src: {} not exists".format(src))
        return -1

    if os.path.isdir(src):
        return __copy_folder(src, dst, overwrite, symlinks)
    else:
        return _copy_file(src, dst, overwrite)


def copy2(src, dst, overwrite=False, symlinks=False):
    """
    拷贝文件/文件夹至目标, 与 copy 的区别在于当 src 为文件，且 dst 不存在时的处理不同。
    当 src 为文件：
        dst 存在：dst 为目录，直接将 src 拷贝至 dst 目录中，若 dst 为文件，则由 overwrite 决定是否覆盖或者什么都不做
        dst 不存在：将 dst 当目标文件路径，将将 src 拷贝至此（文件名可与原文件名不同）
    当 src 为目录：
        dst 存在：由 overwrite 决定是否酸辣或者什么都不做
        dst 不存在：等同于 shutil.copytree
    :param src: 源文件/文件夹
    :param dst: 目标目录/文件
    :param overwrite: 当目标文件存在时，是否覆盖目标文件。True 时覆盖，否则不覆盖。默认为 False
    :param symlinks: 仅在源为文件夹时有效。== True，如果源文件夹中含有软链接，则目标目录中也是软链接；否则目标文件夹中为软链接指向的内容。默认为 False
    :return: 成功返回 0；否则返回非 0
    """
    def _copy_file(_src, _dst, _overwrite):
        error_code = 0
        if not os.path.exists(_dst):
            target_folder = os.path.realpath(os.path.join(_dst, ".."))
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            new_target_path = os.path.join(target_folder, os.path.basename(_dst))
            shutil.copy(_src, new_target_path)
        elif os.path.isdir(_dst):
            shutil.copy(_src, _dst)
        else:
            if _overwrite:
                shutil.copyfile(_src, _dst)
            else:
                print("[*] dst: {} has exists".format(_dst))
                error_code = -2

        return error_code

    if not os.path.exists(src):
        print("[*] src: {} not exists".format(src))
        return -1

    if os.path.isdir(src):
        return __copy_folder(src, dst, overwrite, symlinks)
    else:
        return _copy_file(src, dst, overwrite)


def copy_folder(src, dst_folder, overwrite=False, symlinks=True):
    """
    拷贝 src 至 dst_folder 目录下，若 dst_folder 不存在，则新建目录，并将 src 文件或者文件夹下的内容拷贝至 dst_folder 中
    :param src:源文件/目录
    :param dst_folder: 目标目录
    :param overwrite: 当目录目录中存在与源文件同名文件或源文件夹中同名文件时，是否覆盖目标文件，当为 False 时什么也不做
    :param symlinks: 当为 True 时，源文件为软链接或源文件夹中的软链接，在目标目录中也是软链接；否则为软链接指向的内容。默认为 True
    :return: 成功返回 0；否则返回非 0
    """
    if not os.path.exists(src):
        print("[*] src: {} not exists".format(src))
        return -1

    insure_dir_exists(dst_folder)
    if os.path.isfile(src) or os.path.islink(src):
        if os.path.exists(os.path.join(dst_folder, os.path.basename(src))) and not overwrite:
            return False

        shutil.copyfile(src, dst_folder, follow_symlinks=symlinks)
    elif os.path.isdir(src):
        for _item in os.listdir(src):
            _src_item = os.path.join(src, _item)
            copy(_src_item, dst_folder, overwrite=overwrite, symlinks=symlinks)
    else:
        print("[*] src {} not be support".format(src))
        return False

    return True


def move(src, dst):
    """
    将指定 文件/文件夹 移至 dst 目录下, like Unix 'mv' command
    :param src: 源文件/文件夹
    :param dst: 目标文件夹
    :return: None
    """
    shutil.move(src, dst)


def get_safe_filename(target_path):
    """
    获取一个安全的文件名，避免文件被覆盖
    规则：如果目标文件不存在，直接返回 target_path
    如果目标文件已存在，则在后缀前添加一个数字，从 1 开始
    :param target_path: 目标文件路径
    :return: 安全文件路径，如是目标文件不存在，则返回原值
    """
    if not os.path.exists(target_path):
        return target_path

    basename = os.path.basename(target_path)
    prefix_name, suffix_name = os.path.splitext(basename)
    parent_dir = os.path.dirname(target_path)
    index = 1
    new_target_path = target_path
    while True:
        new_name = "{}.{}{}".format(prefix_name, index, suffix_name)
        new_target_path = os.path.join(parent_dir, new_name)
        if not os.path.exists(new_target_path):
            break

        index += 1

    return new_target_path


def merge_folder(src_folder, dst_folder):
    """
    merge src_folder to dst_folder
    """
    if not os.path.exists(src_folder):
        return
    
    for entity in os.listdir(src_folder):
        if entity == "." or entity == "..":
            continue
        src_entity_path = os.path.join(src_folder, entity)
        dst_entity_path = os.path.join(dst_folder, entity)
        if os.path.isdir(src_entity_path):
            if not os.path.exists(dst_entity_path):
                os.makedirs(dst_entity_path)
            merge_folder(src_entity_path, dst_entity_path)
        elif os.path.isfile(src_entity_path):
            shutil.copy(src_entity_path, dst_entity_path)


def __test():
    tmp_folder = "_test"
    target_folder = "{}/to/target".format(tmp_folder)
    print("call insure_dir_exists func before")
    print("{} exists ? {}".format(target_folder, os.path.exists(target_folder)))

    insure_dir_exists(target_folder)
    print("call insure_dir_exists func after")
    print("{} exists ? {}".format(target_folder, os.path.exists(target_folder)))

    clean_folder(tmp_folder)
    print("call clean_folder('{}') func after".format(tmp_folder))
    print("{} exists ? {}".format(target_folder, os.path.exists(target_folder)))
    print("{} exists ? {}".format(tmp_folder, os.path.exists(tmp_folder)))

    delete(tmp_folder)
    print("call delete('{}') func after".format(tmp_folder))
    print("{} exists ? {}".format(tmp_folder, os.path.exists(tmp_folder)))


if __name__ == "__main__":
    __test()
