#!/usr/bin/env bash
# Prepara a máquina do aluno para o workshop: pré-requisitos, clone do
# repositório, dependências Python e Node, .env e um teste de sanidade.
# As três chaves do .env são preenchidas à mão no fim.
#
#   curl -fsSL https://raw.githubusercontent.com/indigotech/br-taqtile-workshop-agents-eval/main/scripts/setup_workshop.sh | bash
#
# Pode ser rodado de novo quantas vezes quiser: o que já está pronto é pulado.
#
# Variáveis opcionais:
#   WORKSHOP_DIR             onde clonar (padrão: ~/br-taqtile-workshop-agents-eval)
#   WORKSHOP_REPOSITORY_URL  repositório a clonar (padrão: o do workshop no GitHub)
#   WORKSHOP_BRANCH          branch a clonar (padrão: main)
set -euo pipefail

readonly REPOSITORY_URL="${WORKSHOP_REPOSITORY_URL:-https://github.com/indigotech/br-taqtile-workshop-agents-eval.git}"
readonly BRANCH="${WORKSHOP_BRANCH:-main}"
readonly MINIMUM_NODE_MAJOR=22
readonly MINIMUM_NODE_MINOR=22
readonly NODE_VERSION_TO_INSTALL=22
readonly NVM_INSTALLER_VERSION="v0.40.3"
readonly APT_PACKAGES=(git make curl build-essential ca-certificates)

