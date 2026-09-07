# winget 提交说明

VoicePort 通过 Windows Package Manager（winget）分发。需要把 `manifests/` 目录提交到
[microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs) 仓库（PR 方式）。

## 提交步骤

1. 在 GitHub 创建 release，上传 `VoicePort.exe`，得到下载 URL 和 SHA256。
2. 把下面的 `{URL}` 和 `{SHA256}` 替换成实际值。
3. fork winget-pkgs，把 `manifests/` 下的目录放到 `manifests/v/VoicePort/VoicePort/<版本>/`。
4. 提 PR，等待 CI 校验 + 合并。

## 计算 SHA256

```powershell
Get-FileHash .\dist\VoicePort.exe -Algorithm SHA256
```

## manifest 文件位置

- `manifests/VoicePort.yaml` — 版本元信息
- `manifests/VoicePort.installer.yaml` — 安装器（portable）
- `manifests/VoicePort.locale.zh-CN.yaml` — 本地化
