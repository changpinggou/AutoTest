# _*_ coding:UTF-8 _*_
"""
@project -> File :digital_human_code -> pytest_log 
@Author: Dora
@Date: 2023/8/14 14:12
@Desc:
1-功能描述:将pytest执行测试用例时日志保存到指定文件
2-实现步骤：
3-状态（废弃/使用）：可用
"""

import logging,os,sys
PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ_PARENT_ROOT = os.path.abspath(os.path.dirname(PROJ_ROOT))

class Logger:

    def loggering(self,log_file_name):
        # 日志文件
        self.log_file_name = log_file_name
        # 创建logger对象
        logger = logging.getLogger('test_logger')

        # 设置日志等级
        logger.setLevel(logging.DEBUG)

        # 追加写入文件a ，设置utf-8 编码防止中文写入乱码
        logs_dir_path = os.path.join(PROJ_PARENT_ROOT,"logs")
        if os.pat.exists(logs_dir_path) is False:
            os.mkdir(logs_dir_path)
        log_path = os.path.join(logs_dir_path, '{}.log'.format(self.log_file_name))
        test_log = logging.FileHandler(log_path, 'a', encoding='utf-8')

        # 向文件输出的日志级别
        test_log.setLevel(logging.DEBUG)

        # 向文件输出的日志信息格式
        formatter = logging.Formatter(
            '%(asctime)s | %(filename)s | %(funcName)s | line:%(lineno)d | %(levelname)s | %(message)s ')

        test_log.setFormatter(formatter)

        # 加载文件到logger对象中
        logger.addHandler(test_log)

        return logger
    
    def enable_console_logging(self, formatter=None):
        # 启用控制台日志记录
        self.streamhandler = logging.StreamHandler(sys.stdout)
        self.streamhandler.setFormatter(formatter if formatter else self.console_formatter)
        self.streamhandler.setLevel(self.global_log_level)
        self.logger.addHandler(self.streamhandler)


if __name__ == "__main__":
    pass
    # test = loger().logering()
#这种写法
#log_test = Logger().logering('test_digital_human_digital_inference_V160_132_inference')

# 其他文件调用时，在文件开头写
# from conf import pytest_log
#logger = pytest_log.log_test
