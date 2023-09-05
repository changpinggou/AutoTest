#!/usr/bin/env python -u
# coding: utf-8

"""
用于分析用户反馈的崩溃堆栈
简单的启动方式：
python -m zegopy.CrashParser
"""

import os
import sys
import json
# import re

if sys.version_info.major < 3:
    import tkFileDialog
    from Tkinter import *
else:
    from tkinter import *
    from tkinter import filedialog as tkFileDialog

if sys.platform.startswith("darwin"):
    # 解决 MacOS 上按钮显示异常的问题
    # 通过 pip install tkmacosx 安装(pip3 install tkmacosx for python3)
    try:
        from tkmacosx import Button
    except Exception as e:
        pass


def get_screen_size(window):
    return window.winfo_screenwidth(), window.winfo_screenheight()


def set_window_into_center(window, width, height):
    screenw, screenh = get_screen_size(window)
    centerx = int((screenw - width) / 2)
    centery = int((screenh - height) / 2)
    window.geometry("{}x{}+{}+{}".format(width, height, centerx, centery))


def execCmd(cmd):
    mswindows = (sys.platform == 'win32')
    if not mswindows:
        cmd = '{ ' + cmd + '; }'

    pipe = os.popen(cmd + ' 2>&1', 'r')
    text = pipe.read()
    sts = pipe.close()
    if sts is None: sts = 0
    if text[-1:] == '\n': text = text[:-1]
    return sts, text


class AppConfig:
    def __init__(self, config=None):
        fname = config if config is not None else os.path.join(os.path.expanduser('~'), ".zego_crash_parser_config.cfg")
        self.fp_config = open(fname, "a+")
        self.fp_config.seek(0)
        try:
            self.config_info = json.load(self.fp_config)
        except Exception as e:
            print("load app config failed. {}".format(e))
            self.config_info = {}

    def get(self, key):
        return self.config_info.get(key)

    def set(self, key, value):
        self.config_info[key] = value
        self.fp_config.truncate(0)
        json.dump(self.config_info, self.fp_config)
        self.fp_config.flush()
        return self

    def close(self):
        self.config_info.clear()
        self.fp_config.close()

    def has_key(self, key):
        return key in self.config_info

    def get_ndk_bundle(self):
        if self.has_key("ndk_bundle"):
            return self.get("ndk_bundle")
        return ""

    def set_ndk_bundle(self, ndk_root):
        return self.set("ndk_bundle", ndk_root)

    def get_is_64_os(self):
        if self.has_key("is_64"):
            return self.get("is_64")
        return 0

    def set_is_64_os(self, value):
        return self.set("is_64", value)

    def get_is_x86_os(self):
        if self.has_key("is_x86"):
            return self.get("is_x86")
        return 0

    def set_is_x86_os(self, value):
        return self.set("is_x86", value)

    def get_symbol_path(self):
        if self.has_key("symbol"):
            return self.get("symbol")
        return ""

    def set_symbol_path(self, path):
        return self.set("symbol", path)


