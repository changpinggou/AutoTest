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
    parser.add_argument('--buildnumber', type=str, help='jenkins自行建立的序号')
    parser.add_argument('--dockername', type=str, default='v1.5.1.64-202308161414-d450a5d8', help='打包出来的docker文件名')
    parser.add_argument('--digithumanstuburl', type=str, default='', help='打包出来的windows产物压缩包地址')
    parser.add_argument('--digithumanstublocalpath', type=str, default='', help='打包出来的windows产物压缩包本地地址')
    parser.add_argument('--runtype', type=str, default='', help='')
    parser.add_argument('--outtempdir', type=str, default='', help='临时输出目录')
    parser.add_argument('--testcasescope', type=str, default='CI', help='测试用例范畴')
    parser.add_argument('--outputpath', type=str, default='', help='输出路径')

    return parser.parse_args(args)

    
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
    
    docker_controller = docker_ctrl.DockerController()
    docker_container_id, docker_server_name = docker_controller.get_docker(args.dockername)
    if not os.path.exists(args.outputpath):
        os.mkdir(args.outputpath)
    
    if args.platform == 'linux':
        print('\nlinux run linux interface test')
        print('args.runtype is ')
        run_case.run_case(docker_container_id, args.outputpath, args.testcasescope, args.buildnumber)
    elif args.platform == 'windows':
        print('\nlinux run windows interface test')

    json_content = json.load(open(os.path.join(PROJ_ROOT, 'results', 'result.json'), 'r'))
    interface_json = json_content[0]
    map = {
        "type" : interface_json['action'],
        "date" : interface_json['create_time'],
        "state" : f"All Task: {str(interface_json['PASS_nums'] + interface_json['Fail_nums'])};Success:{str(interface_json['PASS_nums'])},Faild:{str(interface_json['Fail_nums'])}"
    }

    # write to new html
    # #临时目录output
    output_dir = os.path.abspath(os.path.join(args.outputpath, os.path.pardir, 'result.html'))
    with open(output_dir, 'w') as html_write:
        map['model_json'] = interface_json['model_json_path']
        map['inference_json'] = interface_json['inference_json_path']
        map['video_json'] = interface_json['video_json_path']
        html_content = json2html.convert(json=map)
        html_write.write(html_content)

    artifact_name = output_dir.split(os.path.sep)[-1]
    artifactory = ZegoArtifactory()
    artifactory.set_raise_exception(True)
    dockername = args.dockername
    artifactory.set_version(dockername.split('-')[0] + '_' + map['date'])
    url = artifactory.upload('digithuman', 'public', artifact_name, output_dir)
    map['link'] = url
    
    # write to new json
    json_path = os.path.abspath(os.path.join(args.outputpath, os.path.pardir, 'result.json'))
    with open(json_path, 'w') as json_write:
        json.dump(map, json_write)

    docker_controller.del_docker(docker_container_id)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))