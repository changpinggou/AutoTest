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
# 引用公共方法
from conf.com_func import ComFunc
com_func = ComFunc()

from tools import process_execute

# DealExcel.get_data() 读excel数据，DealExcel.update_excel()更新excel数据
from conf.deal_excel import DealExcel

# 打印log到终端同时保存到日志文件
from conf.record_log import Logger
logger = Logger(log_path='logs',log_file='test_digital_human.log').get_log()

# 引用基础方法
from conf.base_case import BaseCase



class Test_DigitalHuman:
    def setup_class(self):
        logger.info('~~~~~~start running~~~~~~start running~~~~~~start running~~~~~~')
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        logger.info(f'now_time:{str(now)}')
        self.start_time = time.time()

        # 运行create程序并行数
        self.model_work = 2
        self.inference_work = 5
        self.video_work = 5
                
        # 读取测试数据
        self.excel = DealExcel(excel_name='test_data',sheet_name='ALL_CASES')
        excel_params = DealExcel(excel_name='test_data',sheet_name = 'params')
        self.digital_server = excel_params.get_data(case_name='digital_server',params_name='digital_server')
        print(f'digital_server: {self.digital_server}')
        logger.info(f'{self.digital_server}\n')
        self.output = excel_params.get_data(case_name='output',params_name='output')
        logger.info(f'output: {self.output}')
        self.jinkins_num = excel_params.get_data(case_name='jinkins_num',params_name='jinkins_num')
        logger.info(f'jinkins_num: {self.jinkins_num}')
        self.sys_logs = f"sys_logs_{self.jinkins_num}" # 存放运行接口的系统日志
        
        # 测试完毕，将日志和产物移动到AutoTest_full_path
        AutoTest_path = f'AutoTest_{self.jinkins_num}'
        self.AutoTest_full_path = com_func.mkdir_file(self.output,AutoTest_path)
        logger.info(f'AutoTest_full_path: {self.AutoTest_full_path}')
        self.AutoTest_model = com_func.mkdir_file(self.AutoTest_full_path,'result_models')
        logger.info(f'AutoTest_model: {self.AutoTest_model}')
        self.AutoTest_inference = com_func.mkdir_file(self.AutoTest_full_path,'result_inference')
        self.AutoTest_video = com_func.mkdir_file(self.AutoTest_full_path,'result_video')
        self.AutoTest_audio = com_func.mkdir_file(self.AutoTest_full_path,'use_audio')
        self.AutoTest_log = com_func.mkdir_file(self.AutoTest_full_path,'sys_logs')
        self.json_path = com_func.mkdir_file(PROJ_PARENT_ROOT,'results','result.json')

        # 将测试数据test_data.xlsx复制一份本次测试使用，需要完善逻辑
        test_data = os.path.join(PROJ_PARENT_ROOT, 'conf','test_data.xlsx')
        com_func.cp_file(file_name=test_data,target_path=self.AutoTest_full_path)
        

        # record test result
        self.result = {
            # test_report: test result summary
            "test_report": {"create_time": now,
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



        # 基础case
        self.base_case = BaseCase(self.digital_server,self.result,self.excel,self.sys_logs,self.AutoTest_full_path,self.AutoTest_model,self.AutoTest_inference,self.AutoTest_video,self.AutoTest_audio)

    def teardown_method(self):
        # 每条用例结束后，都执行将self.result写入result.json
        
        with open(self.json_path, 'w') as f:
            f.write(json.dumps(self.result))
        # 将result.json备份到sys_logs_{jenkins_nums}
        com_func.cp_file(file_name=self.json_path,target_path=self.AutoTest_full_path)

    def teardown_class(self):
        self.all_case_use_time = time.time() - self.start_time
        logger.info(f'run all cases use_time:{self.all_case_use_time}')
        # 将/data/digital_datas/sys_logs下的系统日志和结果json传到外部的sys_logs_{jenkins_nums}下
        self.test_log_json_path = f"/data/digital_datas/sys_logs".replace('/',os.path.sep)
        com_func.cp_file(file_path=self.test_log_json_path,target_path=self.AutoTest_log)

        logger.info(f'test_result:\n {json.dumps(self.result, indent=4)}')
        logger.info('~~~~~~done~~~~~~done~~~~~~done~~~~~~done~~~~~~done~~~~~~done~~~~~~')




    @pytest.mark.P0
    @pytest.mark.API
    def test_create_model(self):
        case_name = 'test_create_model'
        logger.info(f'running {case_name}')
        self.base_case.assert_case(case_name=case_name,action='create_model',work=self.model_work)

    
    @pytest.mark.P0
    @pytest.mark.API
    def test_create_inference(self):
        case_name = 'test_create_inference'
        logger.info(f'running {case_name}')
        self.base_case.assert_case(case_name=case_name,action='create_inference',work=self.inference_work)
    
    @pytest.mark.P0
    @pytest.mark.API
    def test_create_inference_interpolation(self):
        case_name = 'test_create_inference_interpolation'
        logger.info(f'running {case_name}')
        self.base_case.assert_case(case_name=case_name,action='create_inference',work=self.inference_work)
    
    @pytest.mark.P0
    @pytest.mark.API
    def test_create_video(self):
        case_name = 'test_create_video'
        logger.info(f'running {case_name}')
        self.base_case.assert_case(case_name=case_name,action='create_video',work=self.video_work)

    @pytest.mark.video_batch
    def test_create_video_batch(self):
        case_name = 'test_create_video_batch'
        logger.info(f'running {case_name}')
        self.base_case.assert_case(case_name=case_name,action='create_video',work=self.video_work)

    @pytest.mark.smoke
    def test_create_video_from_pretrain_model(self):
        case_name = 'test_create_video_from_pretrain_model'
        logger.info(f'running {case_name}')
        self.base_case.assert_case(case_name=case_name,action='create_video',work=self.video_work,pretrain='True')

    @pytest.mark.smoke
    def test_great_change_create_model_inference_video(self):
        case_name = 'test_great_change_create_model_inference_video'
        logger.info(f'running {case_name}')
        state = self.excel.get_data(case_name=case_name,params_name='test_result')
        if state =='PASS':
            # 若用例已测试通过，则跳过执行
            self.result["test_report"]["pass_nums"] = self.result["test_report"]["pass_nums"] + 1
            record_case = f'{case_name}_PASSED_before'
            self.result["test_report"]["pass_cases"].append(record_case)
            logger.info(f'{case_name} has PASSED before')
            pass
        else:
            result_great_change = {
                "action": "test_great_change_create_model_inference_video",
                "pass_action": [],
                "fail_action": []
                }
            quality = self.excel.get_data(case_name=case_name,params_name='quality')
            video_path_to_model = self.excel.get_data(case_name=case_name,params_name='video_path_to_model')
            video_to_model = self.excel.get_data(case_name=case_name,params_name='video_to_model')
            label_config_base64 = self.excel.get_data(case_name=case_name,params_name='label_config_base64')        
            video_path_to_inference = self.excel.get_data(case_name=case_name,params_name='video_path_to_inference')
            video_to_inference = self.excel.get_data(case_name=case_name,params_name='video_to_inference')
            with ThreadPoolExecutor(max_workers=2) as executor:
                logger.info('ready to run create_model/inference')
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
                    logger.info('ready to run create_model/inference')
                    try:
                        assert thread_json["code"] == 0
                        result_great_change["pass_action"].append(action)
                        if action == "create_inference_package":
                            result_great_change["inference_name"] = thread_json["inference_origin"]
                            self.excel.update_excel(case_name=case_name,params_name='result_inference',data=str(thread_json["output"]))
                            result_inference_dict[thread_json["create_inference_log"]] = thread_json["output"]
                            self.result["test_report"]["result_inference_list"].append(result_inference_dict)
                            result_great_change["create_inference_package"] = thread_json
                        elif action == "create_model_from_video":
                            result_great_change["model_name"] = thread_json["model_origin"]
                            self.excel.update_excel(case_name=case_name,params_name='result_model',data=str(thread_json["output"]))
                            result_model_dict[thread_json["create_model_log"]] = thread_json["output"]
                            self.result["test_report"]["result_model_list"].append(result_model_dict)
                            result_great_change["create_model"] = thread_json
                    except AssertionError as e:
                        logger.error(e)
                        result_great_change["fail_action"].append(action)
                        self.result["test_report"]["fail_action"].append("test_great_change_create_model_inference_video")
                        self.excel.update_excel(case_name=case_name, params_name='test_result',data='FAIL')
                        if action == "create_inference_package":
                            result_great_change["create_inference_package"] = thread_json
                            logger.error(f'Fail at:create_inference_package')
                        elif action == "create_model_from_video":
                            result_great_change["create_model"] = thread_json
                            logger.error(f'Fail at:create_model_from_video')

            video_json = {}
            try:
                model_name = result_great_change['model_name'].split('models/')[-1]
                inference_name = result_great_change["inference_name"].split('inference_packages/')[-1]
                audio_name = self.excel.get_data(case_name=case_name,params_name='audio_name')
                video_json = self.base_case.create_video_from_audio(model_name, inference_name,audio_name)            
                assert video_json["code"] == 0
                result_great_change["pass_action"].append("create_video_from_audio")
                result_great_change["code"] = 0
                result_great_change["message"] = 'nothing'
                self.result["test_report"]["pass_nums"] = self.result["test_report"]["pass_nums"]+1
                self.result["test_report"]["pass_cases"].append("test_great_change_create_model_inference_video")
                self.result["test_report"]["result_video_list"].append(video_json["output"])
                self.excel.update_excel(case_name=case_name,params_name='result_video',data=str(video_json["output"]))
                self.excel.update_excel(case_name=case_name, params_name='test_result',data='PASS')
                logger.info(f'test_great_change_model_inference_to_video PASS')
            except AssertionError as e:
                logger.error(e)
                result_great_change["fail_action"].append("create_video_from_audio")
                result_great_change["code"] = -5
                result_great_change["message"] = 'Fail at create_video'
                logger.error(f'Fail at:create_video_from_audio')
                self.result["test_report"]["fail_nums"] = self.result["test_report"]["fail_nums"]+1
                self.result["test_report"]["fail_cases"].append("test_great_change_create_model_inference_video")
                self.excel.update_excel(case_name=case_name, params_name='test_result',data='FAIL')
                raise
            finally:
                result_great_change["create_model"] = video_json
                self.result["detail"][case_name] = result_great_change
                logger.info(f'result_product for test_great_change_create_model_inference_video:{result_great_change}\n')

if __name__ == '__main__':
    logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~running~~~~~~~~~~~~~~~~~~~~~~~~~~~running~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    case_path = os.path.join(PROJ_PARENT_ROOT,"testcase","test_digital_human.py")
    # pytest.main方式执行用例
    pytest.main([f'{case_path}::Test_DigitalHuman::test_create_video','-sv']) 

    # 命令行模式执行用例
    # cmd = f"pytest {case_path}::Test_DigitalHuman::test_create_video -rasv"
    # process_execute.execute_command(cmd)
