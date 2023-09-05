#!/usr/bin/env python3

import os
import requests

"""
Script for store you config in remote server.
"""


class DevOpsRemoteConfig:
    def __init__(self) -> None:
        # Whether to throw the exception to outside when
        self.is_raise_exception = False

    def set_raise_exception(self, is_raise: bool):
        self.is_raise_exception = is_raise

    def get_project_list(self) -> list:
        """Get all project list in remote config server.
        Returns:
            list: List of project name
        """
        try:
            r = requests.get("http://api-mgr.zego.cloud/api/remoteconfig/projects")
            return r.json()['data']['list']
        except Exception as e:
            print(e)
            if self.is_raise_exception:
                raise Exception("Get project list failed")
            return []

    def get_random_key(self, expire_time: int = 3600):
        try:
            r = requests.get("http://api-mgr.zego.cloud/api/remoteconfig/generate_token", params={'expire_time': expire_time})
            return r.json()['data']['token']
        except Exception as e:
            print(e)
            if self.is_raise_exception:
                raise Exception("Get random key failed")
            return ""

    def get_value(self, project_name: str, key: str) -> str:
        """Get value with key 'key' in project with name 'project_name'
        Args:
            project_name(str): Name of the project
            key(str): Key of the value
        Returns:
            str: Value with key, return empty string if not exist.
        """
        try:
            r = requests.get("http://api-mgr.zego.cloud/api/remoteconfig/get",
                             params={'project_name': project_name, 'key': key})
            return r.json()['data']['value']
        except Exception as e:
            print(e)
            if self.is_raise_exception:
                raise Exception("Get value failed")
            return ""

    def set_value(self, project_name: str, key: str, value: str):
        """Set value with key 'key' in project with name 'project_name'
        Args:
            project_name(str): Name of the project, new one will be create if project not exist
            key(str): Key of the value
            value(str): Value that you want to set
        """
        try:
            requests.post("http://api-mgr.zego.cloud/api/remoteconfig/set",
                          data={'project_name': project_name, 'key': key, 'value': value})
        except Exception as e:
            print(e)
            if self.is_raise_exception:
                raise Exception("Set value failed")


if __name__ == '__main__':
    # example

    # New an instance
    config = DevOpsRemoteConfig()

    print(config.get_random_key(), "<<<<<<<<<")
    config.set_raise_exception(True)
    config.set_value('test_project', 'test', 'hello, remote config!')
    print('Value of test: ', config.get_value('test_project', 'test'))
    print('Project list: ', config.get_project_list())
