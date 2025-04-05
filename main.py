import os
os.environ['GIT_PYTHON_GIT_EXECUTABLE'] = "F:\Git\cmd\git.exe"
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk  # 添加PIL支持

from datetime import datetime, timedelta
import subprocess

from git_operations import GitOperations


# 检查并设置Git环境
from git import Repo, GitCommandError


class GitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("迷人小赫敏的傻瓜式Git工具(田佳澍倾情制作！)")
        self.root.geometry("800x700")
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
        
        # 删除以下重复的代码
        # self.repo = None
        # self.repo_path = None
        # self.create_widgets()
        # self.check_status_periodically()

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

            # 添加优雅的欢迎文字
            welcome_text = tk.Label(
                avatar_frame,
                text="你好！迷人小赫敏！",
                font=("华文行楷", 18),
                fg="#FF69B4",  # 温柔的粉色
                bg="#f0f0f0"
            )
            welcome_text.pack(pady=(5, 10))

        except Exception as e:
            print(f"加载头像失败: {str(e)}")

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
        self.status_label = tk.Label(self.main_frame, text="", fg="red", font=("黑体", 10, "bold"), justify=tk.LEFT)
        self.status_label.pack(fill=tk.X, pady=5)

        # Git操作区
        self.git_frame = ttk.LabelFrame(self.main_frame, text="Git操作", padding=10)
        self.git_frame.pack(fill=tk.X, pady=5)

        # Git操作按钮
        ttk.Button(self.git_frame, text="初始化仓库", command=self.init_repo).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.git_frame, text="添加到暂存区", command=self.add_to_stage).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.git_frame, text="提交更改", command=self.commit_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.git_frame, text="推送到远程", command=self.push_to_remote).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.git_frame, text="拉取更新", command=self.pull_from_remote).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.git_frame, text="版本回退", command=self.show_rollback_dialog).pack(side=tk.LEFT, padx=5)

        # GitHub设置区
        self.github_frame = ttk.LabelFrame(self.main_frame, text="GitHub设置", padding=10)
        self.github_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.github_frame, text="GitHub仓库链接:").pack(side=tk.LEFT)
        self.github_url = tk.StringVar()
        self.github_entry = ttk.Entry(self.github_frame, textvariable=self.github_url)
        self.github_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.github_frame, text="添加远程仓库", command=self.add_remote).pack(side=tk.LEFT)

        # 历史记录区
        history_frame = ttk.LabelFrame(self.main_frame, text="提交历史记录（近一个月）", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 创建带滚动条的树形视图
        self.tree_frame = ttk.Frame(history_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        # 修改历史记录视图
        self.history_tree = ttk.Treeview(self.tree_frame,
                                       columns=("提交ID", "日期", "描述", "作者"),
                                       show="headings",
                                       style="Custom.Treeview")

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

    def check_repo_status(self):
        """检查仓库状态并返回提示信息"""
        return self.git_ops.check_repo_status()

    def show_status_message(self):
        """显示状态信息"""
        status_msg = self.git_ops.check_repo_status()
        if status_msg:
            self.status_label.config(text=status_msg)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            try:
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

            except Exception as e:
                messagebox.showerror("错误", f"操作失败: {str(e)}")

    def init_repo(self):
        if not self.git_ops.repo_path:
            messagebox.showerror("错误", "请先选择文件夹！")
            return
        try:
            self.git_ops.init_repo(self.git_ops.repo_path)
            self.update_remote_url()
            messagebox.showinfo("成功", "Git仓库初始化成功！")
            self.show_status_message()
        except Exception as e:
            messagebox.showerror("错误", f"初始化失败: {str(e)}")

    def add_to_stage(self):
        if not self.git_ops.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return
        try:
            self.git_ops.add_to_stage()
            messagebox.showinfo("成功", "文件已添加到暂存区！")
            self.show_status_message()
        except Exception as e:
            messagebox.showerror("错误", f"添加失败: {str(e)}")

    def commit_changes(self):
        if not self.git_ops.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return

        commit_message = simpledialog.askstring("提交", "请输入提交信息:")
        if commit_message:
            try:
                self.git_ops.commit_changes(commit_message)
                messagebox.showinfo("成功", "更改已提交！")
                self.update_history()
                self.show_status_message()
            except Exception as e:
                messagebox.showerror("错误", f"提交失败: {str(e)}")

    def add_remote(self):
        if not self.git_ops.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return

        github_url = self.github_url.get()
        if not github_url:
            messagebox.showerror("错误", "请输入GitHub仓库链接！")
            return

        try:
            self.git_ops.add_remote(github_url)
            messagebox.showinfo("成功", "远程仓库添加成功！")
            self.show_status_message()
        except Exception as e:
            messagebox.showerror("错误", f"添加远程仓库失败: {str(e)}")

    def update_remote_url(self):
        """更新远程仓库链接显示"""
        remote_url = self.git_ops.get_remote_url()
        self.github_url.set(remote_url)

    def update_history(self):
        """更新历史记录"""
        try:
            # 清空现有记录
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)

            # 获取提交历史
            history = self.git_ops.get_commit_history()
            for commit in history:
                self.history_tree.insert("", 0, values=(
                    commit['id'][:7],
                    commit['date'].strftime("%Y-%m-%d %H:%M"),
                    commit['message'],
                    commit['author']
                ))
        except Exception:
            pass

    def show_rollback_dialog(self):
        """显示版本回退选择框"""
        if not self.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return

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
        try:
            for commit in self.repo.iter_commits():
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
                        self.repo.git.reset('--hard', commit_id)
                        messagebox.showinfo("成功", f"已成功回退到提交 {commit_id[:7]}")
                        self.update_history()
                        self.show_status_message()
                        dialog.destroy()
                    except Exception as e:
                        messagebox.showerror("错误", f"回退失败: {str(e)}")

            # 添加按钮
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(fill=tk.X, pady=10)
            ttk.Button(btn_frame, text="回退", command=do_rollback).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("错误", f"获取提交历史失败: {str(e)}")
            dialog.destroy()

    def push_to_remote(self):
        """推送到远程仓库"""
        if not self.git_ops.repo:
            messagebox.showerror("错误", "请先选择仓库！")
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
                self.progress_bar['value'] = progress
                if message:
                    self.progress_label.config(text=f"正在推送: {message}")
                self.root.update()

            # 执行推送
            self.git_ops.push_to_remote(progress_callback=update_progress)

            # 完成后更新进度
            self.progress_bar['value'] = 100
            self.progress_label.config(text="推送完成！")
            self.root.update()

            messagebox.showinfo("成功", "已成功推送到远程仓库！")
            self.show_status_message()

            # 隐藏进度条
            self.progress_frame.pack_forget()

        except GitCommandError as e:
            self.progress_frame.pack_forget()
            error_msg = str(e)
            if "Could not read from remote repository" in error_msg:
                messagebox.showerror("错误",
                    "无法连接到远程仓库！\n可能的原因：\n"
                    "1. 远程仓库地址不正确\n"
                    "2. 没有仓库访问权限\n"
                    "3. 未配置SSH密钥")
            else:
                messagebox.showerror("错误", f"推送失败: {error_msg}")
        except Exception as e:
            self.progress_frame.pack_forget()
            messagebox.showerror("错误", f"推送失败: {str(e)}")

    def pull_from_remote(self):
        """从远程仓库拉取更新"""
        if not self.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return

        try:
            # 检查是否配置了远程仓库
            if 'origin' not in [remote.name for remote in self.repo.remotes]:
                messagebox.showerror("错误", "未配置远程仓库，请先添加远程仓库！")
                return

            # 显示进度条
            self.progress_frame = ttk.Frame(self.main_frame)
            self.progress_frame.pack(fill=tk.X, pady=5)
            self.progress_label = ttk.Label(self.progress_frame, text="正在拉取更新...")
            self.progress_label.pack(side=tk.LEFT, padx=5)
            self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
            self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.progress_bar.start()
            self.root.update()

            # 执行拉取
            origin = self.repo.remote('origin')
            origin.pull()

            # 完成后更新进度
            self.progress_bar.stop()
            self.progress_label.config(text="更新完成！")
            self.root.update()

            messagebox.showinfo("成功", "已成功从远程仓库拉取更新！")

            # 更新历史记录和状态
            self.update_history()
            self.show_status_message()

            # 隐藏进度条
            self.progress_frame.pack_forget()

        except GitCommandError as e:
            self.progress_frame.pack_forget()
            error_msg = str(e)
            if "Could not read from remote repository" in error_msg:
                messagebox.showerror("错误",
                    "无法连接到远程仓库！\n可能的原因：\n"
                    "1. 远程仓库地址不正确\n"
                    "2. 没有仓库访问权限\n"
                    "3. 未配置SSH密钥")
            else:
                messagebox.showerror("错误", f"拉取更新失败: {error_msg}")
        except Exception as e:
            self.progress_frame.pack_forget()
            messagebox.showerror("错误", f"拉取更新失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitGUI(root)
    root.mainloop()

