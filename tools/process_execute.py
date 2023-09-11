import os
import time
import json
import subprocess
from conf import pytest_log

# logger = pytest_log.log_test
def execute_command(command):
    process = subprocess.Popen(command,
                               shell = True,
                               stdout = subprocess.PIPE,
                               stderr = subprocess.PIPE,
                               bufsize = 15 * 1024 * 1024)
    
    start_time = time.time()
    print(str(command))
    print(f'begin run command:{start_time}\n')

    process_pid = process.pid
    with open('/home/aitest/dora/conf/pid.txt', 'w', encoding='utf-8') as file:
        file.write(json.dumps(process_pid))
    output, errors = process.communicate()
    exit_code = process.wait()

    if exit_code == 0:
        try:
            print(str(output.decode()))
            print(output.decode())
        except UnicodeDecodeError:
            print(str(output.decode('gbk')))
            print(output.decode('gbk'))  # 防备windows出现编码问题
    else:
        print(str(output.decode()))
        print(str(f"cmd error:{command}"))
        try:
            print(errors.decode())
        except UnicodeDecodeError:
            print(errors.decode('gbk'))  # 防备windows出现编码问题

    use_time = time.time() - start_time
    print('over sync command, total: ' + str(use_time))
    print(f'total(s):{use_time}')

    return use_time
    