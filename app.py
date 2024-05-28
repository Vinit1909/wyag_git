import os
import shutil
from flask import Flask, render_template, request, redirect, url_for, flash
import subprocess
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Absolute path to the wyag script
WYAG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wyag')
REPOS_DIR = 'repos'  # Directory to store multiple repositories

# Ensure the repos directory exists
if not os.path.exists(REPOS_DIR):
    os.makedirs(REPOS_DIR)
CURRENT_REPO = None

def list_repos():
    """List all directories in REPOS_DIR excluding hidden files."""
    try:
        repos = [repo for repo in os.listdir(REPOS_DIR) if os.path.isdir(os.path.join(REPOS_DIR, repo)) and not repo.startswith('.')]
        return repos
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        return []

@app.route('/')
def home():
    try:
        repos = list_repos()
        if not repos:
            flash("No repositories found. Please initialize a new repository.", "warning")
        return render_template('home.html', repos=repos)
    except Exception as e:
        logger.error(f"Error in home route: {e}")
        return "Internal Server Error", 500

@app.route('/init', methods=['POST'])
def init_repo():
    try:
        global CURRENT_REPO
        repo_name = request.form['repo_name']
        repo_path = os.path.join(REPOS_DIR, repo_name)
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
            CURRENT_REPO = repo_path
            output = run_wyag_command(['init'])
            flash(f"Repository '{repo_name}' initialized successfully.", "success")
        else:
            flash("Repository already exists.", "error")
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Error in init_repo: {e}")
        return "Internal Server Error", 500

@app.route('/switch', methods=['POST'])
def switch_repo():
    try:
        global CURRENT_REPO
        repo_name = request.form['repo_name']
        repo_path = os.path.join(REPOS_DIR, repo_name)
        if os.path.exists(repo_path):
            CURRENT_REPO = repo_path
            flash(f"Switched to repository '{repo_name}'.", "success")
            return redirect(url_for('repo'))
        else:
            flash("Repository does not exist.", "error")
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Error in switch_repo: {e}")
        return "Internal Server Error", 500

@app.route('/delete_repo', methods=['POST'])
def delete_repo():
    try:
        global CURRENT_REPO
        repo_name = request.form['repo_name']
        repo_path = os.path.join(REPOS_DIR, repo_name)
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            flash(f"Repository '{repo_name}' deleted.", "success")
            if CURRENT_REPO == repo_path:
                CURRENT_REPO = None
        else:
            flash("Repository does not exist.", "error")
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Error in delete_repo: {e}")
        return "Internal Server Error", 500

def get_repo_file_tree(repo_path):
    try:
        file_tree = []
        for root, dirs, files in os.walk(repo_path):
            root_path = os.path.relpath(root, repo_path)
            root_dict = {
                'path': root_path,
                'dirs': dirs,
                'files': files
            }
            file_tree.append(root_dict)
        return file_tree
    except Exception as e:
        logger.error(f"Error in get_repo_file_tree: {e}")
        return []

def list_user_files(repo_path):
    try:
        user_files = []
        for root, dirs, files in os.walk(repo_path):
            if '.git' in dirs:
                dirs.remove('.git')  # exclude .git directory
            for file in files:
                if file != '.DS_Store':  # exclude .DS_Store file
                    file_path = os.path.relpath(os.path.join(root, file), repo_path)
                    user_files.append(file_path)
        return user_files
    except Exception as e:
        logger.error(f"Error in list_user_files: {e}")
        return []

@app.route('/repo')
def repo():
    try:
        if CURRENT_REPO:
            status_output = run_wyag_command(['status'])
            log_output = run_wyag_command(['log'])
            user_files = list_user_files(CURRENT_REPO)
        else:
            status_output = log_output = "No repository selected."
            user_files = []
        return render_template('repo.html', status_output=status_output, log_output=log_output, current_repo=CURRENT_REPO, repos=list_repos(), user_files=user_files)
    except Exception as e:
        logger.error(f"Error in repo route: {e}")
        return "Internal Server Error", 500

