param([ValidateSet('default','synesthesia','game')][string]$Skin='default')
$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot "assets/official/$Skin/native.png"
$validation=Get-Content -LiteralPath (Join-Path $PSScriptRoot "assets/official/$Skin/validation.json") -Raw | ConvertFrom-Json
$hash=(Get-FileHash -LiteralPath $source).Hash.ToLowerInvariant()
if(-not $validation.ok -or $validation.sha256 -ne $hash){throw '素材检查结果与文件不一致。'}
$codexDirectory=if($env:CODEX_HOME){$env:CODEX_HOME}else{Join-Path $env:USERPROFILE '.codex'}
$destination=Join-Path $codexDirectory 'pets/irene-lantern-reviewer'
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$installed=Join-Path $destination 'spritesheet.png'
Copy-Item -LiteralPath $source -Destination $installed -Force
$label=@{default='默认';synesthesia='飞羽';game='至高判决'}[$Skin]
$metadata=@{displayName='艾丽妮 · 提灯审阅员';description="2.0.0 · 官方基建小人 · $label";spriteVersionNumber=2;spritesheetPath='spritesheet.png'}
[IO.File]::WriteAllText((Join-Path $destination 'pet.json'),($metadata|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
if((Get-FileHash -LiteralPath $installed).Hash.ToLowerInvariant() -ne $hash){throw '安装文件不一致。'}
Write-Output "已安装艾丽妮 2.0.0 官方小人：$label。请在 Codex 宠物设置中刷新，再重新选择艾丽妮。"
