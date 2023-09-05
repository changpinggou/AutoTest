#!/usr/bin/env python
# coding: utf-8

"""
Judge current operation system type
"""

import os
import sys
import platform

OS_OTHER = 0
OS_WINDOWS = 1  # WINDOWS OS
OS_DARWIN = 2   # Apple OS
OS_LINUX = 3    # LINUX OS


def get_current_os_name():
    return platform.system()


def get_linux_name():
    """
    返回 Linux 操作系統的名稱，目前僅支持 Ubuntu & CentOS
    :return: centos / ubuntu / unknown
    """
    if os.path.exists("/etc/lsb-release"):
        return "ubuntu"
    elif os.path.exists("/etc/redhat-release"):
        return "centos"
    else:
        return "unknown"


def get_current_os_type():
    sys_name = sys.platform
    if sys_name.startswith("win32"):
        return OS_WINDOWS
    elif sys_name.startswith("darwin"):
        return OS_DARWIN
    elif sys_name.startswith("linux"):
        return OS_LINUX
    else:
        return OS_OTHER


def is_windows_os():
    return OS_WINDOWS == get_current_os_type()


def is_darwin_os():
    return OS_DARWIN == get_current_os_type()


def is_linux_os():
    return OS_LINUX == get_current_os_type()


def is_64bit_system():
    m = platform.machine()
    return (m == "x86_64") or (m.lower() == "amd64")

def is_arm64_arch():
    return "ARM64" in version()

def is_arm64_mac():
    return ('arm64' in platform.machine()) and \
        ('darwin' in sys.platform)

def version():
    return platform.version()


if __name__ == "__main__":
    print ("Current Operation System Type: ", get_current_os_type())
    print ("Current Operation System Name: ", get_current_os_name())
    print ("Is 64bit system: ", is_64bit_system())
    print ("Is arm64 arch: ", is_arm64_arch())
    print ("Is arm64 Mac: ", is_arm64_mac())
    print ("Version: ", version())
