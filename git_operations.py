# 设置 Git 可执行文件路径
from utils import handle_exception, require_repo, find_git_executable
import os
from tkinter import messagebox
git_exe = find_git_executable()
if git_exe:
    os.environ['GIT_PYTHON_GIT_EXECUTABLE'] = git_exe
else:
    messagebox.showerror("错误", "未找到 Git 可执行文件，请确保已安装 Git")
from git import Repo
from datetime import datetime

class GitOperations:
    def __init__(self):
        self.repo = None
        self.repo_path = None

    def init_repo(self,path):
        """初始化仓库"""
        if not self.repo_path:
            messagebox.showerror("错误", "请先选择文件夹！")
            return
        try:
            self.repo = Repo.init(path)
            self.repo_path = path
        except Exception as e:
            messagebox.showerror("错误", f"初始化失败: {str(e)}")

    def load_repo(self, path):
        """加载已存在的仓库"""
        self.repo = Repo(path)
        self.repo_path = path
        return self.repo

    @handle_exception("检查状态失败")
    def check_repo_status(self):
        """检查仓库状态并返回提示信息"""
        if not self.repo:
            return "请先选择或初始化Git仓库"

        status = self.repo.git.status()
        messages = []

        if "Changes not staged for commit" in status and "Changes to be committed" in status:
            messages.append("有未暂存和待提交的更改，建议先执行'添加到暂存区'，再执行'提交更改'")
        elif "Changes not staged for commit" in status:
            messages.append("工作区有未暂存的更改，建议执行'添加到暂存区'")
        elif "Changes to be committed" in status:
            messages.append("暂存区有文件待提交，建议执行'提交更改'")

        if "Your branch is ahead" in status:
            messages.append("本地有未推送的提交，建议执行'推送到远程'")

        if not self.repo.remotes:
            messages.append("未配置远程仓库，建议添加GitHub仓库链接")

        return "\n".join(messages) if messages else "仓库状态正常"

    @require_repo
    def add_to_stage(self):
        """添加未暂存的文件到暂存区"""
        # 获取未暂存的文件列表
        untracked = self.repo.untracked_files  # 未跟踪的文件
        modified = [item.a_path for item in self.repo.index.diff(None)]  # 已修改但未暂存的文件
        
        # 添加所有未暂存的文件
        if untracked:
            # 过滤出存在的文件
            existing_untracked = [f for f in untracked if os.path.exists(os.path.join(self.repo_path, f))]
            if existing_untracked:
                self.repo.index.add(existing_untracked)
                
        if modified:
            # 过滤出存在的文件
            existing_modified = [f for f in modified if os.path.exists(os.path.join(self.repo_path, f))]
            if existing_modified:
                self.repo.index.add(existing_modified)

    @require_repo
    def commit_changes(self, message):
        """提交更改"""
        return self.repo.index.commit(message)

    @require_repo
    def add_remote(self, url):
        """添加远程仓库"""
        try:
            self.repo.delete_remote('origin')
        except:
            pass
        return self.repo.create_remote('origin', url)

    @require_repo
    def push_to_remote(self, progress_callback=None):
        """推送到远程仓库"""
        if 'origin' not in [remote.name for remote in self.repo.remotes]:
            raise Exception("未配置远程仓库")

        if not any(self.repo.iter_commits()):
            raise Exception("仓库中没有提交记录")

        origin = self.repo.remote('origin')
        
        def progress_handler(op_code, cur_count, max_count=None, message=''):
            if progress_callback:
                progress = (cur_count / max_count * 100) if max_count else 0
                progress_callback(progress, message)
        
        return origin.push(self.repo.active_branch, progress=progress_handler)

    @require_repo
    def pull_from_remote(self, progress_callback=None):
        """从远程仓库拉取更新"""
        if 'origin' not in [remote.name for remote in self.repo.remotes]:
            raise Exception("未配置远程仓库")
        
        origin = self.repo.remote('origin')
        
        def progress_handler(op_code, cur_count, max_count=None, message=''):
            if progress_callback:
                progress = (cur_count / max_count * 100) if max_count else 0
                progress_callback(progress, message)
        
        return origin.pull(progress=progress_handler)

    @require_repo
    def get_commit_history(self, since=None):
        """获取提交历史"""
        if not self.repo:
            return []
        
        commits = []
        try:
            # 如果指定了时间范围，则按时间范围获取提交记录
            if since:
                for commit in self.repo.iter_commits(since=since):
                    commits.append({
                        'id': commit.hexsha,
                        'date': datetime.fromtimestamp(commit.committed_date),
                        'message': commit.message,
                        'author': commit.author.name
                    })
            else:
                # 默认获取所有提交记录
                for commit in self.repo.iter_commits():
                    commits.append({
                        'id': commit.hexsha,
                        'date': datetime.fromtimestamp(commit.committed_date),
                        'message': commit.message,
                        'author': commit.author.name
                    })
            return commits
        except Exception:
            return []

    @require_repo
    def rollback_to_commit(self, commit_id):
        """回退到指定提交"""
        self.repo.git.reset('--hard', commit_id)

    @require_repo
    def check_git_config(self):
        """检查Git配置"""
        try:
            return {
                'name': self.repo.git.config('user.name'),
                'email': self.repo.git.config('user.email')
            }
        except:
            return None

    @require_repo
    def set_git_config(self, name, email):
        """设置Git配置"""
        self.repo.git.config('--global', 'user.name', name)
        self.repo.git.config('--global', 'user.email', email)

    @require_repo
    def get_remotes(self):
        """获取远程仓库列表"""
        return [remote.name for remote in self.repo.remotes]

    @require_repo
    def get_remote_url(self):
        """获取远程仓库URL"""
        try:
            if self.repo and self.repo.remotes:
                origin = self.repo.remote('origin')
                if origin.urls:
                    return next(origin.urls)
        except:
            pass
        return ""