#! /usr/bin/env python3
# _*_ coding:utf-8 _*_
"""
@Auth : Dora
@Date : 2022/4/2 14:17
"""

import pytest,os,sys
import random
# # 没有用到先注释，后续只加会用到的，确保该模块正常且174服务器的环境已安装
# # 具体先conda deactivate,再pip3/pip list -v @雪琴
# import allure
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from time import sleep
# import requests
# import base64
# import hashlib
#sys.path.insert(0, r'/home/aitest/dora/')
from testcase import test_digital_human
from conf.read_yaml import ReadElemet
# 将控制台输出存入日志文件
from conf import pytest_log
logger = pytest_log.log_test
# 读取配置数据
data_yaml = ReadElemet(fileName='data')
PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))

def run_case(digital_server, output, testcasescope, jenkins_num):
    # 将最新的digital_server写入配置文件
    os.chdir(PROJ_ROOT)
    if not os.path.exists(os.path.join(PROJ_ROOT, 'results')):
        os.mkdir(os.path.join(PROJ_ROOT, 'results'))
        
    data_yaml.update_yaml(k='digital_server',v=digital_server)
    yaml = data_yaml.All_element()
    # todo 雪琴 这个模块我对参数的传入不太懂，按目前的理解发现限制很多，果断注释。pytest如果你需要使用，则一定要熟悉pytest的各种使用方法 --成记
    digital_human_instance = test_digital_human.Test_DigitalHuman()
    digital_human_instance.setup_class(yaml)
    if testcasescope == 'CI':
        digital_human_instance.test_great_change_serial_create(yaml['short_video'], yaml['short_video'], yaml['default_audio'], output)
    elif testcasescope == 'P1':
        digital_human_instance.test_create_model(yaml['default_video'], yaml['high_quality'], output)
        digital_human_instance.test_create_inference(yaml['default_video'], output)
        digital_human_instance.test_create_video(yaml['default_model'], yaml['default_inference'], yaml['default_audio'], output)
    
    digital_human_instance.teardown_method()    
    # pytest.main(['./test_digital_human.py::Test_DigitalHuman::test_great_change_serial_create','-sv'], f'--output={output}') # test_great_change_serial_create
    logger.info('everything is done')
    