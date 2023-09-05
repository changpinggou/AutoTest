# coding=UTF-8
import os
import json
import requests
import time
from typing import List

'''
该脚本可用于Sonar检查多种语言：JavaScript, C#, TypeScript, Kotlin, Ruby, Go, Scala, Flex, Python, PHP, HTML, CSS, XML and VB.NET
该脚本需要在Docker中使用，在pipeline中按如下方式使用即可：
agent中args需要添加' -v $HOME:/home/jenkins/sonar-scanner-3.3.0.1492-linux'，image不限制
agent {
        docker {
            image 'dev-docker.pkg.coding.zego.cloud/ci_docker_images/android/android_ndk_r21d_sdk_30:1.1.12'
            args ' -v $HOME:/home/jenkins/sonar-scanner-3.3.0.1492-linux'
        }
}
添加一个代码扫描的stage
stage('sonar代码扫描') {
    steps {
        script {
            sh "python3 ${WORKSPACE}/path/to/sonar_check_others.py"
        }
    }
}
'''
class SonarCheck:
    def __init__(self, language: str, project_name: str, source_folders: List[str], source_exclusions: List[str]):
        """
        @param language 需要扫描的编程语言
        @param project_name Sonar 项目名称，建议：仓库名 - 分支名，名称不能使用'/'，需要进行替换
        @param source_folders 项目源码路径 eg: ['./sample','./sdk','./script']
        @param source_exclusions Sonar 扫描排除目录, 相对当前路径，注意只需填写相对路径，如果是目录后面以'/**/*'结尾 eg: ['./test/**/*']
        """
        self.SONAR_PROJECT_KEY = project_name
        self.SONAR_SOURCES = source_folders
        self.SONAR_EXCLUSIONS = source_exclusions
        self.SONAR_LANGUAGE = language
        
        # sonar服务地址，默认
        self.SONAR_SERVER_URL = 'http://ci.zego.cloud:9000'
        # sonar令牌，默认
        self.SONAR_LOGIN = 'a2888742660eff6e2ae5c88794527fb6b6c12899'

    def sonar_check(self):
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

        sonar_scanner_cmd = "/home/jenkins/sonar-scanner-3.3.0.1492-linux/bin/sonar-scanner " \
                            "-D\"sonar.projectKey={}\" " \
                            "-D\"sonar.sources={}\" " \
                            "-D\"sonar.exclusions={}\" " \
                            "-D\"sonar.host.url={}\" " \
                            "-D\"sonar.login={}\" ".format(self.SONAR_PROJECT_KEY, sources,
                                                            exclusions, self.SONAR_SERVER_URL,
                                                            self.SONAR_LOGIN)
        if self.SONAR_LANGUAGE == 'java':
            sonar_scanner_cmd += "-D\"sonar.java.binaries={}\" ".format(sources)

        print("exec sonar scanner cmd: {}".format(sonar_scanner_cmd))
        os.system(sonar_scanner_cmd)

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
    project_name = 'roomkit_web'
    source_folders = ['./sample','./sdk','./script']
    source_exclusions = ['./test/**/*']
    sonar = SonarCheck(project_name=project_name, source_folders=source_folders, source_exclusions=source_exclusions)
    sonar.sonar_check()