@app.route('/add', methods=['POST'])
def add_file():
    try:
        filename = request.form['filename']
        content = request.form['content']
        filepath = os.path.join(CURRENT_REPO, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        output = run_wyag_command(['add', filename])
        flash(f"File '{filename}' added.", "success")
        return redirect(url_for('repo'))
    except Exception as e:
        logger.error(f"Error in add_file: {e}")
        return "Internal Server Error", 500

@app.route('/commit', methods=['POST'])
def commit():
    try:
        message = request.form['message']
        run_wyag_command(['add', '.'])  # Ensure all changes are staged before committing
        output = run_wyag_command(['commit', '-m', message])
        flash(f"Commit '{message}' created.", "success")
        return redirect(url_for('repo'))
    except Exception as e:
        logger.error(f"Error in commit: {e}")
        return "Internal Server Error", 500

@app.route('/status', methods=['GET'])
def status():
    try:
        status_output = run_wyag_command(['status'])
        log_output = run_wyag_command(['log'])
        return render_template('repo.html', status_output=status_output, log_output=log_output, current_repo=CURRENT_REPO, repos=list_repos())
    except Exception as e:
        logger.error(f"Error in status: {e}")
        return "Internal Server Error", 500

@app.route('/log', methods=['GET'])
def log():
    try:
        log_output = run_wyag_command(['log'])
        return render_template('repo.html', log_output=log_output, current_repo=CURRENT_REPO, repos=list_repos())
    except Exception as e:
        logger.error(f"Error in log: {e}")
        return "Internal Server Error", 500

@app.route('/read', methods=['POST'])
def read_file():
    try:
        filename = request.form['filename']
        sha = get_file_sha(filename)
        if sha:
            file_content = run_wyag_command(['cat-file', 'blob', sha])
            flash(f"Content of '{filename}' read successfully.", "success")
        else:
            file_content = f"File '{filename}' not found."
            flash(file_content, "error")
        status_output = run_wyag_command(['status'])
        log_output = run_wyag_command(['log'])
        return render_template('repo.html', file_content=file_content, status_output=status_output, log_output=log_output, current_repo=CURRENT_REPO, repos=list_repos())
    except Exception as e:
        logger.error(f"Error in read_file: {e}")
        return "Internal Server Error", 500

@app.route('/delete_file', methods=['POST'])
def delete_file():
    try:
        filename = request.form['filename']
        filepath = os.path.join(CURRENT_REPO, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            run_wyag_command(['rm', filename])
            flash(f"File '{filename}' deleted.", "success")
        else:
            flash("File does not exist.", "error")
        return redirect(url_for('repo'))
    except Exception as e:
        logger.error(f"Error in delete_file: {e}")
        return "Internal Server Error", 500

@app.route('/merge', methods=['POST'])
def merge():
    try:
        branch = request.form['branch']
        output = run_wyag_command(['merge', branch])
        flash(output, "success")
        return redirect(url_for('repo'))
    except Exception as e:
        logger.error(f"Error in merge: {e}")
        return "Internal Server Error", 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('repo'))
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('repo'))
        if file:
            filepath = os.path.join(CURRENT_REPO, file.filename)
            file.save(filepath)
            run_wyag_command(['add', file.filename])
            flash(f"File '{file.filename}' uploaded and added.", 'success')
            return redirect(url_for('repo'))
    except Exception as e:
        logger.error(f"Error in upload_file: {e}")
        return "Internal Server Error", 500

@app.route('/modify_file', methods=['POST', 'GET'])
def modify_file():
    try:
        if request.method == 'POST':
            filename = request.form['filename']
            new_content = request.form['new_content']
            filepath = os.path.join(CURRENT_REPO, filename)
            if os.path.exists(filepath):
                with open(filepath, 'a') as f:
                    f.write('\n' + new_content)  # Add a newline character before appending the new content
                run_wyag_command(['add', filename])
                flash(f"File '{filename}' modified.", 'success')
            else:
                flash("File does not exist.", 'error')
            return redirect(url_for('repo'))
        else:
            filename = request.args.get('filename')
            if filename:
                filepath = os.path.join(CURRENT_REPO, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        current_content = f.read()
                else:
                    current_content = "File does not exist."
            else:
                current_content = ""
            return render_template('modify_file.html', current_content=current_content, filename=filename)
    except Exception as e:
        logger.error(f"Error in modify_file: {e}")
        return "Internal Server Error", 500

def run_wyag_command(command):
    if not CURRENT_REPO:
        return "No repository selected."
    try:
        result = subprocess.run([WYAG_PATH] + command, cwd=CURRENT_REPO, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info(f"Command: {command}\nOutput: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command: {command}\nError: {e.stderr}")
        return e.stderr

def get_file_sha(filename):
    try:
        result = subprocess.run([WYAG_PATH, 'hash-object', filename], cwd=CURRENT_REPO, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting SHA for file {filename}: {e.stderr}")
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
