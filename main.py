import os
import threading
from utils import handle_exception, repo_not_exit, require_repo

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk  # 添加PIL支持
from datetime import datetime, timedelta
from git_operations import GitOperations
# 检查并设置Git环境
from git import GitCommandError


class GitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("迷人小赫敏的傻瓜式Git工具(田佳澍倾情制作！)")
        self.root.geometry("800x780")
        self.root.configure(bg="#f0f0f0")

        # 初始化Git操作对象
        self.git_ops = GitOperations()

        # 添加线程状态标志
        self.is_pushing = False
        self.is_pulling = False

        # 设置样式
        self.setup_styles()

        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建UI元素
        self.create_widgets()

        # 启动定时检查
        self.check_status_periodically()

    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#2196f3")
        style.configure("TLabel", padding=5, background="#f0f0f0")
        style.configure("TFrame", background="#f0f0f0")

    def check_status_periodically(self):
        """定期检查仓库状态"""
        self.show_status_message()
        # 每5秒检查一次
        self.root.after(5000, self.check_status_periodically)

    def create_widgets(self):
        # 添加头像和欢迎文字区域
        avatar_frame = ttk.Frame(self.main_frame)
        avatar_frame.pack(fill=tk.X, pady=(0, 15))

        try:
            # 加载并处理头像
            image = Image.open("zyx.JPG")
            # 调整图片大小为 120x120
            image = image.resize((120, 120), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            # 创建圆角效果的头像标签
            avatar_label = tk.Label(
                avatar_frame,
                image=photo,
                bg="#f0f0f0",
                bd=2,
                relief="groove"
            )
            avatar_label.image = photo
            avatar_label.pack(pady=(10, 5))

        except Exception as e:
            # 创建默认的黑色背景标签
            default_label = tk.Label(
                avatar_frame,
                text="未获取到图像路径 zyx.JPG",
                width=16,  # 设置宽度
                height=7,  # 设置高度
                bg="black",  # 黑色背景
                fg="white",  # 白色文字
                font=("微软雅黑", 10),
                bd=2,
                relief="groove"
            )
            default_label.pack(pady=(10, 5))
            # print(f"加载头像失败: {str(e)}")

        # 添加优雅的欢迎文字
        welcome_text = tk.Label(
            avatar_frame,
            text="你好！迷人小赫敏！",
            font=("华文行楷", 18),
            fg="#FF69B4",
            bg="#f0f0f0"
        )
        welcome_text.pack(pady=(5, 10))

        # 顶部操作区
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # 选择文件夹按钮
        self.select_btn = ttk.Button(top_frame, text="选择文件夹", command=self.select_folder)
        self.select_btn.pack(side=tk.LEFT, padx=5)

        # 当前路径显示
        self.path_label = ttk.Label(top_frame, text="当前未选择仓库")
        self.path_label.pack(side=tk.LEFT, padx=5)

        # 添加状态显示标签
        self.status_label = tk.Label(
            self.main_frame,
            text="",
            fg="red",
            font=("黑体", 10, "bold"),
            justify=tk.CENTER,  # 文本居中对齐
            wraplength=700  # 文本自动换行宽度
        )
        self.status_label.pack(fill=tk.X, pady=5)
        self.status_label.pack(fill=tk.X, pady=5)

        # Git操作区
        self.git_frame = ttk.LabelFrame(self.main_frame, text="Git操作", padding=10)
        self.git_frame.pack(fill=tk.X, pady=5)

        # Git操作按钮
        # ttk.Button(self.git_frame, text="初始化仓库", command=self.init_repo).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.git_frame, text="添加到暂存区", command=self.add_to_stage).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.git_frame, text="提交更改", command=self.commit_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.git_frame, text="推送到远程", command=self.push_to_remote).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.git_frame, text="拉取更新", command=self.pull_from_remote).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.git_frame, text="版本回退", command=self.show_rollback_dialog).pack(side=tk.LEFT, padx=5)

        # GitHub设置区
        self.github_frame = ttk.LabelFrame(self.main_frame, text="GitHub设置(建议使用ssh链接)", padding=10)
        self.github_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.github_frame, text="GitHub仓库链接:").pack(side=tk.LEFT)
        self.github_url = tk.StringVar()
        self.github_entry = ttk.Entry(self.github_frame, textvariable=self.github_url)
        self.github_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.github_frame, text="添加远程仓库", command=self.add_remote).pack(side=tk.LEFT)

        # 历史记录区
        history_frame = ttk.LabelFrame(self.main_frame, text="提交历史记录", padding=10)
        history_frame.pack(fill=tk.X, pady=5)

        # 添加时间范围选择
        time_frame = ttk.Frame(history_frame)
        time_frame.pack(fill=tk.X, pady=(0, 5))

        self.time_range = tk.StringVar(value="近七天")  # 默认选择近七天
        ranges = ["近三小时", "近12小时", "今天", "近七天", "近一个月"]
        for r in ranges:
            ttk.Radiobutton(time_frame, text=r, value=r,
                            variable=self.time_range,
                            command=self.update_history).pack(side=tk.LEFT, padx=5)

        # 创建带滚动条的树形视图
        self.tree_frame = ttk.Frame(history_frame)
        self.tree_frame.pack(fill=tk.BOTH)

        # 修改历史记录视图
        self.history_tree = ttk.Treeview(self.tree_frame,
                                         columns=("提交ID", "日期", "描述", "作者"),
                                         show="headings",
                                         style="Custom.Treeview",
                                         height=8)  # 添加固定高度，显示8行

        self.history_tree.heading("提交ID", text="提交ID", anchor=tk.W)
        self.history_tree.heading("日期", text="日期", anchor=tk.W)
        self.history_tree.heading("描述", text="描述", anchor=tk.W)
        self.history_tree.heading("作者", text="作者", anchor=tk.W)

        self.history_tree.column("提交ID", width=80)
        self.history_tree.column("日期", width=150)
        self.history_tree.column("描述", width=320)
        self.history_tree.column("作者", width=150)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def show_status_message(self):
        """显示状态信息"""
        status_msg = self.git_ops.check_repo_status()
        if status_msg:
            self.status_label.config(text=status_msg)

    @handle_exception("选择文件夹失败")
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            # 检查是否为Git仓库
            is_repo = os.path.exists(os.path.join(folder, '.git'))

            if not is_repo:
                if messagebox.askyesno("提示", "当前文件夹不是仓库，是否初始化为仓库？"):
                    self.git_ops.init_repo(folder)
                    messagebox.showinfo("成功", "Git仓库初始化成功！")
                else:
                    return
            else:
                self.git_ops.load_repo(folder)

            self.path_label.config(text=f"当前仓库: {folder}")
            self.update_remote_url()
            self.update_history()
            self.show_status_message()


    @handle_exception("初始化仓库失败")
    def init_repo(self):
        self.git_ops.init_repo(self.git_ops.repo_path)
        self.update_remote_url()
        messagebox.showinfo("成功", "Git仓库初始化成功！")
        self.show_status_message()

    @require_repo
    @handle_exception("添加到暂存区失败")
    def add_to_stage(self):
        self.git_ops.add_to_stage()
        messagebox.showinfo("成功", "文件已添加到暂存区！")
        self.show_status_message()

    @require_repo
    @handle_exception("提交失败")
    def commit_changes(self):
        commit_message = simpledialog.askstring("提交", "请输入提交信息:")
        if commit_message:
            self.git_ops.commit_changes(commit_message)
            messagebox.showinfo("成功", "更改已提交！")
            self.update_history()
            self.show_status_message()

    @require_repo
    @handle_exception("添加远程仓库失败")
    def add_remote(self):
        github_url = self.github_url.get()
        if not github_url:
            messagebox.showerror("错误", "请输入GitHub仓库链接！")
            return
        self.git_ops.add_remote(github_url)
        messagebox.showinfo("成功", "远程仓库添加成功！")
        self.show_status_message()

    def update_remote_url(self):
        """更新远程仓库链接显示"""
        remote_url = self.git_ops.get_remote_url()
        self.github_url.set(remote_url)

    @require_repo
    @handle_exception("更新历史记录")
    def update_history(self):
        # 清空现有记录
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)

            # 获取时间范围
            time_range = self.time_range.get()
            now = datetime.now()

            if time_range == "近三小时":
                since = now - timedelta(hours=3)
            elif time_range == "近12小时":
                since = now - timedelta(hours=12)
            elif time_range == "今天":
                since = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "近七天":
                since = now - timedelta(days=7)
            else:  # 近一个月
                since = now - timedelta(days=30)

            # 获取提交历史
            history = self.git_ops.get_commit_history(since=since)
            for commit in history:
                self.history_tree.insert("", 0, values=(
                    commit['id'][:7],
                    commit['date'].strftime("%Y-%m-%d %H:%M"),
                    commit['message'],
                    commit['author']
                ))

    @require_repo
    @handle_exception("获取提交历史失败")
    def show_rollback_dialog(self):
        """显示版本回退选择框"""
        # 创建选择框窗口
        dialog = tk.Toplevel(self.root)
        dialog.title("选择回退版本")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # 创建框架
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 创建单选框变量
        selected_commit = tk.StringVar()

        # 获取提交记录
        commits = []

        for commit in self.git_ops.repo.iter_commits():
            commit_date = datetime.fromtimestamp(commit.committed_date)
            commits.append((commit.hexsha, commit_date, commit.message))

            # 创建单选按钮
            radio = ttk.Radiobutton(
                frame,
                text=f"{commit_date.strftime('%Y-%m-%d %H:%M')} - {commit.message}",
                value=commit.hexsha,
                variable=selected_commit
            )
            radio.pack(anchor=tk.W, pady=2)

        def do_rollback():
            commit_id = selected_commit.get()
            if not commit_id:
                messagebox.showerror("错误", "请选择要回退的版本！")
                return

            if messagebox.askyesno("确认", "回退后将丢失该版本之后的所有更改，是否继续？"):
                try:
                    self.git_ops.repo.git.reset('--hard', commit_id)
                    messagebox.showinfo("成功", f"已成功回退到提交 {commit_id[:7]}")
                    self.update_history()
                    self.show_status_message()
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("错误", f"回退失败: {str(e)}")

        # 添加按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="回退", command=do_rollback).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def show_ssh_error_dialog(self):
        """显示SSH错误对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("错误")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # 错误信息
        message_frame = ttk.Frame(dialog, padding="20")
        message_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(message_frame, text="无法连接到远程仓库！", font=("微软雅黑", 11, "bold")).pack(pady=(0, 10))
        ttk.Label(message_frame, text="可能的原因：").pack(anchor=tk.W)
        ttk.Label(message_frame, text="1. 远程仓库地址不正确").pack(anchor=tk.W)
        ttk.Label(message_frame, text="2. 没有仓库访问权限").pack(anchor=tk.W)
        ttk.Label(message_frame, text="3. 未配置SSH密钥").pack(anchor=tk.W)

        def open_tutorial():
            import webbrowser
            webbrowser.open("https://blog.csdn.net/I_loveCong/article/details/139862670")

        # 按钮框架
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(button_frame, text="查看配置教程", command=open_tutorial).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="确定", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    @require_repo
    def push_to_remote(self):
        """推送到远程仓库"""
        if self.is_pushing or self.is_pulling:
            messagebox.showwarning("提示", "有正在进行的操作，请等待完成...")
            return

        try:
            # 检查Git配置
            git_config = self.git_ops.check_git_config()
            if not git_config:
                if messagebox.askyesno("提示", "未配置Git用户信息，是否现在配置？"):
                    name = simpledialog.askstring("配置", "请输入您的用户名:")
                    email = simpledialog.askstring("配置", "请输入您的邮箱:")
                    if name and email:
                        self.git_ops.set_git_config(name, email)
                    else:
                        return
                else:
                    return

            # 显示进度条
            self.progress_frame = ttk.Frame(self.main_frame)
            self.progress_frame.pack(fill=tk.X, pady=5)
            self.progress_label = ttk.Label(self.progress_frame, text="正在推送到远程...")
            self.progress_label.pack(side=tk.LEFT, padx=5)
            self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
            self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.root.update()

            def update_progress(progress, message):
                if not self.is_pushing:  # 如果操作被取消，不更新进度
                    return
                self.progress_bar['value'] = progress
                if message:
                    self.progress_label.config(text=f"正在推送: {message}")
                self.root.update()

            def push_thread():
                error = None
                try:
                    self.is_pushing = True
                    # 执行推送
                    self.git_ops.push_to_remote(progress_callback=update_progress)
                    # 在主线程中更新UI
                    self.root.after(0, self.on_push_complete)
                except Exception as e:
                    error = e
                    # 在主线程中显示错误
                    self.root.after(0, lambda: self.on_push_error(error))
                finally:
                    self.is_pushing = False

            # 启动推送线程
            threading.Thread(target=push_thread, daemon=True).start()

        except Exception as e:
            self.is_pushing = False
            self.progress_frame.pack_forget()
            messagebox.showerror("错误", f"推送失败: {str(e)}")

    def on_push_complete(self):
        """推送完成后的处理"""
        self.progress_bar['value'] = 100
        self.progress_label.config(text="推送完成！")
        self.root.update()
        messagebox.showinfo("成功", "已成功推送到远程仓库！")
        self.show_status_message()
        self.progress_frame.pack_forget()

    def on_push_error(self, error):
        """推送错误处理"""
        self.progress_frame.pack_forget()
        if isinstance(error, GitCommandError):
            error_msg = str(error)
            if "Could not read from remote repository" in error_msg:
                self.show_ssh_error_dialog()
            else:
                messagebox.showerror("错误", f"推送失败: {error_msg}")
        else:
            messagebox.showerror("错误", f"推送失败: {str(error)}")

    @require_repo
    def pull_from_remote(self):
        """从远程仓库拉取更新"""
        if self.is_pushing or self.is_pulling:
            messagebox.showwarning("提示", "有正在进行的操作，请等待完成...")
            return

        try:
            # 检查是否配置了远程仓库
            if 'origin' not in self.git_ops.get_remotes():
                messagebox.showerror("错误", "未配置远程仓库，请先添加远程仓库！")
                return

            # 显示进度条
            self.progress_frame = ttk.Frame(self.main_frame)
            self.progress_frame.pack(fill=tk.X, pady=5)
            self.progress_label = ttk.Label(self.progress_frame, text="正在拉取更新...")
            self.progress_label.pack(side=tk.LEFT, padx=5)
            self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
            self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.root.update()

            def update_progress(progress, message):
                if not self.is_pulling:  # 如果操作被取消，不更新进度
                    return
                self.progress_bar['value'] = progress
                if message:
                    self.progress_label.config(text=f"正在拉取: {message}")
                self.root.update()

            def pull_thread():
                try:
                    self.is_pulling = True
                    # 执行拉取
                    self.git_ops.pull_from_remote(progress_callback=update_progress)
                    # 在主线程中更新UI
                    self.root.after(0, self.on_pull_complete)
                except Exception as e:
                    error = e
                    # 在主线程中显示错误
                    self.root.after(0, lambda: self.on_pull_error(error))
                finally:
                    self.is_pulling = False

            # 启动拉取线程
            threading.Thread(target=pull_thread, daemon=True).start()

        except Exception as e:
            self.is_pulling = False
            self.progress_frame.pack_forget()
            messagebox.showerror("错误", f"拉取失败: {str(e)}")

    def on_pull_complete(self):
        """拉取完成后的处理"""
        self.progress_bar['value'] = 100
        self.progress_label.config(text="拉取完成！")
        self.root.update()
        messagebox.showinfo("成功", "已成功从远程仓库拉取更新！")
        self.update_history()
        self.show_status_message()
        self.progress_frame.pack_forget()

    def on_pull_error(self, error):
        """拉取错误处理"""
        self.progress_frame.pack_forget()
        if isinstance(error, GitCommandError):
            error_msg = str(error)
            if "Could not read from remote repository" in error_msg:
                self.show_ssh_error_dialog()
            else:
                messagebox.showerror("错误", f"拉取失败: {error_msg}")
        else:
            messagebox.showerror("错误", f"拉取失败: {str(error)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GitGUI(root)
    root.mainloop()
