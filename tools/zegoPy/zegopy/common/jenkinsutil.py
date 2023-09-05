#!/usr/bin/env python3
#coding: utf-8


'''
统一处理 Jenkins 环境变量获取及参数传递问题
'''

import os
import json


def get_bool(key):
  return key in os.environ and os.environ[key] == 'true'


def get_string(key, default_value=''):
  return os.environ[key] if key in os.environ else default_value


def get_multi(key, delimiter=','):
  return os.environ[key].split(delimiter) if key in os.environ else []


class Params:
    def __init__(self, *values):
        self._params = []
        self.append(*values)

    def __str__(self):
        _s = ""
        for v in self._params:
            _v = ""
            if isinstance(v, dict):
                _v = json.dumps(v)
            else:
                _v = str(v)

            if "\"" in _v:
                _v = '"' + _v.replace("\"", "\\\"") + '"'
        
            if len(_v) == 0:
                continue

            _s += _v + " "

        return _s

    def append(self, *values):
        for value in values:
            self._params.append(value)
        return self

    def extend(self, values):
        self._params.extend(values)
        return self

    def get(self):
        return self._params

    def to_string(self):
        return self.__str__()


if __name__ == "__main__":
    p = Params("--config", "Release")
    p.append("--ve_package")

    s = '''{"test": "test_value"}'''
    p.append(s)

    print(str(p))
