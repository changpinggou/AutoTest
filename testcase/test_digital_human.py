# _*_ coding:UTF-8 _*_
"""
@project -> File :digital_human_code -> digital_human
@Author: Dora
@Date: 2023/9/10 10:47
@Desc:
1-功能描述：
2-实现步骤：
3-状态（废弃/使用）：
"""

import pytest
import allure
import yaml
import os
import sys
import itertools
import time
import threadpool
import subprocess
import argparse
import datetime, stat,shutil
import json
from time import sleep
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, wait, ALL_COMPLETED

PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ_PARENT_ROOT = os.path.abspath(os.path.dirname(PROJ_ROOT))
sys.path.insert(0, PROJ_PARENT_ROOT)

from tools import process_execute
from conf.read_yaml import ReadElemet
# DealExcel.get_data() 读excel数据，DealExcel.update_excel()更新excel数据
from conf.deal_excel import DealExcel
# 读取配置数据
excel = DealExcel(sheet_name='ALL_CASES')

# 将控制台输出存入日志文件
from conf.pytest_log import Logger
logger = Logger().loggering('test_digital_human_0910')

# 引用基础方法
from conf.base_case import BaseCase



class Test_DigitalHuman:
    def setup_class(self):
        print('~~~~~~start running~~~~~~start running~~~~~~start running~~~~~~')
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        print(f'now_time:{str(now)}')
        self.start_time = time.time()
        excel_params = DealExcel(sheet_name = 'params')
        self.digital_server = excel_params.get_data(case_name='digital_server',params_name='digital_server')
        print(f'digital_server: {self.digital_server}')
        
        self.sys_log_path = excel_params.get_data(case_name='sys_log_path',params_name='sys_log_path')
        print(f'{self.digital_server}\n')
        self.output = excel_params.get_data(case_name='output',params_name='output')
        print(f'output: {self.output}')
        self.jinkins_num = excel_params.get_data(case_name='jinkins_num',params_name='jinkins_num')
        self.result = {
            # 测试结果总结放在第0位置
            "test_report": {"create_time": now,
             "pass_nums": 0,
             "pass_cases": [],
             "result_model_list": [],
             "result_inference_list": [],
             "result_video_list": [],
             "fail_nums": 0,
             "fail_cases": []
             },
             "detail": {}
             }
        print(f'self.result["test_report"]["pass_nums"]: {self.result["test_report"]["pass_nums"]}')
        self.base_case = BaseCase(self.digital_server,self.result)
        # 运行create程序并行数
        self.model_work = 2
        self.inference_work = 5
        self.video_work = 5

    def teardown_method(self):
        sys_log_path = f'sys_logs_{self.jinkins_num}'
        os.chdir(self.output)
        if not os.path.exists(os.path.join(self.output, sys_log_path)):
            os.mkdir(os.path.join(self.output, sys_log_path))
            os.chmod(sys_log_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            
        json_path = os.path.join(PROJ_PARENT_ROOT, "results", "result.json")
        #json_path = os.path.join(output, "result.json") 要把成记给的output传进来
        # with open('/home/aitest/dora/results/result_perftest.json','a+') as f:
        with open(json_path, 'w') as f:
            f.write(json.dumps(self.result))
        print(f'test_report:{type(self.result)},{self.result}')

    def teardown_class(self):
        self.all_case_use_time = time.time() - self.start_time
        print(f'run all cases use_time:{self.all_case_use_time}')
        os.chdir(PROJ_ROOT)
        if not os.path.exists(os.path.join(PROJ_ROOT, 'results')):
            os.mkdir(os.path.join(PROJ_ROOT, 'results'))
            os.chmod('results', stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        json_path = os.path.join(PROJ_PARENT_ROOT, "results", "result.json")
        print('~~~~~~done~~~~~~done~~~~~~done~~~~~~done~~~~~~done~~~~~~done~~~~~~')
    

    @pytest.mark.smoke
    def test_great_change_create_model_inference_video(self):
        case_name = 'test_great_change_create_model_inference_video'
        print(f'running {case_name}')
        state = excel.get_data(case_name=case_name,params_name='test_result')
        if state =='PASS':
            # 若用例已测试通过，则跳过执行
            self.result["test_report"]["pass_nums"] = self.result["test_report"]["pass_nums"] + 1
            record_case = f'{case_name}_PASSED_before'
            self.result["test_report"]["pass_cases"].append(record_case)
            print(f'{case_name} has PASSED before')
            pass
        else:
            result_great_change = {
                "action": "test_great_change_create_model_inference_video",
                "pass_action": [],
                "fail_action": []
                }
            quality = excel.get_data(case_name=case_name,params_name='quality')
            video_path_to_model = excel.get_data(case_name=case_name,params_name='video_path_to_model')
            video_to_model = excel.get_data(case_name=case_name,params_name='video_to_model')
            label_config_base64 = excel.get_data(case_name=case_name,params_name='label_config_base64')        
            video_path_to_inference = excel.get_data(case_name=case_name,params_name='video_path_to_inference')
            video_to_inference = excel.get_data(case_name=case_name,params_name='video_to_inference')
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                future1 = executor.submit(self.base_case.create_model_from_video,video_name=video_to_model, quality=quality,video_path=video_path_to_model)
                future2 = executor.submit(self.base_case.create_inference_package,video_name=video_to_inference, video_path=video_path_to_inference,label_config_base64=label_config_base64)
                futures.append(future1)
                futures.append(future2)
                result_all =[]
                result_model_dict = {}
                result_inference_dict = {}
                for future in as_completed(futures):
                    thread_json = future.result()
                    result_all.append(thread_json)
                    action = thread_json["action"]
                    try:
                        assert thread_json["code"] == 0
                        result_great_change["pass_action"].append(action)
                        if action == "create_inference_package":
                            result_great_change["inference_name"] = thread_json["output"]
                            excel.update_excel(case_name=case_name,params_name='result_inference',data=str(thread_json["output"]))
                            result_inference_dict[thread_json["create_inference_log"]] = thread_json["output"]
                            self.result["test_report"]["result_inference_list"].append(result_inference_dict)
                            result_great_change["create_inference_package"] = thread_json
                        elif action == "create_model_from_video":
                            result_great_change["model_name"] = thread_json["output"]
                            excel.update_excel(case_name=case_name,params_name='result_model',data=str(thread_json["output"]))
                            result_model_dict[thread_json["create_model_log"]] = thread_json["output"]
                            self.result["test_report"]["result_model_list"].append(result_model_dict)
                            result_great_change["create_model"] = thread_json
                    except AssertionError as e:
                        logger.error(e)
                        result_great_change["fail_action"].append(action)
                        self.result["test_report"]["fail_action"].append("test_great_change_create_model_inference_video")
                        excel.update_excel(case_name=case_name, params_name='test_result',data='FAIL')
                        if action == "create_inference_package":
                            result_great_change["create_inference_package"] = thread_json
                            logger.error(f'Fail at:create_inference_package')
                        elif action == "create_model_from_video":
                            result_great_change["create_model"] = thread_json
                            logger.error(f'Fail at:create_model_from_video')

            try:
                model_name = result_great_change["model_name"].split('models/')[-1]
                inference_name = result_great_change["inference_name"].split('inference_packages/')[-1]
                audio_name = excel.get_data(case_name=case_name,params_name='audio_name')
                video_json = self.base_case.create_video_from_audio(model_name, inference_name,audio_name)            
                assert video_json["code"] == 0
                result_great_change["pass_action"].append("create_video_from_audio")
                result_great_change["code"] = 0
                result_great_change["message"] = 'nothing'
                self.result["test_report"]["pass_nums"] = self.result["test_report"]["pass_nums"]+1
                self.result["test_report"]["pass_cases"].append("test_great_change_create_model_inference_video")
                self.result["test_report"]["result_video_list"].append(video_json["output"])
                excel.update_excel(case_name=case_name,params_name='result_video',data=str(video_json["output"]))
                excel.update_excel(case_name=case_name, params_name='test_result',data='PASS')
                print(f'test_great_change_model_inference_to_video PASS')
            except AssertionError as e:
                logger.error(e)
                print(str(e))
                result_great_change["fail_action"].append("create_video_from_audio")
                result_great_change["code"] = -5
                result_great_change["message"] = 'Fail at create_video'
                logger.error(f'Fail at:create_video_from_audio')
                self.result["test_report"]["fail_nums"] = self.result["test_report"]["fail_nums"]+1
                self.result["test_report"]["fail_cases"].append("test_great_change_create_model_inference_video")
                excel.update_excel(case_name=case_name, params_name='test_result',data='FAIL')
                raise
            finally:
                result_great_change["create_model"] = video_json
                self.result["detail"][case_name] = result_great_change
                print(f'result_product for test_great_change_create_model_inference_video:{result_great_change}\n')


    @pytest.mark.P0
    @pytest.mark.API
    def test_create_model(self):
        case_name = 'test_create_model'
        print(f'running {case_name}')
        self.base_case.assert_case(case_name=case_name,action='create_model',work=self.model_work)

    
    @pytest.mark.P0
    @pytest.mark.API
    def test_create_inference(self):
        case_name = 'test_create_inference'
        print(f'running {case_name}')
        self.base_case.assert_case(case_name=case_name,action='create_inference',work=self.inference_work)
    
    @pytest.mark.P0
    @pytest.mark.API
    def test_create_inference_interpolation(self):
        case_name = 'test_create_inference_interpolation'
        print(f'running {case_name}')
        self.base_case.assert_case(case_name=case_name,action='create_inference',work=self.inference_work)
    
    @pytest.mark.P0
    @pytest.mark.API
    def test_create_video(self):
        case_name = 'test_create_video'
        print(f'running {case_name}')
        self.base_case.assert_case(case_name=case_name,action='create_video',work=self.video_work)


if __name__ == '__main__':
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~当前运行~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    pytest.main(['/home/aitest/dora/testcase/test_digital_human.py::Test_DigitalHuman::test_great_change_create_model_inference_video','-sv']) 
    print('everything is good')