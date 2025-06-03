"""
GitHub Integration Wizard API
Provides seamless repository setup and management
"""

import os
import requests
import base64
import json
from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
import subprocess
import tempfile
import shutil

github_integration = Blueprint('github_integration', __name__)

class GitHubIntegrationService:
    def __init__(self):
        self.api_base = "https://api.github.com"
        self.token = None
        
    def set_token(self, token):
        """Set GitHub token for API calls"""
        self.token = token
        
    def get_headers(self):
        """Get authenticated headers for GitHub API"""
        if not self.token:
            return None
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def test_connection(self):
        """Test GitHub API connection and token validity"""
        headers = self.get_headers()
        if not headers:
            return {"success": False, "error": "No token provided"}
        
        try:
            response = requests.get(f"{self.api_base}/user", headers=headers, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "success": True,
                    "user": {
                        "login": user_data.get("login"),
                        "name": user_data.get("name"),
                        "email": user_data.get("email"),
                        "avatar_url": user_data.get("avatar_url"),
                        "public_repos": user_data.get("public_repos", 0),
                        "private_repos": user_data.get("total_private_repos", 0)
                    }
                }
            else:
                return {"success": False, "error": f"Authentication failed: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}
    
    def list_organizations(self):
        """List user's GitHub organizations"""
        headers = self.get_headers()
        if not headers:
            return {"success": False, "error": "No token provided"}
        
        try:
            response = requests.get(f"{self.api_base}/user/orgs", headers=headers, timeout=10)
            if response.status_code == 200:
                orgs = response.json()
                return {
                    "success": True,
                    "organizations": [
                        {
                            "login": org.get("login"),
                            "name": org.get("name") or org.get("login"),
                            "description": org.get("description"),
                            "avatar_url": org.get("avatar_url"),
                            "public_repos": org.get("public_repos", 0)
                        }
                        for org in orgs
                    ]
                }
            else:
                return {"success": False, "error": f"Failed to fetch organizations: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Error fetching organizations: {str(e)}"}
    
    def create_repository(self, repo_config):
        """Create a new GitHub repository"""
        headers = self.get_headers()
        if not headers:
            return {"success": False, "error": "No token provided"}
        
        # Determine API endpoint based on organization
        if repo_config.get("organization"):
            url = f"{self.api_base}/orgs/{repo_config['organization']}/repos"
        else:
            url = f"{self.api_base}/user/repos"
        
        # Prepare repository data
        repo_data = {
            "name": repo_config["name"],
            "description": repo_config.get("description", ""),
            "private": repo_config.get("private", False),
            "auto_init": repo_config.get("auto_init", True),
            "gitignore_template": repo_config.get("gitignore_template"),
            "license_template": repo_config.get("license_template"),
            "allow_squash_merge": True,
            "allow_merge_commit": True,
            "allow_rebase_merge": True,
            "delete_branch_on_merge": True
        }
        
        try:
            response = requests.post(url, headers=headers, json=repo_data, timeout=15)
            if response.status_code == 201:
                repo = response.json()
                return {
                    "success": True,
                    "repository": {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "html_url": repo["html_url"],
                        "clone_url": repo["clone_url"],
                        "ssh_url": repo["ssh_url"],
                        "private": repo["private"],
                        "description": repo["description"]
                    }
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "success": False, 
                    "error": error_data.get("message", f"Failed to create repository: {response.status_code}")
                }
        except Exception as e:
            return {"success": False, "error": f"Error creating repository: {str(e)}"}
    
    def upload_file(self, owner, repo, file_path, content, commit_message):
        """Upload a single file to GitHub repository"""
        headers = self.get_headers()
        if not headers:
            return {"success": False, "error": "No token provided"}
        
        # Encode content to base64
        if isinstance(content, str):
            content = content.encode('utf-8')
        encoded_content = base64.b64encode(content).decode('utf-8')
        
        url = f"{self.api_base}/repos/{owner}/{repo}/contents/{file_path}"
        
        data = {
            "message": commit_message,
            "content": encoded_content,
            "branch": "main"
        }
        
        try:
            response = requests.put(url, headers=headers, json=data, timeout=15)
            if response.status_code in [200, 201]:
                return {"success": True, "file_path": file_path}
            else:
                error_data = response.json() if response.content else {}
                return {
                    "success": False,
                    "error": error_data.get("message", f"Upload failed: {response.status_code}")
                }
        except Exception as e:
            return {"success": False, "error": f"Error uploading file: {str(e)}"}
    
    def sync_project_files(self, owner, repo, project_path="."):
        """Sync project files to GitHub repository"""
        results = {
            "uploaded_files": [],
            "failed_files": [],
            "total_files": 0,
            "success_count": 0
        }
        
        # Priority files to upload first
        priority_files = [
            "README.md",
            "main.py", 
            "app.py",
            "requirements.txt",
            "package.json",
            ".gitignore",
            "RELEASE_NOTES.md"
        ]
        
        # Upload priority files first
        for filename in priority_files:
            if os.path.exists(os.path.join(project_path, filename)):
                results["total_files"] += 1
                file_result = self._upload_project_file(owner, repo, filename, project_path)
                if file_result["success"]:
                    results["uploaded_files"].append(filename)
                    results["success_count"] += 1
                else:
                    results["failed_files"].append({"file": filename, "error": file_result["error"]})
        
        # Upload key directories
        key_directories = ["api/", "core/", "routes/", "templates/", "static/", "docs/"]
        
        for directory in key_directories:
            dir_path = os.path.join(project_path, directory)
            if os.path.exists(dir_path):
                dir_results = self._upload_directory(owner, repo, directory, dir_path)
                results["total_files"] += dir_results["total_files"]
                results["success_count"] += dir_results["success_count"]
                results["uploaded_files"].extend(dir_results["uploaded_files"])
                results["failed_files"].extend(dir_results["failed_files"])
        
        return results
    
    def _upload_project_file(self, owner, repo, filename, project_path):
        """Upload a single project file"""
        file_path = os.path.join(project_path, filename)
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Skip large files (>25MB)
            if len(content) > 25 * 1024 * 1024:
                return {"success": False, "error": "File too large (>25MB)"}
            
            return self.upload_file(owner, repo, filename, content, f"Add {filename}")
        except Exception as e:
            return {"success": False, "error": f"Error reading file: {str(e)}"}
    
    def _upload_directory(self, owner, repo, rel_dir, abs_dir):
        """Upload all files in a directory"""
        results = {
            "uploaded_files": [],
            "failed_files": [],
            "total_files": 0,
            "success_count": 0
        }
        
        for root, dirs, files in os.walk(abs_dir):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, ".")
                
                results["total_files"] += 1
                
                try:
                    # Skip large files
                    if os.path.getsize(file_path) > 25 * 1024 * 1024:
                        results["failed_files"].append({
                            "file": rel_path, 
                            "error": "File too large (>25MB)"
                        })
                        continue
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    upload_result = self.upload_file(owner, repo, rel_path, content, f"Add {rel_path}")
                    
                    if upload_result["success"]:
                        results["uploaded_files"].append(rel_path)
                        results["success_count"] += 1
                    else:
                        results["failed_files"].append({
                            "file": rel_path,
                            "error": upload_result["error"]
                        })
                
                except Exception as e:
                    results["failed_files"].append({
                        "file": rel_path,
                        "error": f"Error processing file: {str(e)}"
                    })
        
        return results

