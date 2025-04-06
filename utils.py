

import functools
from tkinter import messagebox
import os
import winreg

def handle_exception(error_message):
    """异常处理装饰器"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                messagebox.showerror("错误", f"{error_message}: {str(e)}")
                raise e

        return wrapper

    return decorator

def require_repo(func):
    """检查是否选择仓库的装饰器"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'repo') and not self.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return
        elif hasattr(self, 'git_ops') and not self.git_ops.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return
        return func(self, *args, **kwargs)
    return wrapper

def find_git_executable():
    """自动查找 git.exe 的位置"""
    # 常见的 Git 安装路径
    common_paths = [
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
    ]
    
    # 从注册表查找 Git 安装路径
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GitForWindows", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            git_path = winreg.QueryValueEx(key, "InstallPath")[0]
            exe_path = os.path.join(git_path, "bin", "git.exe")
            if os.path.exists(exe_path):
                return exe_path
    except WindowsError:
        pass

    # 检查常见路径
    for path in common_paths:
        if os.path.exists(path):
            return path

    # 检查环境变量 PATH
    for path in os.environ["PATH"].split(os.pathsep):
        exe_path = os.path.join(path, "git.exe")
        if os.path.exists(exe_path):
            return exe_path

    return None