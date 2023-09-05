// jenkins/vars/setup_pyscripts.groovy
// 将此脚本在 Manager Jenkins -> Configure System -> Global Pipeline Libraries 里面添加

def call() {
    // 使用了 zegopy (pyscripts) 的构建脚本，在构建前需要安装或更新 zegopy 库
    install_cmd = "python3 -m pip install -i http://dev-pypi.pkg.coding.zego.cloud/common_utils/zegopy/simple zegopy --trusted-host dev-pypi.pkg.coding.zego.cloud --upgrade"
    if (isUnix()) {
        sh(script: install_cmd)
    } else {
        bat(script: install_cmd)
    }
}
