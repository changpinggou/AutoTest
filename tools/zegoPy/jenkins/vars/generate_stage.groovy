// jenkins/vars/generate_stage.groovy
// 将此脚本在 Manager Jenkins -> Configure System -> Global Pipeline Libraries 里面添加

// 使用方式:
// cmd = "python3 build.py --android"
// generate_stage("android", cmd)

// "target" 的取值如下
// --- "android"
// --- "ios"
// --- "mac"
// --- "win"
// --- "ubuntu"
// --- "centos"
// --- "hisi"
// --- "myir"
// --- "rockchip"
// --- "allwinner"
// --- "raspberrypi"
// --- "novatek"
// --- "neoway"
// --- "gokeic"
// --- "ingenic"
// --- "linaro"
// --- "alios"
// --- "armlinux"
// --- "ohos"

/// 生成一个可供 Scripted Pipeline 执行的 stage 代码块以用于 parallel 并发构建
/// 一般用于生成多平台的任务，此处封装了各个平台的执行环境
///
/// @param stageName 用于标识这个 Stage 的名称
/// @param target 要构建的目标平台，取值参考上方注释
/// @param executeCommand 要执行的任务代码，例如 "python3 -u build.py --ios"
/// @param extraScript 额外需要执行的闭包，默认不用传，传了则在构建完成后执行此闭包
/// @param overrideRunner 如果需要使用自定义的 docker image 或 agent label，则通过此参数覆盖，默认传空则使用以下定义的
def call(String stageName, String target, String executeCommand, Closure extraScript=null, String overrideRunner=null, Boolean cleanCheckout=false) {

  def useDocker = true
  def dockerImage = "dev-docker.pkg.coding.zego.cloud/ci_docker_images/"
  def agentLabel = ""

  if (target == "android") {
    dockerImage += "android/android_ndk_r21d_sdk_30_compiler:1.0.0"
  } else if (target == "ios") {
    useDocker = false
    agentLabel = "xcode"
  } else if (target == "mac") {
    useDocker = false
    agentLabel = "xcode"
  } else if (target == "win") {
    useDocker = false
    agentLabel = "vs2019"
  } else if (target == "ubuntu") {
    dockerImage += "linux/ubuntu_compiler:1.0.2"
  } else if (target == "centos") {
    dockerImage += "linux/centos_compiler:1.0.2"
  } else if (target == "hisi") {
    dockerImage += "embedded/em_hisi_compiler:1.0.1"
  } else if (target == "myir") {
    dockerImage += "embedded/em_myir_compiler:1.0.1"
  } else if (target == "rockchip") {
    dockerImage += "embedded/em_rockchip_compiler:1.0.7"
  } else if (target == "allwinner") {
    dockerImage += "embedded/em_allwinner_compiler:1.0.1"
  } else if (target == "raspberrypi") {
    dockerImage += "embedded/em_raspberrypi_compiler:1.0.4"
  } else if (target == "novatek") {
    dockerImage += "embedded/em_novatek_compiler:1.0.0"
  } else if (target == "neoway") {
    dockerImage += "embedded/em_neoway_compiler:1.0.1"
  } else if (target == "gokeic") {
    dockerImage += "embedded/em_gokeic_compiler:1.0.1"
  } else if (target == "ingenic") {
    dockerImage += "embedded/em_ingenic_compiler:1.0.1"
  } else if (target == "linaro") {
    dockerImage += "embedded/em_linaro_compiler:1.0.3"
  } else if (target == "alios") {
    dockerImage += "embedded/em_alios_compiler:1.0.1"
  } else if (target == "armlinux") {
    dockerImage += "embedded/arm_linux_compiler:1.0.5"
  } else if (target == "ohos") {
    useDocker = false
    agentLabel = "harmonyos"
  } else {
    throw new Exception("[ERROR] Unknown target name: ${target}")
  }

  if (overrideRunner != null && overrideRunner != "") {
    println("[*] Detect overrideRunner: '${overrideRunner}', use it as dockerImage or agentLabel!")
    dockerImage = overrideRunner
    agentLabel = overrideRunner
  }

  return {
    stage("${stageName}") {
      if (useDocker == true) {
        node("docker") {
          docker.image(dockerImage).inside("-u jenkins:root -v /home/jenkins:/home/jenkins") {
            doJob(executeCommand, extraScript, cleanCheckout)
          }
        }
      } else {
        node(agentLabel) {
          doJob(executeCommand, extraScript, cleanCheckout)
        }
      }
    }
  }
}

def doJob(String executeCommand, Closure extraScript=null, Boolean cleanCheckout=false) {
  if (cleanCheckout) { cleanWs() }

  // If you need to do some git operation (e.g. git pull, git push) in your script,
  // you should set the Jenkins credential ID as environment variable "GIT_CREDENTIAL_ID"
  if (env.GIT_CREDENTIAL_ID) {
    withCredentials([sshUserPrivateKey(credentialsId: env.GIT_CREDENTIAL_ID, keyFileVariable: 'SSH_KEY')]) {
      def sshKey = env.SSH_KEY
      if (!isUnix()) {
        // The credential stored in Jenkins are unix-style and
        // need to be escaped before being passed to Windows Batch
        sshKey = env.SSH_KEY.replaceAll("\\\\","/")
      }
      withEnv(["GIT_SSH_COMMAND=ssh -i $sshKey -o StrictHostKeyChecking=no"]) {
        doJobInner(executeCommand, extraScript)
      }
    }
  } else {
    doJobInner(executeCommand, extraScript)
  }
}

def doJobInner(String executeCommand, Closure extraScript=null) {

  def gitEnv = checkout(scm)
  withEnv(["GIT_COMMIT=${gitEnv.GIT_COMMIT}", "GIT_BRANCH=${gitEnv.GIT_BRANCH}"]) {
    setup_pyscripts()
    if (isUnix()) {
      sh(script: executeCommand)
    } else {
      bat(script: executeCommand)
    }
    if (extraScript) {
      extraScript()
    }
  }
}
