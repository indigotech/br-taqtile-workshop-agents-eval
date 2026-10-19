# Desfaz o que setup_workshop.ps1 e setup_workshop_node20.ps1 fizeram numa maquina Windows.
#
#   powershell -ExecutionPolicy Bypass -File undo_setup_workshop.ps1
#
#
# Variaveis de ambiente opcionais (as mesmas do setup):
#   WORKSHOP_DIR  pasta do clone (padrao: %USERPROFILE%\br-taqtile-workshop-agents-eval)

# Messages are ASCII on purpose: Windows PowerShell 5.1 reads a local .ps1
# without a BOM as ANSI, which garbles accents.

$ErrorActionPreference = 'Continue'

$RepositoryName = 'br-taqtile-workshop-agents-eval'

function Main {
    Assert-Windows

    Remove-RepositoryClone
    Remove-UvPython
    Remove-WingetPackage -PackageId 'ezwinports.make' -Name 'GNU Make'
    Remove-WingetPackage -PackageId 'astral-sh.uv' -Name 'uv'

    Write-Step 'Pronto. Abra um novo PowerShell para o PATH atualizado valer.'
    Write-Notice 'O .env copiado de Downloads (se houve) continua la, e a conta do Langfuse nao e afetada.'
}

function Write-Step([string]$Message) {
    Write-Host ''
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Success([string]$Message) {
    Write-Host "OK  $Message" -ForegroundColor Green
}

function Write-Notice([string]$Message) {
    Write-Host "!   $Message" -ForegroundColor Yellow
}

function Assert-Windows {
    if ($env:OS -ne 'Windows_NT') {
        Write-Host 'ERRO: Este script e para Windows.' -ForegroundColor Red
        throw 'Undo do workshop interrompido.'
    }
}

function Get-RepositoryDirectory {
    if ($env:WORKSHOP_DIR) { return $env:WORKSHOP_DIR }
    return Join-Path $env:USERPROFILE $RepositoryName
}

function Test-WorkshopClone([string]$Directory) {
    $pyproject = Join-Path $Directory 'pyproject.toml'
    if (-not (Test-Path -LiteralPath (Join-Path $Directory '.git'))) { return $false }
    if (-not (Test-Path -LiteralPath $pyproject)) { return $false }
    return [bool](Select-String -LiteralPath $pyproject -Pattern "^name = `"$RepositoryName`"" -Quiet)
}

# Removes the clone with its .venv, node_modules and .env (which holds the API keys).
function Remove-RepositoryClone {
    $directory = Get-RepositoryDirectory
    Write-Step "Clone do workshop ($directory)"
    if (-not (Test-Path -LiteralPath $directory)) {
        Write-Success 'Nao existe, nada a fazer'
        return
    }
    if (-not (Test-WorkshopClone -Directory $directory)) {
        Write-Notice 'A pasta existe mas nao parece o clone do workshop; deixei como esta.'
        return
    }

    Set-Location -LiteralPath $env:USERPROFILE
    Remove-Item -LiteralPath $directory -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $directory) {
        cmd /c rmdir /s /q "`"$directory`""
    }
    if (Test-Path -LiteralPath $directory) {
        Write-Notice "Nao consegui apagar tudo em $directory. Feche editores/terminais que usem a pasta e rode de novo."
        return
    }
    Write-Success 'Clone apagado'
}

# Must run before uv itself is uninstalled.
function Remove-UvPython {
    Write-Step 'Python 3.13 instalado pelo uv'
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Success 'uv nao esta instalado, nada a fazer'
        return
    }
    uv python uninstall 3.13
    uv cache clean
    Write-Success 'Python do uv e cache removidos'
}

function Remove-WingetPackage([string]$PackageId, [string]$Name) {
    Write-Step "$Name ($PackageId)"
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Notice 'winget nao encontrado; desinstale pelo Painel de Controle.'
        return
    }
    winget list --id $PackageId --exact --source winget *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Success 'Nao esta instalado pelo winget, nada a fazer'
        return
    }
    winget uninstall --id $PackageId --exact --silent --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Write-Notice "O winget nao conseguiu desinstalar $Name (codigo $LASTEXITCODE)."
        return
    }
    Write-Success "$Name desinstalado"
}

Main
