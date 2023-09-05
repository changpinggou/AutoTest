// jenkins/vars/report_wecom.groovy
// 将此脚本在 Manager Jenkins -> Configure System -> Global Pipeline Libraries 里面添加

// 使用方式: report_wecom("your url", true, "your project name", "userid", "content")

/// 发起企业微信通知
/// @param webhook 企业微信机器人完整的 WebHook 链接
/// @param success 构建状态
/// @param projectName 项目名称，用于标题
/// @param mentionUser 额外发一条 at 提醒通知的用户名，传空则不发
/// @param content 通知的正文，Markdown 格式
def call(String webhook, Boolean success, String projectName, String mentionUser, String content) {
    if (mentionUser) {
        def code = "import requests,json,sys;requests.post(sys.argv[1],data=json.dumps({'msgtype':'text','text':{'content':'⬇️请进行处理⬇️','mentioned_list':[sys.argv[2]]}}))"
        sh(returnStatus: true, script: "python3 -c \"exec(\\\"${code}\\\")\" '${webhook}' '${mentionUser}' ")
    }
    def emoji = success ? "🌞" : "⛈"
    def title = "### ${emoji} **${projectName}** <font color=\"comment\">(build:${BUILD_NUMBER})</font>"
    def jobLink = "\n- <font color=\"comment\">Jenkins 链接：</font>[**点击查看**](${BUILD_URL})"
    def pycode = "import requests,json,sys;requests.post(sys.argv[1],data=json.dumps({'msgtype':'markdown','markdown':{'content':sys.argv[2]}}))"
    sh(returnStatus: true, script: "python3 -c \"exec(\\\"${pycode}\\\")\" '${webhook}' '${title}\n\n${jobLink}\n${content}' ")
}
