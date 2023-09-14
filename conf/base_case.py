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
# 引用公共方法
from conf.com_func import ComFunc
com_func = ComFunc()

# 打印log到终端同时保存到日志文件
from conf.record_log import Logger
logger = Logger(log_path='logs',log_file='test_digital_human.log').get_log()

class BaseCase:
    def __init__(self,digital_server,result,excel,sys_logs,AutoTest_full_path,AutoTest_model,AutoTest_inference,AutoTest_video,AutoTest_audio):
        self.digital_server = digital_server
        self.result = result  # record test result json
        self.excel = excel  # test data
        self.sys_logs = sys_logs

        # 测试完毕，将日志和产物移动到AutoTest_full_path
        self.AutoTest_full_path = AutoTest_full_path
        logger.info(f'AutoTest_full_path: {self.AutoTest_full_path}')
        self.AutoTest_model = AutoTest_model
        self.AutoTest_inference = AutoTest_inference
        self.AutoTest_video = AutoTest_video
        self.AutoTest_audio = AutoTest_audio
        logger.info(f'AutoTest_model: {self.AutoTest_model}')

        # 终端输出日志，若run_logs不存在则创建
        self.run_logs = com_func.mkdir_file(PROJ_PARENT_ROOT,'run_logs')

    def create_model_from_video(self, video_name, video_path='1_test_origin_video', quality='train_quality_demo'):
        start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        video_full_path = ''
        if type(video_name) == str:
            # 传入单个视频，使用单个视频训练model
            #create_model_log = 'create_model_'+quality+'_'+video_name.split('.')[0]+'_'+start_time
            create_model_log = f"create_model_{quality}_{video_name.split('.')[0]}_{start_time}"
            video_full_path = f"test/{video_path}/{video_name}".replace('/',os.path.sep)
        elif len(video_name) > 1:
            # 多个视频拼接训练model（v1.6.0开始支持），使用第一个和最后一个video命名
            create_model_log = f"create_model_{quality}_{video_name[0].split('.')[0]}_{video_name[-1].split('.')[0]}_{start_time}"
            for video in video_name:
                #video_full_path += 'test'+ os.path.sep + video_path +os.path.sep +video +','
                video_full_path += f"test/{video_path}/{video},".replace('/',os.path.sep)
            video_full_path = video_full_path.strip(',')
            logger.info(f'video_name: {video_full_path}')

        result_json = f"{create_model_log}.json"
        # 终端输出日志
        cmd_log_path = os.path.join(self.run_logs,f"{create_model_log}.log")
        logger.info(f'cmd_log_path: {cmd_log_path}\n')

        cmd = f"echo 'zegoai@test' | sudo -S docker exec -i {self.digital_server} ./dist/run/run --action create_model_from_video --video_path {video_full_path} --data_root /data --profile {quality} --output_file {self.sys_logs}/{result_json} --log_file {self.sys_logs}/{create_model_log}.log --debug > {cmd_log_path} 2>&1".replace('/',os.path.sep)
        logger.info(f'create_model cmd:\n {cmd}\n')

        with ProcessPoolExecutor(max_workers=2) as executor:
            feature = executor.submit(process_execute.execute_command, cmd)
            use_time = feature.result()

        json_path = f'/data/digital_datas/{self.sys_logs}/{result_json}'.replace('/',os.path.sep)
        logger.info(f'result_json_path:{json_path}')
        model_json = {"action": "create_model_from_video"}
        if os.path.exists(json_path):
            log_cmd = f'cat {json_path}'
            logger.info(f'model_result:{os.popen(log_cmd).read()}')
            result_json = os.popen(log_cmd).read()
            result_dict = json.loads(result_json)  # 将json内容转为字典
            code = result_dict['code']

            if code == 0:
                # new_model_path = os.path.join('/data/digital_datas/', model_name)
                model_json["code"] = code
                model_json["message"] = "nothing"

                # 完整格式： "model_path": "models/af74d800-5f1e-4521-9a31-c0211da47fa1/af74d800-5f1e-4521-9a31-c0211da47fa1.zip"
                # model 只取xx.zip部分
                model_origin = result_dict['data']['model_path']
                model_zip = model_origin.split(str(os.path.sep))[-1]
                model_json["model_name"] = model_zip
                model_path = f"/data/digital_datas/{model_origin}".replace('/',os.path.sep)
                logger.info(f'model_path: {type(model_path)}\n,{model_path}')

                # 备份model（此处做cp，保留源model）
                com_func.cp_file(file_name=model_path,target_path=self.AutoTest_model)
                # model写移动后到位置
                model_json["output"] = os.path.join(self.AutoTest_model,model_zip)
                logger.info(f'result model path after cp: {model_json["output"]}')

                model_json["quality"] = quality
                model_json["original_video"] = result_dict['data']['video_path']
                model_json["use_time"] = round(use_time, 3)
                model_json["ai_temp"] = result_dict['data']['model_id']
                model_json["create_model_log"] = create_model_log
                logger.info(f'model_name: {model_json["output"]}')
            else:
                logger.error('create_model fail')
                msg = result_dict['message']
                model_json["code"] = code
                model_json["message"] = msg
                model_json["output"] = "null"
                model_json["command_log_path"] = cmd_log_path
                model_json["create_model_log"] = create_model_log
                logger.error('error code:{},msg:{}'.format(code, msg))
                #logger.info(f'original_video: {video_name}')

        elif os.path.exists(cmd_log_path):
            # 当前时间 - 终端输出日志最新修改时间，若超过1分钟未修改，视为已经停止推理视频
            if (time.time() - os.path.getmtime(cmd_log_path)) > 60:
                # 没有生成json文件（通过第一个if得知），且终端日志1分钟左右没更新,视为异常中断
                model_json["code"] = -1
                model_json["message"] = "Fail,no result_json"
                model_json["output"] = "null"
                model_json["command_log_path"] = cmd_log_path
                logger.info(f'create_mode fail,cmd log:{cmd_log_path}')
            else:
                model_json["code"] = -2
                model_json["message"] = "Fail,no cmd log"
                model_json["output"] = "null"
                model_json["command_log_path"] = "null"
                logger.info('create_mode Fail,no cmd log')
        return model_json

    def create_inference_package(self, video_name,label_config_base64,video_path='1_test_clip_video'):
        # label_config_base64是否带插帧包，value格式: --label_config_base64 ewogICJmcmFtZXMiOiBbCiAgICAiMDA6MDA6MDA6NCIsCiAgICAiMDA6MDA6MDE6MTAiLAogICAgIjAwOjAwOjI6MTYiLAogICAgIjAwOjAwOjU6MTgiLAogICAgIjAwOjAwOjMwOjEwIiwKICAgICIwMDowMDo1MjoxMCIsCiAgICAiMDA6MDA6NTY6OSIKICBdLAogICJhY3Rpb24iOiBbCiAgICB7CiAgICAgICJuYW1lIjogImhlc2h1aSIsCiAgICAgICJzdGFydF90aW1lIjogIjAwOjAwOjAwOjAwIiwKICAgICAgImVuZF90aW1lIjogIjAwOjAwOjEwOjAwIgogICAgfSwKICAgIHsKICAgICAgIm5hbWUiOiAieHgiLAogICAgICAic3RhcnRfdGltZSI6ICIwMDowMDoxMDowMCIsCiAgICAgICJlbmRfdGltZSI6ICIwMDowMDoyMDowMCIKICAgIH0KICBdCn0K 
        start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        logger.info(f'start time: {start_time}')
        video_full_path = f"test/{video_path}/{video_name}".replace('/',os.path.sep)
        create_inference_log = f"create_inference_package_{video_name.split('.')[0]}_{start_time}"
        result_json = f"{create_inference_log}.json"
        # 终端输出日志
        cmd_log_path = os.path.join(self.run_logs,f"{create_inference_log}.log")
        cmd = ''
        if label_config_base64:
            cmd = f"echo 'zegoai@test' | sudo -S docker exec -i {self.digital_server} ./dist/run/run --action create_inference_package --video_path {video_full_path} --data_root /data --output_file {self.sys_logs}/{result_json} --log_file {self.sys_logs}/{create_inference_log}.log --debug  {label_config_base64} > {cmd_log_path} 2>&1".replace('/',os.path.sep)
        else:
            cmd = f"echo 'zegoai@test' | sudo -S docker exec -i {self.digital_server} ./dist/run/run --action create_inference_package --video_path {video_full_path} --data_root /data --output_file {self.sys_logs}/{result_json} --log_file {self.sys_logs}/{create_inference_log}.log --debug > {cmd_log_path} 2>&1".replace('/',os.path.sep)
        logger.info(f'create_inference cmd:\n {cmd}\n')
        with ProcessPoolExecutor(max_workers=5) as executor:
            feature = executor.submit(process_execute.execute_command, cmd)
            use_time = feature.result()

        json_path = f'/data/digital_datas/{self.sys_logs}/{result_json}'.replace('/',os.path.sep)
        logger.info(f'result_json_path:{json_path}')
        inference_json = {"action": "create_inference_package"}
        if os.path.exists(json_path):
            json_cmd = f'cat {json_path}'
            logger.info(f'inference_result: {os.popen(json_cmd).read()}')
            result_json = os.popen(json_cmd).read()
            result_dict = json.loads(result_json)  # 将json内容转为字典
            code = result_dict['code']
            if code == 0:
                inference_json["code"] = code
                inference_json["message"] = "nothing"

                # 完整格式："output_path": "inference_packages/e2e6a813-e0ba-4259-87c6-4fc1deedf906.zip"
                inference_origin = result_dict['data']['output_path']
                inference_zip = inference_origin.split(str(os.path.sep))[-1]
                inference_json["inference_name"] = inference_zip
                inference_origin_path = f"/data/digital_datas/{inference_origin}".replace('/',os.path.sep)
                logger.info(f'inference_path: {type(inference_origin_path)}\n,{inference_origin_path}')
                # 备份inference（此处做cp，保留源inference）
                com_func.cp_file(file_name=inference_origin_path,target_path=self.AutoTest_inference)
                # inference写移动后到位置
                inference_json["output"] = os.path.join(self.AutoTest_inference,inference_zip)
                logger.info(f'result inference path after cp: {inference_json["output"]}')

                inference_json["original_video"] = video_name
                inference_json["use_time"] = round(use_time, 3)
                inference_json["create_inference_log"] = create_inference_log
                logger.info(f'inference_name: {inference_json["output"]}')
                # 插帧包
                if label_config_base64:                    
                    interpolation_origin = result_dict['data']['interpolation_path']
                    interpolation_zip = interpolation_origin.split(str(os.path.sep))[-1]
                    interpolation_origin_path = f"/data/digital_datas/{interpolation_origin}".replace('/',os.path.sep)
                    logger.info(f'interpolation_path: {type(interpolation_origin_path)}\n,{interpolation_origin_path}')
                    # 备份interpolation（此处做cp，保留源interpolation）
                    com_func.cp_file(file_name=interpolation_origin_path,target_path=self.AutoTest_inference)
                    # inference写移动后到位置
                    inference_json["interpolation_path"] = os.path.join(self.AutoTest_inference,interpolation_zip)
                    logger.info(f'result interpolation path after cp: {inference_json["interpolation_name"]}')
            else:
                logger.error('create_inference_package fail')
                msg = result_dict['message']
                inference_json["code"] = code
                inference_json["message"] = msg
                inference_json["output"] = "null"
                inference_json["result_json"] = json_path
                inference_json["command_log_path"] = cmd_log_path
                logger.error('error code:{},msg:{}'.format(code, msg))
                logger.info(f'original_video_to_inference: {video_name}')

        elif os.path.exists(cmd_log_path):
            # 当前时间 - 终端输出日志最新修改时间，若超过1分钟未修改，视为已经停止推理视频
            if (time.time() - os.path.getmtime(cmd_log_path)) > 60:
                # 没有生成json文件（通过第一个if得知），且终端日志1分钟左右没更新,视为异常中断
                inference_json["code"] = -1
                inference_json["message"] = "create inference package fail, neither no result_json"
                inference_json["output"] = "null"
                inference_json["command_log_path"] = cmd_log_path
                logger.error('create_inference fail,cmd log:\n {}'.format(cmd_log_path))
            else:
                inference_json["code"] = -2
                inference_json["message"] = "run cmd fail, neither no cmd log"
                inference_json["output"] = "null"
                inference_json["command_log_path"] = "null"
                logger.error('create_inference fail, neither no cmd log')
        return inference_json

    def create_video_from_audio(self, model_name, inference_name, audio_name, model_path='',inference_path='',audio_path='1_official_audio',pretrain='False'):
        start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        audio_full_path = f"test/{audio_path}/{audio_name}".replace('/',os.path.sep)
        model_mark = ''
        if os.path.sep in model_name:
            model_mark = model_name.split(os.path.sep)[0]
        else:
            model_mark = model_name.split('.zip')[0]
        create_video_log = f"create_video_{model_mark}_{audio_name.split('.')[0]}_{start_time}".replace('/',os.path.sep)
        result_json = f"{create_video_log}.json"
        # 终端输出日志
        cmd_log_path = os.path.join(self.run_logs,f"{create_video_log}.log")
        logger.info(f'cmd_log_path:{cmd_log_path}\n')
        
        cmd = f"echo 'zegoai@test' | sudo -S docker exec -i {self.digital_server} ./dist/run/run --action create_video_from_audio --model_path models/{model_name} --inference_package_path inference_packages/{inference_name} --data_root /data --log_file {self.sys_logs}/{create_video_log}.log --output_file {self.sys_logs}/{result_json} --audio_path {audio_full_path} --audio_language 'zh-CN' --use_pretrain_model {pretrain} > {cmd_log_path}".replace('/',os.path.sep)        #logger.info(f"create_model command:{cmd}\n")
        logger.info(f'create_video cmd:\n {cmd}\n')

        with ProcessPoolExecutor(max_workers=5) as executor:
            feature = executor.submit(process_execute.execute_command, cmd)
            use_time = feature.result()
        
        # 将所用的model、inference、audio备份到{output}_{jenkins_num}
        model_backup = f'/data/digital_datas/models/{model_name}'.replace('/',os.path.sep)
        com_func.cp_file(file_name=model_backup,target_path=self.AutoTest_model)
        inference_backup = f'/data/digital_datas/inference_packages/{inference_name}'.replace('/',os.path.sep)
        com_func.cp_file(file_name=inference_backup,target_path=self.AutoTest_inference)
        audio_backup = f'/data/digital_datas/test/{audio_path}/{audio_name}'.replace('/',os.path.sep)
        com_func.cp_file(file_name=audio_backup,target_path=self.AutoTest_audio)

        json_path = f'/data/digital_datas/{self.sys_logs}/{result_json}'.replace('/',os.path.sep)
        logger.info(f'result_json_path:{json_path}')
        video_json = {
            "action": "create_video_from_audio",
            "original_model": os.path.join(self.AutoTest_model,f'{model_mark}.zip'),
            "original_inference": os.path.join(self.AutoTest_inference,inference_name),
            "original_audio": os.path.join(self.AutoTest_audio,audio_name)
            }
        """
        video_json["original_model"] = os.path.join(self.AutoTest_model,f'{model_mark}.zip')
        video_json["original_inference"] = os.path.join(self.AutoTest_inference,inference_name)
        video_json["original_audio"] = os.path.join(self.AutoTest_audio,audio_name)
        """
        if os.path.exists(json_path):
            log_cmd = f'cat {json_path}'
            logger.info(f'video_result: {os.popen(log_cmd).read()}')
            result_json = os.popen(log_cmd).read()
            result_dict = json.loads(result_json)  # 将json内容转为字典
            code = result_dict['code']

            if code == 0:
                video_json["code"] = code
                video_json["message"] = "nothing"
                # 备份result video
                # 完整格式： "video_path": "results/b31fff12-98ac-4c54-bf19-39225a0f1cc8.mp4"
                # video 只取xx.mp4部分
                video_origin = result_dict['data']['video_path']
                video_mp4 = video_origin.split(str(os.path.sep))[-1]
                
                video_origin_path = f"/data/digital_datas/{video_origin}".replace('/',os.path.sep)
                logger.info(f'result video original path: {type(video_origin_path)}\n,{video_origin_path}')
                # 备份video（此处做cp，保留源video）
                com_func.cp_file(file_name=video_origin_path,target_path=self.AutoTest_video)
                # video写移动后到位置
                video_json["output"] = os.path.join(self.AutoTest_video,video_mp4)
                logger.info(f'result video path after cp: {video_json["output"]}')


                video_json["use_time"] = round(use_time, 3)
                video_json["create_video_log"] = create_video_log
                logger.info(f'video_name: {video_json["output"]}')
            else:
                logger.error('create_video fail')
                msg = result_dict['message']
                video_json["code"] = code
                video_json["message"] = msg
                video_json["output"] = "null"
                video_json["command_log_path"] = cmd_log_path
                video_json["create_video_log"] = create_video_log
                logger.error('error code:{},msg:{}'.format(code, msg))
                logger.info(f'original_audio: {audio_name}')

        elif os.path.exists(cmd_log_path):
            # 当前时间 - 终端输出日志最新修改时间，若超过1分钟未修改，视为已经停止推理视频
            if (time.time() - os.path.getmtime(cmd_log_path)) > 60:
                # 没有生成json文件（通过第一个if得知），且终端日志1分钟左右没更新,视为异常中断
                video_json["code"] = -1
                video_json["message"] = "Fail,no result_json"
                video_json["output"] = "null"
                video_json["command_log_path"] = cmd_log_path
                logger.info(f'create_video fail,cmd log:{cmd_log_path}')
            else:
                video_json["code"] = -2
                video_json["message"] = "Fail,no cmd log"
                video_json["output"] = "null"
                video_json["command_log_path"] = "null"
                logger.info('create_video Fail,no cmd log')
        return video_json
    

    def case_create_model(self, case_name,model_work=1):
        quality = self.excel.get_data(case_name=case_name,params_name='quality')
        print(f'quality instance: {quality}')
        video_path_to_model = self.excel.get_data(case_name=case_name,params_name='video_path_to_model')
        print(f'video_path_to_model: {video_path_to_model}')
        video_to_model = self.excel.get_data(case_name=case_name,params_name='video_to_model')

        video_list = []
        if type(video_to_model) == str:
            video_list.append(video_to_model)
        else:
            video_list = video_to_model

        result_models = {
             "pass_action": [],
             "pass_nums": 0,
             "model_dict": {},
             "fail_action": [],
             "fail_nums": 0
             }
        with ThreadPoolExecutor(max_workers=model_work) as executor:
            futures = [executor.submit(self.create_model_from_video,video_name=video_name, quality=quality,video_path=video_path_to_model) for video_name in video_list]

            for future in as_completed(futures):
                model_json = future.result()
                if model_json["code"] == 0:
                    logger.info(f'model_json["create_model_log"]: {model_json["create_model_log"]}')
                    result_models["model_dict"][model_json["create_model_log"]] = model_json["output"]
                    result_models["pass_action"].append(f'{case_name}--{model_json["create_model_log"]}')
                    result_models["pass_nums"] = result_models["pass_nums"] + 1
                    result_models[f'{case_name}_{model_json["create_model_log"]}'] = model_json

                else:
                    start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
                    result_models["fail_action"].append(f'{case_name}_{start_time}')
                    result_models["fail_nums"] = result_models["fail_nums"] + 1
                    result_models[f'{case_name}_{start_time}'] = model_json

        # 将产物model一起写入测试数据文件test_data.xlsx
        self.excel.update_excel(case_name=case_name,params_name='result_model',data=str(result_models["model_dict"]))
        self.result["test_report"]["result_model_list"].append(result_models["model_dict"])
        if (result_models["pass_nums"] > 0) and (result_models["fail_nums"] == 0):
            self.result["test_report"]["pass_nums"] = self.result["test_report"]["pass_nums"] + 1
            self.result["test_report"]["pass_cases"].append(case_name)
        else:
            self.result["test_report"]["fail_nums"] = self.result["test_report"]["fail_nums"] + 1
            self.result["test_report"]["fail_cases"].append(case_name)
            
        self.result["detail"][case_name] = result_models
        return result_models
    
    def case_create_inference(self, case_name,inference_work=1):
        label_config_base64 = self.excel.get_data(case_name=case_name,params_name='label_config_base64')        
        video_path_to_inference = self.excel.get_data(case_name=case_name,params_name='video_path_to_inference')
        video_to_inference = self.excel.get_data(case_name=case_name,params_name='video_to_inference')

        video_list = []
        if type(video_to_inference) == str:
            video_list.append(video_to_inference)
        else:
            video_list = video_to_inference

        result_inferences = {
             "pass_action": [],
             "pass_nums": 0,
             "inference_dict": {},
             "fail_action": [],
             "fail_nums": 0
             }
        result_inference_dict = {}
        with ThreadPoolExecutor(max_workers=inference_work) as executor:
            futures = [executor.submit(self.create_inference_package,video_name=video_name, video_path=video_path_to_inference,label_config_base64=label_config_base64) for video_name in video_list]
            for future in as_completed(futures):
                inference_json = future.result()
                if inference_json["code"] == 0:
                    print(f'inference_json["create_inference_log"]: {inference_json["create_inference_log"]}')
                    result_inferences["inference_dict"][inference_json["create_inference_log"]] = inference_json["output"]
                    result_inferences["pass_action"].append(f'{case_name}--{inference_json["create_inference_log"]}')
                    result_inferences["pass_nums"] = result_inferences["pass_nums"] + 1
                    result_inference_dict[inference_json["create_inference_log"]] = inference_json["output"]
                    result_inferences[f'{case_name}_{inference_json["create_inference_log"]}'] = inference_json

                else:
                    start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
                    result_inferences["fail_action"].append(f'{case_name}_{start_time}')
                    result_inferences["fail_nums"] = result_inferences["fail_nums"] + 1
                    result_inferences[f'{case_name}_{start_time}'] = inference_json

        # 将产物inference一起写入测试数据文件test_data.xlsx
        self.excel.update_excel(case_name=case_name,params_name='result_inference',data=str(result_inferences["inference_dict"]))
        self.result["test_report"]["result_inference_list"].append(result_inference_dict)
        if (result_inferences["pass_nums"] > 0) and (result_inferences["fail_nums"] == 0):
            self.result["test_report"]["pass_nums"] = self.result["test_report"]["pass_nums"] + 1
            self.result["test_report"]["pass_cases"].append(case_name)
        else:
            self.result["test_report"]["fail_nums"] = self.result["test_report"]["fail_nums"] + 1
            self.result["test_report"]["fail_cases"].append(case_name)
            
        self.result["detail"][case_name] = result_inferences
        return result_inferences


    def case_create_video(self, case_name,video_work=5,pretrain='False'):
        input_model = self.excel.get_data(case_name=case_name,params_name='input_model')
        input_inference = self.excel.get_data(case_name=case_name,params_name='input_inference')
        audio_path = self.excel.get_data(case_name=case_name,params_name='audio_path')
        audio_name = self.excel.get_data(case_name=case_name,params_name='audio_name')

        audio_list = []
        if type(audio_name) == str:
            audio_list.append(audio_name)
        else:
            audio_list = audio_name
        result_videos = {
             "pass_action": [],
             "pass_nums": 0,
             "video_dict": {},
             "fail_action": [],
             "fail_nums": 0
             }
        result_video_list = []
        with ThreadPoolExecutor(max_workers=video_work) as executor:
            futures = [executor.submit(self.create_video_from_audio,model_name=input_model, inference_name=input_inference,audio_path=audio_path,audio_name=audio,pretrain=pretrain) for audio in audio_list]

            for future in as_completed(futures):
                video_json = future.result()
                if video_json["code"] == 0:
                    logger.info(f'video_json["create_video_log"]: {video_json["create_video_log"]}')
                    result_videos["video_dict"][video_json["create_video_log"]] = video_json["output"]
                    result_videos["pass_action"].append(f'{case_name}--{video_json["create_video_log"]}')
                    result_videos["pass_nums"] = result_videos["pass_nums"] + 1
                    result_videos[f'{case_name}_{video_json["create_video_log"]}'] = video_json
                    #result_video_dict[video_json["create_video_log"]] = video_json["output"]
                    self.result["test_report"]["result_model_list"].append(video_json["output"])
                    result_video_list.append(video_json["output"])


                else:
                    start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
                    result_videos["fail_action"].append(f'{case_name}_{start_time}')
                    result_videos["fail_nums"] = result_videos["fail_nums"] + 1
                    result_videos[f'{case_name}_{start_time}'] = video_json

        # 将产物model一起写入测试数据文件test_data.xlsx
        self.excel.update_excel(case_name=case_name,params_name='result_video',data=str(result_video_list))
        #self.result["test_report"]["result_model_list"].append(result_video_dict)
        if (result_videos["pass_nums"] > 0) and (result_videos["fail_nums"] == 0):
            self.result["test_report"]["pass_nums"] = self.result["test_report"]["pass_nums"] + 1
            self.result["test_report"]["pass_cases"].append(case_name)
        else:
            self.result["test_report"]["fail_nums"] = self.result["test_report"]["fail_nums"] + 1
            self.result["test_report"]["fail_cases"].append(case_name)
            
        self.result["detail"][case_name] = result_videos
        logger.info(f'result_videos: {result_videos}')
        return result_videos
    
    def assert_case(self,case_name,action,work='2',pretrain='False'):
        state = self.excel.get_data(case_name=case_name,params_name='test_result')
        if state =='PASS':
            # 若用例已测试通过，则跳过执行
            self.result["test_report"]["pass_nums"] = self.result["test_report"]["pass_nums"] + 1
            record_case = f'{case_name}_PASSED_before'
            self.result["test_report"]["pass_cases"].append(record_case)
            logger.info(f'{case_name} has PASSED before')
            pass
        else:
            try:
                if action == 'create_model':
                    result = self.case_create_model(case_name,model_work=work)
                elif action == 'create_inference':
                    result = self.case_create_inference(case_name,inference_work=work)
                elif action == 'create_video':
                    result = self.case_create_video(case_name=case_name,pretrain=pretrain,video_work=5)
                assert (result["pass_nums"] > 0) and (result["fail_nums"] == 0)
                self.excel.update_excel(case_name=case_name, params_name='test_result',data='PASS')
            except AssertionError as e:
                logger.error(e)
                print(e)
                self.excel.update_excel(case_name=case_name, params_name='test_result',data='FAIL')
                raise

if __name__ == '__main__':
    logger.info(f'PROJ_ROOT: {PROJ_ROOT}')
    logger.info(f'PROJ_PARENT_ROOT: {PROJ_PARENT_ROOT}')
    


        



            
    