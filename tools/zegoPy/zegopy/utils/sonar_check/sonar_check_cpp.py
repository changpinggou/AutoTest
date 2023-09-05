# coding=UTF-8
import os
import json
import requests
import time
from typing import List
 
'''
该脚本支持扫描C和C++源码，请根据项目需求更改初始化参数。目前只在Windows机器上配置相关工具。Linux请使用Docker镜像。
在pipeline中按如下方式使用即可：
stage('sonar代码扫描') {
    steps {
        script {
            bat "python3.exe %WORKSPACE%\\jenkins_build\\qt\\sonar_check.py"
        }
    }
}
'''
class SonarCheck:
    def __init__(self, language: str, project_name: str, source_folders: List[str], source_exclusions: List[str]):
        """
        @param language 代码语言（c或者c++）
        @param project_name Sonar 项目名称，建议：仓库名 - 分支名，名称不能使用'/'，需要进行替换
        @param source_folders 项目源码路径 eg: ['.\\TalkLineSDK', '.\\Demo']
        @param source_exclusions Sonar 扫描排除目录, 相对当前路径，注意只需填写相对路径，如果是目录后面以'/**/*'结尾 eg: ['TalkLineSDK\\TalkLineBase\\3rdparty\\**\\*', 'TalkLineSDK\\TalkLineBase\\zego_sdks\\**\\*']
        """
        self.SONAR_LANGUAGE = language
        self.SONAR_PROJECT_KEY = project_name
        self.SONAR_SOURCES = source_folders
        self.SONAR_EXCLUSIONS = source_exclusions
 
        # 启动 <jobs> 线程数
        self.CPPCHECK_JOB_NUM = 8
        # 生成cppcheck文件路径
        self.CPPCHECK_RESULT_FILE = ".\\cppcheck_result.xml"
        # sonar服务地址，默认
        self.SONAR_SERVER_URL = 'http://ci.zego.cloud:9000'
        # sonar令牌，默认
        self.SONAR_LOGIN = 'a2888742660eff6e2ae5c88794527fb6b6c12899'
 
    def sonar_check(self):
        self.cpp_check_execute()
        self.sonar_scanner_execute()
        if self.wait_result():
            print('sonar代码扫描成功！')
        else:
            raise Exception("sonar代码扫描失败！")
 
    def sonar_scanner_execute(self):
        """
        sonar参数说明地址：https://docs.sonarqube.org/latest/analysis/analysis-parameters/
        通过sonar-scanner执行sonar代码扫描。如果需要添加额外参数，需要改执行参数。
        """
        sources = ""
        for src in self.SONAR_SOURCES:
            sources += "{},".format(src)
        sources = sources[:-1]
        print("current sources: {}".format(sources))

        exclusions = ""
        for exclusion in self.SONAR_EXCLUSIONS:
            exclusions += "{},".format(exclusion)
        exclusions = exclusions[:-1]
        print("current exclusions: {}".format(exclusions))


        sonar_scanner_cmd = "sonar-scanner.bat " \
                            "-D\"sonar.projectKey={}\" " \
                            "-D\"sonar.sources={}\" " \
                            "-D\"sonar.exclusions={}\" " \
                            "-D\"sonar.host.url={}\" " \
                            "-D\"sonar.login={}\" " \
                            "-D\"sonar.language={}\" " \
                            "-D\"sonar.cxx.cppcheck.reportPath={}\"".format(self.SONAR_PROJECT_KEY, sources,
                                                                            exclusions, self.SONAR_SERVER_URL,
                                                                            self.SONAR_LOGIN, self.SONAR_LANGUAGE,
                                                                            self.CPPCHECK_RESULT_FILE)
        print("exec sonar scanner cmd: {}".format(sonar_scanner_cmd))
        os.system(sonar_scanner_cmd)
 
    def cpp_check_execute(self):
        """
        执行cppCheck命令
        """
        cpp_check_cmd = "cppcheck.exe -j {} ".format(self.CPPCHECK_JOB_NUM)
        for exclusion in self.SONAR_EXCLUSIONS:
            cpp_check_cmd += "-i{} ".format(exclusion)
        for src in self.SONAR_SOURCES:
            cpp_check_cmd += "%WORKSPACE%{} ".format(src)
        cpp_check_cmd += "--xml-version=2 --output-file={} --enable=all".format(self.CPPCHECK_RESULT_FILE)

        print("exec cpp check cmd: {}".format(cpp_check_cmd))
        os.system(cpp_check_cmd)
 
    def wait_result(self):
        """
        sonar 结果检查，如果结果异常，会抛出错误，超时时间1分钟
        """
        for i in range(60):
            result = requests.get('{}/api/qualitygates/project_status?projectKey={}'.format(self.SONAR_SERVER_URL,
                                                                                            self.SONAR_PROJECT_KEY))
            result_json = json.loads(str(result.text))
            if result_json.get('errors'):
                return False
            elif result_json.get('projectStatus').get('status') == 'OK':
                return True
            elif result_json.get('projectStatus').get('status') == 'ERROR':
                return False
            elif result_json.get('projectStatus').get('status') == 'CANCEL':
                return False
            else:
                time.sleep(1)
 
 
if __name__ == "__main__":
    language = 'c++'
    project_name = 'roomkit_windows'
    source_folders = ['.\\TalkLineSDK', '.\\Demo']
    source_exclusions = ['TalkLineSDK\\TalkLineBase\\3rdparty\\**\\*', 'TalkLineSDK\\TalkLineBase\\zego_sdks\\**\\*']
    sonar = SonarCheck(language=language, project_name=project_name, source_folders=source_folders, source_exclusions=exclusions)
    sonar.sonar_check()