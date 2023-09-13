# _*_ coding:UTF-8 _*_
"""
@project -> File :digital_human_code -> digital_human 
@Author: Dora
@Date: 2023/8/11 17:44
"""

import subprocess,datetime,os,sys,stat,json
PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ_PARENT_ROOT = os.path.abspath(os.path.dirname(PROJ_ROOT))
sys.path.insert(0, PROJ_PARENT_ROOT)

print(f'PROJ_ROOT: {PROJ_ROOT}')
print(f'PROJ_PARENT_ROOT: {PROJ_PARENT_ROOT}')
from tools import process_execute

class ComFunc:
    def __init__(self):
        pass

    def mkdir_file(self, father_path,file_path,file_name=''):
        if not os.path.exists(os.path.join(father_path, file_path)):
            os.mkdir(os.path.join(father_path,file_path))
        file_path = os.path.join(father_path, file_path)
        # 在文件夹下再创建文件file_name
        if file_name:
            return os.path.join(file_path,file_name)
        else:
            return file_path
    
    def cp_file(self,target_path,file_path='',file_name=''):
        # 将file_path文件夹下的所有文件，复制到target_path
        #cmd =["echo 'zegoai@test' | sudo -S",'mv',file_path,target_path]
        # -r 递归处理，-f强制覆盖同名文件
        if not file_name:
            cmd = f"echo 'zegoai@test' | sudo -S cp -rf {file_path}/* {target_path}"
        else:
            cmd = f"echo 'zegoai@test' | sudo -S cp -f {file_name} {target_path}"
        process_execute.execute_command(cmd)

if __name__ == '__main__':
    result = {
            # test_report: test result summary
            "test_report": {"create_time": 'now',
             "pass_nums": 0,
             "pass_cases": [],
             "result_model_list": [],
             "result_inference_list": [],
             "result_video_list": [],
             "fail_nums": 0,
             "fail_cases": []
             },
             # detail: run case detail
             "detail": {}
             }
    com_func = ComFunc()
    json_path = com_func.mkdir_file(PROJ_PARENT_ROOT,'results','result.json')
    print(f'json_path: {json_path}')
    with open(json_path, 'w') as f:
        f.write(json.dumps(result))
    
    com_func.mkdir_file(PROJ_PARENT_ROOT,'aa_results')


    
