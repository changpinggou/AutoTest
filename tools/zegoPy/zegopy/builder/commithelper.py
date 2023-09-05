# This Python file uses the following encoding: utf-8
import os
import subprocess
import shutil


class CommitHelper:
    def __init__(self):
        self._commit_message = ""

    def set_commit_message(self, message: str):
        self._commit_message = message

    def get_tapd_url(self) -> str:
        """
        从Commit信息中获取 Tapd 的链接，注意，每个 Commit 中查找到第一个链接立即返回
        :return:
        """
        if self._commit_message is None:
            return ""
        lines = self._commit_message.split('\n')
        for line in lines:
            if line.startswith('tapd:'):
                return line.replace('tapd:', '').strip()
            elif line.startswith('tapd：'):
                return line.replace('tapd：', '').strip()
        return ''
