# Append a well-formed row to a show-me-your-work decision log (TSV).
# Windows counterpart of log.sh; same arguments, same output.
# Usage: log.ps1 <logfile> <phase> <decision> <why> <evidence> <result>
param(
  [Parameter(Position = 0)][string]$LogFile,
  [Parameter(Position = 1)][string]$Phase,
  [Parameter(Position = 2)][string]$Decision,
  [Parameter(Position = 3)][string]$Why,
  [Parameter(Position = 4)][string]$Evidence,
  [Parameter(Position = 5)][string]$Result
)
$ErrorActionPreference = 'Stop'

if ($PSBoundParameters.Count -ne 6) {
  [Console]::Error.WriteLine('usage: log.ps1 <logfile> <phase> <decision> <why> <evidence> <result>')
  exit 1
}

$dir = Split-Path -Parent $LogFile
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

# Strip tabs/newlines/CR so cells stay on one line, and prefix any cell whose
# first char a spreadsheet would parse as a formula (=, +, -, @) with a single
# quote: evidence can hold attacker-controlled text (PR titles, filenames).
function Clean([string]$Value) {
  $v = $Value -replace "[`t`r`n]", ' '
  if ($v -match '^[=+\-@]') { return "'" + $v }
  return $v
}

$utf8 = New-Object System.Text.UTF8Encoding($false)
if (-not (Test-Path $LogFile) -or (Get-Item $LogFile).Length -eq 0) {
  [System.IO.File]::AppendAllText($LogFile, "ts`tphase`tdecision`twhy`tevidence`tresult`n", $utf8)
}
$ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$row = @($ts, (Clean $Phase), (Clean $Decision), (Clean $Why), (Clean $Evidence), (Clean $Result)) -join "`t"
[System.IO.File]::AppendAllText($LogFile, $row + "`n", $utf8)
