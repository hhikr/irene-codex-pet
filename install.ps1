param([ValidateSet('walk','run')][string]$Movement='walk')
$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot "assets/native/$Movement.png"
$validation=Get-Content -LiteralPath (Join-Path $PSScriptRoot "assets/native/$Movement-validation.json") -Raw | ConvertFrom-Json
$hash=(Get-FileHash -LiteralPath $source).Hash.ToLowerInvariant()
if(-not $validation.ok -or $validation.sha256 -ne $hash){throw '素材检查结果与文件不一致。'}
$codexDirectory=if($env:CODEX_HOME){$env:CODEX_HOME}else{Join-Path $env:USERPROFILE '.codex'}
$destination=Join-Path $codexDirectory 'pets/irene-lantern-reviewer'
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$installed=Join-Path $destination 'spritesheet.png'
if((Test-Path -LiteralPath $installed) -and -not(Test-Path -LiteralPath (Join-Path $destination 'spritesheet-before-v4.png'))){Copy-Item -LiteralPath $installed -Destination (Join-Path $destination 'spritesheet-before-v4.png')}
Copy-Item -LiteralPath $source -Destination $installed -Force
$label=if($Movement -eq 'walk'){'慢走'}else{'原跑步'}
$metadata=@{displayName='艾丽妮 · 提灯审阅员';description="第四版 · $label · 睁眼待机、提灯微动回应";spriteVersionNumber=2;spritesheetPath='spritesheet.png'}
[IO.File]::WriteAllText((Join-Path $destination 'pet.json'),($metadata|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
if((Get-FileHash -LiteralPath $installed).Hash.ToLowerInvariant() -ne $hash){throw '安装文件不一致。'}
Write-Output '已更新艾丽妮第四版。请在 Codex 宠物设置中刷新列表，再重新选择艾丽妮。'
