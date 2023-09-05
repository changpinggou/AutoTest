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
    agent { label 'winpyinstaller' }
    options {
        timeout(time: 50, unit: 'MINUTES') // 设置 30 分钟超时
    }

    parameters {
        string(
            name: 'JENKINS_CONTEXT',
            defaultValue: '我很懒, 什么都没有填',
            description: '填写编包目的（或需求描述），编包任务上下文，最后会在飞书机器人通知中发送出来，方便未来查找\n'
        )

        string(name: 'BRANCH', defaultValue: 'master', description: '要构建的分支')
        string(name: 'WINDOWS_DIST_URL', defaultValue: "",  description: 'windows产物包地址')
        string(name: 'WINDOWS_DIST_LOCAL_PATH', defaultValue: "",  description: 'windows产物包本地地址')
        string(name: 'HOST_BRANCH', defaultValue: 'master', description: '被测试的数字人分支标志')
        string(name: 'HOST_COMMITID', defaultValue: '8d7d79', description: '被测试的数字人Commit节点')
        string(name: 'HOST_VERSION', defaultValue: '1.5.1.78', description: '被测试的数字人包版本')
        string(name: 'TEST_CASE_SCOPE',defaultValue: 'CI',  description: '测试用例范畴\n')
        choice(
            name: 'PLATFORM',
            choices: ['linux', 'windows'],
            description: '自动化测试平台[linux, windows] \n'
        )

        booleanParam(name: 'SEND_NOTICE', defaultValue: true, description: '是否发送飞书通知\n')
        string(name: 'NOTICE_USER', defaultValue: '', description: '构建消息额外通知谁, 如果米有填, 则at构建触发人. \n多个人的时候用英文逗号分割.\n')
    }

    environment {
        PROJECT_NAME = 'DigitalHumanWinTest'
        WECOM_WEBHOOK = 'https://open.feishu.cn/open-apis/bot/v2/hook/03f0abb4-679d-41a8-8036-1eb373b55b11'
        // WECOM_WEBHOOK = 'https://open.feishu.cn/open-apis/bot/v2/hook/f5449473-5ab6-48ac-8546-c3de0900ec29'
        GIT_URL = "git@git.e.coding.zego.cloud:dev/digitalhuman/DigitalHumanTest.git"
        GIT_CREDENTIALS_ID = 'kiwi_builder_ssh'
    }

    stages {
        stage('checkout') {
            steps {
                script {
                    if (params.BUILD_TARGET == 'linux'){
                        echo "applechang-test 该stage是用来做windows单元测试的"
                        error 'BUILD_TARGET is linux, but only Support windows test on this machine!!!'
                    }

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
                }
            }
        }

        stage('windows-UnitTest') {
            steps {
                // 通用变量
                script {
                    // 启动单元测试
                    platform = params.PLATFORM
                    if(params.PLATFORM == 'both'){
                        platform='windows'
                    }

                    def outTempDir = "${WORKSPACE}\\__out"
                    args = "--jenkins --platform=" + platform + " "
                    args+= "--digithumanstuburl=" + params.WINDOWS_DIST_URL + " "
                    args+= "--digithumanstublocalpath=" + params.WINDOWS_DIST_LOCAL_PATH + " "
                    args+= "--outtempdir=" + outTempDir + " "
                    args+= "--testcasescope=" + params.TEST_CASE_SCOPE + " "

                    echo "windows unittest begine"
                    cmd = "python -u unittest_entry.py ${args}"
                    def returnValue = bat(label: '', returnStdout: true, script: cmd)
                    echo "windows unittest end: ${returnValue}"
                }
            }
        }

        stage('windows-PerfTest') {
            steps {
                script {
                    def outTempDir = "${WORKSPACE}\\__out"
                    args = "--jenkins --platform=" + platform + " "
                    args+= "--digithumanstuburl=" + params.WINDOWS_DIST_URL + " "
                    args+= "--digithumanstublocalpath=" + params.WINDOWS_DIST_LOCAL_PATH + " "
                    args+= "--outtempdir=" + outTempDir + " "
                    args+= "--testcasescope=" + params.TEST_CASE_SCOPE + " "
                    
                    echo "windows perftest begine"
                    cmd = "python -u perftest_entry.py ${args}"
                    def returnValue = bat(label: '', returnStdout: true, script: cmd)
                    echo "windows perftest end: ${returnValue}"
                }
            }
        }
    }
    post {
        success {
            script {
                // 拼接产物信息
                productJsonObj = [:]
                // 构造通知消息
                def mdBody = ""
                if(product_output_list.size() < 1){
                    mdBody += "<br/>- <font color='grey'>嘿, 没有产物</font>"
                }else{
                    mdBody += "<br/>- <font color='grey'>产物: </font>"
                    // 获取字典中所有键的集合
                    for (def item in product_output_list) {
                        def keys = item.keySet()
                        // 遍历键集合并打印每个键本身
                        for (def key in keys) {
                            productJsonObj[key] = item[key]
                            mdBody += "<br/>    - ${key}:    [${item[key]}](${item[key]})"
                        }
                    }
                }

                println("\n\n***PRODUCT***\n\n${productJsonObj}\n\n")

                // 写入环境变量中，给下游任务使用
                env.ZEF_PRODUCT_JSON = JsonOutput.toJson(productJsonObj)

                def resultJsonString = JsonOutput.prettyPrint(env.ZEF_PRODUCT_JSON)

                // 写入产物信息到文件
                writeFile(file: "${WORKSPACE}/products.json", text: resultJsonString)

                // 归档产物信息文件到 Jenkins 制品库
                archiveArtifacts 'products.json'

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
