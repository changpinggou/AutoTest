#!/usr/bin/env python -u
# coding:utf-8

import sys
import json


class CmdParam(object):
    """
    commandline params util
    """
    def __init__(self, args=sys.argv[1:]):
        self._args = args

    def __str__(self):
        _s = ""
        for v in self._args:
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

    def __index(self, key):
        if sys.version_info.major == 3:
            _xrange = range
        else:
            _xrange = xrange

        for idx in _xrange(len(self._args)):
            if self._args[idx] == key:
                return idx
        return -1

    def check_argument(self, key, **kwargs):
        """
        Describe an argument's information
        :param key: argument alias
        :param kwargs: argument restrain
        :return:
        :exception:
        """
        idx = self.__index(key)
        if ('optional' not in kwargs or ('optional' in kwargs and kwargs['optional'] is False)) and idx < 0:
            raise Exception("Argument '{}' must be exists".format(key))

    def get(self, key):
        idx = self.__index(key)
        if idx < 0:
            raise Exception("No argument '{}' be found in {}".format(key, self._args))

        idx += 1

        values = []
        while idx < len(self._args):
            item = self._args[idx]
            if item.startswith('-'):
                break

            values.append(item)

            idx += 1

        return values

    def get_all(self):
        return self._args

    def has(self, key):
        return self.__index(key) >= 0

    def append(self, key, *values):
        self._args.append(key)
        for value in values:
            self._args.append(value)
        return self

    def insert(self, index, key, *values):
        self._args.insert(index, key)
        for value in values:
            index += 1
            self._args.insert(index, value)
        return self

    def update(self, key, *values):
        idx = self.__index(key)
        if idx < 0:
            print ("[*] Warning, the key: {} not exists, will append to the end of param list".format(key))
            self.append(key, *values)
        else:
            self.remove(key)
            self.insert(idx, key, *values)
        return self

    def remove(self, key):
        idx = self.__index(key)
        if idx < 0:
            return []

        self._args.pop(idx)

        _will_removed = []
        while idx < len(self._args) and not self._args[idx].startswith('-'):
            item = self._args.pop(idx)
            _will_removed.append(item)

        return _will_removed

    def clone(self):
        _copy_args = [arg for arg in self._args]
        return CmdParam(_copy_args)


if __name__ == "__main__":
    _args = ['--key1', 'value1', '--key2', 'value21', 'value22', '--bkey']
    au = CmdParam(_args)
    print ("all arguments: {}, must {}".format(au.get_all(), _args))
    print ("has key: --bkey ? {}, must True".format(au.has('--bkey')))
    print ("--key1's value: {}, must 'value1'".format(au.get('--key1')))
    print ("--key2's value: {}, must ['value21', 'value22]".format(au.remove('--key2')))
    print ("all arguments: {}, must ['--key1', 'value1', '--bkey']".format(au.get_all()))
    print ("check_argument bkey ok".format(au.check_argument('--bkey')))
    au.append('--ckey', 'cvalue1', 'cvalue2').insert(0, 'xx.py', 'test')
    print ("after append argument: ckey, {}".format(au.get_all()))

    new_au = au.clone()
    print ("all arguments: {}, must ['--key1', 'value1', '--bkey']".format(new_au.get_all()))

    print ("all arguments before update: {}".format(au.get_all()))
    au.update('--dkey', 'dvalue1', 'dvalue2')

    print ("all arguments: {}".format(au.get_all()))
    au.update('--dkey', 'dvalue1')
    print ("all arguments: {}".format(au.get_all()))

    print ("check_argument ekey exception".format(au.check_argument('--ekey', optional=False)))

