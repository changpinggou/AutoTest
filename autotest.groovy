import groovy.json.JsonOutput

def formatDuration(long durationInMillis) {
    def elapsedTimeInSeconds = (durationInMillis / 1000).intValue()
    def minutes = (elapsedTimeInSeconds / 60).intValue()
    def seconds = (elapsedTimeInSeconds % 60).intValue()
    return String.format("%02d分钟%02d秒", minutes, seconds)
}

NOTIFY_TMPL = '''
{
    "config": {
        "wide_screen_mode": true
    },
    "elements": [
        {
            "tag": "markdown",
            "content": "<br/>- <font color='grey'>发起人: </font>${build_triggers}<br/>- <font color='grey'>上下文: </font>${build_context}<br/>- <font color='grey'>被测分支: </font>${build_branch}<br/>- <font color='grey'>被测CommitId: </font>${build_commit}<br/>- **<font color='green'>${build_state}</font>**<br/>- <font color='grey'>被测版本: </font><font color='green'>${build_version}</font>${build_content}<br/> --------------<br/><br/>"
        },
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": "构建链接"
                    },
                    "type": "default",
                    "multi_url": {
                        "url": "${jenkins_url}",
                        "pc_url": "",
                        "android_url": "",
                        "ios_url": ""
                    }
                }
            ]
        }
    ],
    "header": {
        "template": "blue",
        "title": {
            "content": "${build_title}(${build_number})",
            "tag": "plain_text"
        }
    }
}
'''

/// 发起企业微信通知
/// @param webhook 企业微信机器人完整的 WebHook 链接
/// @param success 构建状态
/// @param projectName 项目名称，用于标题
/// @param mentionUser 额外发一条 at 提醒通知的用户名，传空则不发
/// @param content 通知的正文，Markdown 格式
def send_wecom_notification(String webhook, Boolean success, String projectName, String mentionUser, String content) {
    List<String> mentionUsers = []
    if (mentionUser) {
        String[] list = mentionUser.split(',')
        for( String value : list ){
            // 补两头的双引号
            mentionUsers.add("<at id='${value}'></at> ")
        }
        // 去重
        mentionUsers.unique()
    }

    def title = "💔💔${projectName} 编译失败!!! "
    def state = "Build failure"
    if(success) {  
        title = "✅✅${projectName} 编译成功!!! "  
        state = "Build success"
    }


    def notifyBody = NOTIFY_TMPL
        .replace('${build_number}', BUILD_NUMBER)
        .replace('${build_context}', JENKINS_CONTEXT)
        .replace('${build_version}', BUILD_VERSION)
        .replace('${jenkins_url}', BUILD_URL)
        .replace('${build_branch}', BUILD_HOST_BRANCH)
        .replace('${build_commit}', BUILD_HOST_COMMIT)
        .replace('${build_title}', title)
        .replace('${build_state}', state)
        .replace('${build_triggers}', mentionUsers.join(' '))
        .replace('${build_content}', content)
        .replaceAll("<br/>", "\\\\n")


    def requestBody = """{
            "msg_type": "interactive",
            "card": ${notifyBody}
        }"""

    writeFile(file: "${WORKSPACE}/${projectName}.json", text: requestBody)


    def response = httpRequest(
        url: webhook, // 请求地址
        // quiet: true, // 不显示请求日志
        consoleLogResponseBody: true,
        httpMode: 'POST',
        ignoreSslErrors: true,
        acceptType: 'APPLICATION_JSON',
        contentType: "APPLICATION_JSON_UTF8",
        requestBody: requestBody
    )


}

