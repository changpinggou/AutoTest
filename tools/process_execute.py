import os
import time
import json
import subprocess,sys
PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ_PARENT_ROOT = os.path.abspath(os.path.dirname(PROJ_ROOT))
parentdir = os.path.dirname(PROJ_ROOT) 
sys.path.insert(0,parentdir)

def execute_command(command):
    process = subprocess.Popen(command,
                               shell = True,
                               stdout = subprocess.PIPE,
                               stderr = subprocess.PIPE,
                               bufsize = 15 * 1024 * 1024)
    
    start_time = time.time()
    #print(str(command))
    print(f'begin run command:{start_time}\n')

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
        print(output.decode())
        print(f"cmd error:{command}")
        try:
            print(errors.decode())
            print(errors.decode())
        except UnicodeDecodeError:
            print(errors.decode('gbk'))  # 防备windows出现编码问题

    use_time = round(time.time() - start_time, 3)
    print('over sync command, total: ' + str(use_time))
    print(f'total time(s):{use_time}')

    return use_time
    