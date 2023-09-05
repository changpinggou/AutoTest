#!/usr/bin/env python -u
# encoding: utf-8

def d(debug):
    try:
        print('[-] %s' % debug)     # str.format() may cause non-asiic encoding error!
    except:
        pass

def i(info):
    try:
        print('[*] %s' % info)
    except:
        pass

def e(error, abort=True):
    try:
        print('[+] %s' % error)
    except:
        pass
    if abort:
        raise Exception(error)
