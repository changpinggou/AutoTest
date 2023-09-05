# This Python file uses the following encoding: utf-8
import os
import subprocess
import shutil
import json
import requests
from dataclasses import dataclass
from enum import Enum


@dataclass
class TapdComments:
    """
    数据参见 https://www.tapd.cn/help/show#1120003271001000339
    """
    workspace_id: int = 0  # 自动从URL解析，用户不用填写
    entry_id: int = 0  # 自动从URL解析，用户不用填写
    description: str = ""
    author: str = ""
    entry_type: str = ""
    fields: str = ""


class TapdBugStatus(Enum):
    resolved = 0


class Tapd:
    def __init__(self):
        self._user_name = ""
        self._password = ""
        self._api_comments_url = "https://api.tapd.cn/comments"
        self._api_bug_url = 'https://api.tapd.cn/bugs'

    @staticmethod
    def _extra_bug_entry_id_from_url(url: str):
        # https://www.tapd.cn/33116467/bugtrace/bugs/view/1133116467001070722
        # https://www.tapd.cn/33116467/bugtrace/bugs/view/1133116467001070671?corpid=ww9450793b98306b4c&agentid=1000003&jump_count=2
        if 'bugtrace/bugs/view/' in url:
            return url.split('bugtrace/bugs/view/')[1].split('?')[0]
        # https://www.tapd.cn/33116467/bugtrace/bugs/view?bug_id=1133116467001071410
        elif 'bugtrace/bugs/view?' in url:
            bug_id = url.split('bug_id=')[1]
            # https://www.tapd.cn/46956246/bugtrace/bugs/view?bug_id=1146956246001074296&url_cache_key=43acdaa9ec6660d089b948cff4015cee
            if '&url_cache_key' in url:
                return bug_id.split('&url_cache_key=')[0]
            return bug_id
        else:
            return 0

    def _extra_url(self, url: str):
        if not url:
            return 0, 0
        print("Extra URL: ", url)
        workspace_id = url.split('https://www.tapd.cn/')[1].split('/')[0]
        entry_id = 0
        if 'bugtrace/bugs/view' in url:
            entry_id = self._extra_bug_entry_id_from_url(url)
        return workspace_id, entry_id

    def set_auth(self, user_name: str, password: str):
        self._user_name = user_name
        self._password = password

    def add_comments(self, bug_url: str, comments_obj: TapdComments):
        workspace_id, entry_id = self._extra_url(bug_url)
        comments_obj.workspace_id = workspace_id
        comments_obj.entry_id = entry_id
        comments = json.dumps(comments_obj.__dict__)
        try:
            r = requests.post(self._api_comments_url, comments, auth=(self._user_name, self._password))
            print(r)
        except requests.exceptions.HTTPError as e:
            print(e)
        print("Add comments: ", comments)

    def update_bug_status(self, bug_url: str, status: TapdBugStatus):
        workspace_id, entry_id = self._extra_url(bug_url)
        data = json.dumps({"workspace_id": workspace_id, "id": entry_id, "status": status.name})
        try:
            r = requests.post(self._api_bug_url, data, auth=(self._user_name, self._password))
            print(r)
        except requests.exceptions.HTTPError as e:
            print(e)
        print("Update bug status: ", data)
