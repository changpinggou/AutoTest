// Jenkins build entry

@Library("pyscripts") _

pipeline {

    agent { label "${env.LABEL_PIPELINE}" }

    options {
        timeout(time: 30, unit: 'MINUTES') // 设置 30 分钟超时
    }

    parameters {

        string(
            name: "JENKINS_CONTEXT",
            defaultValue: "",
            description: "填写 SDK 名称，作为上下文，例如 ZegoExpressEngine / ZegoLiveRoom / ZegoEffects / ZIM / ZegoConnection"
        )

        string(
            name: "GRADLE_LIBRARY_NAME",
            defaultValue: "",
            description: "选择 Jitpack 的 gradle 仓库"
        )

        string(
            name: "SDK_DOWNLOAD_URL",
            defaultValue: "",
            description: "SDK 压缩包的路径，填写 https 开头的完整路径，仅支持 oss 上已发布 SDK 的地址"
        )

        string(
            name: "SDK_ZIP_ROOT_FOLDER",
            defaultValue: "",
            description: "SDK 解压后相对于 jar 存放位置的根目录"
        )

        string(
            name: "RELEASE_TAG",
            defaultValue: "",
            description: "待发布的版本号"
        )

        booleanParam(
            name: "SEND_WECOM_NOTIFICATION",
            defaultValue: true,
            description: "是否发送企业微信通知\n\n"
        )
    }

    stages {

        stage("Upload") {

            agent {
                docker {
                    image 'ci_docker_images/android/android_ndk_r21d_sdk_30:1.1.13'
                    args '-u jenkins:root'
                    label 'docker'
                }
            }

            steps {
                // 安装 pyscripts 仓库
                setup_pyscripts()

                // 获取 Github 账号 zegolibrary 的 token
                withCredentials([sshUserPrivateKey(credentialsId: '2b454be1-7cc5-45fe-87fd-ff972da44564', keyFileVariable: 'SSH_KEY', usernameVariable: 'username')]) {
                    withEnv(["GIT_SSH_COMMAND=ssh -i $SSH_KEY -o StrictHostKeyChecking=no"]) {

                        script {
                            currentBuild.description = "${params.JENKINS_CONTEXT} - \"${params.GRADLE_LIBRARY_NAME}\""

                            // 获取发起构建任务的用户 ID
                            build_user = get_build_user()

                            github_username = "${username}"
                            args = "--uploader_username $username --gradle_library_name ${params.GRADLE_LIBRARY_NAME} --sdk_download_url ${params.SDK_DOWNLOAD_URL} --release_tag ${params.RELEASE_TAG} "
                            if(params.SDK_ZIP_ROOT_FOLDER != "") {
                                args += "--sdk_zip_root_folder ${params.SDK_ZIP_ROOT_FOLDER} "
                            }
                            cmd = "python3 -u zegopy/utils/jitpack_uploader/jitpack_uploader.py ${args}"
                            sh(script: cmd, label: STAGE_NAME)
                        }
                    }
                }
                cleanWs()
            }
        }
    }

    post {
        success {
            script {
                // 发送成功通知
                if (params.SEND_WECOM_NOTIFICATION) {
                    def mdBody = "\n- 上下文: ${env.JENKINS_CONTEXT}"
                    mdBody += "\n- **<font color=\"info\">构建产物</font>**\n"
                    mdBody += "\n- SDK 已上传到 Github 仓库，请点击以下链接发布到 Jitpack：[https://jitpack.io/#${github_username}/${params.GRADLE_LIBRARY_NAME}](https://jitpack.io/#${github_username}/${params.GRADLE_LIBRARY_NAME}) \n"
                    // 企业微信群机器人 WebHook 使用环境变量
                    report_wecom("${env.WECOM_WEBHOOK}", true, "JitpackUploader", build_user, mdBody)
                }
            }
        }

        unsuccessful {
            script {
                // 发送失败通知
                if (params.SEND_WECOM_NOTIFICATION) {
                    def mdBody = "\n- 上下文: ${env.JENKINS_CONTEXT}"
                    mdBody += "\n- **<font color=\"warning\">构建失败</font>**"
                    // 企业微信群机器人 WebHook 使用环境变量
                    report_wecom("${env.WECOM_WEBHOOK}", false, "JitpackUploader", build_user, mdBody)
                }
            }
        }

        always {
            // 完成后清理 WorkSpace
            cleanWs()
        }
    }
}
