# Prepara uma maquina Windows 10/11 para o workshop: pre-requisitos via winget,
# clone do repositorio, dependencias Python e Node, .env e um teste de sanidade.
# As tres chaves do .env sao preenchidas a mao no fim.
#
#   irm https://raw.githubusercontent.com/indigotech/br-taqtile-workshop-agents-eval/main/scripts/setup_workshop.ps1 | iex
#
# Ou, de dentro de um clone:
#
#   powershell -ExecutionPolicy Bypass -File scripts\setup_workshop.ps1
#
# Pode ser rodado de novo quantas vezes quiser: o que ja esta pronto e pulado.
#
# Variaveis de ambiente opcionais:
#   WORKSHOP_DIR             onde clonar (padrao: %USERPROFILE%\br-taqtile-workshop-agents-eval)
#   WORKSHOP_REPOSITORY_URL  repositorio a clonar (padrao: o do workshop no GitHub)
#   WORKSHOP_BRANCH          branch a clonar (padrao: main)

# Messages are ASCII on purpose: Windows PowerShell 5.1 reads a local .ps1
# without a BOM as ANSI, which garbles accents, and a BOM would break `irm | iex`.

# 'Stop' would turn anything a native command writes to stderr (git's progress,
# npm's warnings) into a terminating error when output is redirected, so native
# commands are checked through their exit codes instead.
$ErrorActionPreference = 'Continue'

$RepositoryName = 'br-taqtile-workshop-agents-eval'
$MinimumNodeMajor = 22
$MinimumNodeMinor = 22

function Main {
    Assert-Windows
    Assert-Winget

    Write-Step 'Conferindo os programas necessarios (o Windows pode pedir permissao de administrador)'
    Install-IfMissing -Command 'git' -PackageId 'Git.Git' -Name 'Git'
    Add-GitShellToPath
    Install-IfMissing -Command 'uv' -PackageId 'astral-sh.uv' -Name 'uv (ele instala o Python 3.13 sozinho)'
    Install-Node
    Install-IfMissing -Command 'make' -PackageId 'ezwinports.make' -Name 'GNU Make'

    $repositoryDirectory = Resolve-RepositoryDirectory
    Set-Location -LiteralPath $repositoryDirectory

    Write-Step 'Instalando as dependencias Python (make install)'
    Invoke-Checked -Description 'make install' -Command { make install }
    Write-Step 'Instalando o promptfoo (make install-judge), pode levar alguns minutos'
    Invoke-Checked -Description 'make install-judge' -Command { make install-judge }

    Initialize-EnvFile
    Write-Step 'Rodando os testes como checagem de sanidade (make test-ci, nao chama o modelo)'
    Invoke-Checked -Description 'make test-ci' -Command { make test-ci }

    Write-Checklist -RepositoryDirectory $repositoryDirectory
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

# `exit` would close the student's PowerShell window under `irm | iex`, so a
# failure throws instead; run with -File, the throw still exits with code 1.
function Stop-Setup([string]$Message) {
    Write-Host "ERRO: $Message" -ForegroundColor Red
    throw 'Setup do workshop interrompido.'
}

function Invoke-Checked([string]$Description, [scriptblock]$Command) {
    & $Command
    if ($LASTEXITCODE -ne 0) {
        Stop-Setup "$Description falhou (codigo $LASTEXITCODE). Mande a saida acima pra quem esta conduzindo o workshop."
    }
}

function Assert-Windows {
    if ($env:OS -ne 'Windows_NT') {
        Stop-Setup 'Este script e para Windows. No macOS ou Linux, use o scripts/setup_workshop.sh.'
    }
}

function Assert-Winget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Stop-Setup 'O winget nao esta instalado. Instale o "App Installer" pela Microsoft Store (https://apps.microsoft.com/detail/9NBLGGH4NNS1), abra um novo PowerShell e rode este comando de novo. Outra opcao e usar a VM do workshop.'
    }
}

function Install-IfMissing([string]$Command, [string]$PackageId, [string]$Name) {
    if (Get-Command $Command -ErrorAction SilentlyContinue) {
        Write-Success "$Name ja instalado"
        return
    }
    Install-WingetPackage -PackageId $PackageId -Name $Name
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Stop-Setup "$Name foi instalado mas o comando '$Command' nao aparece. Feche o PowerShell, abra outro e rode este comando de novo."
    }
    Write-Success "$Name instalado"
}

