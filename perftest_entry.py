from ast import arg
import os
import sys
import json
import argparse
import socket

PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))

def __parse_args(args):
    args = args[1:]
    parser = argparse.ArgumentParser(description='The root build script.')
    parser.add_argument('--jenkins', default=False, action='store_true',  help='Whether build in jenkins')
    parser.add_argument('--platform', type=str, choices=['linux', 'windows'], default='linux',
                        help='性能测试平台, default:linux')
    parser.add_argument('--dockername', type=str, default='v1.5.1.64-202308161414-d450a5d8', help='打包出来的docker文件名')
    parser.add_argument('--windisturl', type=str, default='', help='打包出来的windows产物压缩包地址')
    parser.add_argument('--outtempdir', type=str, default='', help='临时输出目录')
    parser.add_argument('--testcasescope', type=str, default='CI', help='测试用例范畴')

    return parser.parse_args(args)

def main(argv):
    os.chdir(PROJ_ROOT)
    args = __parse_args(argv)
    print('\n[*] platform={} '.format(args.platform))
    print('\n[*] dockername={} '.format(args.dockername))
    print('\n[*] digithumanstuburl={} '.format(args.windisturl))
    print('\n[*] outtempdir={} '.format(args.outtempdir))
    if args.platform == 'linux':
        print('\n 请成记在此添加linux性能自动化测试')
    elif args.platform == 'windows':
        print('\n 请成记在此添加windows性能自动化测试')
