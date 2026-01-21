import json
import re
import os
import subprocess
import datetime
import shutil
import sys

# --- Cấu hình ---
FILES = {
    "package.json": "Frontend/package.json",
    "tauri.conf.json": "Frontend/src-tauri/tauri.conf.json",
    "Cargo.toml": "Frontend/src-tauri/Cargo.toml",
    "version.py": "Backend/app/version.py"
}

# Đường dẫn build output của Tauri (trên Windows)
TAURI_BUNDLE_DIR = os.path.join("Frontend", "src-tauri", "target", "release", "bundle", "nsis")
UPDATER_JSON_PATH = "latest.json"

def run_command(command, cwd=None, env=None):
    """Chạy lệnh shell và in ra output."""
    print(f"🔹 Executing: {command}")
    try:
        # Nếu không truyền env riêng, dùng os.environ mặc định
        # Nếu có truyền, subprocess sẽ dùng cái đó
        run_env = env if env else os.environ
        subprocess.check_call(command, shell=True, cwd=cwd, env=run_env)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {command}")
        sys.exit(1)

def update_json(file_path, new_version):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['version'] = new_version
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Updated {file_path}")

def update_toml(file_path, new_version):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'^version = ".*?"', f'version = "{new_version}"', content, flags=re.MULTILINE)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Updated {file_path}")

def update_python(file_path, new_version):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'__version__ = ".*?"', f'__version__ = "{new_version}"', content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Updated {file_path}")

def build_app():
    """Build app bằng Tauri CLI."""
    print("\n🔨 Building application...")
    
    key_path = os.path.join("Frontend", "src-tauri", "tauri.key")
    
    # Ưu tiên đọc từ file tauri.key nếu có (để override biến môi trường cũ có thể bị sai)
    if os.path.exists(key_path):
        print(f"🔹 Loading private key from {key_path}...")
        with open(key_path, 'r') as f:
            os.environ["TAURI_SIGNING_PRIVATE_KEY"] = f.read().strip()
        
        if "TAURI_SIGNING_PRIVATE_KEY_PASSWORD" in os.environ:
            del os.environ["TAURI_SIGNING_PRIVATE_KEY_PASSWORD"]
        # Set mật khẩu cố định 123456 theo yêu cầu
        os.environ["TAURI_SIGNING_PRIVATE_KEY_PASSWORD"] = "123456"
            
    # Nếu không có file, mới check biến môi trường
    elif not os.environ.get("TAURI_SIGNING_PRIVATE_KEY"):
        print("⚠️  WARNING: TAURI_SIGNING_PRIVATE_KEY is not set and tauri.key file not found.")
        print("   Updater signature might fail!")
    
    # Chạy lệnh build từ thư mục Frontend
    # Lưu ý: os.environ đã được update ở trên sẽ tự động truyền vào subprocess
    # Tuy nhiên explicit passing vẫn an toàn hơn
    run_command("npm run tauri build", cwd="Frontend", env=os.environ)

def generate_updater_json(version, notes):
    """Tạo file updater.json từ kết quả build."""
    print("\n📝 Generating updater.json...")

    # Tìm file build .zip và .sig
    # Tauri v2 updater thường dùng file zip đính kèm signature
    # Hoặc .msi.zip / .nsis.zip
    
    # Giả định Windows NSIS build
    if not os.path.exists(TAURI_BUNDLE_DIR):
        print(f"❌ Bundle dir not found: {TAURI_BUNDLE_DIR}")
        return

    files = os.listdir(TAURI_BUNDLE_DIR)
    
    # Tìm file cài đặt và file signature
    # Pattern: setup file .exe, và file signature .sig (nếu có)
    # Tuy nhiên, Tauri updater v1/v2 có logic khác nhau.
    # Với Tauri v1: cần pub signature.
    # Với Tauri v2 plugin updater: Cấu trúc json có thể khác.
    # Dưới đây là format chuẩn cho Tauri Updater.

    # Tìm file cài đặt (.exe) và file signature (.sig)
    # Với config hiện tại, Tauri tạo ra ...-setup.exe và ...-setup.exe.sig
    
    installer_file = None
    sig_file = None
    
    for f in files:
        if f.endswith("-setup.exe") and f"_{version}_" in f:
            installer_file = f
        elif f.endswith("-setup.exe.sig") and f"_{version}_" in f:
            sig_file = f
            
    if not installer_file or not sig_file:
        print("❌ Could not find ...-setup.exe or ...-setup.exe.sig file in bundle directory.")
        print(f"   Files found: {files}")
        return

    # Đọc signature content
    with open(os.path.join(TAURI_BUNDLE_DIR, sig_file), 'r') as f:
        signature = f.read().strip()
        
    # Tạo URL download (Sửa lại theo repo của bạn)
    # Format: https://github.com/USERNAME/REPO/releases/download/vVERSION/FILENAME
    repo_url = "https://github.com/QHanh/INS_Automation_Platform/releases/download"
    download_url = f"{repo_url}/v{version}/{installer_file}"
    
    updater_data = {
        "version": f"v{version}",
        "notes": notes,
        "pub_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platforms": {
            "windows-x86_64": {
                "signature": signature,
                "url": download_url
            }
        }
    }
    
    with open(UPDATER_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(updater_data, f, indent=2)
        
    print(f"✅ Created {UPDATER_JSON_PATH}")

def git_tasks(version):
    """Commit, tag và push."""
    print("\n📦 Helper Git Commands (Run manually if checking locally):")
    cmds = [
        "git add .",
        f'git commit -m "chore(release): v{version}"',
        f'git tag v{version}',
        "git push",
        f"git push origin v{version}"
    ]
    for cmd in cmds:
        print(f"  {cmd}")

    do_git = input("\nDo you want to run these git commands now? (y/n): ").strip().lower()
    if do_git == 'y':
        try:
            for cmd in cmds:
                run_command(cmd)
            print("✅ Git Release Pushed.")
        except Exception:
            print("❌ Git operations failed.")

def main():
    print("🚀 INS Automation Platform - Release Manager")
    
    # 1. Ask for version
    # (Có thể đọc từ package.json, nhưng lười thì nhập tay hoặc cải tiến sau)
    
    new_version = input("Enter new version (e.g., 0.1.0): ").strip()
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("❌ Invalid version format. Use x.y.z")
        return

    notes = input("Enter release notes: ").strip()

    root_dir = os.getcwd()

    # 2. Bump Versions
    update_json(os.path.join(root_dir, FILES["package.json"]), new_version)
    update_json(os.path.join(root_dir, FILES["tauri.conf.json"]), new_version)
    update_toml(os.path.join(root_dir, FILES["Cargo.toml"]), new_version)
    update_python(os.path.join(root_dir, FILES["version.py"]), new_version)
    
    # 3. Build App
    build_app()
    
    # 4. Generate Updater JSON
    generate_updater_json(new_version, notes)
    
    # 5. Git Tagging
    git_tasks(new_version)
    
    print("\n✨ Release Process Finished!")
    print(f"👉 Go to GitHub Releases and upload the files from: {TAURI_BUNDLE_DIR}")
    print(f"👉 Also upload/update 'updater.json' to the location: https://github.com/QHanh/INS_Automation_Platform/releases/latest/download/latest.json (or wherever you host it)")

if __name__ == "__main__":
    main()
