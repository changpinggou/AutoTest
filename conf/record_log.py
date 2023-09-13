# _*_ coding:UTF-8 _*_
"""
@project -> File :digital_human_code -> change 
@Author: Dora
@Date: 2023/9/9 00:11
@Desc:
1-功能描述：
2-实现步骤：
3-状态（废弃/使用）：
"""
import os,stat,sys
import logging
from time import sleep
from conf.com_func import ComFunc
com_func = ComFunc()

PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ_PARENT_ROOT = os.path.abspath(os.path.dirname(PROJ_ROOT))
sys.path.insert(0, PROJ_PARENT_ROOT)  

class Logger:
    def __init__(self, log_path,log_file,logger=None, level=logging.DEBUG):#log_path = 'logs'
        """
        file_path = com_func.mkdir_file(file_path=log_path)
        log_file_path = os.path.join(PROJ_PARENT_ROOT, file_path, log_file)  
         """
        log_file_path = com_func.mkdir_file(PROJ_PARENT_ROOT,log_path,log_file)

        #log_file_path = com_func.mkdir_file(log_path=log_path,log_file=log_file)

        self.logger = logging.getLogger(logger)
        self.logger.propagate = False  # 防止终端重复打印
        self.logger.setLevel(level)
        fh = logging.FileHandler(log_file_path, 'a+', encoding='utf-8')
        fh.setLevel(level)
        sh = logging.StreamHandler()
        sh.setLevel(level)
        formatter = logging.Formatter("%(asctime)s-%(filename)s[line:%(lineno)d]-%(levelname)s: %(message)s")
        fh.setFormatter(formatter)
        sh.setFormatter(formatter)
        self.logger.handlers.clear()
        self.logger.addHandler(fh)
        self.logger.addHandler(sh)
        fh.close()
        sh.close()

    def get_log(self):
        return self.logger

