#!/usr/bin/env python3
# coding:utf-8

"""
解析 XCode 编译时产生的 LinkMap.txt 文件, 用于分析 iOS 库各静态库、模块所占空间大小
"""

import os
import re
from zegopy.common import io as zegoio

_SDK_TOTAL_KEY = "_sdk_total"
_SDK_CODE_KEY = "_sdk_code"
_VE_TOTAL_KEY = "_ve_total"

_SDK_DEPENDS_LIBRARIES = (
    "libprotobuf.a",
    "libprotobuf-lite.a",
    "libleveldb.a",
    "libcurl.a",
    "libzegonetwork.a",
    "libquic.a",
    "libssl.a",
    "libevent.a",
    "libcrypto.a",
    "libzegoconnection.a"
    )

_PLATFORM_Unknown = None
_PLATFORM_iOS = "iOS"
_PLATFORM_Android_ARMv7a = "Android-v7a"
_PLATFORM_Android_ARMv8a = "Android-v8a"
_PLATFORM_Linux = "Linux"


def _byte2humanSize(bytesize):
    unit = 'K'
    if bytesize <= 1024:
        bytesize /= 1024
    else:
        if bytesize >= 1024:
            bytesize /= 1024

        if bytesize > 1024:
            bytesize /= 1024
            unit = 'M'

    return "%.2f%s" % (bytesize, unit)


def _detect_keys(link_map_file):
    _skip_detect = False
    keys = []
    fr = open(link_map_file, 'rb')
    try:
        cur_line_number = 0
        while True:
            text = bytes.decode(fr.readline(), 'utf-8', 'ignore')
            if len(text) == 0:  # EOF
                break

            cur_line_number += 1
            text = text.rstrip()

            if text == '': # empty line
                continue

            if text[0] == ' ':
                continue

            if text.startswith('/') or text.startswith('CMakeFiles'): # file path line
                continue

            if text.startswith('LOAD') or text.startswith('START GROUP') or text.startswith('END GROUP'):
                continue

            if text.startswith('As-needed library included to satisfy reference by file'):
                _skip_detect = True
                keys.append((text, cur_line_number))

            if text.startswith('Allocating common symbols'):
                _skip_detect = True
                keys.append((text, cur_line_number))

            if text.startswith('Discarded input sections'):
                _skip_detect = False

            if _skip_detect:
                continue

            key = None
            if text.startswith('.'):
                key = text.split()[0]
            else:
                key = text.rstrip()

            if key is None or len(key) == 0:
                print (text)
                print (cur_line_number)
                break
            keys.append((key, cur_line_number))
    finally:
        if fr:
            fr.close()

    print ("== All Keys ==")
    for (key, line) in keys:
        print ("{} : L{}".format(key, line))


class _SymbolItem:
    def __init__(self, name, size=0):
        self.name = name
        self.size = size
        self._children = []

    def __getitem__(self, index):
        return self._children[index]

    def __str__(self):
        return "(name: {} size: {})".format(self.name, self.size)

    def _compare_key(self, item):
        return item.size

    def has_child(self):
        return len(self._children) > 0

    def append_child(self, item):
        self._children.append(item)

    def all_children(self, sort=False):
        if sort:
            self._children.sort(key=self._compare_key, reverse=True)

        return self._children

    def print(self, depth=0, count=0, output=None):
        indent = "   " * max(0, depth)
        text = "{}{}({}B) : {}".format(indent, _byte2humanSize(self.size), self.size, self.name)
        print (text)
        if output:
            output.write(text)
            output.write("\r\n")

        if self.has_child():
            depth += 1
            i = 0
            for item in self.all_children(sort=True):
                if i > count and count != 0:
                    break

                item.print(depth, count, output)
                i += 1


class _EOF(Exception):
    pass