# Global service instance
github_service = GitHubIntegrationService()

@github_integration.route('/github-wizard')
def github_wizard():
    """Main GitHub Integration Wizard interface"""
    return render_template('github_wizard.html')

@github_integration.route('/api/github/test-connection', methods=['POST'])
def test_github_connection():
    """Test GitHub API connection"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({"success": False, "error": "GitHub token is required"})
    
    github_service.set_token(token)
    result = github_service.test_connection()
    
    return jsonify(result)

@github_integration.route('/api/github/organizations', methods=['POST'])
def get_organizations():
    """Get user's GitHub organizations"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({"success": False, "error": "GitHub token is required"})
    
    github_service.set_token(token)
    result = github_service.list_organizations()
    
    return jsonify(result)

@github_integration.route('/api/github/create-repository', methods=['POST'])
def create_repository():
    """Create a new GitHub repository"""
    data = request.get_json()
    token = data.get('token')
    repo_config = data.get('repository', {})
    
    if not token:
        return jsonify({"success": False, "error": "GitHub token is required"})
    
    if not repo_config.get('name'):
        return jsonify({"success": False, "error": "Repository name is required"})
    
    github_service.set_token(token)
    result = github_service.create_repository(repo_config)
    
    return jsonify(result)

@github_integration.route('/api/github/sync-project', methods=['POST'])
def sync_project():
    """Sync current project to GitHub repository"""
    data = request.get_json()
    token = data.get('token')
    owner = data.get('owner')
    repo = data.get('repository')
    
    if not all([token, owner, repo]):
        return jsonify({
            "success": False, 
            "error": "Token, owner, and repository name are required"
        })
    
    github_service.set_token(token)
    result = github_service.sync_project_files(owner, repo)
    
    return jsonify({
        "success": True,
        "sync_results": result
    })

@github_integration.route('/api/github/project-status')
def get_project_status():
    """Get current project status for GitHub sync"""
    try:
        # Analyze current project
        stats = {
            "total_files": 0,
            "total_size": 0,
            "file_types": {},
            "large_files": []
        }
        
        for root, dirs, files in os.walk('.'):
            # Skip hidden and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.startswith('.') and file != '.gitignore':
                    continue
                
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    stats["total_files"] += 1
                    stats["total_size"] += file_size
                    
                    # Track file types
                    ext = os.path.splitext(file)[1].lower()
                    if ext:
                        stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
                    
                    # Track large files
                    if file_size > 1024 * 1024:  # Files larger than 1MB
                        stats["large_files"].append({
                            "path": os.path.relpath(file_path, '.'),
                            "size_mb": round(file_size / (1024 * 1024), 2)
                        })
                
                except:
                    continue
        
        return jsonify({
            "success": True,
            "project_stats": stats,
            "ready_for_sync": stats["total_files"] > 0
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error analyzing project: {str(e)}"
        })

def register_github_integration(app):
    """Register GitHub integration with Flask app"""
    app.register_blueprint(github_integration)
    print("GitHub Integration Wizard registered successfully")