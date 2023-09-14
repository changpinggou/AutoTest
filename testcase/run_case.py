#! /usr/bin/env python3
# _*_ coding:utf-8 _*_
"""
@Auth : Dora
@Date : 2022/4/2 14:17
"""

import pytest,os,sys,allure,datetime
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import requests
import base64
import hashlib
PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ_PARENT_ROOT = os.path.abspath(os.path.dirname(PROJ_ROOT))
parentdir = os.path.dirname(PROJ_ROOT)
sys.path.insert(0, parentdir)



# 打印log到终端同时保存到日志文件
from conf.record_log import Logger
logger = Logger(log_path='logs',log_file='test_digital_human.log').get_log()

# 读取配置数据
from conf.deal_excel import DealExcel

def run_case(digital_server, output, case_scope,jinkins_num=''):
    # 将digital_server, output写入配置文件
    excel_params = DealExcel(excel_name='test_data',sheet_name ='params')
    excel_params.update_excel(case_name='digital_server',data=digital_server)
    excel_params.update_excel(case_name='output',data=output)
    excel_params.update_excel(case_name='jinkins_num',data=str(jinkins_num))

    # 将测试时间、测试范围case_scope记录在配置文件
    test_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    excel_params.update_excel(case_name='test_time',data=test_time)
    excel_params.update_excel(case_name='case_scope',data=case_scope)
    case_path = os.path.join(PROJ_PARENT_ROOT,"testcase","test_digital_human.py")  # 终端输出日志

    if case_scope == 'SMOKE_CASES':
        logger.info('run smoke testcase')
        print('run smoke testcase')
        pytest.main([f'{case_path}::Test_DigitalHuman','-m smoke','-sv'])
    elif case_scope == 'API_CASES':
        logger.info('run API testcase')
        pytest.main([f'{case_path}::Test_DigitalHuman','-m API','-sv']) 
    elif case_scope == 'ALL_CASES':
        logger.info('run ALL testcases')
        pytest.main([f'{case_path}::Test_DigitalHuman','-sv']) 
    elif case_scope == 'video_batch':
        logger.info('batch create videos')
        pytest.main([f'{case_path}::Test_DigitalHuman','-m video_batch','-sv']) 
    else:
        logger.warning(f'{case_scope} out of case range')
    logger.info('everything is done')

if __name__ == '__main__':
    digital_server = 'digital_server-v1.6.0.79-202309111040-520bd81c-2023-09-11-20-02'
    output = f"/home/aitest/dora".replace('/', os.path.sep)
    case_scope = 'ALL_CASES'
    jinkins_num = 303
    run_case(digital_server,output,case_scope,jinkins_num)
    excel_params = DealExcel(sheet_name ='params')
    server = excel_params.get_data(case_name='digital_server',params_name='digital_server')
    print(f'server: {server}')
    output = excel_params.get_data(case_name='output',params_name='output')
    print(f'output: {output}')

    excel_params = DealExcel(excel_name='test_data_own',sheet_name = 'params')

    digital_server = excel_params.get_data(case_name='digital_server',params_name='digital_server')
    print(f'digital_server: {digital_server}')
