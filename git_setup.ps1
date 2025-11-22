# Git Setup and Commit Helper
# Run this to prepare your repository for submission

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Git Repository Setup - Assignment Submission Helper   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
}
else {
    Write-Host "✅ Git repository already initialized" -ForegroundColor Green
}

# Check current status
Write-Host "`nCurrent Git status:" -ForegroundColor Yellow
git status --short

# Show files to be committed
Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "Files to be committed:" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

$files = @(
    "producer.py",
    "consumer.py",
    "dlq_consumer.py",
    "order.avsc",
    "docker-compose.yml",
    "pyproject.toml",
    "requirements.txt",
    "README.md",
    "QUICKSTART.md",
    "SUBMISSION_CHECKLIST.md",
    "PROJECT_SUMMARY.txt",
    "test_system.py",
    "run_demo.ps1",
    ".gitignore"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    }
    else {
        Write-Host "  ✗ $file (missing)" -ForegroundColor Red
    }
}

Write-Host "`n" + "=" * 60 + "`n" -ForegroundColor Cyan

# Ask to proceed
$response = Read-Host "Add all files and commit? (y/N)"

if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host "`nAdding files to Git..." -ForegroundColor Yellow
    git add .
    
    Write-Host "Creating commit..." -ForegroundColor Yellow
    git commit -m "feat: Kafka order processing system with Avro, retry logic, and DLQ

- Implemented Kafka producer with Avro serialization and delivery callbacks
- Built consumer with retry logic (exponential backoff) and DLQ support
- Added real-time aggregation (running average, min, max, revenue)
- Created DLQ monitoring tool for failed message analysis
- Comprehensive error handling and graceful shutdown
- Production-grade logging and metrics tracking
- Automated test suite and demo launcher
- Extensive documentation with architecture diagrams

Technologies: Python 3.12, Kafka 7.6.1, Avro, Docker Compose
Features: Retry logic, DLQ, real-time aggregation, monitoring"
    
    Write-Host "`n✅ Files committed successfully!" -ForegroundColor Green
    
    # Show commit
    Write-Host "`nCommit details:" -ForegroundColor Yellow
    git log -1 --stat
    
    Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "1. Create remote repository on GitHub/GitLab" -ForegroundColor White
    Write-Host "2. Add remote: git remote add origin <your-repo-url>" -ForegroundColor White
    Write-Host "3. Push: git push -u origin main" -ForegroundColor White
    Write-Host "`nOr continue with local repository for now." -ForegroundColor Gray
    
}
else {
    Write-Host "`nSkipped. You can manually commit later with:" -ForegroundColor Yellow
    Write-Host "  git add ." -ForegroundColor White
    Write-Host "  git commit -m 'your message'" -ForegroundColor White
}

Write-Host "`n✨ Repository ready for submission!" -ForegroundColor Green
Write-Host "`n"