function Install-WingetPackage([string]$PackageId, [string]$Name) {
    Write-Host "Instalando $Name pelo winget ($PackageId)"
    winget install --id $PackageId --exact --source winget --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Stop-Setup "O winget nao conseguiu instalar $Name ($PackageId, codigo $LASTEXITCODE). Instale na mao: abra um NOVO PowerShell, rode 'winget install --id $PackageId -e' e depois rode este comando de novo."
    }
    Update-SessionPath
}

# Installers write the new directories to the registry PATH, which only new
# terminals read; session-only entries are kept so nothing already found is lost.
function Update-SessionPath {
    $entries = @()
    foreach ($source in @(
            [Environment]::GetEnvironmentVariable('Path', 'Machine'),
            [Environment]::GetEnvironmentVariable('Path', 'User'),
            $env:Path)) {
        if ($source) { $entries += $source -split ';' | Where-Object { $_ } }
    }
    $env:Path = ($entries | Select-Object -Unique) -join ';'
}

# The Makefile's recipes are POSIX shell, and GNU Make for Windows runs them in
# sh.exe only when it finds one on PATH. Git\bin holds just git, bash and sh,
# unlike Git\usr\bin, whose Unix tools (find, sort) would shadow Windows' own.
function Add-GitShellToPath {
    $gitExecutable = (Get-Command git).Source
    $gitRoot = Split-Path (Split-Path $gitExecutable -Parent) -Parent
    $gitShellDirectory = Join-Path $gitRoot 'bin'
    if (-not (Test-Path (Join-Path $gitShellDirectory 'sh.exe'))) {
        Stop-Setup "Nao achei o sh.exe do Git em $gitShellDirectory. Reinstale o Git com: winget install --id Git.Git -e"
    }

    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $persistedEntries = @("$userPath;$machinePath" -split ';' | ForEach-Object { $_.TrimEnd('\') })
    if ($persistedEntries -notcontains $gitShellDirectory.TrimEnd('\')) {
        $newUserPath = if ($userPath) { "$userPath;$gitShellDirectory" } else { $gitShellDirectory }
        [Environment]::SetEnvironmentVariable('Path', $newUserPath, 'User')
        Write-Success "Adicionei $gitShellDirectory ao PATH do usuario (o make usa o sh do Git)"
    }
    else {
        Write-Success 'sh do Git ja esta no PATH'
    }
    Update-SessionPath
    if (-not (($env:Path -split ';') -contains $gitShellDirectory)) {
        $env:Path = "$env:Path;$gitShellDirectory"
    }
}

# Node 22 rather than the LTS channel (now 24): it is the line the macOS/Linux
# setup installs too, and promptfoo's native SQLite binding ships prebuilt for it.
function Install-Node {
    if (Test-NodeRecentEnough) {
        Write-Success "Node.js $(node -v) ja instalado"
        return
    }
    if (Get-Command node -ErrorAction SilentlyContinue) {
        Write-Host "O Node.js $(node -v) e antigo demais; vou instalar o 22."
    }
    Install-WingetPackage -PackageId 'OpenJS.NodeJS.22' -Name 'Node.js 22'
    if (-not (Test-NodeRecentEnough)) {
        Stop-Setup "O Node.js 22 foi instalado, mas o PATH ainda acha outro mais antigo ($((Get-Command node).Source)). Desinstale o Node antigo (ou o nvm-windows), abra um novo PowerShell e rode de novo."
    }
    Write-Success "Node.js $(node -v) instalado"
}

function Test-NodeRecentEnough {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) { return $false }
    $version = (node -v).TrimStart('v').Split('.')
    $major = [int]$version[0]
    $minor = [int]$version[1]
    return ($major -gt $MinimumNodeMajor) -or ($major -eq $MinimumNodeMajor -and $minor -ge $MinimumNodeMinor)
}

# Returns the directory through the pipeline, so every native command in here
# and in Sync-Clone sends its output to the host instead.
# An explicit WORKSHOP_DIR wins; otherwise a clone the script runs from (or the
# current directory) is reused; otherwise the default directory is cloned.
function Resolve-RepositoryDirectory {
    Write-Step 'Conferindo o repositorio'
    if ($env:WORKSHOP_DIR) {
        return Sync-Clone -Directory $env:WORKSHOP_DIR
    }

    $candidates = @()
    if ($PSScriptRoot) { $candidates += (Split-Path $PSScriptRoot -Parent) }
    $candidates += (Get-Location).Path
    foreach ($candidate in $candidates) {
        if (Test-WorkshopClone -Directory $candidate) {
            $topLevel = (git -C $candidate rev-parse --show-toplevel) -replace '/', '\'
            Write-Success "Usando o clone em $topLevel (sem git pull: suas mudancas locais ficam como estao)"
            return $topLevel
        }
    }

    return Sync-Clone -Directory (Join-Path $env:USERPROFILE $RepositoryName)
}

function Test-WorkshopClone([string]$Directory) {
    $pyproject = Join-Path $Directory 'pyproject.toml'
    if (-not (Test-Path -LiteralPath $pyproject)) { return $false }
    if (-not (Select-String -LiteralPath $pyproject -Pattern "^name = `"$RepositoryName`"" -Quiet)) { return $false }
    git -C $Directory rev-parse --show-toplevel *> $null
    return $LASTEXITCODE -eq 0
}

function Sync-Clone([string]$Directory) {
    $repositoryUrl = if ($env:WORKSHOP_REPOSITORY_URL) { $env:WORKSHOP_REPOSITORY_URL } else { "https://github.com/indigotech/$RepositoryName.git" }
    $branch = if ($env:WORKSHOP_BRANCH) { $env:WORKSHOP_BRANCH } else { 'main' }

    if (Test-Path -LiteralPath (Join-Path $Directory '.git')) {
        if (-not (Test-WorkshopClone -Directory $Directory)) {
            Stop-Setup "$Directory ja existe e nao e um clone deste workshop. Apague a pasta ou defina outra em WORKSHOP_DIR."
        }
        Write-Host "Atualizando o clone em $Directory"
        git -C $Directory pull --ff-only | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Write-Notice 'Nao consegui atualizar o clone (mudancas locais ou branch diferente). Sigo com a versao que esta ai.'
        }
    }
    elseif (Test-Path -LiteralPath $Directory) {
        Stop-Setup "$Directory ja existe e nao e um repositorio git. Apague a pasta ou defina outra em WORKSHOP_DIR."
    }
    else {
        Write-Host "Clonando $repositoryUrl ($branch) em $Directory"
        git clone --branch $branch $repositoryUrl $Directory | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Stop-Setup "Nao consegui clonar $repositoryUrl. Confira a internet e rode de novo."
        }
    }
    Write-Success "Repositorio pronto em $Directory"
    return $Directory
}

function Initialize-EnvFile {
    Write-Step 'Conferindo o .env'
    if (Test-Path -LiteralPath '.env') {
        Write-Success '.env ja existe, deixei como esta'
        return
    }
    Invoke-Checked -Description 'make setup-env' -Command { make setup-env }
}

function Write-Checklist([string]$RepositoryDirectory) {
    Write-Step 'Tudo instalado! Falta pouco:'
    $item = 1
    $missingKeys = @(Get-MissingEnvKeys)
    if ($missingKeys.Count -gt 0) {
        Write-Host "  $item. Abra o $RepositoryDirectory\.env (no Bloco de Notas, por exemplo) e preencha estas chaves com os valores que voce recebeu:"
        foreach ($key in $missingKeys) {
            Write-Host "       $key"
        }
        Write-Host "     Cole cada valor entre as aspas, por exemplo: MODEL_API_KEY='sk-...'"
        Write-Host '     As do Langfuse ficam no seu projeto em https://cloud.langfuse.com > Settings > API Keys.'
        $item++
    }
    Write-Host "  $item. Feche este PowerShell e abra um NOVO antes de usar o make (so assim o PATH novo vale). Nele, rode:"
    Write-Host "       cd $RepositoryDirectory"
    Write-Host '       make check-env   # confere as chaves: uma chamada ao modelo e um trace no Langfuse'
    Write-Host '       make run'
}

# A key still holding sample.env's placeholder ('changethis') or nothing counts
# as missing, so running the script again lists only what is left to fill in.
function Get-MissingEnvKeys {
    foreach ($key in @('MODEL_API_KEY', 'LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY')) {
        if (-not (Select-String -LiteralPath '.env' -Pattern "^$key=" -Quiet) -or
            (Select-String -LiteralPath '.env' -Pattern "^$key=('changethis'|''|`"`")?\s*$" -Quiet)) {
            $key
        }
    }
}

Main
