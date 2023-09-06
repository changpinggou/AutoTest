# _*_ coding:UTF-8 _*_
"""
@project -> File :digital_human_code -> digital_human
@Author: Dora
@Date: 2023/6/6 22:47
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
import datetime
import threadpool
import subprocess
import argparse
import datetime, random, requests
import json
from time import sleep
from tools import process_execute
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, wait, ALL_COMPLETED

PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ_PARENT_ROOT = os.path.abspath(os.path.dirname(PROJ_ROOT))
parentdir = os.path.dirname(PROJ_ROOT)
sys.path.insert(0, parentdir)
# sys.path.insert(0, r'/home/aitest/dora/')
from conf.read_yaml import ReadElemet

# 将控制台输出存入日志文件
from conf import pytest_log

logger = pytest_log.log_test

# 读取配置数据
#
data_yaml = ReadElemet(fileName='data')
yaml = data_yaml.All_element()


class Test_DigitalHuman:
    def setup_class(self, _yaml):
        logger.info('~~~~~~start running~~~~~~start running~~~~~~start running~~~~~~')
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        logger.info(f'now_time:{now}')
        yaml = _yaml
        self.start_time = time.time()
        self.digital_server = yaml['digital_server']
        logger.info(f'{self.digital_server}\n')
        self.result = [
            # 测试结果总结放在第0位置
            {"action": "test_report",
             "create_time": now,
             "PASS_nums": 0,
             "PASS_cases": [],
             "result_model_list": [],
             "result_inference_list": [],
             "result_video_list": [],
             "Fail_nums": 0,
             "Fail_cases": []
             }]

    def teardown_method(self):
        json_path = os.path.join(PROJ_PARENT_ROOT, "results", "result.json")
        # with open('/home/aitest/dora/results/result_perftest.json','a+') as f:
        with open(json_path, 'w') as f:
            f.write(json.dumps(self.result))
        logger.info(f'test_report:{type(self.result)},{self.result}')

    def teardown_class(self):
        self.all_case_use_time = time.time() - self.start_time
        logger.info(f'run all cases use_time:{self.all_case_use_time}')
        logger.info('~~~~~~done~~~~~~done~~~~~~done~~~~~~done~~~~~~done~~~~~~done~~~~~~')

    def create_model_from_video(self, video_to_model, quality='train_quality_demo'):
        # 用视频生成model
        # 生成结果的json路径：/data/digital_datas/dora_results
        # cmd: create_model_from_video
        # model路径：/data/digital_datas/model
        start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        video_log = video_to_model.split('.')[0]
        if '/' in video_log:
            video_log = video_log.split('/')[-1]
        result_json = 'create_model-' + quality + '-' + video_log + '-' + start_time + '-dora.json'
        cmd_log_path = '/home/aitest/dora/run_logs/create_model_{}_{}_{}.log'.format(quality, video_log,
                                                                                     start_time)  # 终端输出日志
        logger.info(f'cmd_log_path:{cmd_log_path}\n')
        # 1_test_origin_video ,  --debug ， custom_source,test/后再拼接一段路径
        cmd = "echo 'zegoai@test' | sudo -S docker exec -i {} ./dist/run/run --action create_model_from_video --video_path test/{} --data_root /data --profile {} --output_file results/{} > {}".format(
            self.digital_server, video_to_model, quality, result_json, cmd_log_path)
        logger.info(f"create_model命令:{cmd}\n")

        with ProcessPoolExecutor(max_workers=5) as executor:
            feature = executor.submit(process_execute.execute_command, cmd)
            use_time = feature.result()

        json_path = '/data/digital_datas/results/%s' % result_json
        self.result_great_change_model_json_path = json_path
        logger.info(f'result_json_path:{json_path}')
        result_model = {"action": "create_model_from_video"}
        if os.path.exists(json_path):
            log_cmd = 'cat /data/digital_datas/results/%s' % result_json
            logger.info(f'model_json:{os.popen(log_cmd).read()}')
            result_json = os.popen(log_cmd).read()
            result_dict = json.loads(result_json)  # 将json内容转为字典
            code = result_dict['code']

            if code == 0:
                origin_model_path = result_dict['data']['model_path']
                model_name = origin_model_path.split('models/')[-1]
                # new_model_path = os.path.join('/data/digital_datas/', model_name)

                ai_temp = result_dict['data']['model_id']
                result_model["code"] = code
                result_model["message"] = "nothing"
                result_model["output"] = model_name
                result_model["ai_temp"] = ai_temp
                result_model["quality"] = quality
                result_model["original_video"] = video_to_model
                result_model["use_time"] = round(use_time, 3)
                logger.info(f'model_name: {model_name}')
                logger.info(f'ai_temp: {ai_temp}')
            else:
                logger.info('create_model失败')
                msg = result_dict['message']
                result_model["code"] = code
                result_model["message"] = msg
                result_model["output"] = "null"
                result_model["command_log_path"] = cmd_log_path
                logger.info('error code:{},msg:{}'.format(code, msg))
                logger.info(f'使用视频video_to_model:{video_to_model}')

        elif os.path.exists(cmd_log_path):
            # 当前时间 - 终端输出日志最新修改时间，若超过1分钟未修改，视为已经停止推理视频
            if (time.time() - os.path.getmtime(cmd_log_path)) > 60:
                # 没有生成json文件（通过第一个if得知），且终端日志1分钟左右没更新,视为异常中断
                result_model["code"] = -1
                result_model["message"] = "运行失败,没有result_json文件生成"
                result_model["output"] = "null"
                result_model["command_log_path"] = cmd_log_path
                logger.info('create_mode失败,查看终端日志:cat {}\n'.format(cmd_log_path))
            else:
                result_model["code"] = -2
                result_model["message"] = "运行失败,且没有终端日志生成"
                result_model["output"] = "null"
                result_model["command_log_path"] = "null"
                logger.info('create_mode失败且无终端日志文件生成')
        return result_model

    def create_inference_package(self, video_to_inference):
        # 用视频生成素材
        # 生成结果的json路径：/data/digital_datas/dora_results
        # inference路径：/data/digital_datas/inference_packages
        start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        logger.info(f'开始时间:{start_time}')
        video_log = video_to_inference.split('.')[0]
        if '/' in video_log:
            video_log = video_log.split('/')[-1]
        result_json = 'create_inference_package-' + video_log + '-' + start_time + '-dora.json'
        cmd_log_path = '/home/aitest/dora/run_logs/create_inference_{}.log'.format(video_log,
                                                                                   start_time)  # 终端输出日志
        # 源视频路径custom_source/  ，在test后再拼接一段
        cmd = "echo 'zegoai@test' | sudo -S docker exec -i {} ./dist/run/run --action create_inference_package --video_path test/{} --output_file results/{} --data_root /data > {}".format(
            self.digital_server, video_to_inference, result_json, cmd_log_path)
        logger.info(f"训练素材inference命令:{cmd}\n")

        with ProcessPoolExecutor(max_workers=5) as executor:
            feature = executor.submit(process_execute.execute_command, cmd)
            use_time = feature.result()

        json_path = '/data/digital_datas/results/%s' % result_json
        self.result_great_change_infernece_json_path = json_path
        logger.info(f'result_json_path:{json_path}')
        result_inference = {"action": "create_inference_package"}
        if os.path.exists(json_path):
            log_cmd = 'cat /data/digital_datas/results/%s' % result_json
            logger.info(f'inference_json:{os.popen(log_cmd).read()}')
            result_json = os.popen(log_cmd).read()
            result_dict = json.loads(result_json)  # 将json内容转为字典
            code = result_dict['code']
            if code == 0:
                origin_inference_path = result_dict['data']['output_path']
                inference_name = origin_inference_path.split('inference_packages/')[-1]
                # new_inference_path = os.path.join('/data/digital_datas/results', inference_name)
                #todo 这里准备转移资源处理

                result_inference["code"] = code
                result_inference["message"] = "nothing"
                result_inference["output"] = inference_name
                result_inference["original_video"] = video_to_inference
                result_inference["use_time"] = round(use_time, 3)
                logger.info(f'inference_name:{inference_name}')
            else:
                logger.info('create_inference失败')
                msg = result_dict['message']
                result_inference["code"] = code
                result_inference["message"] = msg
                result_inference["output"] = "null"
                result_inference["command_log_path"] = cmd_log_path
                logger.info('error code:{},msg:{}'.format(code, msg))
                logger.info(f'使用video_to_inference:{video_to_inference}')

        elif os.path.exists(cmd_log_path):
            # 当前时间 - 终端输出日志最新修改时间，若超过1分钟未修改，视为已经停止推理视频
            if (time.time() - os.path.getmtime(cmd_log_path)) > 60:
                # 没有生成json文件（通过第一个if得知），且终端日志1分钟左右没更新,视为异常中断
                result_inference["code"] = -1
                result_inference["message"] = "运行失败,没有result_json文件生成"
                result_inference["output"] = "null"
                result_inference["command_log_path"] = cmd_log_path
                logger.info('create_inference失败，查看终端日志：\n,cat {}'.format(cmd_log_path))
            else:
                result_inference["code"] = -2
                result_inference["message"] = "运行失败,且没有终端日志生成"
                result_inference["output"] = "null"
                result_inference["command_log_path"] = "null"
                logger.info('create_inference失败且无终端日志文件生成')
        return result_inference

    def create_inference_package_interpolation(self, video_to_inference):
        # 用视频生成带插帧包素材
        start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")
        logger.info(f'运行create_inference_package_interpolation()开始时间：{start_time}')
        video_log = video_to_inference.split('.')[0]
        if '/' in video_log:
            video_log = video_log.split('/')[-1]
        result_json = 'create_inference_package_interpolation-' + video_log + '-' + start_time + '-dora.json'

        cmd_log_path = '/home/aitest/dora/run_logs/create_inference_interpolation-{}_{}.log'.format(video_log,
                                                                                                    start_time)  # 终端输出日志
        cmd = "echo 'zegoai@test' | sudo -S docker exec -i {} ./dist/run/run --action create_inference_package --video_path test/1_test_clip_video/{} --output_file dora_results/{} --data_root /data --label_config_base64 ewogICJmcmFtZXMiOiBbCiAgICAiMDA6MDA6MDA6NCIsCiAgICAiMDA6MDA6MDE6MTAiLAogICAgIjAwOjAwOjI6MTYiLAogICAgIjAwOjAwOjU6MTgiLAogICAgIjAwOjAwOjMwOjEwIiwKICAgICIwMDowMDo1MjoxMCIsCiAgICAiMDA6MDA6NTY6OSIKICBdLAogICJhY3Rpb24iOiBbCiAgICB7CiAgICAgICJuYW1lIjogImhlc2h1aSIsCiAgICAgICJzdGFydF90aW1lIjogIjAwOjAwOjAwOjAwIiwKICAgICAgImVuZF90aW1lIjogIjAwOjAwOjEwOjAwIgogICAgfSwKICAgIHsKICAgICAgIm5hbWUiOiAieHgiLAogICAgICAic3RhcnRfdGltZSI6ICIwMDowMDoxMDowMCIsCiAgICAgICJlbmRfdGltZSI6ICIwMDowMDoyMDowMCIKICAgIH0KICBdCn0K > {}".format(
            self.digital_server, video_to_inference, result_json, cmd_log_path)
        logger.info(f"训练素材inference命令:{cmd}\n")

        with ProcessPoolExecutor(max_workers=5) as executor:
            feature = executor.submit(process_execute.execute_command, cmd)
            use_time = feature.result()

        json_path = '/data/digital_datas/dora_results/%s' % result_json
        logger.info(f'result_json_path:{json_path}')
        result_inference = {"action": "create_inference_package_interpolation"}
        if os.path.exists(json_path):
            log_cmd = 'cat /data/digital_datas/dora_results/%s' % result_json
            logger.info(f'inference_json:{os.popen(log_cmd).read()}')
            result_json = os.popen(log_cmd).read()
            result_dict = json.loads(result_json)  # 将json内容转为字典
            code = result_dict['code']
            if code != 0:
                logger.error('create_inference失败')
                msg = result_dict['message']
                result_inference["code"] = code
                result_inference["message"] = msg
                result_inference["output"] = "null"
                result_inference["command_log_path"] = cmd_log_path
                logger.error('error code:{},msg:{}'.format(code, msg))
                logger.info(f'使用video_to_inference:{video_to_inference}')
            else:
                inference_name = result_dict['data']['output_path'].split('inference_packages/')[-1]
                interpolation_name = result_dict['data']['interpolation_path'].split('inference_packages/')[-1]
                result_inference["code"] = code
                result_inference["message"] = "nothing"
                result_inference["output"] = inference_name
                result_inference["interpolation_name"] = interpolation_name
                result_inference["use_time"] = round(use_time, 3)
                result_inference["original_video"] = video_to_inference
                logger.info(f'inference_name:{inference_name}')
        elif os.path.exists(cmd_log_path):
            # 当前时间 - 终端输出日志最新修改时间，若超过1分钟未修改，视为已经停止推理视频
            if (time.time() - os.path.getmtime(cmd_log_path)) > 60:
                # 没有生成json文件（通过第一个if得知），且终端日志1分钟左右没更新,视为异常中断
                result_inference["code"] = -1
                result_inference["message"] = "运行失败,没有result_json文件生成"
                result_inference["output"] = "null"
                result_inference["command_log_path"] = cmd_log_path
                logger.info('create_inference失败，查看终端日志：\n,cat {}'.format(cmd_log_path))
            else:
                result_inference["code"] = -2
                result_inference["message"] = "运行失败,且没有终端日志生成"
                result_inference["output"] = "null"
                result_inference["command_log_path"] = "null"
                logger.info('create_inference失败且无终端日志文件生成')
        return result_inference

    def create_video_from_audio(self, model_name, inference_name, audio_name, is_pretrain='False'):
        # 推理视频
        # is_pretrain 是否使用预训练model推理视频，默认False
        start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        logger.info(f'开始时间：{start_time}')

        result_json = model_name.split('.')[0] + '-' + audio_name.split('.')[0] + '-' + start_time + '-dora-test.json'
        # 终端日志
        cmd_log_path = '/home/aitest/dora/run_logs/create_video_{}_{}_{}_{}.log'.format(model_name, audio_name,
                                                                                        inference_name, start_time)
        cmd = "echo 'zegoai@test' | sudo -S docker exec -i {} ./dist/run/run --action create_video_from_audio --model_path models/{} --inference_package_path inference_packages/{} --data_root /data --output_file results/{} --audio_path test/1_official_audio/{} --audio_language 'zh-CN' --use_pretrain_model {} > {}".format(
            self.digital_server, model_name, inference_name, result_json, audio_name, is_pretrain, cmd_log_path)
        logger.info(f'{cmd}\n')

        with ProcessPoolExecutor(max_workers=5) as executor:
            feature = executor.submit(process_execute.execute_command, cmd)
            use_time = feature.result()

        json_path = '/data/digital_datas/results/%s' % result_json
        self.result_great_change_video_json_path = json_path
        logger.info(f'result_json_path:{json_path}')
        sleep(1)
        result_video = {"action": "create_video_from_audio"}
        # create_video_tag = 'video_result_'+model_name + '_' + inference_name + '_' + start_time
        if os.path.exists(json_path):
            log_cmd = 'cat /data/digital_datas/results/%s' % result_json
            logger.info(f'\nvideo_json:{os.popen(log_cmd).read()}')
            result_json = os.popen(log_cmd).read()
            result_dict = json.loads(result_json)  # 将json内容转为字典
            code = result_dict['code']
            if code != 0:
                logger.error('create_video失败')
                msg = result_dict['message']
                # result_video[create_video_tag] = {"code":code,"message":msg}
                result_video["code"] = code
                result_video["message"] = msg
                result_video["output"] = "null"
                result_video["command_log_path"] = cmd_log_path
                logger.error('error code:{},msg:{}'.format(code, msg))
                logger.error('失败结果:{}'.format(result_video))
            else:
                video_name = result_dict['data']['video_path'].split('results/')[-1]
                result_video["code"] = code
                result_video["message"] = "nothing"
                result_video["output"] = video_name
                result_video["original_model"] = model_name
                result_video["original_inference"] = inference_name
                result_video["original_audio"] = audio_name
                result_video["use_time"] = round(use_time, 3)
                logger.info(f'result_video:{result_video}')
        elif os.path.exists(cmd_log_path):
            # 当前时间 - 终端输出日志最新修改时间，若超过1分钟未修改，视为已经停止推理视频
            if (time.time() - os.path.getmtime(cmd_log_path)) > 60:
                # 没有生成json文件（通过第一个if得知），且终端日志1分钟左右没更新,视为异常中断
                result_video["code"] = -1
                result_video["message"] = "运行失败,没有result_json文件生成"
                result_video["output"] = "null"
                result_video["command_log_path"] = cmd_log_path
                logger.error('create_video失败,查看终端日志,cat {}\n'.format(cmd_log_path))
            else:
                result_video["code"] = -2
                result_video["message"] = "运行失败,且没有终端日志生成"
                result_video["output"] = "null"
                result_video["command_log_path"] = "null"
                logger.error('create_video失败且无终端日志文件生成')
        return result_video

    @allure.feature('全功能用例')
    @allure.title('create_custom_model_batch批量训练客户model')
    @pytest.mark.batch
    @pytest.mark.P1
    @pytest.mark.parametrize(('videos_to_model', 'quality'), [(yaml['custom_video_list_to_model'], yaml['normal_quality'])])
    def test_create_custom_model_batch(self, videos_to_model, quality):
        result_models = [
            {"case_name": "test_create_custom_model_batch",
             "PASS_action": [],
             "PASS_nums": 0,
             "mode_list": [],
             "Fail_action": [],
             "Fail_nums": 0
             }]
        video_list = []
        for video in videos_to_model:
            video = 'custom_source/' + video
            video_list.append(video)
        result_all = []
        result_model_dict = {}
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(self.create_model_from_video, video, quality) for video in video_list]
            for future in as_completed(futures):
                result = future.result()
                result_all.append(result)
                try:
                    assert result["code"] == 0
                    result_models[0]["mode_list"].append(result["output"])
                    result_models[0]["PASS_action"].append(f'creat_mode_from_{result["original_video"]}')
                    result_models[0]["PASS_nums"] = result_models[0]["PASS_nums"] + 1
                    original = result["original_video"] + '-' + result["quality"]
                    result_model_dict[original] = result["output"]
                except AssertionError as e:
                    logger.error(e)
                    result_models[0]["Fail_action"].append(f'creat_mode_from_{result["original_video"]}')
                    result_models[0]["Fail_nums"] = result_models[0]["Fail_nums"] + 1
                    raise

        result_models = result_models + result_all
        self.result[0]["result_model_list"].append([result_model_dict])
        if result_models[0]["Fail_nums"] == 0:
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("create_custom_model_batch")
            self.result.append(result_models)
        else:
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("create_custom_model_batch")
            self.result.insert(1, result_models)
        logger.info(f'result_product for result_models:{result_models}\n')

    @allure.feature('全功能用例')
    @allure.title('create_model_batch批量训练内部模特model')
    @pytest.mark.batch
    @pytest.mark.P1
    @pytest.mark.debug
    @pytest.mark.parametrize(('videos_to_model', 'quality'), [(yaml['video_list_to_model'], yaml['normal_quality'])])
    def test_create_model_batch(self, videos_to_model, quality):
        result_models = [
            {"case_name": "test_create_model_batch",
             "PASS_action": [],
             "PASS_nums": 0,
             "mode_list": [],
             "Fail_action": [],
             "Fail_nums": 0
             }]
        video_list = []
        for video in videos_to_model:
            video = '1_test_origin_video/' + video
            video_list.append(video)

        result_all = []
        result_model_dict = {}
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(self.create_model_from_video, video, quality) for video in video_list]
            for future in as_completed(futures):
                result = future.result()
                result_all.append(result)
                try:
                    assert result["code"] == 0
                    result_models[0]["mode_list"].append(result["output"])
                    result_models[0]["PASS_action"].append(f'creat_mode_from_{result["original_video"]}')
                    result_models[0]["PASS_nums"] = result_models[0]["PASS_nums"] + 1
                    original = result["original_video"] + '-' + result["quality"]
                    result_model_dict[original] = result["output"]
                except AssertionError as e:
                    logger.error(e)
                    result_models[0]["Fail_action"].append(f'creat_mode_from_{result["original_video"]}')
                    result_models[0]["Fail_nums"] = result_models[0]["Fail_nums"] + 1
                    raise

        result_models = result_models + result_all
        self.result[0]["result_model_list"].append([result_model_dict])
        if result_models[0]["Fail_nums"] == 0:
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_create_model_batch")
            self.result.append(result_models)
        else:
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_create_model_batch")
            self.result.insert(1, result_models)
        logger.info(f'result_product for result_models:{result_models}\n')

    @allure.feature('全功能用例')
    @allure.title('test_four_qualities_to_create_model所有的quality级别')
    @pytest.mark.P1
    @pytest.mark.batch
    @pytest.mark.parametrize(('video_to_model', 'quality_list'), [(yaml['video_to_create_model_P0'], yaml['quality_list'])])
    def test_four_qualities_to_create_model(self, video_to_model, quality_list):
        result_models = [
            {"case_name": "test_four_qualities_to_create_model",
             "PASS_action": [],
             "PASS_nums": 0,
             "mode_list": [],
             "Fail_action": [],
             "Fail_nums": 0
             }]
        result_all = []
        result_model_dict = {}
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(self.create_model_from_video, video_to_model, quality) for quality in
                       quality_list]

            for future in as_completed(futures):
                thread_result = future.result()
                result_all.append(thread_result)
                try:
                    assert thread_result["code"] == 0
                    result_models[0]["mode_list"].append(thread_result["output"])
                    result_models[0]["PASS_action"].append(f'creat_mode_from_{video_to_model}')
                    result_models[0]["PASS_nums"] = result_models[0]["PASS_nums"] + 1
                    original = thread_result["original_video"] + '-' + thread_result["quality"]
                    result_model_dict[original] = thread_result["output"]
                except AssertionError as e:
                    logger.error(e)
                    result_models[0]["Fail_action"].append(f'creat_mode_from_{video_to_model}')
                    result_models[0]["Fail_nums"] = result_models[0]["Fail_nums"] + 1
                    raise

        result_models = result_models + result_all
        self.result[0]["result_model_list"].append([result_model_dict])
        if result_models[0]["Fail_nums"] == 0:
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_four_qualities_to_create_model")
            self.result.append(result_models)
        else:
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_four_qualities_to_create_model")
            self.result.insert(1, result_models)
        logger.info(f'result_product for result_models:{result_models}\n')
        logger.info(f'result_model_dict:{result_model_dict}\n')

    @allure.feature('全功能用例')
    @allure.title('create_inference_batch批量训练素材')
    @pytest.mark.batch
    @pytest.mark.P1
    @pytest.mark.parametrize(('videos_to_inference'), [(yaml['video_list_to_inference'])])
    def test_create_inference_batch(self, videos_to_inference):
        result_inferences = [
            {"case_name": "test_create_inference_batch",
             "PASS_action": [],
             "PASS_nums": 0,
             "result_inference_list": [],
             "Fail_action": [],
             "Fail_nums": 0
             }]
        video_list = []
        for video in videos_to_inference:
            video = '1_test_clip_video/' + video  # 内部
            # video = 'custom_source/'+video   # 客户
            video_list.append(video)
        result_all = []
        result_inference_dict = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.create_inference_package, video) for video in video_list]
            for future in as_completed(futures):
                thread_result = future.result()
                result_all.append(thread_result)
                try:
                    assert thread_result["code"] == 0
                    result_inferences[0]["result_inference_list"].append(thread_result["output"])
                    result_inferences[0]["PASS_action"].append(
                        f'creat_inference_from_{thread_result["original_video"]}')
                    result_inferences[0]["PASS_nums"] = result_inferences[0]["PASS_nums"] + 1
                    result_inference_dict[thread_result["original_video"]] = thread_result["output"]
                except AssertionError as e:
                    logger.error(e)
                    result_inferences[0]["Fail_action"].append(
                        f'creat_inference_from_{thread_result["original_video"]}')
                    result_inferences[0]["Fail_nums"] = result_inferences[0]["Fail_nums"] + 1
                    raise

        result_inferences = result_inferences + result_all
        self.result[0]["result_inference_list"].append([result_inference_dict])
        if result_inferences[0]["Fail_nums"] == 0:
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_create_inference_batch")
            self.result.append(result_inferences)
        else:
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_create_inference_batch")
            self.result.insert(1, result_inferences)
        logger.info(f'result_product for result_inferences:{result_inferences}\n')

    @allure.feature('全功能用例')
    @allure.title('test_create_inference_interpolation_batch批量训练素材')
    @pytest.mark.batch
    @pytest.mark.P1
    @pytest.mark.parametrize(('videos_to_inference'), [(yaml['custom_video_list_to_inference'])])
    def test_create_inference_interpolation_batch(self, videos_to_inference):
        # 使用客户视频
        result_inferences = [
            {"case_name": "test_create_inference_interpolation_batch",
             "PASS_action": [],
             "PASS_nums": 0,
             "result_inference_list": [],
             "Fail_action": [],
             "Fail_nums": 0
             }]
        video_list = []
        for video in videos_to_inference:
            # video = '1_test_clip_video/'+video
            video = 'custom_source/' + video
            video_list.append(video)
        result_all = []
        result_inference_dict = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.create_inference_package, video) for video in video_list]
            for future in as_completed(futures):
                thread_result = future.result()
                result_all.append(thread_result)
                try:
                    assert thread_result["code"] == 0
                    result_inferences[0]["result_inference_list"].append(thread_result["output"])
                    result_inferences[0]["PASS_action"].append(
                        f'creat_inference_from_{thread_result["original_video"]}')
                    result_inferences[0]["PASS_nums"] = result_inferences[0]["PASS_nums"] + 1
                    result_inference_dict[thread_result["original_video"]] = thread_result["output"]
                except AssertionError as e:
                    logger.error(e)
                    result_inferences[0]["Fail_action"].append(
                        f'creat_inference_from_{thread_result["original_video"]}')
                    result_inferences[0]["Fail_nums"] = result_inferences[0]["Fail_nums"] + 1
                    raise

        result_inferences = result_inferences + result_all
        self.result[0]["result_inference_list"].append([result_inference_dict])
        if result_inferences[0]["Fail_nums"] == 0:
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_create_inference_interpolation_batch")
            self.result.append(result_inferences)
        else:
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_create_inference_interpolation_batch")
            self.result.insert(1, result_inferences)
        logger.info(f'result_product for test_create_inference_interpolation_batch:{result_inferences}\n')

    # todo 雪琴 这里临时写个类变量，以便于我获取json的路径，之后要想办法把jenkins发过来的路径接到这里，然后在转移存档素材和视频 --成记
    ## 这些变量我取成这样为了方便你理解，但是变量严格来说不能太过长，所以不同用例都独立出来是最好的选择，变量名、类名、函数名清晰的话对后面的拓展效率有很大的提升 --成记
    result_great_change_model_json_path = ''
    result_great_change_infernece_json_path = ''
    result_great_change_video_json_path = ''

    @allure.feature('冒烟测试主流程')
    @allure.title('变动较大,重跑全流程,quality-test:训练model-训练素材-再推理视频')
    @pytest.mark.great_change
    @pytest.mark.flag
    @pytest.mark.parametrize(('video_to_model', 'video_to_inference', 'audio_name', 'output'), [
        (yaml['short_video'], yaml['short_video'], yaml['default_audio'])], 'dora must to fix')
    def test_great_change_serial_create(self, video_to_model, video_to_inference, audio_name, output):
        unsuccessful = False
        result_great_change = {
            "action": "test_great_change_serial_create",
            "PASS_action": [],
            "Fail_action": [],
            "model_json_path" : "",
            "inference_json_path" : "",
            "video_json_path" : ""
        }
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            future1 = executor.submit(self.create_model_from_video, video_to_model, quality='train_quality_test')
            future2 = executor.submit(self.create_inference_package, video_to_inference)
            futures.append(future1)
            futures.append(future2)
            result_all = []
            result_model_dict = {}
            for future in as_completed(futures):
                thread_result = future.result()
                result_all.append(thread_result)
                action = thread_result["action"]
                try:
                    assert thread_result["code"] == 0
                    result_great_change["PASS_action"].append(action)
                    if action == "create_inference_package":
                        result_great_change["inference_name"] = thread_result["output"]
                        self.result[0]["result_inference_list"].append(thread_result["output"])
                    elif action == "create_model_from_video":
                        result_great_change["model_name"] = thread_result["output"]
                        original = thread_result["original_video"] + '-' + thread_result["quality"]
                        result_model_dict[original] = thread_result["output"]
                        self.result[0]["result_model_list"].append(result_model_dict)
                except AssertionError as e:
                    print(str(e))
                    logger.error(e)
                    unsuccessful = True
                    result_great_change["Fail_action"].append(action)
                    self.result[0]["Fail_action"] = []
                    self.result[0]["Fail_action"].append("test_great_change_serial_create")
                    if action == "create_inference_package":
                        logger.error(f'Fail at:create_inference_package')
                    elif action == "create_model_from_video":
                        logger.error(f'Fail at:create_model_from_video')
        try:
            if unsuccessful == False:
                model_name = result_great_change["model_name"]
                inference_name = result_great_change["inference_name"]
                result_video = self.create_video_from_audio(model_name, inference_name, audio_name)
                assert result_video["code"] == 0
                result_great_change["PASS_action"].append("create_video_from_audio")
                result_great_change["code"] = 0
                result_great_change["message"] = 'nothing'
                self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
                self.result[0]["PASS_cases"].append("test_great_change_serial_create")
                self.result[0]["result_video_list"].append(result_video["output"])
                result_great_change['detail'] = result_video
                self.result.append(result_great_change)
                logger.info(f'test_great_change_model_inference_to_video全流程测试通过')
        except Exception as e:
            print(str(e))
            logger.error(e)
            result_great_change["Fail_action"].append("create_video_from_audio")
            result_great_change["code"] = -5
            result_great_change["message"] = 'Fail at create_video'
            logger.error(f'Fail at:create_video_from_audio')
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_great_change_serial_create_default_quality")
            self.result.insert(1, result_great_change)
            raise
        finally:
            # todo 雪琴 这里我先临时把逻辑写到这里，你之后组织一下 --成记
            if unsuccessful == False:
                new_model_json_path = f"{os.path.join(output, self.result_great_change_model_json_path.split('/')[-1])}"
                command = ['sudo', 'mv', self.result_great_change_model_json_path, new_model_json_path]
                subprocess.run(command)
                new_inference_json_path = f"{os.path.join(output, self.result_great_change_infernece_json_path.split('/')[-1])}"
                command = ['sudo', 'mv', self.result_great_change_infernece_json_path, new_inference_json_path]
                subprocess.run(command)
                new_video_json_path = f"{os.path.join(output, self.result_great_change_video_json_path.split('/')[-1])}"
                command = ['sudo', 'mv', self.result_great_change_video_json_path, new_video_json_path]
                subprocess.run(command)
    
                self.result[0]['model_json_path'] = new_model_json_path
                self.result[0]['inference_json_path'] = new_inference_json_path
                self.result[0]['video_json_path'] = new_video_json_path
            
            logger.info(f'result_product for test_great_change_serial_create:{result_great_change}\n')
            #end

    @allure.feature('冒烟测试主流程')
    @allure.title('变化较小,并行测试接口:训练model-训练素材-推理视频')
    @pytest.mark.small_change
    @pytest.mark.flag
    # @pytest.mark.skip(reason='no')
    @pytest.mark.parametrize(('video_to_model', 'video_to_inference', 'model_name', 'inference_name', 'audio_name'), [
        (yaml['short_video'], yaml['short_video'], yaml['default_model'], yaml['default_inference'], yaml['default_audio'])])
    def test_samll_change_parallel_create(self, video_to_model, video_to_inference, model_name, inference_name,
                                          audio_name):
        result_small_change = [
            {"action": "test_samll_change_parallel_create",
             "PASS_action": [],
             "Fail_action": []
             }]
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            future1 = executor.submit(self.create_model_from_video, video_to_model, quality='train_quality_test')
            future2 = executor.submit(self.create_inference_package, video_to_inference)
            future3 = executor.submit(self.create_video_from_audio, model_name, inference_name, audio_name)
            futures.append(future1)
            futures.append(future2)
            futures.append(future3)
            thread_result_all = []
            result_model_dict = {}
            for future in as_completed(futures):
                thread_result = future.result()
                thread_result_all.append(thread_result)
                try:
                    assert thread_result["code"] == 0
                    action = thread_result["action"]
                    result_small_change[0]["PASS_action"].append(action)
                    if action == "create_video_from_audio":
                        self.result[0]["result_video_list"].append(thread_result["output"])
                    elif action == "create_inference_package":
                        self.result[0]["result_inference_list"].append(thread_result["output"])
                    elif action == "create_model_from_video":
                        original = thread_result["original_video"] + '-' + thread_result["quality"]
                        result_model_dict[original] = thread_result["output"]
                        self.result[0]["result_model_list"].append(result_model_dict)
                except AssertionError as e:
                    logger.error(e)
                    result_small_change[0]["Fail_action"].append(thread_result["action"])
                    raise

        result_small_change += thread_result_all
        logger.info(f'result_small_change:{result_small_change}')
        if (result_small_change[1]["code"] == 0 and result_small_change[2]["code"] == 0 and result_small_change[3][
            "code"] == 0) == 1:
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_samll_change_parallel_create")
            self.result.append(result_small_change)
        else:
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_samll_change_parallel_create")
            self.result.insert(1, result_small_change)

    @allure.feature('全功能')
    @allure.title('并行测试接口:训练model-训练素材-推理视频')
    @pytest.mark.P0
    # @pytest.mark.skip(reason='no')
    @pytest.mark.parametrize(
        ('video_to_model', 'quality', 'video_to_inference', 'model_name', 'inference_name', 'audio_name'), [
            (yaml['custom_default_video_to_model'], yaml['default_quality'], yaml['custom_default_video_to_model'],
             yaml['default_model'], yaml['default_inference'], yaml['default_audio'])])
    def test_samll_change_parallel_create_default_quality(self, video_to_model, quality, video_to_inference, model_name,
                                                          inference_name, audio_name):
        result_small_change = [
            {"action": "test_samll_change_parallel_create_default_quality",
             "PASS_action": [],
             "Fail_action": []
             }]
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            future1 = executor.submit(self.create_model_from_video, video_to_model, quality)
            future2 = executor.submit(self.create_inference_package, video_to_inference)
            future3 = executor.submit(self.create_video_from_audio, model_name, inference_name, audio_name)
            futures.append(future1)
            futures.append(future2)
            futures.append(future3)
            thread_result_all = []
            result_model_dict = {}
            for future in as_completed(futures):
                thread_result = future.result()
                thread_result_all.append(thread_result)
                try:
                    assert thread_result["code"] == 0
                    action = thread_result["action"]
                    result_small_change[0]["PASS_action"].append(action)
                    if action == "create_video_from_audio":
                        self.result[0]["result_video_list"].append(thread_result["output"])
                    elif action == "create_inference_package":
                        self.result[0]["result_inference_list"].append(thread_result["output"])
                    elif action == "create_model_from_video":
                        original = thread_result["original_video"] + '-' + thread_result["quality"]
                        result_model_dict[original] = thread_result["output"]
                        self.result[0]["result_model_list"].append(result_model_dict)
                except AssertionError as e:
                    logger.error(e)
                    result_small_change[0]["Fail_action"].append(thread_result["action"])
                    raise

        result_small_change += thread_result_all
        logger.info(f'result_small_change:{result_small_change}')
        if (result_small_change[1]["code"] == 0 and result_small_change[2]["code"] == 0 and result_small_change[3][
            "code"] == 0) == 1:
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_samll_change_parallel_create_default_quality")
            self.result.append(result_small_change)
        else:
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_samll_change_parallel_create_default_quality")
            self.result.insert(1, result_small_change)

    @allure.feature('冒烟测试主流程')
    @allure.title('create_model')
    @pytest.mark.P1
    @pytest.mark.parametrize(('video_to_model', 'quality', 'output'), [(yaml['default_video'], yaml['high_quality'], 'dora fix it')])
    def test_create_model(self, video_to_model, quality, output):
        result_model = self.create_model_from_video(video_to_model, quality)
        result_model["case_name"] = "test_create_model"
        result_model_dict = {}
        unsuccessful = False
        try:
            assert result_model["code"] == 0
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_create_model")
            original = result_model["original_video"] + '-' + result_model["quality"]
            result_model_dict[original] = result_model["output"]
            self.result[0]["result_model_list"].append(result_model_dict)
            self.result.append(result_model)
            data_yaml.update_yaml(k='create_model_result', v=result_model["output"])
        except AssertionError as e:
            unsuccessful = True
            print(str(e))
            logger.error(e)
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_create_model")
            self.result.insert(1, result_model)
            raise
        finally:
            #todo 雪琴 这里我先临时把逻辑写到这里，你之后组织一下 --成记
            if unsuccessful == False:
                new_model_json_path = f"{os.path.join(output, self.result_great_change_model_json_path.split('/')[-1])}"
                command = ['sudo', 'mv', self.result_great_change_model_json_path, new_model_json_path]
                subprocess.run(command)
    
                self.result[0]['model_json_path'] = new_model_json_path
            
            logger.info(f'result_product for result_model:{result_model}\n')
            

    @allure.feature('冒烟测试主流程')
    @allure.title('create_inference')
    @pytest.mark.P1
    @pytest.mark.parametrize(('video_to_inference', 'output'), [(yaml['default_video'], 'dora fix it')])  #
    def test_create_inference(self, video_to_inference, output):
        result_inference = self.create_inference_package(video_to_inference)
        result_inference["case_name"] = "test_create_inference"
        unsuccessful = False
        try:
            assert result_inference["code"] == 0
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_create_inference")
            self.result[0]["result_inference_list"].append(result_inference["output"])
            data_yaml.update_yaml(k='create_inference_result', v=result_inference["output"])
            self.result.append(result_inference)
        except AssertionError as e:
            unsuccessful = True
            print(str(e))
            logger.error(e)
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_create_inference")
            self.result.insert(1, result_inference)
            raise
        finally:
            #todo 雪琴 这里我先临时把逻辑写到这里，你之后组织一下 --成记
            if unsuccessful == False:
                new_inference_json_path = f"{os.path.join(output, self.result_great_change_infernece_json_path.split('/')[-1])}"
                command = ['sudo', 'mv', self.result_great_change_infernece_json_path, new_inference_json_path]
                subprocess.run(command)
                self.result[0]['inference_json_path'] = new_inference_json_path
                
            logger.info(f'result_inference:{result_inference}\n')

    @allure.feature('冒烟测试主流程')
    @allure.title('create_video')
    @pytest.mark.P1
    @pytest.mark.flag
    @pytest.mark.parametrize(('model_name', 'inference_name', 'audio_name', 'output'),
                             [(yaml['default_model'], yaml['default_inference'], yaml['default_audio'], 'dora fix it')])
    def test_create_video(self, model_name, inference_name, audio_name, output):
        result_video = self.create_video_from_audio(model_name, inference_name, audio_name)
        result_video["case_name"] = "test_create_video"
        unsuccessful = False
        try:
            assert result_video["code"] == 0
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_create_video")
            self.result[0]["result_video_list"].append(result_video["output"])
            self.result.append(result_video)
        except AssertionError as e:
            unsuccessful = True
            print(str(e))
            logger.error(e)
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_create_video")
            self.result.insert(1, result_video)
            raise
        finally:
            # todo 雪琴 这里我先临时把逻辑写到这里，你之后组织一下 --成记
            if unsuccessful == False:
                new_video_json_path = f"{os.path.join(output, self.result_great_change_video_json_path.split('/')[-1])}"
                command = ['sudo', 'mv', self.result_great_change_video_json_path, new_video_json_path]
                subprocess.run(command)
                self.result[0]['video_json_path'] = new_video_json_path
            
            logger.info(f'result_product for result_video:{result_video}\n')

    @allure.feature('全功能用例')
    @allure.title('test_create_inference_interpolation:训练带插帧包的素材')
    @pytest.mark.P1
    @pytest.mark.parametrize(('video_to_inference'), [(yaml['default_video_to_model'])])
    def test_create_inference_interpolation(self, video_to_inference):
        result_inference = self.create_inference_package_interpolation(video_to_inference)
        result_inference["case_name"] = "test_create_inference_interpolation"
        try:
            assert result_inference["code"] == 0
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append(result_inference["case_name"])
            self.result[0]["result_inference_list"].append(result_inference["output"])
            data_yaml.update_yaml(k='create_inference_interpolation_result', v=result_inference["output"])
            self.result.append(result_inference)
        except AssertionError as e:
            logger.error(e)
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append(result_inference["case_name"])
            self.result.insert(1, result_inference)
            raise
        finally:
            logger.info(f'result_inference:{result_inference}\n')

    @allure.feature('冒烟测试主流程')
    @allure.title('test_pretrain_model_to_create_video使用预训练model推理视频')
    @pytest.mark.P0
    @pytest.mark.great_change
    @pytest.mark.parametrize(('model_name', 'inference_name', 'audio_name'),
                             [(yaml['no_model'], yaml['default_inference'], yaml['default_audio']),
                              (yaml['default_model'], yaml['create_inference_result'], yaml['default_audio'])])
    def test_pretrain_model_to_create_video(self, model_name, inference_name, audio_name):
        result_video = self.create_video_from_audio(model_name, inference_name, audio_name, is_pretrain='True')
        result_video["case_name"] = f"test_pretrain_model_to_create_video-{inference_name}"
        try:
            assert result_video["code"] == 0
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append(result_video["case_name"])
            self.result[0]["result_video_list"].append(result_video["output"])
            self.result.append(result_video)
        except AssertionError as e:
            logger.error(e)
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append(result_video["case_name"])
            self.result.insert(1, result_video)
            raise
        finally:
            logger.info(f'result_product for result_video:{result_video}\n')

    @allure.feature('全功能')
    @allure.title('串行全流程:训练model-训练素材-再推理视频')
    @pytest.mark.P0
    @pytest.mark.great_change
    @pytest.mark.parametrize(('video_to_model', 'quality', 'video_to_inference', 'audio_name'), [
        (yaml['default_video_to_model'], yaml['default_quality'], yaml['default_video_to_inference'], yaml['default_audio'])])
    def test_great_change_serial_create_default_quality(self, video_to_model, quality, video_to_inference, audio_name):
        result_great_change = [
            {"action": "test_great_change_serial_create_default_quality",
             "PASS_action": [],
             "Fail_action": []
             }]
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            future1 = executor.submit(self.create_model_from_video, video_to_model, quality)
            future2 = executor.submit(self.create_inference_package, video_to_inference)
            futures.append(future1)
            futures.append(future2)
            result_all = []
            result_model_dict = {}
            for future in as_completed(futures):
                thread_result = future.result()
                result_all.append(thread_result)
                action = thread_result["action"]
                try:
                    assert thread_result["code"] == 0
                    result_great_change[0]["PASS_action"].append(action)
                    if action == "create_inference_package":
                        result_great_change[0]["inference_name"] = thread_result["output"]
                        self.result[0]["result_inference_list"].append(thread_result["output"])
                    elif action == "create_model_from_video":
                        result_great_change[0]["model_name"] = thread_result["output"]
                        original = thread_result["original_video"] + '-' + thread_result["quality"]
                        result_model_dict[original] = thread_result["output"]
                        self.result[0]["result_model_list"].append(result_model_dict)
                except AssertionError as e:
                    logger.error(e)
                    result_great_change[0]["Fail_action"].append(action)
                    self.result[0]["Fail_action"].append("test_great_change_serial_create")
                    if action == "create_inference_package":
                        logger.error(f'Fail at:create_inference_package')
                    elif action == "create_model_from_video":
                        logger.error(f'Fail at:create_model_from_video')
        try:
            model_name = result_great_change[0]["model_name"]
            inference_name = result_great_change[0]["inference_name"]
            result_video = self.create_video_from_audio(model_name, inference_name, audio_name)
            assert result_video["code"] == 0
            result_great_change[0]["PASS_action"].append("create_video_from_audio")
            result_great_change[0]["code"] = 0
            result_great_change[0]["message"] = 'nothing'
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_great_change_serial_create_default_quality")
            self.result[0]["result_video_list"].append(result_video["output"])
            result_great_change.append(result_video)
            self.result.append(result_great_change)
            logger.info(f'test_great_change_model_inference_to_video全流程测试通过')
        except AssertionError as e:
            logger.error(e)
            result_great_change[0]["Fail_action"].append("create_video_from_audio")
            result_great_change[0]["code"] = -5
            result_great_change[0]["message"] = 'Fail at create_video'
            logger.error(f'Fail at:create_video_from_audio')
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_great_change_serial_create_default_quality")
            result_great_change.append(result_video)
            self.result.insert(1, result_great_change)
            raise
        finally:
            logger.info(f'result_product for test_great_change_serial_create_default_quality:{result_great_change}\n')

    @allure.feature('全功能用例')
    @allure.title('create_video_batch:批量推理视频')
    @pytest.mark.batch
    @pytest.mark.thread
    @pytest.mark.parametrize(('model_name', 'inference_name', 'audio_list'), [(yaml[
                                                                                   'normal_custom_blue_stripe_skirt_hongsong_man_model'],
                                                                               yaml[
                                                                                   'custom_blue_stripe_skirt_hongsong_man_inference'],
                                                                               yaml['boy_audio_list'])])
    def test_create_video_batch(self, model_name, inference_name, audio_list):
        start_time = time.time()
        result_videos = [
            {"case_name": "test_create_video_batch",
             "PASS_action": [],
             "PASS_nums": 0,
             "mode_list": [],
             "Fail_action": [],
             "Fail_nums": 0
             }]

        result_all = []
        result_video_dict = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.create_video_from_audio, model_name, inference_name, audio) for audio in
                       audio_list]
            for future in as_completed(futures):
                result = future.result()
                result_all.append(result)
                try:
                    assert result["code"] == 0
                    result_videos[0]["PASS_action"].append(f'creat_video_from_{result["original_audio"]}')
                    result_videos[0]["PASS_nums"] = result_videos[0]["PASS_nums"] + 1
                    self.result[0]["result_video_list"].append(result["output"])
                    k = 'video_batch-' + result["original_audio"]
                    data_yaml.update_yaml(k=k, v=result["output"])
                except AssertionError as e:
                    logger.error(e)
                    result_videos[0]["Fail_action"].append(f'creat_video_from_{result["original_audio"]}')
                    result_videos[0]["Fail_nums"] = result_videos[0]["Fail_nums"] + 1
                    raise
        result_videos = result_videos + result_all
        if result_videos[0]["Fail_nums"] == 0:
            self.result[0]["PASS_nums"] = self.result[0]["PASS_nums"] + 1
            self.result[0]["PASS_cases"].append("test_create_video_batch")
            self.result.append(result_videos)
        else:
            self.result[0]["Fail_nums"] = self.result[0]["Fail_nums"] + 1
            self.result[0]["Fail_cases"].append("test_create_video_batch")
            self.result.insert(1, result_videos)
        logger.info(f'result_product for result_videos:{result_videos}\n')
        case_use_time = time.time() - start_time
        logger.info(f'case_use_time--test_create_video_batch:{case_use_time}')

    @allure.feature('全功能用例')
    @allure.title('test_create_video_debug:debug推理视频')
    @pytest.mark.P2
    @pytest.mark.parametrize(('model_list', 'inference_name', 'audio_list'), [
        (yaml['low_custom_white_dress_aiqidao_model'], yaml['custom_white_dress_aiqidao_inference'], yaml['boy_audio_list'])])
    def test_create_video_debug(self, model_list, inference_name, audio_list):
        result_video_list = []
        result_all_list = []
        for model_name in model_list:
            for audio_name in audio_list:
                result_video = self.create_video_from_audio(model_name, inference_name, audio_name)
                pytest.assume(result_video['code'] == 0)
                result_video_list.append(result_video["output"])
                result_all_list.append(result_video)
        logger.info('********************************')
        logger.info(f'{model_name}, {inference_name}\n产物result_video_list:{result_video_list}\n')
        logger.info('********************************')
        logger.info(f'所有数据：result_all_list:{result_all_list}')

if __name__ == '__main__':
    logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~当前运行~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    pytest.main(['/home/aitest/dora/testcase/test_digital_human.py::Test_DigitalHuman::test_create_inference',
                 '-sv'])  # test_create_inference_batch
    logger.info('everything is good')
