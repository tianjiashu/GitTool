

import functools
from tkinter import messagebox


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
        if not self.repo and not self.git_ops.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return
        return func(self, *args, **kwargs)
    return wrapper