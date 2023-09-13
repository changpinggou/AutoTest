import os
import sys
import json
import argparse


def get_args(params):
    params = params[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('--inner_json_path',type=str, help='用例json完整路径')
    parser.add_argument('--output', type=str, help='输出路径')
    
    args = parser.parse_args(params)
    return args


def make_json(output, inner_json_path):
    json_file = open(inner_json_path)
    content = json.load(json_file)
    json_file.close()
    
    map = {
        'create_time' : content['test_report']['create_time'],
        'case' : []
    }
    
    inner_detail_map = content['detail']
    for key in inner_detail_map:
        case_map = {}
        value = inner_detail_map[key]
        case_map['case_name'] = value['action']
        case_map['describe'] = '下个版本同步'
        case_map['model'] = value['create_model']['original_model']
        case_map['inference_packages'] = value['create_model']['original_inference']
        case_map['audio'] = value['create_model']['original_audio']
        case_map['output'] = value['create_model']['output']
        
        map['case'].append(case_map)
        
    with open(os.path.join(output, 'results.json'), 'w+') as fs:
        json.dump(map, fs, indent = 4) 
    

def main(argv):
    try:
        args = get_args(argv)
        make_json(args.output, args.inner_json_path)
        print('>>> inductive_json.py -> done')
    except Exception as e:
        print('>>> inductive_json.py -> error: ' + str(e))
    

if __name__ == '__main__' : 
    sys.exit(main(sys.argv))