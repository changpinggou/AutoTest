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

# 将控制台输出存入日志文件
from conf.pytest_log import Logger
Logger = Logger()
logger = Logger.loggering('test_digital_human')
# 读取配置数据
from conf.deal_excel import DealExcel

def run_case(digital_server, output, case_scope,jinkins_num=''):
    # 将digital_server, output写入配置文件
    excel_params = DealExcel(sheet_name ='params')
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
        print('run smoke testcase -- run_case.py')
        pytest.main([f'{case_path}::Test_DigitalHuman','-m smoke','-sv'])
        print('smoke case done -- run_case.py')
    elif case_scope == 'API_CASES':
        logger.info('run API testcase')
        pytest.main([f'{case_path}::Test_DigitalHuman','-m API','-sv']) 
    elif case_scope == 'ALL_CASES':
        logger.info('run ALL testcases')
        pytest.main([f'{case_path}::Test_DigitalHuman','-sv']) 
    else:
        logger.warning(f'{case_scope} out of case range')
    logger.info('everything is done')

if __name__ == '__main__':
    digital_server = 'digital_server-v1.6.0.142-202309080839-feature-69cf6c0f-2023-09-08-21-47'
    #digital_server = 'test'
    output = f'{os.path.sep}home{os.path.sep}aitest{os.path.sep}dora'
    case_scope = 'SMOKE_CASES'
    jinkins_num = '123'
    run_case(digital_server,output,case_scope,jinkins_num)
    excel_params = DealExcel(sheet_name ='params')
    server = excel_params.get_data(case_name='digital_server',params_name='digital_server')
    print(f'server: {server}')
    output = excel_params.get_data(case_name='output',params_name='output')
    print(f'output: {output}')