# Everything runs inside main, called on the last line, so that with
# `curl | bash` the whole script is read before any command can consume stdin.
main() {
  setup_colors
  local operating_system
  operating_system="$(detect_operating_system)"
  info "Sistema detectado: ${operating_system}"

  case "${operating_system}" in
    macos) ensure_macos_prerequisites ;;
    linux | wsl) ensure_linux_prerequisites ;;
  esac
  ensure_uv
  ensure_node

  local repository_directory
  repository_directory="$(resolve_repository_directory)"
  if [[ "${operating_system}" == "wsl" && "${repository_directory}" == /mnt/* ]]; then
    warn "O repositório está no disco do Windows (${repository_directory}), o que deixa tudo bem mais lento. Prefira uma pasta dentro do Linux, como o padrão ~/br-taqtile-workshop-agents-eval."
  fi
  cd "${repository_directory}"

  step "Instalando as dependências Python (make install)"
  make install
  step "Instalando o promptfoo (make install-judge), pode levar alguns minutos"
  make install-judge

  ensure_env_file
  step "Rodando os testes como checagem de sanidade (make test-ci, não chama o modelo)"
  if ! make test-ci; then
    fail "Os testes falharam. Mande a saída acima pra quem está conduzindo o workshop."
  fi

  print_checklist "${repository_directory}"
}

setup_colors() {
  if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
    BOLD=$'\033[1m'
    GREEN=$'\033[32m'
    YELLOW=$'\033[33m'
    RED=$'\033[31m'
    RESET=$'\033[0m'
  else
    BOLD=""
    GREEN=""
    YELLOW=""
    RED=""
    RESET=""
  fi
}

step() {
  printf '\n%s==> %s%s\n' "${BOLD}" "$1" "${RESET}"
}

info() {
  printf '%s\n' "$1"
}

success() {
  printf '%s✔ %s%s\n' "${GREEN}" "$1" "${RESET}"
}

warn() {
  printf '%s! %s%s\n' "${YELLOW}" "$1" "${RESET}" >&2
}

fail() {
  printf '%s✘ %s%s\n' "${RED}" "$1" "${RESET}" >&2
  exit 1
}

detect_operating_system() {
  case "$(uname -s)" in
    Darwin) echo "macos" ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then
        echo "wsl"
      else
        echo "linux"
      fi
      ;;
    MINGW* | MSYS* | CYGWIN*)
      fail "Windows nativo (Git Bash, MSYS ou Cygwin) não é suportado. Instale o WSL2 com Ubuntu (no PowerShell como administrador: wsl --install -d Ubuntu), abra o terminal do Ubuntu e rode este comando de novo lá dentro. Outra opção é usar a VM do workshop."
      ;;
    *)
      fail "Sistema operacional não suportado: $(uname -s). Use macOS, Linux (Ubuntu/Debian) ou Windows com WSL2, ou a VM do workshop."
      ;;
  esac
}

ensure_macos_prerequisites() {
  step "Conferindo as Command Line Tools do Xcode (git e make)"
  # On a Mac without the Command Line Tools, /usr/bin/git and /usr/bin/make
  # exist as stubs that open an installer dialog, so `command -v` is not enough.
  if xcode-select -p >/dev/null 2>&1; then
    success "Command Line Tools instaladas"
    return
  fi
  xcode-select --install >/dev/null 2>&1 || true
  fail "Faltam as Command Line Tools do Xcode. Uma janela de instalação deve ter aberto: clique em Instalar, espere terminar e rode este comando de novo. Se a janela não abriu, rode: xcode-select --install"
}

ensure_linux_prerequisites() {
  step "Conferindo os pacotes do sistema (${APT_PACKAGES[*]})"
  if ! command -v apt-get >/dev/null 2>&1; then
    local missing_command
    for missing_command in git make curl; do
      command -v "${missing_command}" >/dev/null 2>&1 \
        || fail "Esta distribuição não usa apt-get e falta o comando ${missing_command}. Instale git, make, curl e um compilador C pelo gerenciador de pacotes dela e rode de novo, ou use Ubuntu/Debian."
    done
    warn "Distribuição sem apt-get: seguindo com o git, make e curl que já estão instalados."
    return
  fi

  local missing_packages=()
  local package
  for package in "${APT_PACKAGES[@]}"; do
    if ! dpkg-query -W -f='${Status}' "${package}" 2>/dev/null | grep -q "install ok installed"; then
      missing_packages+=("${package}")
    fi
  done
  if ((${#missing_packages[@]} == 0)); then
    success "Pacotes do sistema já instalados"
    return
  fi

  local sudo_command=()
  if ((EUID != 0)); then
    command -v sudo >/dev/null 2>&1 || fail "Preciso instalar ${missing_packages[*]}, mas o sudo não existe. Rode como root: apt-get install -y ${missing_packages[*]}"
    sudo_command=(sudo)
    info "Vou instalar ${missing_packages[*]} com sudo; ele pode pedir a sua senha do Linux."
  fi
  "${sudo_command[@]}" apt-get update
  "${sudo_command[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${missing_packages[@]}"
  success "Pacotes do sistema instalados"
}

ensure_uv() {
  step "Conferindo o uv (ele instala o Python 3.13 sozinho)"
  # The uv installer puts the binary in ~/.local/bin and edits the shell
  # profile, which only takes effect in new terminals, so this run needs the
  # PATH itself.
  export PATH="${HOME}/.local/bin:${PATH}"
  if command -v uv >/dev/null 2>&1; then
    success "uv já instalado ($(uv --version))"
    return
  fi
  curl -LsSf https://astral.sh/uv/install.sh | sh
  command -v uv >/dev/null 2>&1 || fail "O uv foi instalado mas não está no PATH. Abra um novo terminal e rode este comando de novo."
  success "uv instalado ($(uv --version))"
}

# nvm, for both macOS and Linux: it needs neither sudo nor Homebrew (absent on
# Linux and on many student Macs), installs under ~/.nvm, and its installer
# adds itself to the shell profile. Homebrew's node@22 is keg-only, so it would
# still need a PATH edit, and a second code path to support.
ensure_node() {
  step "Conferindo o Node.js (precisa de ${MINIMUM_NODE_MAJOR}.${MINIMUM_NODE_MINOR} ou mais novo, pro promptfoo)"
  if node_is_recent_enough; then
    success "Node.js $(node -v) já instalado"
    return
  fi
  if command -v node >/dev/null 2>&1; then
    info "O Node.js $(node -v) é antigo demais; vou instalar o ${NODE_VERSION_TO_INSTALL} pelo nvm, sem mexer no que já existe."
  fi

  export NVM_DIR="${NVM_DIR:-${HOME}/.nvm}"
  if [[ ! -s "${NVM_DIR}/nvm.sh" ]]; then
    info "Instalando o nvm ${NVM_INSTALLER_VERSION} em ${NVM_DIR}"
    # The nvm installer only edits a profile file that already exists, and a
    # fresh macOS account has no ~/.zshrc.
    case "${SHELL:-}" in
      */zsh) touch "${HOME}/.zshrc" ;;
      */bash) touch "${HOME}/.bashrc" ;;
    esac
    curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_INSTALLER_VERSION}/install.sh" | bash
  fi

  # nvm.sh is not written for `set -eu`: it reads unset variables and returns
  # non-zero from internal checks.
  set +eu
  # shellcheck source=/dev/null
  . "${NVM_DIR}/nvm.sh"
  nvm install "${NODE_VERSION_TO_INSTALL}"
  nvm alias default "${NODE_VERSION_TO_INSTALL}"
  nvm use default
  set -eu

  node_is_recent_enough || fail "Não consegui deixar o Node.js ${MINIMUM_NODE_MAJOR}.${MINIMUM_NODE_MINOR}+ ativo. Abra um novo terminal, rode 'nvm install ${NODE_VERSION_TO_INSTALL}' e rode este comando de novo."
  success "Node.js $(node -v) instalado pelo nvm"
}

