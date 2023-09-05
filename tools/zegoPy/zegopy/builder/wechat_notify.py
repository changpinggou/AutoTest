# coding=UTF-8
import os
import sys
import json
import argparse
import requests


# 定义一个数组，如果传递的key与其中某项的key匹配，那么就发到对应的微信群里
# [
#     {
#         "key": "Succeed",
#         "content_type": "内容类型，详情参考： https://work.weixin.qq.com/help?doc_id=13376",
#         "content": "要发送的内容",
#         "url": "机器人URL",
#         "members": ["oliveryang", "adam", "..."]
#     },
#     {
#         "key": "Failed",
#         "content_type": "内容类型，详情参考： https://work.weixin.qq.com/help?doc_id=13376",
#         "content": "要发送的内容",
#         "url": "机器人URL",
#         "members": ["oliveryang", "adam", "..."]
#     }
# ]
class WechatNotify:
    def __init__(self):
        self._config_list = []  # 配置信息列表

    def load_config_list(self, config_list: list):
        """
        加载微信通知配置项列表，如果不想从文件加载，可以使用该方法
        :param config_list: 配置项列表
        :return:
        """
        self._config_list = config_list

    def load_config_file(self, file_path):
        """
        加载微信通知的配置文件
        :param file_path: 配置文件路径
        :return:
        """
        try:
            with open(file_path, encoding='utf-8') as json_file:
                self._config_list = json.load(json_file)
        except Exception as e:
            print(e)

    def notify(self, key: str):
        """
        在加载的配置列表中，触发 key 对应配置项的通知
        :param key: 配置项中的 key 值
        :return:
        """
        for config in self._config_list:
            if config["key"] == key:
                self._notify_with_obj(config)
                return

    def notify_and_replace_content(self, key: str, replace_str_list: list):
        """
        在加载的配置列表中，触发 key 对应的配置项的通知，并且对内容调用字符串 format 方法，按顺序替换内容
        :param key: 配置项中的 key 值
        :param replace_str_list: 用于替换内容文本的字符串列表
        :return:
        """
        for config in self._config_list:
            if config["key"] == key:
                config["content"] = config["content"].format(*replace_str_list)
                self._notify_with_obj(config)
                return

    @staticmethod
    def _robot(url, json_data):
        headers = {'content-type': 'application/json'}  # 请求头
        r = requests.post(url, headers=headers, data=json.dumps(json_data))
        r.encoding = 'utf-8'
        return r.text

    def _notify_with_obj(self, config):
        json_data = {
            "msgtype": config["content_type"]
        }
        if config["content_type"] == "text":
            text_obj = {
                "content": config["content"],
                "mentioned_list": config["members"]
            }
            json_data["text"] = text_obj
        else:
            # @人字符串
            at_users_str = ""
            for user in config["members"]:
                if user == "":
                    continue
                at_users_str += "<@{}>".format(user)
            if at_users_str:
                config["content"] = config["content"] + "\n\n{}".format(at_users_str)
            markdown_obj = {
                "content": config["content"]
            }
            json_data["markdown"] = markdown_obj
        self._robot(config["url"], json_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='根据指定的配置文件发送企业微信通知')
    parser.add_argument('-f', '--file', dest='file', help='配置文件路径')
    parser.add_argument('-k', '--key', dest='key', help='配置文件中对应 key 的节点会被使用。')
    parser.add_argument('-r', '--replace', dest='replace', nargs='+', help='要替换的字符内容，可以多个值，会按顺序进行替换。')
    args = parser.parse_args()

    hook = WechatNotify()
    hook.load_config_file(args.file)
    if args.replace:
        hook.notify_and_replace_content(args.key, args.replace)
    else:
        hook.notify(args.key)
