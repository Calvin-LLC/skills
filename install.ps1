param(
  [string]$Source,
  [switch]$Stash
)

$ErrorActionPreference = "Stop"
$RepoSlug = "Calvin-LLC/skills"
$RepoUrl = "https://github.com/$RepoSlug.git"

# SKILLS_HOME points the whole install at another directory (tests).
$UserHome = if ($env:SKILLS_HOME) { $env:SKILLS_HOME } else { $HOME }
$Dest = Join-Path $UserHome ".agents\calvin-skills"

function Invoke-Git {
  & git @args
  if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') failed (exit $LASTEXITCODE)" }
}

function Stop-Install($Message) {
  [Console]::Error.WriteLine($Message)
  exit 1
}

function Remove-Entry($Path) {
  $Item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
  if (-not $Item) { return }
  # Delete a link itself. Remove-Item -Recurse on a junction can reach into its target.
  if ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
    if ($Item.PSIsContainer) { [IO.Directory]::Delete($Path) } else { [IO.File]::Delete($Path) }
  } else {
    Remove-Item -Recurse -Force -LiteralPath $Path
  }
}

function Get-MuseCommand {
  $Cmd = Get-Command muse -CommandType Application, ExternalScript -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $Cmd) { return $null }
  # A test home must never reach the real Muse, so only a muse stub inside it counts.
  if ($env:SKILLS_HOME) {
    $Root = [IO.Path]::GetFullPath($UserHome).TrimEnd('\', '/')
    if (-not [IO.Path]::GetFullPath($Cmd.Source).StartsWith($Root, [StringComparison]::OrdinalIgnoreCase)) { return $null }
  }
  return $Cmd
}

function Invoke-Muse($MuseArgs) {
  $ErrorActionPreference = "Continue"
  $Output = & $Muse.Source @MuseArgs 2>&1 | Out-String
  return [pscustomobject]@{ Code = $LASTEXITCODE; Output = $Output.Trim() }
}

if ($Source) {
  $Source = (Resolve-Path -LiteralPath $Source).Path
  & git -C $Source rev-parse --verify --quiet refs/heads/main *> $null
  if ($LASTEXITCODE -ne 0) { Stop-Install "Source $Source is not a git checkout with a main branch." }
}

New-Item -ItemType Directory -Force -Path (Join-Path $UserHome ".agents\skills") | Out-Null

