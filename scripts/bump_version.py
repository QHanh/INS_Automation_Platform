import json
import re
import os

# Cấu hình các file cần update version
FILES = {
    "package.json": "Frontend/package.json",
    "tauri.conf.json": "Frontend/src-tauri/tauri.conf.json",
    "Cargo.toml": "Frontend/src-tauri/Cargo.toml",
    "version.py": "Backend/app/version.py"
}

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
    
    # Update version = "x.y.z"
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

def main():
    print("🚀 INS Automation Platform - Version Bumper")
    new_version = input("Enter new version (e.g., 0.2.0): ").strip()
    
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("❌ Invalid version format. Use x.y.z")
        return

    root_dir = os.getcwd()
    
    # Update package.json
    update_json(os.path.join(root_dir, FILES["package.json"]), new_version)
    
    # Update tauri.conf.json
    update_json(os.path.join(root_dir, FILES["tauri.conf.json"]), new_version)
    
    # Update Cargo.toml
    update_toml(os.path.join(root_dir, FILES["Cargo.toml"]), new_version)
    
    # Update version.py
    update_python(os.path.join(root_dir, FILES["version.py"]), new_version)
    
    print(f"\n✨ Successfully bumped version to {new_version}!")
    print("\nNext steps:")
    print(f"1. git commit -am \"Release v{new_version}\"")
    print(f"2. git push")
    print(f"3. git tag v{new_version}")
    print(f"4. git push origin v{new_version}")

if __name__ == "__main__":
    main()
