from ast import arg
import os
import sys
import json
from json2html import json2html
from tools.zegoPy.zegopy.builder.zego_artifactory import ZegoArtifactory
import argparse
import socket
import tools.docker_ctrl as docker_ctrl
import testcase.run_case as run_case
PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))

def __parse_args(args):
    args = args[1:]
    parser = argparse.ArgumentParser(description='The root build script.')

    parser.add_argument('--platform', type=str, choices=['linux', 'windows'], default='linux',
                        help='性能测试平台, default:linux')
    parser.add_argument('--jenkins', default=False, action='store_true',  help='Whether build in jenkins')
    parser.add_argument('--dockername', type=str, default='v1.5.1.64-202308161414-d450a5d8', help='打包出来的docker文件名')
    parser.add_argument('--digithumanstuburl', type=str, default='', help='打包出来的windows产物压缩包地址')
    parser.add_argument('--digithumanstublocalpath', type=str, default='', help='打包出来的windows产物压缩包本地地址')
    parser.add_argument('--runtype', type=str, default='', help='')
    parser.add_argument('--outtempdir', type=str, default='', help='临时输出目录')
    parser.add_argument('--testcasescope', type=str, default='CI', help='测试用例范畴')
    parser.add_argument('--buildnumber', type=str, help='jenkins任务序号')
    parser.add_argument('--outputpath', type=str, default='', help='输出路径')

    return parser.parse_args(args)

def run_linux_interface(args):
    docker_controller = docker_ctrl.DockerController()
    docker_container_id, docker_server_name = docker_controller.get_docker(args.dockername)
    if not os.path.exists(args.outputpath):
        os.mkdir(args.outputpath)
    
    #interface main function   
    # run_case.run_case(docker_container_id, args.outputpath, args.testcasescope)
    run_case.run_case(docker_container_id, args.outputpath, args.testcasescope, args.buildnumber)

    docker_controller.del_docker(docker_container_id)
    
def main(argv):
    os.chdir(PROJ_ROOT)
    args = __parse_args(argv)
    print('\n[*] platform={} '.format(args.platform))
    print('\n[*] dockername={} '.format(args.dockername))
    print('\n[*] digithumanstuburl={} '.format(args.digithumanstuburl))
    print('\n[*] digithumanstublocalpath={} '.format(args.digithumanstublocalpath))
    print('\n[*] runtype={} '.format(args.runtype))
    print('\n[*] outtempdir={} '.format(args.outtempdir))
    print('\n[*] outputpath={} '.format(args.outputpath))
    
    if args.platform == 'linux':
        print('\nrun linux interface test')
        run_linux_interface(args)
        print('\nlinux test finish')
    elif args.platform == 'windows':
        print('\nrun windows interface test')
        print('\nwindow test finish')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))