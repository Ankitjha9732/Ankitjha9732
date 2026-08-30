# setup-profile.ps1
# Automates the GitHub profile/repo polish that needs your account auth.
# Prereq: GitHub CLI installed + logged in once:
#   winget install GitHub.cli
#   gh auth login
# Then run from anywhere:
#   powershell -ExecutionPolicy Bypass -File setup-profile.ps1

$ErrorActionPreference = "Stop"

$USER = "Ankitjha9732"
$LOCATION = "India"

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Error "GitHub CLI not found. Install via: winget install GitHub.cli"
}

Step "Checking gh auth…"
gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "Run 'gh auth login' first." }

Step "Updating profile bio + location"
gh api -X PATCH user -f bio="Frontend Developer focused on UI/UX | React - JavaScript - SCSS | Full-Stack (MERN) | B.Tech CSE (AI & ML)" -f location=$LOCATION | Out-Null

$repos = @{
  "SYLLABUS-TRACKER" = @{
    desc = "Full-stack MERN study platform - modules, topics, subtopics, streaks, charts"
    topics = @("react","nodejs","express","mongodb","jwt","vercel")
  }
  "RESTRO-ORDER-NEW" = @{
    desc = "Full-stack MERN QR restaurant ordering with real-time order updates (Socket.IO)"
    topics = @("mern","react","nodejs","express","mongodb","socket-io")
  }
  "ankit-portfolio" = @{
    desc = "Design-first personal portfolio built with React, GSAP, Three.js & Lenis"
    topics = @("react","gsap","threejs","vite","tailwindcss")
  }
  "REEL-PROJ" = @{
    desc = "Interactive prototype of the Instagram Reels section - like, comment, follow & share"
    topics = @("javascript","ui","prototype","vanilla-js")
  }
  "RESPONSIVE-WEBPAGE" = @{
    desc = "Responsive landing page built with HTML and SCSS (design tokens + breakpoints)"
    topics = @("scss","sass","html5","css3","responsive-design")
  }
  "RESTRO-ORDER" = @{
    desc = "Early frontend prototype of the restro ordering concept (superseded by RESTRO-ORDER-NEW)"
    topics = @("javascript","prototype")
  }
}

foreach ($name in $repos.Keys) {
  Step "Repo: $name"
  gh api -X PATCH "repos/$USER/$name" -f description=$repos[$name].desc | Out-Null
  $topicArg = ($repos[$name].topics | ForEach-Object { $_.Replace("#", "%23") }) -join ","
  gh api -X PUT -H "Accept: application/vnd.github+json" "repos/$USER/$name/topics" -f names="$topicArg" | Out-Null
  Write-Host "  - description + topics set"
}

Step "Archiving superseded/junk repos"
gh repo archive "$USER/RESTRO-ORDER" --yes
gh repo archive "$USER/Ankitjha-demo" --yes

Write-Host "`nDone. Remaining manual steps:" -ForegroundColor Green
Write-Host "  1. Pin repos (Settings > Profile): SYLLABUS-TRACKER, RESTRO-ORDER-NEW, ankit-portfolio, REEL-PROJ"
Write-Host "  2. RESPONSIVE-WEBPAGE: Settings > Branches > change default branch from 'master' to 'main'"
Write-Host "  3. Watch the profile overview - the card grid + pipeline hero are live."