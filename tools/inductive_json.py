import os
import sys
import json
import argparse

# 因为有些case json 键的生成没有固定变量或者没有规律，这里要配合case json过滤
ignore_key_list = ['pass_action', 'pass_nums', 'video_dict', 'fail_action', 'fail_nums', 
                   'model_name', 'inference_name', 'model_dict', 'inference_dict', 'video_dict',
                   'message', 'code']

def get_args(params):
    params = params[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('--innerjson',type=str, help='用例json完整路径')
    parser.add_argument('--outputpath', type=str, help='输出路径')
    parser.add_argument('--testcasescope', type=str, help='用例范畴')
    
    args = parser.parse_args(params)
    return args


def make_more_video_json(output, inner_json_path):
    print('待确定格式')
    #待确定格式
        
        

def make_richer_case_json(output, inner_json_path):
    json_file = open(inner_json_path)
    content = json.load(json_file)
    json_file.close()
    
    richer_map = {
        'result' : str(content['test_report']),
        'case' : []
    }
    print('map init:' + str(richer_map))
    
    inner_detail_map = content['detail']
    for key in inner_detail_map:
        value = inner_detail_map[key]
        for case_key in value:
            if case_key in ignore_key_list:
                continue
            case_value = value[case_key]
        
            if case_value['output'].endswith('.mp4'):
                case_map = {}
                case_map['case_name'] = case_value['action']
                case_map['describe'] = "下个版本同步"
                case_map['output'] = case_value['output']
                if 'original_model' in case_value:
                    case_map['model'] = case_value['original_model']
                if 'original_inference' in case_value:
                    case_map['inference_packages'] = case_value['original_inference']
                if 'original_audio' in case_value:
                    case_map['audio'] = case_value['original_audio']

                richer_map['case'].append(case_map)
    print('map final: ' + str(richer_map))
    with open(os.path.join(output, 'results.json'), 'w+', encoding='utf-8') as fs:
        json.dump(richer_map, fs, indent = 4, ensure_ascii = False) 
    

def main(argv):
    try:
        args = get_args(argv)
        if args.testcasescope in ['SMOKE_CASES', 'API_CASES', 'ALL_CASES', 'VIDEO_BATCH']:
            make_richer_case_json(args.outputpath, args.innerjson)
        print('>>> inductive_json.py -> done')
    except Exception as e:
        print('>>> inductive_json.py -> error: ' + str(e))
    

if __name__ == '__main__' : 
    sys.exit(main(sys.argv))