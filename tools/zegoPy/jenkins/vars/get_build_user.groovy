// jenkins/vars/get_build_user.groovy
// 将此脚本在 Manager Jenkins -> Configure System -> Global Pipeline Libraries 里面添加

// 使用方式: def user = get_build_user()
// 如果返回值是空字符串，则说明来自远程 IP 触发

/// 获取发起构建任务的用户 ID
def call() {
    def build_user = ""
    wrap([$class: "BuildUser"]) {
        // 可能来自远程触发，此时 BUILD_USER 为 IP 地址例如 "192.168.50.100"
        if (!"${BUILD_USER}".startsWith("1")) {
            build_user = "${BUILD_USER}"
        } else {
            println("This build is triggered by remote IP: ${BUILD_USER}")
        }
    }
    return build_user
}