class _Analyzer:
    def __init__(self):
        self.cur_line_number = 0    # for debug

    def _do_analyze(self, link_map_file, group) -> dict:
        return {}

    def _read_line(self, fd, ignore_empty_line=True) -> str:
        text = None
        while True:
            text = fd.readline()
            if len(text) == 0:
                raise _EOF()

            self.cur_line_number += 1
            text = text.rstrip()

            if text == b'' and ignore_empty_line:
                continue

            break

        return bytes.decode(text, 'utf-8', 'ignore')

    def _sort(self, symbols, reverse=True):
        def _compare_key(item):
            return item.size

        # symbols.sort(key=_compare_key, reverse=True)
        return sorted(symbols, key=_compare_key, reverse=reverse)


'''
LinkMap 文件分析器 for iOS
'''
class _iOSLinkMapAnalyzer(_Analyzer):
    _BLACK_LIBRARIES = (
            "libarclite_iphoneos.a",
            "libclang_rt.ios.a",
            )

    def __init__(self):
        _Analyzer.__init__(self)

    def _do_analyze(self, link_map_file, group) -> dict:
        if not os.path.exists(link_map_file) or not os.path.isfile(link_map_file):
            print ("the link map file: {} not exists")
            return False
        
        _fr = open(link_map_file, 'rb')
        contents = [line_bytes.decode("utf-8", "ignore").strip() for line_bytes in _fr]
        _fr.close()

        if not self._check(contents):
            print ("Link Map file format invalid")
            return False

        symbolItems = self._parseSymbols(contents)

        sortedSymbols = self._sort(symbolItems)

        groupSymbols = self._buildGroupResult(sortedSymbols)

        if group:
            return self._buildSDKResult(groupSymbols)
        else:
            return groupSymbols

    def _check(self, content) -> bool:
        flag = "# Object files:" in content and "# Symbols:" in content
        if flag:
            for line in content:
                if line.startswith("# Path:"):
                    return True

        return False

    def _parseSymbols(self, content):
        reachFiles = False
        reachSymbols = False
        reachSections = False
        
        symbolMap = {}
        for line in content:
            if line.startswith('#'):
                if line.startswith("# Object files:"):
                    reachFiles = True
                elif line.startswith("# Sections:"):
                    reachSections = True
                elif line.startswith("# Symbols:"):
                    reachSymbols = True
            else:
                if reachFiles and not reachSections and not reachSymbols:
                    pos = line.find(']')
                    if (pos >= 0):
                        symbol_item = _SymbolItem(line[pos + 1 : ])
                        key = line[0 : pos + 1]
                        symbolMap[key] = symbol_item
                elif reachFiles and reachSections and reachSymbols:
                    _symbolsArr = line.split('\t')
                    if len(_symbolsArr) == 3:
                        fileKeyAndName = _symbolsArr[2]
                        size = int(_symbolsArr[1], 16)

                        pos = fileKeyAndName.find(']')
                        if pos >= 0:
                            key = fileKeyAndName[:pos + 1]
                            symbolItem = symbolMap[key]
                            if symbolItem:
                                symbolItem.size += size

        return symbolMap.values();


    '''
    基于 _parseSymbols 结果做分组
    '''
    def _buildGroupResult(self, symbols):
        _groupResult = {}
        for item in symbols:
            basename = os.path.basename(item.name)
            if basename.rfind('(') > 0 and basename.rfind(')') > 0:
                pos = basename.rfind('(')
                libname = basename[ : pos]
                symbolItem = _groupResult.get(libname)
                if not symbolItem:
                    symbolItem = _SymbolItem(libname)
                    _groupResult[libname] = symbolItem

                symbolItem.size += item.size
            else:
                symbolItem = _SymbolItem(basename)
                symbolItem.size = item.size
                _groupResult[basename] = symbolItem

        return self._sort(_groupResult.values())


    '''
    基于 _buildGroupResult 结果做二次加工
    '''
    def _buildSDKResult(self, grouped_result):
        _sdkCodeItem = _SymbolItem(_SDK_CODE_KEY)
        _result = { _SDK_TOTAL_KEY: _SymbolItem(_SDK_TOTAL_KEY), _VE_TOTAL_KEY: _SymbolItem(_VE_TOTAL_KEY) }
        for item in grouped_result:
            if item.name.endswith(".a") and item.name.lower() not in _SDK_DEPENDS_LIBRARIES and item.name.lower() not in _iOSLinkMapAnalyzer._BLACK_LIBRARIES: # ve & ve's depends
                _result[_VE_TOTAL_KEY].size += item.size
                _result[_VE_TOTAL_KEY].append_child(item)
            elif item.name.endswith(".o"): # sdk code
                _sdkCodeItem.size += item.size
                _sdkCodeItem.append_child(item)
                _result[_SDK_TOTAL_KEY].size += item.size
            elif item.name.lower() in _SDK_DEPENDS_LIBRARIES: # sdk's depends
                _result[_SDK_TOTAL_KEY].size += item.size
                _result[_SDK_TOTAL_KEY].append_child(item)
            else:
                _result[item.name] = item

        _result[_SDK_TOTAL_KEY].append_child(_sdkCodeItem)

        return self._sort(_result.values())


