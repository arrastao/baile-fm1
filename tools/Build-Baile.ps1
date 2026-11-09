# SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception
# Reuse the pinned official build/checks. Only the documented storage partition
# and output label differ. SDK files and boot resources are never rewritten.
[CmdletBinding()]
param([string]$Toolchain = $env:FM1_PI32_TOOLCHAIN)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$sdk = Join-Path $root 'sdk'
$manifest = Get-Content (Join-Path $sdk 'manifest.json') -Raw | ConvertFrom-Json
foreach ($entry in $manifest.files.PSObject.Properties) {
    $actual = (Get-FileHash (Join-Path $root $entry.Name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -cne $entry.Value) { throw "SDK integrity failure: $($entry.Name)" }
}
$config = Get-Content (Join-Path $root 'baile-layout.json') -Raw | ConvertFrom-Json
if ($config.user_bytes -ne 405504) { throw 'Unsupported BAILE partition configuration.' }
$work = Join-Path $root 'build/baile-tools'
[IO.Directory]::CreateDirectory($work) | Out-Null
$utf8 = New-Object Text.UTF8Encoding $false
$package = [IO.File]::ReadAllText((Join-Path $sdk 'Package.cs'))
if (!$package.Contains('UserSize = 536576')) { throw 'Unexpected upstream packager.' }
$package = $package.Replace('UserSize = 536576','UserSize = 405504').Replace('class Package','class BailePackage')
[IO.File]::WriteAllText((Join-Path $work 'BailePackage.cs'), $package, $utf8)
$script = [IO.File]::ReadAllText((Join-Path $sdk 'Build.ps1'))
function Replace-Once([string]$text,[string]$before,[string]$after) {
    if (($text.Split(@($before),[StringSplitOptions]::None)).Count -ne 2) { throw "Upstream build changed: $before" }
    return $text.Replace($before,$after)
}
$quotedRoot = "'" + $root.Replace("'","''") + "'"
$script = Replace-Once $script '$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ''..''))' ('$root = '+$quotedRoot)
$script = Replace-Once $script '$sdk = $PSScriptRoot' '$sdk = Join-Path $root ''sdk'''
$script = Replace-Once $script 'user_bytes=536576' 'user_bytes=405504'
$script = Replace-Once $script '(V(?:0[1-9]|[1-9][0-9]{1,2}))' '(BAILE 0\.4-dev)'
$script = Replace-Once $script "Add-Type -Path (Join-Path `$sdk 'Package.cs')" "Add-Type -Path (Join-Path `$root 'build/baile-tools/BailePackage.cs')"
$script = Replace-Once $script '[FM1.Package]::Create' '[FM1.BailePackage]::Create'
# Retain the public BLE entry points required by the upstream verifier, even
# though the small BAILE panel has no Bluetooth configuration page.
$roots = '$link += @(''--undefined=fm1_ble_scan'',''--undefined=fm1_ble_connect'',''--undefined=fm1_ble_disconnect'',''--undefined=fm1_ble_get_status'',''--undefined=fm1_ble_get_device'',''--undefined=fm1_bluetooth_get_status'')'
$script = Replace-Once $script '    Run (Join-Path $bin ''pi32v2-ld.exe'') $link' ($roots + "`n" + '    Run (Join-Path $bin ''pi32v2-ld.exe'') $link')
$script = $script.Replace('FM1_OFFICIAL_OPEN.fwsc','BAILE-0.4-dev.fwsc')
[IO.File]::WriteAllText((Join-Path $work 'Build.ps1'), $script, $utf8)
& (Join-Path $work 'Build.ps1') -FirmwareOnly -Toolchain $Toolchain