node_is_recent_enough() {
  command -v node >/dev/null 2>&1 || return 1
  local version major minor
  version="$(node -v)"
  version="${version#v}"
  major="${version%%.*}"
  minor="${version#*.}"
  minor="${minor%%.*}"
  ((major > MINIMUM_NODE_MAJOR || (major == MINIMUM_NODE_MAJOR && minor >= MINIMUM_NODE_MINOR)))
}

# An explicit WORKSHOP_DIR wins; otherwise a clone the script runs from (or the
# current directory) is reused; otherwise the default directory is cloned.
resolve_repository_directory() {
  step "Conferindo o repositório" >&2
  if [[ -n "${WORKSHOP_DIR:-}" ]]; then
    clone_or_update "${WORKSHOP_DIR}"
    return
  fi

  local candidates=("${PWD}")
  # Piped through `curl | bash`, there is no script file to locate a clone from.
  if [[ -f "${BASH_SOURCE[0]:-}" ]]; then
    candidates=("$(dirname "${BASH_SOURCE[0]}")/.." "${PWD}")
  fi
  local candidate
  for candidate in "${candidates[@]}"; do
    if is_workshop_clone "${candidate}"; then
      candidate="$(cd "${candidate}" && git rev-parse --show-toplevel)"
      success "Usando o clone em ${candidate} (sem git pull: suas mudanças locais ficam como estão)" >&2
      echo "${candidate}"
      return
    fi
  done

  clone_or_update "${HOME}/br-taqtile-workshop-agents-eval"
}

is_workshop_clone() {
  local directory="$1"
  grep -qs '^name = "br-taqtile-workshop-agents-eval"' "${directory}/pyproject.toml" \
    && git -C "${directory}" rev-parse --show-toplevel >/dev/null 2>&1
}

# Progress goes to stderr: stdout carries only the resolved directory.
clone_or_update() {
  local directory="$1"
  if [[ -d "${directory}/.git" ]]; then
    is_workshop_clone "${directory}" || fail "${directory} já existe e não é um clone deste workshop. Apague a pasta ou rode com outro WORKSHOP_DIR."
    info "Atualizando o clone em ${directory}" >&2
    if ! git -C "${directory}" pull --ff-only >&2; then
      warn "Não consegui atualizar o clone (mudanças locais ou branch diferente da main). Sigo com a versão que está aí."
    fi
  elif [[ -e "${directory}" ]]; then
    fail "${directory} já existe e não é um repositório git. Apague a pasta ou rode com outro WORKSHOP_DIR."
  else
    info "Clonando ${REPOSITORY_URL} (${BRANCH}) em ${directory}" >&2
    git clone --branch "${BRANCH}" "${REPOSITORY_URL}" "${directory}" >&2
  fi
  success "Repositório pronto em ${directory}" >&2
  echo "${directory}"
}

ensure_env_file() {
  step "Conferindo o .env"
  if [[ -f .env ]]; then
    success ".env já existe, deixei como está"
    return
  fi
  make setup-env
}

print_checklist() {
  local repository_directory="$1"
  step "Tudo instalado! Falta pouco:"
  local item=1
  local missing_keys
  missing_keys="$(missing_env_keys)"
  if [[ -n "${missing_keys}" ]]; then
    info "  ${item}. Abra o ${repository_directory}/.env e preencha estas chaves com os valores que você recebeu:"
    local key
    for key in ${missing_keys}; do
      info "       ${key}"
    done
    info "     Cole cada valor entre as aspas, por exemplo: MODEL_API_KEY='sk-...'"
    info "     As do Langfuse ficam no seu projeto em https://cloud.langfuse.com > Settings > API Keys."
    item=$((item + 1))
  fi
  info "  ${item}. Abra um terminal novo (pro uv e o Node entrarem no PATH) e rode:"
  info "       cd ${repository_directory}"
  info "       make check-env   # confere as chaves: uma chamada ao modelo e um trace no Langfuse"
  info "       make run"
}

# A key still holding sample.env's placeholder ('changethis') or nothing counts
# as missing, so running the script again lists only what is left to fill in.
missing_env_keys() {
  local key
  for key in MODEL_API_KEY LANGFUSE_PUBLIC_KEY LANGFUSE_SECRET_KEY; do
    if ! grep -q "^${key}=" .env || grep -qE "^${key}=('changethis'|''|\"\")?[[:space:]]*$" .env; then
      echo "${key}"
    fi
  done
}

main "$@"