class _LinuxLinkMapAnalyzer(_Analyzer):
    _BLACK_LIBRARIES = (
            # for armeabi-v7a
            "libc++_static.a",
            "libc++abi.a",
            "libandroid_support.a",
            "libgcc.a",
            "libunwind.a",
            "crtbegin_so.o",
            "crtend_so.o",
            
            # for arm64-v8a
            "liblog.so",
            "libGLESv2.so",
            "libEGL.so",
            "libandroid.so",
            "libjnigraphics.so",
            "libOpenSLES.so",
            "libstdc++.so",
            "libm.so",
            "libdl.so",
            "libc.so",
            "libatomic.a",

            # for linux
            "crtendS.o",
            "crtn.o",
            "crti.o",
            "crtbeginS.o",
            "libc_nonshared.a",
            "libgcc.a",
            "libgcc_s.so",
            "libgcc_s.so.1",
            )

    _SCOPE_TYPE_UNKNOWN = -1
    _SCOPE_TYPE_ARCHIVE_MEMBER = 1
    _SCOPE_TYPE_ALLOCATING_SYMBOL = 2
    _SCOPE_TYPE_DISCARDED_SECTION = 3
    _SCOPE_TYPE_MEMORY_MAP = 4
    _SCOPE_TYPE_MEMORY_CONFIGURATION = 5
    _SCOPE_TYPE_LINKER_SCRIPT_MEMORY = 6

    def __init__(self):
        _Analyzer.__init__(self)
        self.path_pattern = re.compile('^CMakeFiles[\s\S]*\.dir')

    def _get_real_path(self, raw_path):
        m = self.path_pattern.search(raw_path)
        if m:
            return raw_path.replace(m.group(), "")

        return raw_path

    def _merge_result(self, src, dst):
        for key in src:
            item = src[key]
            if key in dst:
                dst[key].size += item.size
            else:
                dst[key] = _SymbolItem(item.name, item.size)

    def _do_analyze(self, link_map_file, group) -> dict:
        _archive_result, _allocating_symbol_result, _discarded_section_result, _memory_map_result, _script_memory_map_result = {}, {}, {}, {}, {}
        _current_scope_type = _LinuxLinkMapAnalyzer._SCOPE_TYPE_UNKNOWN
        fd = open(link_map_file, 'rb')
        try:
            while True:
                text = self._read_line(fd)
                if text.startswith("Archive member included"):
                    _current_scope_type = _LinuxLinkMapAnalyzer._SCOPE_TYPE_ARCHIVE_MEMBER
                elif text.startswith("Allocating common symbols"):
                    _current_scope_type = _LinuxLinkMapAnalyzer._SCOPE_TYPE_ALLOCATING_SYMBOL
                    self._read_line(fd) # ignore line: Common symbol       size              file
                elif text.startswith("Discarded input sections"):
                    _current_scope_type = _LinuxLinkMapAnalyzer._SCOPE_TYPE_DISCARDED_SECTION
                elif text.startswith("Memory map"):
                    _current_scope_type = _LinuxLinkMapAnalyzer._SCOPE_TYPE_MEMORY_MAP
                elif text.startswith("Memory Configuration"):
                    _current_scope_type = _LinuxLinkMapAnalyzer._SCOPE_TYPE_MEMORY_CONFIGURATION
                elif text.startswith("Linker script and memory map"):
                    _current_scope_type = _LinuxLinkMapAnalyzer._SCOPE_TYPE_LINKER_SCRIPT_MEMORY
                else:
                    if _current_scope_type == _LinuxLinkMapAnalyzer._SCOPE_TYPE_ARCHIVE_MEMBER:
                        self._parseArchiveMember(text, fd, _archive_result)
                    elif _current_scope_type == _LinuxLinkMapAnalyzer._SCOPE_TYPE_ALLOCATING_SYMBOL:
                        self._parseAllocatingSymbol(text, fd, _allocating_symbol_result)
                    elif _current_scope_type == _LinuxLinkMapAnalyzer._SCOPE_TYPE_DISCARDED_SECTION:
                        self._parseDiscardedSection(text, fd, _discarded_section_result)
                    elif _current_scope_type == _LinuxLinkMapAnalyzer._SCOPE_TYPE_MEMORY_MAP:
                        self._parseMemoryMap(text, fd, _memory_map_result)
                    elif _current_scope_type == _LinuxLinkMapAnalyzer._SCOPE_TYPE_MEMORY_CONFIGURATION:
                        pass
                    elif _current_scope_type == _LinuxLinkMapAnalyzer._SCOPE_TYPE_LINKER_SCRIPT_MEMORY:
                        self._parseLinkerScriptMemory(text, fd, _script_memory_map_result)
        except _EOF as e:
            pass
        finally:
            if fd:
                fd.close()

        show_details = False
        if show_details:
            print ("== Archive member included ==")
            _sorted_result = self._sort(_archive_result.values(), reverse=False)
            for item in _sorted_result:
                print (item.name)

            print("\n== Allocating common symbols ==")
            total_size = 0
            _sorted_result = self._sort(_allocating_symbol_result.values())
            for item in _sorted_result:
                total_size += item.size
                print ("{}({}B) -- {}".format(_byte2humanSize(item.size), total_size, item.name))

            print ("Total size: {}({}B)".format(_byte2humanSize(total_size), total_size))

            print ("\n== Discarded input sections ==")
            total_size = 0
            _sorted_result = self._sort(_discarded_section_result.values())
            for item in _sorted_result:
                total_size += item.size
                print ("{}({}B) : {}".format(_byte2humanSize(item.size), total_size, item.name))

            print ("Total size: {}({}B)".format(_byte2humanSize(total_size), total_size))

            print ("\n== Memory map ==")
            total_size = 0
            _sorted_result = self._sort(_memory_map_result.values())
            for item in _sorted_result:
                total_size += item.size
                print ("{}({}B) : {}".format(_byte2humanSize(item.size), item.size, item.name))

            print ("Total size: {}({}B)".format(_byte2humanSize(total_size), total_size))

        total_size = 0
        _summery_result = {}
        self._merge_result(_allocating_symbol_result, _summery_result)
        self._merge_result(_discarded_section_result, _summery_result)
        self._merge_result(_memory_map_result, _summery_result)
        self._merge_result(_script_memory_map_result, _summery_result)
        sortedSymbols = self._sort(_summery_result.values())
        if group:
            return self._buildSDKResult(sortedSymbols)
        else:
            return self._buildGroupResult(sortedSymbols)

    def _parseArchiveMember(self, cur_line, fd, result):
        name = os.path.normpath(cur_line.strip())
        pos = name.find('(')
        if pos > 0:
            filepath = name[ : pos]
            filepath = self._get_real_path(filepath)
            if filepath in result:
                result[filepath].size += 1
            else:
                result[filepath] = _SymbolItem(filepath, 1)
        else:
            print (">>> unrecognize line: {} in L{}".format(cur_line, self.cur_line_number))

    def _parseAllocatingSymbol(self, cur_line, fd, result):
        data = None
        pos = cur_line.find('0x')
        if pos > 0:
            data = cur_line[pos : ]
        else:
            data = self._read_line(fd).strip()

        pos = data.find(' ')
        if pos > 0:
            size = int(data[: pos], 16)
            pos2 = data.find('(')
            filepath = os.path.normpath(data[pos : pos2].strip())
            filepath = self._get_real_path(filepath)
            if filepath in result:
                result[filepath].size += size
            else:
                result[filepath] = _SymbolItem(filepath, size)
        else:
            print (">>> unrecognize line: {} in L{}".format(data, self.cur_line_number))

    def _parseDiscardedSection(self, cur_line, fd, result):
        tag = None
        data = None
        pos = cur_line.find('0x')
        if pos > 0:
            tag = cur_line[ : pos].strip()
            data = cur_line[pos : ].strip()
        else:
            tag = cur_line.strip()
            data = self._read_line(fd).strip()

        if tag.startswith(".debug"):
            pass  # ignore
        else:
            pos = data.find(' ')
            sizeAndPath = data[pos : ].strip()
            pos = sizeAndPath.find(' ')
            size = int(sizeAndPath[ : pos], 16)
            path = sizeAndPath[pos : ].strip()

            while True:
                if path.endswith(')'):
                    pos = path.rfind('(')
                    path = path[ : pos].strip()
                else:
                    break

            path = os.path.normpath(path).strip()
            filepath = self._get_real_path(path)
            if filepath in result:
                result[filepath].size += size
            else:
                result[filepath] = _SymbolItem(filepath, size)

    '''
    当起始地址遇到 0xffffffffffffffff 时，可能存在 size 有误差的情况
    '''
    def _parseMemoryMap(self, cur_line, fd, result):
        if cur_line.strip().startswith('0x'): #invalid data
            return

        tag = None
        data = None
        pos = cur_line.find('0x')
        if pos > 0:
            tag = cur_line[: pos].rstrip()
            data = cur_line[pos : ].strip()
        else:
            tag = cur_line.rstrip()
            data = self._read_line(fd).strip()

        is_top_tag = False
        path = None
        if tag in [" ** file header", " ** segment headers"]:
            is_top_tag = True
            size = int(data.split()[1], 16)
            path = tag
        elif tag.startswith('.'):
            next_line = self._read_line(fd)
            if next_line.strip().startswith("**"):
                is_top_tag = True
                size = int(data.split()[1], 16)
                path = tag
                pos = next_line.find('0x')
                if pos < 0:
                    self._read_line(fd)
            else:
                is_top_tag = False
                data = None
                pos = next_line.find('0x')
                if pos > 0:
                    data = next_line[pos : ].strip()
                else:
                    data = self._read_line(fd).strip()

                pos = data.find(' ')
                sizeAndPath = data[pos : ].strip()
                pos = sizeAndPath.find(' ')
                size = int(sizeAndPath[ : pos], 16)
                path = sizeAndPath[pos : ].strip()
        elif tag.startswith(' '):
            is_top_tag = False
            pos = data.find(' ')
            sizeAndPath = data[pos : ].strip()
            pos = sizeAndPath.find(' ')
            if pos > 0:
                size = int(sizeAndPath[ : pos], 16)
                path = sizeAndPath[pos : ].strip()
            else:
                # invalid data
                return
        else:
            print (">>> recognize line: {} in L{}".format(cur_line, self.cur_line_number))
            return

        filepath = os.path.normpath(path)
        filepath = self._get_real_path(filepath)
        while not is_top_tag:
            if filepath.endswith(')'):
                pos = filepath.rfind('(')
                filepath = filepath[ : pos].strip()
            else:
                break

        if filepath in result:
            result[filepath].size += size
        else:
            result[filepath] = _SymbolItem(filepath, size)

    def _parseLinkerScriptMemory(self, cur_line, fd, result):
        if cur_line.startswith("LOAD") or cur_line.startswith("START GROUP") or cur_line.startswith("END GROUP"):
            return

        if cur_line.strip().startswith('0x') or cur_line.strip().startswith('['): #invalid data
            return

        tag = None
        data = None
        pos = cur_line.find('0x')
        if pos > 0:
            tag = cur_line[: pos].rstrip()
            data = cur_line[pos : ].strip()
        else:
            tag = cur_line.rstrip()
            data = self._read_line(fd).strip()
            if data.strip().startswith('*'):
                return

        is_top_tag = False
        path = None
        if tag in [" ** file header", " ** segment headers"]:
            is_top_tag = True
            size = int(data.split()[1], 16)
            path = tag
        elif tag.startswith('.'):
            next_line = self._read_line(fd)
            if next_line.strip().startswith("**"):
                is_top_tag = True
                size = int(data.split()[1], 16)
                path = tag
                pos = next_line.find('0x')
                if pos < 0:
                    self._read_line(fd)
            else:
                if next_line.strip().startswith('*'):
                    while  True:
                        next_line = self._read_line(fd, ignore_empty_line=False)
                        if next_line.strip().startswith('*'):
                            continue
                        elif len(next_line.strip()) == 0:
                            is_top_tag = True
                            size = int(data.split()[1], 16)
                            path = tag
                            break
                        elif next_line.strip().startswith('.'):
                            is_top_tag = False
                            pos = next_line.find('0x')
                            if pos > 0:
                                data = next_line[pos : ].strip()
                            else:
                                data = self._read_line(fd).strip()

                            break
                else:
                    is_top_tag = False
                    data = None
                    pos = next_line.find('0x')
                    if pos > 0:
                        data = next_line[pos : ].strip()
                    else:
                        data = self._read_line(fd).strip()

                if not is_top_tag:
                    pos = data.find(' ')
                    sizeAndPath = data[pos : ].strip()
                    pos = sizeAndPath.find(' ')
                    if len(sizeAndPath[ : pos]) == 0:
                        print (data)
                        raise Exception(cur_line)

                    size = int(sizeAndPath[ : pos], 16)
                    path = sizeAndPath[pos : ].strip()
        elif tag.startswith(' '):
            if tag.strip().startswith('*'):
                return

            is_top_tag = False
            pos = data.find(' ')
            sizeAndPath = data[pos : ].strip()
            pos = sizeAndPath.find(' ')
            if pos > 0:
                size = int(sizeAndPath[ : pos], 16)
                path = sizeAndPath[pos : ].strip()
            else:
                # invalid data
                return
        else:
            print (">>> recognize line: {} in L{}".format(cur_line, self.cur_line_number))
            return

        filepath = os.path.normpath(path)
        filepath = self._get_real_path(filepath)
        while not is_top_tag:
            if filepath.endswith(')'):
                pos = filepath.rfind('(')
                filepath = filepath[ : pos].strip()
            else:
                break

        if filepath in result:
            result[filepath].size += size
        else:
            result[filepath] = _SymbolItem(filepath, size)

    def _buildGroupResult(self, sortedSymbols):
        _all_symbols = []
        _system_symbols = []
        for item in sortedSymbols:
            if item.name.startswith(".") or item.name.startswith(' '):
                _system_symbols.append(item)
            else:
                _all_symbols.append(_SymbolItem(os.path.basename(item.name), item.size))

        _all_symbols.extend(_system_symbols)
        return _all_symbols

    def _buildSDKResult(self, sortedSymbols) -> list:
        _sdkCodeItem = _SymbolItem(_SDK_CODE_KEY)
        _result = { _SDK_TOTAL_KEY: _SymbolItem(_SDK_TOTAL_KEY), _VE_TOTAL_KEY: _SymbolItem(_VE_TOTAL_KEY) }
        for item in sortedSymbols:
            _name = os.path.basename(item.name)
            if _name.endswith(".a") and _name not in _SDK_DEPENDS_LIBRARIES and _name not in _LinuxLinkMapAnalyzer._BLACK_LIBRARIES: # ve & ve's depends
                _result[_VE_TOTAL_KEY].size += item.size
                _result[_VE_TOTAL_KEY].append_child(_SymbolItem(_name, item.size))
            elif _name.endswith(".o") and _name not in _LinuxLinkMapAnalyzer._BLACK_LIBRARIES: # sdk code
                _sdkCodeItem.size += item.size
                _sdkCodeItem.append_child(_SymbolItem(_name, item.size))
                _result[_SDK_TOTAL_KEY].size += item.size
            elif _name in _SDK_DEPENDS_LIBRARIES: # sdk's depends
                _result[_SDK_TOTAL_KEY].size += item.size
                _result[_SDK_TOTAL_KEY].append_child(_SymbolItem(_name, item.size))
            else:
                _result[_name] = _SymbolItem(_name, item.size)

        _result[_SDK_TOTAL_KEY].append_child(_sdkCodeItem)

        return self._sort(_result.values())


