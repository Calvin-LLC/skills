$ErrorActionPreference = "Stop"
$RepoSlug = "Calvin-LLC/skills"
$RepoUrl = "https://github.com/$RepoSlug.git"
$Dest = Join-Path $HOME ".agents\calvin-skills"

New-Item -ItemType Directory -Force -Path (Join-Path $HOME ".agents\skills") | Out-Null

if (Test-Path (Join-Path $Dest ".git")) {
  git -C $Dest pull --ff-only
} else {
  if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
  if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh repo clone $RepoSlug $Dest -- --depth 1
  } else {
    git clone --depth 1 $RepoUrl $Dest
  }
}

$TargetRoots = @(
  (Join-Path $HOME ".agents\skills"),
  (Join-Path $HOME ".claude\skills"),
  (Join-Path $HOME ".pi\agent\skills"),
  (Join-Path $HOME ".omp\agent\skills"),
  (Join-Path $HOME ".hermes\skills")
)

$SkillDirs = Get-ChildItem -Path (Join-Path $Dest "skills") -Directory | Where-Object {
  Test-Path (Join-Path $_.FullName "SKILL.md")
}

foreach ($Root in $TargetRoots) {
  New-Item -ItemType Directory -Force -Path $Root | Out-Null
  foreach ($Skill in $SkillDirs) {
    $LinkPath = Join-Path $Root $Skill.Name
    if (Test-Path $LinkPath) { Remove-Item -Recurse -Force $LinkPath }
    New-Item -ItemType Junction -Path $LinkPath -Target $Skill.FullName | Out-Null
  }
  Write-Host "Linked all skills -> $Root"
}

if (Test-Path (Join-Path $Dest "SOUL.md")) {
  $SoulSource = Join-Path $Dest "SOUL.md"
  $SoulRoots = @(
    (Join-Path $HOME ".pi\agent"),
    (Join-Path $HOME ".hermes"),
    (Join-Path $HOME ".omp\agent"),
    (Join-Path $HOME ".agents")
  )
  foreach ($SRoot in $SoulRoots) {
    if (-not (Test-Path $SRoot)) { New-Item -ItemType Directory -Force -Path $SRoot | Out-Null }
    $SoulLink = Join-Path $SRoot "SOUL.md"
    if (Test-Path $SoulLink) { Remove-Item -Force $SoulLink }
    New-Item -ItemType HardLink -Path $SoulLink -Target $SoulSource | Out-Null
    Write-Host "Linked SOUL.md -> $SoulLink"
  }
}
