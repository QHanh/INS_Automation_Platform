# Setup Guide: Auto-Update System

Hướng dẫn thiết lập hệ thống auto-update cho INS Automation Platform.

## 1. Generate Signing Keys

Mở terminal trong thư mục `Frontend` và chạy:

```bash
npm run tauri signer generate -- -w ~/.tauri/ins-automation.key
```

**Kết quả:**
- Private key: `~/.tauri/ins-automation.key` (GIỮ BÍ MẬT!)
- Public key: Sẽ hiển thị trên terminal → copy để dùng

## 2. Cập nhật Public Key

Mở file `Frontend/src-tauri/tauri.conf.json` và thay thế:

```json
"pubkey": "REPLACE_WITH_YOUR_PUBLIC_KEY"
```

Bằng public key bạn vừa generate.

## 3. Cấu hình GitHub Secrets

Vào **Settings → Secrets and variables → Actions** trong repo GitHub, thêm:

| Secret Name | Value |
|-------------|-------|
| `TAURI_SIGNING_PRIVATE_KEY` | Nội dung file `ins-automation.key` |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Password khi generate (nếu có) |

## 4. Tạo Release

### Cách 1: Manual (Web)
1. Vào repo GitHub → **Releases** → **Create a new release**
2. Tag version: `v0.1.0`
3. Upload files:
   - `ins-automation-platform_0.1.0_x64-setup.exe`
   - `latest.json`

### Cách 2: Automatic (GitHub Actions)
1. Commit code
2. Create tag: `git tag v0.2.0`
3. Push: `git push origin v0.2.0`
4. GitHub Actions sẽ tự build và release

## 5. Format của latest.json

```json
{
  "version": "0.2.0",
  "notes": "Bug fixes and improvements",
  "pub_date": "2024-12-22T00:00:00Z",
  "platforms": {
    "windows-x86_64": {
      "signature": "SIGNATURE_FROM_SIG_FILE",
      "url": "https://github.com/QHanh/INS_Automation_Platform/releases/download/v0.2.0/ins-automation-platform_0.2.0_x64-setup.nsis.zip"
    }
  }
}
```

## 6. Lưu ý cho Private Repo

Vì repo của bạn là **private**, users cần token để download:

1. Tạo Personal Access Token với permission `repo`
2. Thêm vào `UpdateService.ts`:

```typescript
const response = await fetch(GITHUB_RELEASES_API, {
  headers: {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': 'token YOUR_GITHUB_TOKEN'
  }
});
```

**Hoặc** chuyển repo thành public (khuyến nghị cho open-source tools).