class LinkMapAnalyzer:
    def __init__(self):
        self._analyzers = {}

    def _guess_platform(self, link_map_file) -> int:
        #OUTPUT(libzegoliveroom.so elf64-littleaarch64)   Android_arm64-v8a
        #OUTPUT(libzegoliveroom.so elf64-x86-64)       Linux-x86_64
        #OUTPUT(libzegoliveroom.so elf32-littlearm)    Linux-HISI
        fr = open(link_map_file, 'rb')
        first_line = fr.readline()

        platform = _PLATFORM_Unknown
        if first_line.startswith(b'''# Path:'''):
            platform = _PLATFORM_iOS
        elif first_line.startswith(b'''Archive member included because of file'''):
            platform = _PLATFORM_Android_ARMv7a
        elif first_line.startswith(b'''Archive member included to satisfy reference by file'''):
            fr.seek(os.path.getsize(link_map_file) - 100)
            tail = fr.read(100)
            if re.search(b"^OUTPUT\(lib[^\.]+\.so elf[\d]{2}-x[\d]{2}(-[\d]{2}){0,1}\)$", tail, flags=re.M) \
                or re.search(b"^OUTPUT\(lib[^\.]+\.so elf[\d]{2}-littlearm\)$", tail, flags=re.M):
                platform = _PLATFORM_Linux
            elif re.search(b"^OUTPUT\(lib[\s\S]+\.so elf64-littleaarch64\)$", tail, flags=re.M):
                platform = _PLATFORM_Android_ARMv8a

        fr.close()
        return platform

    def analyze(self, link_map_file, group) -> dict:
        platform = self._guess_platform(link_map_file)
        print ("platform: " + str(platform))
        _analyzer = self._analyzers.get(platform)
        if _analyzer is None:
            if platform == _PLATFORM_iOS:
                _analyzer = _iOSLinkMapAnalyzer()
            elif platform in (_PLATFORM_Android_ARMv7a, _PLATFORM_Android_ARMv8a, _PLATFORM_Linux):
                _analyzer = _LinuxLinkMapAnalyzer()
            else:
                raise Exception(">>> Unrecognize file format <<<")

            self._analyzers[platform] = _analyzer

        return _analyzer._do_analyze(link_map_file, group)

    def export(self, output_file, symols, number) -> bool:
        output = None
        if symols and output_file:
            output_file = os.path.realpath(output_file)
            zegoio.insure_dir_exists(os.path.dirname(output_file))
            output = open(output_file, "w", encoding="utf-8")

        i = 0
        total_size = 0
        for item in symols:
            if i <= number or number == 0:
                item.print(0, number, output)

            i += 1
            total_size += item.size

        text = "Total Size: {}({}B)".format(_byte2humanSize(total_size), total_size)
        print (text)
        if output:
            output.write(text)
            output.write("\r\n")
            output.flush()
            output.close()
            print (">> Save Result to: " + output.name)

        return True

def analyze(link_map_file, output=None, group=False, number=0):
    analyzer = LinkMapAnalyzer()
    symbols = analyzer.analyze(link_map_file, group)
    analyzer.export(output, symbols, number)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("link_map_file", action="store", help="specify an link map file path")
    parser.add_argument("--output", '-o', action='store', help="the result will be save to this file, default only show on console")
    parser.add_argument("--group", '-g', action='store_true', default=False, help="group the result, default False")
    parser.add_argument("--number", '-n', action='store', type=int, default=0, help="show items, default 0 for unlimit")
    args = parser.parse_args()

    # _detect_keys(args.link_map_file)

    analyzer = LinkMapAnalyzer()
    symbols = analyzer.analyze(args.link_map_file, args.group)
    analyzer.export(args.output, symbols, args.number)
