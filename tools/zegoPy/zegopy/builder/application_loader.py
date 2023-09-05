#!/usr/bin/env python3

import os

class ApplicationLoader:
    def __init__(self) -> None:
        self.apiKey: str = ""
        self.apiIssuer: str = ""
        # 失败重试次数 默认为3次
        self.retry_times = 3

    def set_auth(self, apiKey, apiIssuer):
        self.apiKey = apiKey
        self.apiIssuer = apiIssuer

    def set_auth_for_zego(self):
        # 设置为 ZEGO 账号的授权
        self.apiKey = 'H959S8PX4L'
        self.apiIssuer = '69a6de92-2395-47e3-e053-5b8c7c11a4d1'

    def set_retry_times(self, times):
        if times < 1: return
        self.retry_times = times

    # validate app
    # file_path: the ipa path
    # type: ios | osx | appletvos
    def validate_app(self, file_path, type):
        if len(self.apiKey) == 0 or len(self.apiIssuer) == 0:
            msg = "Please call `set_auth` to set apiKey and apiIssuer."
            raise Exception(msg)
        cmd = "xcrun altool --validate-app -f {} -t {} --apiKey {} --apiIssuer {} --verbose".format(file_path, type, self.apiKey, self.apiIssuer)

        state = 0
        for i in range(0, self.retry_times):
            print("start to validate app: ", i+1)
            state = os.system(cmd)
            print("state: ", state)
            if state == 0:
                break

        if state != 0:
            raise Exception('validate app failed')

    # upload app to appstore
    # file_path: the ipa path
    # type: ios | osx | appletvos
    def upload_app(self, file_path, type):
        if len(self.apiKey) == 0 or len(self.apiIssuer) == 0:
            msg = "Please call `set_auth` to set apiKey and apiIssuer."
            raise Exception(msg)
        cmd = "xcrun altool --upload-app -f {} -t {} --apiKey {} --apiIssuer {} --verbose".format(
            file_path, type, self.apiKey, self.apiIssuer)

        state = 0
        for i in range(0, self.retry_times):
            print("start to upload app: ", i+1)
            state = os.system(cmd)
            print("state: ", state)
            if state == 0: break

        if state != 0:
            raise Exception('upload app failed')

    # notarize macos app
    # file_path: should be 'zip, pkg, dmg' file
    def notarize_app(self, file_path, bundle_id):
        if len(self.apiKey) == 0 or len(self.apiIssuer) == 0:
            msg = "Please call `set_auth` to set apiKey and apiIssuer."
            raise Exception(msg)
        cmd = "xcrun altool --notarize-app -f {} --primary-bundle-id {} --apiKey {} --apiIssuer {} --verbose".format(
            file_path, bundle_id, self.apiKey, self.apiIssuer)

        state = 0
        for i in range(0, self.retry_times):
            print("start to notarize app: ", i+1)
            state = os.system(cmd)
            print("state: ", state)
            if state == 0:
                break

        if state != 0:
            raise Exception('notarize app failed')

if __name__ == '__main__':

    #example

    loader = ApplicationLoader()

    # set the apiKey and apiIssuer
    # For the ZEGO use: `6357Z2K9GU`, `69a6de92-2395-47e3-e053-5b8c7c11a4d1`
    # For the DOUDONG use: `4GN6WAY4P5`, `962ccd9a-a5bc-42e5-8bb0-105841ebfc8c`
    # Also you can add a new api key on AppStore Connect
    loader.set_auth('6357Z2K9GU', '69a6de92-2395-47e3-e053-5b8c7c11a4d1')

    ipa_path = "/Users/xxx/Desktop/Roomkit/roomkit-edu-demo.ipa"
    dmg_file = "/Users/xxx/Desktop/Roomkit/roomkit-edu-demo.dmg"

    # validate app
    loader.validate_app(ipa_path, 'ios')

    # upload app to appstore
    loader.upload_app(ipa_path, 'ios')

    # notarize macos app
    loader.notarize_app(dmg_file, 'im.zego.ZegoRoomKitDemo')
