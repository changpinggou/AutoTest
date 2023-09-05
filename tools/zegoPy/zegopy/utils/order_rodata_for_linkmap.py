#!/usr/bin/env python
#coding: utf-8

"""
通过对编译阶段产生的 map 文件进行分析，查找占用空间最大的几个 rodata 数据，便于优化库文件尺寸。目前仅支持 Android \\ armeabi-v7a 架构 
--input: 待分析的 map 文件
--top: 指定占用空间最大的项的输出个数
--verbose: 是否输出子项信息，默认关闭
--rule: 输出子项的规则，支持格式: [m|s]xxx: 当以 m 开头时，后面的 xxx 表示最多输出几条子项; 当以 s 开头时，后面的 xxx 表示子项的大小须大于此值
--output: 结果保存至此文件中，默认仅输出到控制台
"""

import sys
import os
import re


class ChildItem:
    def __init__(self, start_address=0, name=''):
        self.address = start_address
        self.name = name
        self.size = 0

    def __eq__(self, o):
        return self.size == o.size

    def __gt__(self, o):
        return self.size > o.size

    def __lt__(self, o):
        return self.size < o.size

    def __str__(self):
        return "    0x%08x\t%s[%d]\t%s" % (self.address, hex(self.size), self.size, self.name)

    def set_size(self, size):
        self.size = size


class DataItem:
    def __init__(self, name='', start_address=0, size=0, module=''):
        self.name = name
        self.address = start_address
        self.size = size
        self.module = module
        self.children = []  # ChildItem
        self.expand_children = False
        self.children_show_rule = ''

    def __eq__(self, o):
        return self.size == o.size

    def __gt__(self, o):
        return self.size > o.size

    def __lt__(self, o):
        return self.size < o.size

    def __str__(self):
        s = "%s\t0x%08x\t%s[%d]\t%s" % (self.name, self.address, hex(self.size), self.size, os.path.basename(self.module))
        if self.children and self.expand_children:
            children = self.children.copy()
            children.sort(reverse=True)

            max_cnt = min(len(children), int(self.children_show_rule[1: ]) if self.children_show_rule.startswith('m') else sys.maxsize)
            limit_size = int(self.children_show_rule[1: ]) if self.children_show_rule.startswith('s') else 0
            for child in children[: max_cnt]:
                if child.size >= limit_size:
                    s += "\r\n" + str(child)
        return s

    def set_children_rule(self, expand_children, rule):
        self.expand_children = expand_children
        self.children_show_rule = rule

    def append_child(self, child):
        last_child = None
        if self.children:
            last_child = self.children[-1]
            last_child.set_size(child.address - last_child.address)

        self.children.append(child)


class Logger:
    def __init__(self, log_file):
        if log_file:
            root_folder = os.path.dirname(log_file)
            if root_folder and not os.path.exists(root_folder):
                os.makedirs(root_folder)

            self.fd = open(log_file, "w")
        else:
            self.fd = None

    def write(self, content):
        print(content)
        if self.fd:
            self.fd.write(content)
            self.fd.write("\r\n")


def parse(args):
    map_file = args.input
    top_count = args.top
    verbose = args.verbose
    rule = args.rule
    output_file = args.output

    fr = open(map_file)

    logger = Logger(output_file)

    logger.write("command: %s" % (" ".join(sys.argv)))
    logger.write("parse the map file: %s\r\n" % (os.path.realpath(map_file)))

    rodata_arr = []
    prefix_pattern = re.compile(r'^[\s]{4,}')
    raw_line = fr.readline()
    while raw_line:
        striped_line = raw_line.strip()
        if striped_line.startswith('.rodata'):
            item = None
            items = striped_line.split()
            if len(items) == 4:
                item = DataItem(items[0], int(items[1], 16), int(items[2], 16), items[3])
            elif len(items) == 1:  # read next line
                size_line = fr.readline()
                striped_size_line = size_line.strip()
                _items = striped_size_line.split()
                item = DataItem(striped_line, int(_items[0], 16), int(_items[1], 16), _items[2])
            else:
                logger.write("[*] unknown line: {}".format(raw_line))
                raw_line = fr.readline()
                continue

            raw_line = fr.readline()
            has_subitem = prefix_pattern.match(raw_line)
            while has_subitem:
                striped_line = raw_line.strip()
                space_pos = striped_line.find(' ')
                if space_pos < 0:
                    break
                else:
                    address = int(striped_line[: space_pos], 16)
                    name = striped_line[space_pos + 1 : ].strip()
                    child = ChildItem(address, name)
                    item.append_child(child)

                raw_line = fr.readline()
                has_subitem = prefix_pattern.match(raw_line)

            if item:
                item.set_children_rule(verbose, rule)
                rodata_arr.append(item)
        else:
            raw_line = fr.readline()

    rodata_arr.sort(reverse=True)
    logger.write("=====" * 8)
    order_num = 1
    logger.write("order\tname\taddress\tsize\tmodule")
    for item in rodata_arr[: min(len(rodata_arr), top_count)]:
        logger.write("%d). %s" % (order_num, item))
        order_num += 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', action='store', type=str, default='armeabi-v7a.map', help="will be processed the map file")
    parser.add_argument('-t', '--top', action='store', type=int, default=10, help="how many items will be shown?")
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help="whether show children's info")
    parser.add_argument('-r', '--rule', action='store', type=str, default='', help="the rule which children will be shown")
    parser.add_argument('-o', '--output', action='store', type=str, default='', help="the result will be saved to this file")
    args = parser.parse_args()
    parse(args)

