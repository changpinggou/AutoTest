// Jenkins build entry

@Library("pyscripts") _

// 每个 Stage 构建成功后，更新 Pipeline 全局信息: 向产物信息列表添加结果
def update_global_result() {
    // 获取产物信息
    def output_json_name = "zegopy/utils/count_package_size/_output.json"
    if (fileExists("${WORKSPACE}/${output_json_name}")) {
        def output_json = readJSON(file: "${WORKSPACE}/${output_json_name}")
        // 向全局产物 Map 添加此 stage 的产物
        products_map[output_json['key']] = output_json['value']
        println("\n*** Get output json: ***\n*****\n${output_json}\n*****\n")
    } else {
      println("\n[ERROR] Can not find output json file '${WORKSPACE}/${output_json_name}', skip.\n")
    }
}

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

        choice(
            name: "PLATFORM",
            choices: "android\nios\nmac\nwin\nlinux",
            description: "选择 SDK 的平台类型"
        )

        choice(
            name: "ARCH",
            choices: "armv7\narm64\nx86\nx64",
            description: "选择要计算的 SDK 的架构"
        )

        string(
            name: "SDK_PATH",
            defaultValue: "",
            description: "SDK 压缩包的路径，填写 smb 或 http 开头的完整路径"
        )

        string(
            name: "LIB_PATH",
            defaultValue: "",
            description: "待统计的实际动态库 (framework/dylib/dll/so/jar) 在 zip 包中的相对路径\n例:\n1. iOS: \"SDK/ZegoEffects.xcframework/ios-arm64_armv7/ZegoEffects.framework\" (具体的 .framework 路径)\n2. Android: \"ZegoExpressEngine-video-android-java\" (包含 jar + 各个 so 目录 的那个目录)\n3. macOS: \"product/ZegoLiveRoom/Release/ZegoLiveRoomOSX.framework\" (具体的 .framework 路径)\n4. Win: \"libs/x64\" (包含 dll + lib 的那个目录)\n5. Linux: \"libs/x86/libzegoconnection.so\" (具体的 .so 路径)\n"
        )

    }

    stages {

        stage("Prepare") {

            options { skipDefaultCheckout() }

            steps {
                script {
                    currentBuild.description = "${params.JENKINS_CONTEXT} - ${params.PLATFORM} - ${params.ARCH}"

                    // 获取发起构建任务的用户 ID
                    build_user = get_build_user()

                    // 用于保存多个 stage 产物的全局 Map
                    products_map = [:]
                }
            }
        }

        stage("Apple") {

            agent { label "${env.LABEL_APPLE}" }

            when {
                beforeAgent true
                expression { return (params.PLATFORM == "ios" || params.PLATFORM == "mac") }
            }

            steps {
                // 安装 pyscripts 仓库
                setup_pyscripts()

                script {
                    args = "${params.PLATFORM} ${params.SDK_PATH} ${params.LIB_PATH} ${params.ARCH}"
                    cmd = "python3 -u zegopy/utils/count_package_size/count_package_size.py ${args}"
                    sh(script: cmd, label: STAGE_NAME)

                    // 向全局结果更新 stage 的结果
                    update_global_result()
                }
                cleanWs()
            }
        }

        stage("Docker") {

            agent {
                docker {
                    image 'ci_docker_images/android/android_ndk_r21d_sdk_30:1.1.13'
                    args '-u jenkins:root'
                    label 'docker'
                }
            }

            when {
                beforeAgent true
                expression { return (params.PLATFORM == "android" || params.PLATFORM == "win" || params.PLATFORM == "linux") }
            }

            steps {
                // 安装 pyscripts 仓库
                setup_pyscripts()

                script {
                    args = "${params.PLATFORM} ${params.SDK_PATH} ${params.LIB_PATH} ${params.ARCH}"
                    cmd = "python3 -u zegopy/utils/count_package_size/count_package_size.py ${args}"
                    sh(script: cmd, label: STAGE_NAME)

                    // 向全局结果更新 stage 的结果
                    update_global_result()
                }
                cleanWs()
            }
        }
    }

    post {
        success {
            script {
                println("\n\n***PRODUCTS***\n\n${products_map}\n\n")

                // 写入环境变量中，给下游任务使用
                env.PRODUCTS_JSON = writeJSON(json: products_map, returnText: true)

                // 写入产物信息到文件并归档到 Jenkins 制品库
                writeJSON(json: products_map, file: "${WORKSPACE}/products.json", pretty: 4)
                archiveArtifacts "products.json"
            }
        }

        always {
            // 完成后清理 WorkSpace
            cleanWs()
        }
    }
}
