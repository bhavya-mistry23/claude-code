[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$data = $input | Out-String | ConvertFrom-Json
$model = $data.model.display_name
if (-not $model) { $model = "Claude" }

$pct = $data.context_window.used_percentage
if ($null -eq $pct) { $pct = 0 }
$pct = [int][math]::Floor($pct)

$dir = $data.workspace.current_dir
if (-not $dir) { $dir = $data.cwd }

$branch = $null
if ($data.worktree.branch) { 
    $branch = $data.worktree.branch 
} elseif ($dir) { 
    $branch = (git -C $dir --no-optional-locks branch --show-current 2>$null) 
}

$f = [math]::Min(10, [math]::Max(0, [int][math]::Floor($pct / 10)))
$bar = ([string][char]0x2588 * $f) + ([string][char]0x2591 * (10 - $f))

# ANSI Color Codes
$ESC = [char]27
$reset = "$ESC[0m"
$orange = "$ESC[38;5;208m"
$dim = "$ESC[2m"

if ($pct -lt 50) {
    $barColor = "$ESC[32m"
} elseif ($pct -lt 80) {
    $barColor = "$ESC[33m"
} else {
    $barColor = "$ESC[31m"
}

$out = "$ESC[35m$model$reset $dim|$reset $barColor$bar$reset $pct%"

if ($branch) {
    $out += " $dim|$reset $ESC[35m$branch$reset"
}

$fiveHPct = $data.rate_limits.five_hour.used_percentage
if ($null -ne $fiveHPct) {
    $fiveHPctVal = [int][math]::Floor($fiveHPct)
    if ($fiveHPctVal -lt 50) {
        $rateColor5h = "$ESC[32m"
    } elseif ($fiveHPctVal -lt 80) {
        $rateColor5h = "$ESC[33m"
    } else {
        $rateColor5h = "$ESC[31m"
    }

    $f5h = if ($fiveHPctVal -gt 0) { [math]::Min(8, [int][math]::Ceiling($fiveHPctVal / 12.5)) } else { 0 }
    $bar5h = ([string][char]0x2588 * $f5h) + ([string][char]0x2591 * (8 - $f5h))
    $out += " $dim|$reset 5h:$rateColor5h$bar5h$reset $fiveHPctVal%"
}

[Console]::Out.Write($out)