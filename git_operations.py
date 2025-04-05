from git import Repo, GitCommandError
from datetime import datetime, timedelta
import os

class GitOperations:
    def __init__(self):
        self.repo = None
        self.repo_path = None

    def init_repo(self, path):
        """初始化仓库"""
        self.repo = Repo.init(path)
        self.repo_path = path
        return self.repo

    def load_repo(self, path):
        """加载已存在的仓库"""
        self.repo = Repo(path)
        self.repo_path = path
        return self.repo

    def check_repo_status(self):
        """检查仓库状态并返回提示信息"""
        if not self.repo:
            return "请先选择或初始化Git仓库"

        try:
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

        except Exception as e:
            return f"检查状态失败: {str(e)}"

    def add_to_stage(self):
        """添加文件到暂存区"""
        self.repo.index.add('*')

    def commit_changes(self, message):
        """提交更改"""
        return self.repo.index.commit(message)

    def add_remote(self, url):
        """添加远程仓库"""
        try:
            self.repo.delete_remote('origin')
        except:
            pass
        return self.repo.create_remote('origin', url)

    def push_to_remote(self, progress_callback=None):
        """推送到远程仓库"""
        if 'origin' not in [remote.name for remote in self.repo.remotes]:
            raise Exception("未配置远程仓库")

        if not any(self.repo.iter_commits()):
            raise Exception("仓库中没有提交记录")

        origin = self.repo.remote('origin')
        return origin.push(self.repo.active_branch, progress=progress_callback)

    def pull_from_remote(self, progress_callback=None):
        """从远程仓库拉取更新"""
        if 'origin' not in [remote.name for remote in self.repo.remotes]:
            raise Exception("未配置远程仓库")
        
        origin = self.repo.remote('origin')
        return origin.pull(progress=progress_callback)

    def get_commit_history(self, days=30):
        """获取指定天数内的提交历史"""
        if not self.repo:
            return []

        history = []
        one_month_ago = datetime.now() - timedelta(days=days)

        for commit in self.repo.iter_commits():
            commit_date = datetime.fromtimestamp(commit.committed_date)
            if commit_date < one_month_ago:
                break
            
            history.append({
                'id': commit.hexsha,
                'date': commit_date,
                'message': commit.message,
                'author': commit.author.name
            })

        return history

    def rollback_to_commit(self, commit_id):
        """回退到指定提交"""
        self.repo.git.reset('--hard', commit_id)

    def check_git_config(self):
        """检查Git配置"""
        try:
            return {
                'name': self.repo.git.config('user.name'),
                'email': self.repo.git.config('user.email')
            }
        except:
            return None

    def set_git_config(self, name, email):
        """设置Git配置"""
        self.repo.git.config('--global', 'user.name', name)
        self.repo.git.config('--global', 'user.email', email)

    def get_remotes(self):
        """获取远程仓库列表"""
        return [remote.name for remote in self.repo.remotes]

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