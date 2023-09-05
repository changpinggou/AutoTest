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
            defaultValue: "【填写客户名称】填写 TAPD 工单链接（或问题描述）",
            description: "上下文，建议填写 TAPD 工单链接，或描述一下情况，客户名称等，将出现在历史构建信息中，以及输出结果 TXT 文件中，方便未来查找。"
        )

        string(
            name: "PRODUCT_NAME",
            defaultValue: "ZegoExpressEngine",
            description: "填写 SDK 包名，必填！必须与动态库名称一致。 例如: ZegoExpressEngine / ZegoLiveRoom / ZegoAudioRoom / ZIM / ZegoEffects"
        )

        choice(
            name: "PLATFORM",
            choices: "Android\niOS\nmacOS\nWindows\nLinux",
            description: "选择 SDK 的平台类型"
        )

        choice(
            name: "IOS_ARCH",
            choices: "arm64\narmv7\narm64-simulator\nx86_64-simulator\narm64-catalyst\nx86_64-catalyst\n",
            description: "如果要还原 iOS，请选择要还原的 iOS SDK 的架构"
        )

        choice(
            name: "ANDROID_ARCH",
            choices: "arm64-v8a\narmeabi-v7a\nx86\nx86_64",
            description: "如果要还原 Android，选择要还原的 Android SDK 的架构"
        )

        choice(
            name: "MAC_ARCH",
            choices: "arm64\nx86_64",
            description: "如果要还原 macOS，选择要还原的 macOS SDK 的架构"
        )

        booleanParam(
            name: "IS_APPLE_FRAMEWORK",
            defaultValue: true,
            description: "如果要还原 iOS 或 macOS，要还原的 SDK 封装类型是 framework 还是 dylib？ true: framework, false: dylib，一般来说，Objective-C SDK 是 framework，C++ SDK 是 dylib。"
        )

        string(
            name: "UUID",
            defaultValue: "",
            description: "Apple SDK 的 UUID。仅 iOS 和 macOS 平台可选填"
        )

        string(
            name: "SYMBOL_DOWNLOAD_URL",
            defaultValue: "",
            description: "SDK 符号表的下载路径，仅支持制品库完整路径（若 URL 带有版本信息，则需包含），必填"
        )

        string(
            name: "SYMBOL_BINARY_FILE_PATH",
            defaultValue: "",
            description: "SDK 符号表 zip 文件里面的二进制文件相对于解压后的根目录位置。如果是使用 GN Build 构建的 SDK 例如 RTC / ZIM / Effects 等产品则不用填。"
        )

        string(
            name: "BASE_ADDRESS",
            defaultValue: "",
            description: "崩溃基址。iOS / macOS 必填，Android 可选填"
        )

        text(
            name: "CRASH_ADDRESSES",
            defaultValue: "",
            description: "崩溃地址。必填，可填多行"
        )

    }

    stages {

        stage("Apple") {

            agent { label "${env.LABEL_APPLE}" }

            when {
                beforeAgent true
                expression { return (params.PLATFORM == "iOS" || params.PLATFORM == "macOS") }
            }

            steps {
                // 安装 pyscripts 仓库
                setup_pyscripts()

                script {
                    if (params.JENKINS_CONTEXT.length() < 3 || params.JENKINS_CONTEXT.contains("【填写客户名称】")) {
                        throw new Exception("请按照说明认真填写上下文字段 [JENKINS_CONTEXT]")
                    }
                    currentBuild.description = "${params.PRODUCT_NAME} - ${params.JENKINS_CONTEXT} - ${params.PLATFORM}"
                    env.JENKINS_CONTEXT = params.JENKINS_CONTEXT
                    // TODO: 处理多行文本
                    def formatedCrashAddresses = "${params.CRASH_ADDRESSES}".replace('\n', ' ')

                    args = "--product-name ${params.PRODUCT_NAME} "
                    args += "--base-address ${params.BASE_ADDRESS} "
                    args += "--crash-addresses ${formatedCrashAddresses} "
                    if (params.PLATFORM == "iOS") { args += "--ios --ios-arch ${params.IOS_ARCH} " }
                    if (params.PLATFORM == "macOS") { args += "--mac --mac-arch ${params.MAC_ARCH} " }
                    if (params.IS_APPLE_FRAMEWORK) { args += "--is-apple-framework "}
                    if (params.UUID) { args += "--uuid ${params.UUID} " }
                    if (params.SYMBOL_DOWNLOAD_URL) { args += "--symbol-download-url ${params.SYMBOL_DOWNLOAD_URL} " }
                    if (params.SYMBOL_BINARY_FILE_PATH) { args += "--symbol-binary-path ${params.SYMBOL_BINARY_FILE_PATH} " }

                    cmd = "python3 -u zegopy/utils/crash_analysis/crash_analysis.py ${args}"
                    sh(script: cmd, label: STAGE_NAME)

                    if (fileExists("${WORKSPACE}/zegopy/utils/crash_analysis/crash_stack.txt")) {
                        archiveArtifacts(artifacts: "zegopy/utils/crash_analysis/crash_stack.txt")
                    }
                }
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
                expression { return (params.PLATFORM == "Android" || params.PLATFORM == "Windows" || params.PLATFORM == "Linux") }
            }

            steps {
                // 安装 pyscripts 仓库
                setup_pyscripts()

                script {
                    if (params.JENKINS_CONTEXT.length() < 3 || params.JENKINS_CONTEXT.contains("【填写客户名称】")) {
                        throw new Exception("请按照说明认真填写上下文字段 [JENKINS_CONTEXT]")
                    }
                    currentBuild.description = "${params.PRODUCT_NAME} - ${params.JENKINS_CONTEXT} - ${params.PLATFORM}"
                    env.JENKINS_CONTEXT = params.JENKINS_CONTEXT
                    // TODO: 处理多行文本
                    def formatedCrashAddresses = "${params.CRASH_ADDRESSES}".replace('\n', ' ')

                    args = "--product-name ${params.PRODUCT_NAME} "
                    args += "--crash-addresses ${formatedCrashAddresses} "
                    if (params.PLATFORM == "Android") { args += "--android --android-arch ${params.ANDROID_ARCH} " }
                    if (params.SYMBOL_DOWNLOAD_URL) { args += "--symbol-download-url ${params.SYMBOL_DOWNLOAD_URL} " }
                    if (params.SYMBOL_BINARY_FILE_PATH) { args += "--symbol-binary-path ${params.SYMBOL_BINARY_FILE_PATH} " }

                    cmd = "python3 -u zegopy/utils/crash_analysis/crash_analysis.py ${args}"
                    sh(script: cmd, label: STAGE_NAME)

                    if (fileExists("${WORKSPACE}/zegopy/utils/crash_analysis/crash_stack.txt")) {
                        archiveArtifacts(artifacts: "zegopy/utils/crash_analysis/crash_stack.txt")
                    }
                }
            }
        }
    }
}