pipeline {
    agent { label 'docker-autotest' }
    options {
        timeout(time: 50, unit: 'MINUTES') // 设置 30 分钟超时
    }

    parameters {
        string(
            name: 'JENKINS_CONTEXT',
            defaultValue: 'Linux自动化测试',
            description: '填写编包目的（或需求描述），编包任务上下文，最后会在飞书机器人通知中发送出来，方便未来查找\n'
        )

        string(name: 'LINUX_DOCKER_FULL_NAME', defaultValue: '',  description: '完整的被测docker路径\n')
        string(name: 'LINUX_DOCKER_NAME',defaultValue: '',  description: '被测docker名\n')
        choice(
            name: 'TEST_CASE_SCOPE',
            choices: ['CI', 'P1'],
            description: '测试用例范畴\n'
        )
        // string(name: 'TEST_CASE_SCOPE',defaultValue: 'CI',  description: '测试用例范畴\n')
        string(name: 'BRANCH', defaultValue: 'master', description: '要构建的分支')
        string(name: 'HOST_BRANCH', defaultValue: 'master', description: '被测试的数字人分支标志')
        string(name: 'HOST_COMMITID', defaultValue: '8d7d79', description: '被测试的数字人Commit节点')
        string(name: 'HOST_VERSION', defaultValue: '1.5.1.78', description: '被测试的数字人包版本')
        choice(
            name: 'PLATFORM',
            choices: ['linux', 'windows'],
            description: '自动化测试平台,both两个平台都要测试 \n'
        )

        booleanParam(name: 'SEND_NOTICE', defaultValue: true, description: '是否发送飞书通知\n')
        string(name: 'NOTICE_USER', defaultValue: '', description: '构建消息额外通知谁, 如果米有填, 则at构建触发人. \n多个人的时候用英文逗号分割.\n')
    }

    environment {
        PROJECT_NAME = 'DigitalHumanLinuxTest'
        // WECOM_WEBHOOK = 'https://open.feishu.cn/open-apis/bot/v2/hook/f5449473-5ab6-48ac-8546-c3de0900ec29'
        WECOM_WEBHOOK = 'https://open.feishu.cn/open-apis/bot/v2/hook/03f0abb4-679d-41a8-8036-1eb373b55b11'
        GIT_URL = "git@git.e.coding.zego.cloud:dev/digitalhuman/DigitalHumanTest.git"
        GIT_CREDENTIALS_ID = 'kiwi_builder_ssh'
    }

    stages {

        stage('checkout') {
            steps {
                script {
                    if (params.BUILD_TARGET == 'windows'){
                        echo "applechang-test 该stage是用来做windows单元测试的"
                        error 'BUILD_TARGET is linux, but only Support windows test on this machine!!!'
                    }

                    // 读取 package.json 文件并解析为 JSON 对象
                    // def packageJsonPath = "${WORKSPACE}/package.json"
                    // echo "WORKSPACE: ${WORKSPACE}"
                    // echo "packageJsonPath: ${packageJsonPath}"
                    // def packageJsonObj = readJSON(file: packageJsonPath)
                    // // 获取 version 字段
                    // def version = packageJsonObj.version
                    // echo "Package version: ${version}"

                    env.BUILD_VERSION = params.HOST_VERSION
                    echo "test source BUILD_VERSION: ${env.BUILD_VERSION}"

                    env.BUILD_BRANCH = params.BRANCH
                    env.BUILD_HOST_BRANCH = params.HOST_BRANCH
                    env.BUILD_HOST_COMMIT = params.HOST_COMMITID

                    // 收集构建结果
                    product_output_list = []
                    // 触发构建的人
                    wrap([$class: 'BuildUser']) {
                        if (!"${BUILD_USER}".startsWith('1')) {
                            TRIGGERED_USER = "${BUILD_USER}"
                        }
                    }
                    if (params.NOTICE_USER) {
                        TRIGGERED_USER = TRIGGERED_USER + ",${params.NOTICE_USER}"
                    }
                    echo "TRIGGERED_USER: ${TRIGGERED_USER}"

                    def repository = "git@github.com:changpinggou/AutoTest.git"
                    def output = sh(script: "bash /data2/AutoTest/git_load.sh ${WORKSPACE} ${repository} ${env.BRANCH}", returnStdout: true)
                    echo output

                    // 获取最新 commit 的 ID (暂时不走拉取库形式，所以注释掉)
                    // env.GIT_COMMIT_ID = sh(script: "cd ${WORKSPACE} && git rev-parse --short HEAD", returnStdout: true).trim()
                    // def sdkCloneDir = "${WORKSPACE}/applechangtest"
                    // def temp = new File(sdkCloneDir)
                    // if(!temp.exists()){
                    //     temp.mkdir()
                    // }
                    // dir(sdkCloneDir) {
                    //     checkout scmGit(branches: [[name: params.BRANCH]], extensions: [], userRemoteConfigs: [[credentialsId: '24f85527-7905-4551-873c-1173e0a87733', url: 'git@github.com:changpinggou/AutoTest.git']])
                    // }
                    // 当前还是用git的所有文件替换到workspace上去
                    // sh(script: "rm -r ${WORKSPACE}/* && rm -rf ${WORKSPACE}/* && cp /data2/AutoTest/ ${WORKSPACE}", returnStdout: true)

                }
            }
        }

        stage('linux-UnitTest') {
            steps {
                // 通用变量
                script {
                    // 启动单元测试
                    platform = params.PLATFORM
                    if(params.PLATFORM == 'both'){
                        echo "开始进行linux单元测试"
                        platform='linux'
                    }

                    def outTempDir = "${WORKSPACE}/__out"
                    args = "--jenkins --platform=" + params.PLATFORM + " "
                    args+= "--dockername=" + params.LINUX_DOCKER_NAME + " "
                    args+= "--outtempdir=" + outTempDir + " "
                    args+= "--testcasescope=" + params.TEST_CASE_SCOPE + " "
                    // 临时输出参数
                    args+= "--outputpath=" + "${WORKSPACE}/results" + " "
                    // args+= "--outputpath=" + params.outputpath + " "
                    
                    echo "args:${args}"
                    cmd = "python3 -u AutoTest/unittest_entry.py ${args}"
                    sh(script: cmd, label: STAGE_NAME)
                }
            }
        }

        // stage('linux-PerfTest') {
        //     steps {
        //         script {
        //             // 启动单元测试
        //             // platform = params.PLATFORM
        //             // if(params.PLATFORM == 'both'){
        //             //     platform='linux'
        //             // }
        //             // def outTempDir = "${WORKSPACE}\\__out"
        //             // args = "--jenkins --platform=" + params.PLATFORM + " "
        //             // args+= "--dockername=" + params.LINUX_DOCKER_NAME + " "
        //             // args+= "--outtempdir=" + outTempDir + " "
        //             // args+= "--testcasescope=" + params.TEST_CASE_SCOPE + " "
        //             // cmd = "python3 -u perftest_entry.py ${args}"
        //             // sh(script: cmd, label: STAGE_NAME)
        //         }
        //     }
        // }
    }
    post {
        success {
            script {
                // 读取 result.json 文件并解析为 JSON 对象
                def resultJsonPath = "${WORKSPACE}/result.json"
                echo "resultJsonPath: ${resultJsonPath}"
                // 拼接产物信息
                def resultJsonObj = readJSON(file: resultJsonPath)
                // 构造通知消息
                def mdBody = ""
                if(resultJsonObj.size() < 1){
                    mdBody += "<br/>- <font color='grey'>嘿, 没有产物</font>"
                }else{
                    mdBody += "<br/>- <font color='grey'>产物: </font>"
                    // 获取字典中所有键的集合
                    def keys = resultJsonObj.keySet()
                    for (def key in keys) {
                        if(key == "link"){
                            mdBody += "<br/> - ${key}: [${resultJsonObj[key]}](${resultJsonObj[key]})"
                        }else if(resultJsonObj[key].endsWith('.json') || resultJsonObj[key].endsWith('.log')){
                            echo "originPath: ${resultJsonObj[key]}"
                            def cSubFileName = "results/" + resultJsonObj[key].substring(resultJsonObj[key].lastIndexOf('/') + 1)
                            echo "subFileName: ${cSubFileName}"
                            archiveArtifacts cSubFileName
                        }else{
                            mdBody += "<br/> - ${key}: ${resultJsonObj[key]}"
                        }
                    }
                }


                println("\n\n***PRODUCT***\n\n${resultJsonObj}\n\n")

                // 写入环境变量中，给下游任务使用
                env.ZEF_PRODUCT_JSON = JsonOutput.toJson(resultJsonObj)

                def resultJsonString = JsonOutput.prettyPrint(env.ZEF_PRODUCT_JSON)

                // 写入产物信息到文件
                writeFile(file: "${WORKSPACE}/products.json", text: resultJsonString)

                // 归档产物信息文件到 Jenkins 制品库
                archiveArtifacts 'products.json'
                archiveArtifacts 'result.html'

                echo "SUCCESS!!! BUILD_VERSION=${env.BUILD_VERSION}"
                
                if (params.SEND_NOTICE) {
                    // 发送成功通知
                    send_wecom_notification(WECOM_WEBHOOK, true, PROJECT_NAME, TRIGGERED_USER, mdBody)
                }
            }
        }

        unsuccessful {
            script {
                if (params.SEND_NOTICE) {
                    // 发送失败通知
                    send_wecom_notification(WECOM_WEBHOOK, false, PROJECT_NAME, TRIGGERED_USER, "")
                }
            }
        }
    }
}
