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

import logging,os
PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ_PARENT_ROOT = os.path.abspath(os.path.dirname(PROJ_ROOT))

class Logger:
    def logering(self,log_file_name):
        # 创建logger对象
        logger = logging.getLogger('test_logger')

        # 设置日志等级
        logger.setLevel(logging.DEBUG)

        # 追加写入文件a ，设置utf-8 编码防止中文写入乱码
        logs_dir = os.path.join(PROJ_PARENT_ROOT,"logs")
        if os.path.exists(logs_dir):
            os.mkdir(logs_dir)
        log_path = os.path.join(logs_dir,'{}.log'.format(log_file_name))
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


if __name__ == "__main__":
    pass
    # test = loger().logering()
#这种写法
log_test = Logger().logering('test_digital_human')

# 其他文件调用时，在文件开头写
# from conf import pytest_log
#logger = pytest_log.log_test