class App(Tk):
    def __init__(self, title):
        Tk.__init__(self)
        self.title(title)
        self.config = AppConfig()
        self.width = 720
        self.height = 480
        self.background_color = "#f3f3f3"
        self.minsize(400, 240)
        set_window_into_center(self, self.width, self.height)
        self._set_background()
        self._add_ndk_row()
        self._add_symbol_row()
        self._add_arch_type_row()
        self._add_address_list_row()
        self._add_parse_button()
        self._add_output_frame()
        self.grid_columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self._on_quit)

    def focus_set(self):
        if sys.platform.startswith("darwin"):
            os.system('''/usr/bin/osascript -e 'tell app"Finder" to set frontmost of process"Python" to true' ''')
        else:
            Tk.focus_set(self)

    def _on_quit(self):
        self._save_last_config()
        self.config.close()
        sys.exit()

    def _set_background(self):
        frame = Frame(self, width=self.width, height=self.height, bg=self.background_color)
        frame.grid(row=0, column=0, rowspan=6, columnspan=4, sticky=N+S+E+W)

    @staticmethod
    def _bind_events(widget):
        def _handle_event_sel_all(event):
            if hasattr(event.widget, 'tag_add'):
                event.widget.tag_add(SEL, "1.0", END)
            elif hasattr(event.widget, 'selection_range'):
                event.widget.selection_range(0, 'end')
            else:
                print("*** Not support the widget '{}' just now ***".format(event.widget.__class__.__name__))
            return 'break'

        def _handle_event_copy(event):
            select_text = event.widget.selection_get()
            event.widget.clipboard_clear()
            event.widget.clipboard_append(select_text)
            return 'break'

        if sys.platform == "darwin":
            widget.bind("<Command-a>", _handle_event_sel_all)
            widget.bind("<Command-A>", _handle_event_sel_all)
            widget.bind("<Command-c>", _handle_event_copy)
            widget.bind("<Command-C>", _handle_event_copy)
        else:
            widget.bind("<Control-a>", _handle_event_sel_all)
            widget.bind("<Control-A>", _handle_event_sel_all)
            widget.bind("<Control-c>", _handle_event_copy)
            widget.bind("<Control-C>", _handle_event_copy)

    def _add_ndk_row(self):
        label = Label(self, text="NDK_HOME:", bg=self.background_color)
        label.grid(row=0, column=0)

        ndk_bundle = self.config.get_ndk_bundle()
        if ndk_bundle is None or len(ndk_bundle) == 0:
            ndk_bundle = os.environ['NDK_HOME']
        
        self._ndk_bundle = StringVar()
        self._ndk_bundle.set(ndk_bundle)
        entry = Entry(self, textvariable=self._ndk_bundle)
        self._bind_events(entry)
        entry.grid(row=0, column=1, columnspan=3, sticky="we", padx=10)

    def _add_symbol_row(self):
        label = Label(self, text="Symbol Path:", bg=self.background_color)
        label.grid(row=1, column=0, sticky="e")

        self._symbol_path = StringVar()
        self._symbol_path.set(self.config.get_symbol_path())
        entry = Entry(self, textvariable=self._symbol_path)
        self._bind_events(entry)
        entry.grid(row=1, column=1, columnspan=2, sticky="we", padx=10)

        def open_file_dialog():
            selected_file_path = tkFileDialog.askopenfilename()
            self._symbol_path.set(selected_file_path)
        button = Button(self, text="...", command=open_file_dialog)
        # button.configure(bg='#ffffff', fg='#000000', relief=RAISED)
        button.grid(row=1, column=3, sticky="e", padx=10, pady=10)

    def _add_arch_type_row(self):
        def v8_check_event_cb():
            if self._is_bit64_os.get() == 1:
                self._is_x86_os.set(0)

        def x86_check_event_cb():
            if self._is_x86_os.get() == 1:
                self._is_bit64_os.set(0)

        label = Label(self, text="Is 64 Arch:", bg=self.background_color)
        label.grid(row=2, column=0, sticky="e")

        self._is_bit64_os = IntVar()
        self._is_bit64_os.set(self.config.get_is_64_os())
        checkbox = Checkbutton(self, variable=self._is_bit64_os, onvalue=1, offvalue=0, bg=self.background_color
                               , command=v8_check_event_cb)
        checkbox.grid(row=2, column=1, sticky="w", padx=10)

        label_x86 = Label(self, text="Is x86 Arch:", bg=self.background_color)
        label_x86.grid(row=2, column=2, sticky="e")

        self._is_x86_os = IntVar()
        self._is_x86_os.set(self.config.get_is_x86_os())
        checkbox = Checkbutton(self, variable=self._is_x86_os, onvalue=1, offvalue=0, bg=self.background_color
                               , command=x86_check_event_cb)
        checkbox.grid(row=2, column=3, sticky="w", padx=10)

    def _add_address_list_row(self):
        label = Label(self, text="Crash Log:", bg=self.background_color)
        label.grid(row=3, column=0, sticky="e")

        lfc_field_1_t_sv = Scrollbar(self, orient=VERTICAL)  # 文本框-竖向滚动条
        lfc_field_1_t_sh = Scrollbar(self, orient=HORIZONTAL)
        self._crash_log = Text(self, height=8, yscrollcommand=lfc_field_1_t_sv.set,
                               xscrollcommand=lfc_field_1_t_sh.set, wrap="none")
        self._crash_log.focus_force()
        self._bind_events(self._crash_log)
        self._crash_log.grid(row=3, column=1, columnspan=3, sticky="we", padx=10)

    def _add_parse_button(self):
        button = Button(self, text="Parse", command=self.parse_callback)
        button.grid(row=4, column=0, columnspan=4, sticky="e", padx=10, pady=10)

    def _add_output_frame(self):
        label = Label(self, text="Crash Stack:", bg=self.background_color)
        label.grid(row=5, column=0, sticky="e")

        lfc_field_1_t_sv = Scrollbar(self, orient=VERTICAL)  # 文本框-竖向滚动条
        lfc_field_1_t_sh = Scrollbar(self, orient=HORIZONTAL)
        self._crash_stack_output = Text(self, height=6, yscrollcommand=lfc_field_1_t_sv.set,
                                        xscrollcommand=lfc_field_1_t_sh.set, wrap="none")
        self._crash_stack_output.insert("0.0", "parse result will be shown in here")
        # self._crash_stack_output.config(state=DISABLED)
        self._crash_stack_output.grid(row=5, column=1, columnspan=3, sticky="nswe", padx=10, pady=10)
        self._bind_events(self._crash_stack_output)
        self.grid_rowconfigure(5, weight=1)

    def _get_cmd_line(self):
        ndk_bundle = self._ndk_bundle.get()
        os_name = None
        if sys.platform == 'win32':
            os_name = "windows"
        elif sys.platform.startswith("linux"):
            os_name = "linux"
        elif sys.platform.startswith("darwin"):
            os_name = "darwin"
        else:
            raise Exception("unknown system")

        is_64 = self._is_bit64_os.get() == 1
        is_x86 = self._is_x86_os.get() == 1
        if is_64:
            cmd_file = "toolchains/aarch64-linux-android-4.9/prebuilt/{}-x86_64/bin/aarch64-linux-android-addr2line".format(os_name)
        elif is_x86:
            cmd_file = "toolchains/x86-4.9/prebuilt/{}-x86_64/bin/i686-linux-android-addr2line".format(os_name)
        else:
            cmd_file = "toolchains/arm-linux-androideabi-4.9/prebuilt/{}-x86_64/bin/arm-linux-androideabi-addr2line".format(os_name)
        
        cmd_file_path = os.path.join(ndk_bundle, cmd_file)
        if not os.path.exists(cmd_file_path):
            raise Exception("File {} not found error".format(cmd_file_path))

        return cmd_file_path

    def _parse_crash_log(self):
        """
        return stack address list
        """
        crash_log = self._crash_log.get("0.0", END)
        lines = crash_log.split(os.linesep)
        address_pattern = re.compile(r'''#[\d]{2} pc ([0-9a-fA-F]{8,16})''')
        for line in lines:
            if len(line) == 0: continue

            try:
                int(line, base=16)
                yield line
            except Exception as e:
                result = re.findall(address_pattern, line)
                if not result:
                    continue
                
                yield result[0]

    def _clear_message(self):
        # self._crash_stack_output.config(state=NORMAL)
        self._crash_stack_output.delete("0.0", END)
        # self._crash_stack_output.config(state=DISABLED)

    def _append_message(self, message):
        # self._crash_stack_output.config(state=NORMAL)
        self._crash_stack_output.insert("0.0", message)
        # self._crash_stack_output.config(state=DISABLED)

    def _save_last_config(self):
        self.config.set_ndk_bundle(self._ndk_bundle.get())
        self.config.set_is_64_os(self._is_bit64_os.get())
        self.config.set_symbol_path(self._symbol_path.get())

    def parse_callback(self):
        self._save_last_config()
        self._clear_message()

        output = []
        cmd_line = self._get_cmd_line()
        symbol = self._symbol_path.get()
        for address in self._parse_crash_log():
            cmd = "{cmd} {addr} -e {sym} -f -p -i".format(cmd=cmd_line, addr=address, sym=symbol)
            stat, text = execCmd(cmd)
            if stat == 0:
                output.append(text)
            else:
                print ("{} >>> *** {} ***".format(stat, text))
        message = "\r\n".join(output) + "\r\n"
        self._append_message(message)


def start():
    app = App("CrashParser")
    app.focus_set()
    app.mainloop()


if __name__ == "__main__":
    start()
