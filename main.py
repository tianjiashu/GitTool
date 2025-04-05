import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from datetime import datetime, timedelta
import subprocess
os.environ['GIT_PYTHON_GIT_EXECUTABLE'] = "F:\Git\cmd\git.exe"
# 检查并设置Git环境
from git import Repo, GitCommandError


class GitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("迷人小赫敏的傻瓜式Git工具")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # 设置样式
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#2196f3")
        style.configure("TLabel", padding=5, background="#f0f0f0")
        style.configure("TFrame", background="#f0f0f0")
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 仓库对象
        self.repo = None
        self.repo_path = None
        
        # 创建UI元素
        self.create_widgets()
        
        # 启动定时检查
        self.check_status_periodically()

    def check_status_periodically(self):
        """定期检查仓库状态"""
        self.show_status_message()
        # 每5秒检查一次
        self.root.after(5000, self.check_status_periodically)
    
    def create_widgets(self):
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
        
        self.history_tree = ttk.Treeview(self.tree_frame, 
                                       columns=("日期", "描述", "作者"), 
                                       show="headings",
                                       style="Custom.Treeview")
        
        # 设置列宽和对齐方式
        self.history_tree.heading("日期", text="日期", anchor=tk.W)
        self.history_tree.heading("描述", text="描述", anchor=tk.W)
        self.history_tree.heading("作者", text="作者", anchor=tk.W)
        
        self.history_tree.column("日期", width=150)
        self.history_tree.column("描述", width=400)
        self.history_tree.column("作者", width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def check_repo_status(self):
        """检查仓库状态并返回提示信息"""
        if not self.repo:
            return "请先选择或初始化Git仓库"
            
        try:
            status = self.repo.git.status()
            messages = []
            
            # 检查工作区是否有更改
            if "Changes not staged for commit" in status:
                messages.append("工作区有未暂存的更改，建议执行'添加到暂存区'")
            
            # 检查暂存区是否有文件待提交
            if "Changes to be committed" in status:
                messages.append("暂存区有文件待提交，建议执行'提交更改'")
            
            # 检查是否有未推送的提交
            if "Your branch is ahead" in status:
                messages.append("本地有未推送的提交，建议执行'推送到远程'")
                
            # 检查远程仓库配置
            if not self.repo.remotes:
                messages.append("未配置远程仓库，建议添加GitHub仓库链接")
                
            return "\n".join(messages) if messages else "仓库状态正常"
            
        except Exception as e:
            return f"检查状态失败: {str(e)}"

    def show_status_message(self):
        """显示状态信息"""
        status_msg = self.check_repo_status()
        if status_msg:
            self.status_label.config(text=status_msg)
            # messagebox.showinfo("仓库状态", status_msg)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            try:
                # 检查是否为Git仓库
                is_repo = os.path.exists(os.path.join(folder, '.git'))
                
                if not is_repo:
                    if messagebox.askyesno("提示", "当前文件夹不是仓库，是否初始化为仓库？"):
                        self.repo = Repo.init(folder)
                        messagebox.showinfo("成功", "Git仓库初始化成功！")
                    else:
                        return
                else:
                    self.repo = Repo(folder)
                
                self.repo_path = folder
                self.path_label.config(text=f"当前仓库: {folder}")
                self.update_history()
                self.show_status_message()  # 添加状态检查
                
            except Exception as e:
                messagebox.showerror("错误", f"操作失败: {str(e)}")

    def init_repo(self):
        if not self.repo_path:
            messagebox.showerror("错误", "请先选择文件夹！")
            return
        try:
            self.repo = Repo.init(self.repo_path)
            messagebox.showinfo("成功", "Git仓库初始化成功！")
            self.show_status_message()  # 添加状态检查
        except Exception as e:
            messagebox.showerror("错误", f"初始化失败: {str(e)}")

    def add_to_stage(self):
        if not self.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return
        try:
            self.repo.index.add('*')
            messagebox.showinfo("成功", "文件已添加到暂存区！")
            self.show_status_message()  # 添加状态检查
        except Exception as e:
            messagebox.showerror("错误", f"添加失败: {str(e)}")

    def commit_changes(self):
        if not self.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return
        
        commit_message = simpledialog.askstring("提交", "请输入提交信息:")
        if commit_message:
            try:
                self.repo.index.commit(commit_message)
                messagebox.showinfo("成功", "更改已提交！")
                self.update_history()
                self.show_status_message()  # 添加状态检查
            except Exception as e:
                messagebox.showerror("错误", f"提交失败: {str(e)}")

    def add_remote(self):
        if not self.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return
        
        github_url = self.github_url.get()
        if not github_url:
            messagebox.showerror("错误", "请输入GitHub仓库链接！")
            return
        
        try:
            # 尝试删除已存在的远程仓库
            try:
                self.repo.delete_remote('origin')
            except:
                pass
            
            self.repo.create_remote('origin', github_url)
            messagebox.showinfo("成功", "远程仓库添加成功！")
            self.show_status_message()  # 添加状态检查
        except Exception as e:
            messagebox.showerror("错误", f"添加远程仓库失败: {str(e)}")

    def push_to_remote(self):
        if not self.repo:
            messagebox.showerror("错误", "请先选择仓库！")
            return
        
        try:
            # 检查是否配置了远程仓库
            if 'origin' not in [remote.name for remote in self.repo.remotes]:
                messagebox.showerror("错误", "未配置远程仓库，请先添加远程仓库！")
                return

            # 检查是否有提交记录
            if not any(self.repo.iter_commits()):
                messagebox.showerror("错误", "仓库中没有提交记录，请先提交更改！")
                return

            # 检查Git配置
            try:
                user_name = self.repo.git.config('user.name')
                user_email = self.repo.git.config('user.email')
            except:
                if messagebox.askyesno("提示", "未配置Git用户信息，是否现在配置？"):
                    name = simpledialog.askstring("配置", "请输入您的用户名:")
                    email = simpledialog.askstring("配置", "请输入您的邮箱:")
                    if name and email:
                        self.repo.git.config('--global', 'user.name', name)
                        self.repo.git.config('--global', 'user.email', email)
                    else:
                        return
                else:
                    return

            # 显示进度条
            self.progress_frame = ttk.Frame(self.main_frame)
            self.progress_frame.pack(fill=tk.X, pady=5)
            self.progress_label = ttk.Label(self.progress_frame, text="")
            self.progress_label.pack(side=tk.LEFT, padx=5)
            self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=300)
            self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 显示初始状态
            self.progress_label.config(text="正在推送...")
            self.progress_bar['value'] = 0
            self.root.update()

            # 定义进度回调函数
            def progress(op_code, cur_count, max_count=None, message=''):
                if max_count:
                    percentage = (cur_count / max_count) * 100
                    self.progress_bar['value'] = percentage
                    self.progress_label.config(text=f"正在推送... {percentage:.1f}%")
                    self.root.update()

            # 执行推送
            origin = self.repo.remote('origin')
            origin.push(self.repo.active_branch, progress=progress)
            
            # 完成后更新进度
            self.progress_bar['value'] = 100
            self.progress_label.config(text="推送完成！")
            self.root.update()
            
            messagebox.showinfo("成功", "推送成功！")
            
            # 隐藏进度条
            self.progress_frame.pack_forget()
            
            self.show_status_message()
            
        except GitCommandError as e:
            self.progress_frame.pack_forget()  # 发生错误时隐藏进度条
            error_msg = str(e)
            if "Could not read from remote repository" in error_msg:
                messagebox.showerror("错误", 
                    "无法连接到远程仓库！\n可能的原因：\n"
                    "1. 远程仓库地址不正确\n"
                    "2. 没有仓库访问权限\n"
                    "3. 未配置SSH密钥\n\n"
                    "SSH密钥配置教程：https://blog.csdn.net/Serena_tz/article/details/115109206\n")
            else:
                messagebox.showerror("错误", f"推送失败: {error_msg}")
        except Exception as e:
            messagebox.showerror("错误", f"推送失败: {str(e)}")
            raise e

    def update_history(self):
        if not self.repo:
            return
        
        try:
            # 清空现有记录
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # 获取一个月内的提交记录
            one_month_ago = datetime.now() - timedelta(days=30)
            
            for commit in self.repo.iter_commits():
                commit_date = datetime.fromtimestamp(commit.committed_date)
                if commit_date < one_month_ago:
                    break
                    
                self.history_tree.insert("", 0, values=(
                    commit_date.strftime("%Y-%m-%d %H:%M"),
                    commit.message,
                    commit.author.name
                ))
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = GitGUI(root)
    root.mainloop()