if (Test-Path (Join-Path $Dest ".git")) {
  if ($Source) {
    $Dirty = @(git -C $Dest status --porcelain | Where-Object { $_ })
    if ($Dirty.Count -gt 0 -and $Stash) {
      $Identity = @()
      & git -C $Dest config user.name *> $null
      if ($LASTEXITCODE -ne 0) { $Identity = @("-c", "user.name=calvin-skills", "-c", "user.email=calvin-skills@localhost") }
      $Stamp = [DateTime]::UtcNow.ToString("yyyy-MM-dd HH:mm:ss") + " UTC"
      Invoke-Git @Identity -C $Dest stash push --include-untracked -m "calvin-skills install $Stamp"
      Write-Host "Stashed $($Dirty.Count) uncommitted paths from $Dest. Restore with: git -C `"$Dest`" stash list"
    } elseif ($Dirty.Count -gt 0) {
      Stop-Install ("Refusing to update $Dest. It has $($Dirty.Count) uncommitted paths, so it no longer matches any commit.`n" +
        "Rerun with -Stash to set them aside in a git stash, which deletes nothing:`n" +
        "  powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Source `"$Source`" -Stash")
    }
    Invoke-Git -C $Dest fetch --quiet $Source main
    & git -C $Dest merge-base --is-ancestor HEAD FETCH_HEAD
    if ($LASTEXITCODE -ne 0) {
      $Old = (& git -C $Dest rev-parse --short HEAD).Trim()
      Write-Host "Clone was at $Old, which the source's main no longer contains (amended or rebased). Moving it; $Old stays in the clone's reflog."
    }
    # The tree is clean here, and --keep refuses to move over a local change.
    Invoke-Git -C $Dest reset --quiet --keep FETCH_HEAD
  } else {
    Invoke-Git -C $Dest pull --ff-only
  }
} else {
  if (Test-Path $Dest) { Remove-Entry $Dest }
  if ($Source) {
    Invoke-Git clone --branch main $Source $Dest
    Invoke-Git -C $Dest remote set-url origin $RepoUrl
  } elseif (Get-Command gh -ErrorAction SilentlyContinue) {
    gh repo clone $RepoSlug $Dest -- --depth 1
  } else {
    Invoke-Git clone --depth 1 $RepoUrl $Dest
  }
}

if ($Source) {
  Invoke-Git -C $Source config core.hooksPath scripts/hooks
}

$TargetRoots = @(
  (Join-Path $UserHome ".agents\skills"),
  (Join-Path $UserHome ".claude\skills"),
  (Join-Path $UserHome ".pi\agent\skills"),
  (Join-Path $UserHome ".hermes\skills"),
  (Join-Path $UserHome ".config\muse\skills"),
  (Join-Path $UserHome ".codex\skills")
)

$SkillDirs = @(Get-ChildItem -Path (Join-Path $Dest "skills") -Directory | Where-Object {
  Test-Path (Join-Path $_.FullName "SKILL.md")
})
$SkillsDir = [IO.Path]::GetFullPath((Join-Path $Dest "skills")) + "\"

function Test-RemovedSkill($Path) {
  $Full = "$Path" -replace '^\\\\\?\\', ''
  return $Full.StartsWith($SkillsDir, [StringComparison]::OrdinalIgnoreCase) -and -not (Test-Path -LiteralPath $Full)
}

$MuseSkills = Join-Path $UserHome ".config\muse\skills"
$MuseManaged = Test-Path (Join-Path $MuseSkills ".muse")

foreach ($Root in $TargetRoots) {
  if ($MuseManaged -and $Root -eq $MuseSkills) {
    Write-Host "Muse Code manages its own copies -> $Root"
    continue
  }
  New-Item -ItemType Directory -Force -Path $Root | Out-Null
  foreach ($Skill in $SkillDirs) {
    $LinkPath = Join-Path $Root $Skill.Name
    Remove-Entry $LinkPath
    New-Item -ItemType Junction -Path $LinkPath -Target $Skill.FullName | Out-Null
  }
  foreach ($Entry in Get-ChildItem -LiteralPath $Root -Force -Attributes ReparsePoint) {
    if (Test-RemovedSkill ($Entry.Target | Select-Object -First 1)) { Remove-Entry $Entry.FullName }
  }
  Write-Host "Linked all skills -> $Root"
}

$OmpSkills = Join-Path $UserHome ".omp\agent\skills"
if (Test-Path -LiteralPath $OmpSkills) {
  foreach ($Entry in Get-ChildItem -LiteralPath $OmpSkills -Force -Attributes ReparsePoint) {
    $Target = "$($Entry.Target | Select-Object -First 1)" -replace '^\\\\\?\\', ''
    if ($Target.StartsWith($SkillsDir, [StringComparison]::OrdinalIgnoreCase)) { Remove-Entry $Entry.FullName }
  }
  if (-not (Get-ChildItem -LiteralPath $OmpSkills -Force)) { Remove-Item -LiteralPath $OmpSkills }
}
Write-Host "OMP loads skills from its plugin: omp plugin install github:Calvin-LLC/skills, then omp plugin upgrade @calvin-llc/skills after each push"

# Muse Code copies skills into its own folder and tracks them in .muse; only muse may change that folder.
$Muse = Get-MuseCommand
if ($Muse) {
  if ($MuseManaged) {
    foreach ($Skill in $SkillDirs) {
      if (Test-Path (Join-Path $MuseSkills $Skill.Name)) {
        $MuseArgs = @("skills", "update", $Skill.Name)
      } else {
        $MuseArgs = @("skills", "install", $Skill.FullName, "--scope", "user")
      }
      $Result = Invoke-Muse $MuseArgs
      if ($Result.Code -ne 0) { Write-Warning "muse $($MuseArgs -join ' ') exited $($Result.Code): $($Result.Output)" }
    }
    $LockPath = Join-Path $MuseSkills ".muse\lock.json"
    $Lock = if (Test-Path -LiteralPath $LockPath) { Get-Content -Raw -LiteralPath $LockPath | ConvertFrom-Json }
    if ($Lock.skills) {
      foreach ($Entry in $Lock.skills.PSObject.Properties) {
        if (-not (Test-RemovedSkill $Entry.Value.source.path)) { continue }
        $Result = Invoke-Muse @("skills", "uninstall", $Entry.Name)
        if ($Result.Code -ne 0) { Write-Warning "muse skills uninstall $($Entry.Name) exited $($Result.Code): $($Result.Output)" }
      }
    }
    Write-Host "Updated Muse Code skills with muse"
  }
  foreach ($Skill in $SkillDirs) {
    Invoke-Muse @("skills", "enable", $Skill.Name, "--scope", "user") | Out-Null
  }
  Write-Host "Enabled all skills in Muse Code"
} elseif ($MuseManaged) {
  Write-Host "Muse Code skills in $MuseSkills are managed by muse and muse is not on PATH. Left unchanged. Run this installer again where muse is available."
}

if (Test-Path (Join-Path $Dest "SOUL.md")) {
  $SoulSource = Join-Path $Dest "SOUL.md"
  # OMP reads RULES.md, in main sessions and subagents, and Muse Code reads AGENTS.md. Neither reads SOUL.md.
  $SoulLinks = @(
    (Join-Path $UserHome ".pi\agent\SOUL.md"),
    (Join-Path $UserHome ".hermes\SOUL.md"),
    (Join-Path $UserHome ".agents\SOUL.md"),
    (Join-Path $UserHome ".omp\agent\RULES.md"),
    (Join-Path $UserHome ".config\muse\AGENTS.md")
  )
  foreach ($SoulLink in $SoulLinks) {
    $SRoot = Split-Path -Parent $SoulLink
    if (-not (Test-Path $SRoot)) { New-Item -ItemType Directory -Force -Path $SRoot | Out-Null }
    Remove-Entry $SoulLink
    # A symlink follows git rewriting the file; a hard link does not. Hard link only without symlink rights.
    try {
      New-Item -ItemType SymbolicLink -Path $SoulLink -Target $SoulSource | Out-Null
    } catch {
      New-Item -ItemType HardLink -Path $SoulLink -Target $SoulSource | Out-Null
    }
    Write-Host "Linked SOUL.md -> $SoulLink"
  }
}

$OmpRules = Join-Path $UserHome ".omp\agent\rules"
$RulesDir = [IO.Path]::GetFullPath((Join-Path $Dest "rules")) + "\"
New-Item -ItemType Directory -Force -Path $OmpRules | Out-Null
if (Test-Path -LiteralPath $RulesDir) {
  foreach ($Rule in Get-ChildItem -LiteralPath $RulesDir -Filter "*.md" -File) {
    $RuleLink = Join-Path $OmpRules $Rule.Name
    Remove-Entry $RuleLink
    try {
      New-Item -ItemType SymbolicLink -Path $RuleLink -Target $Rule.FullName | Out-Null
    } catch {
      New-Item -ItemType HardLink -Path $RuleLink -Target $Rule.FullName | Out-Null
    }
  }
}
foreach ($Entry in Get-ChildItem -LiteralPath $OmpRules -Force -Attributes ReparsePoint) {
  $Target = "$($Entry.Target | Select-Object -First 1)" -replace '^\\\\\?\\', ''
  if ($Target.StartsWith($RulesDir, [StringComparison]::OrdinalIgnoreCase) -and -not (Test-Path -LiteralPath $Target)) { Remove-Entry $Entry.FullName }
}
Write-Host "Linked OMP rules -> $OmpRules"

Write-Host "Invoke a skill: Claude Code/Hermes/Muse Code: /<name> | OMP/Pi: /skill:<name> | Codex: `$<name>"
$Head = (& git -C $Dest rev-parse --short HEAD).Trim()
Write-Host "Synced calvin-skills at $Head ($($SkillDirs.Count) skills) -> $Dest"
