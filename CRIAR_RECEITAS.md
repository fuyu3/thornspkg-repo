# Como criar receitas para o thornspkg

Este guia ensina, do zero, como criar receitas (`.toml`) para o thornspkg —
tanto para uso local em `/etc/thornspkg/recipes/` quanto para publicar em
repositórios remotos.

---

## Sumário

1. [Anatomia de uma receita](#1-anatomia-de-uma-receita)
2. [Sua primeira receita (5 minutos)](#2-sua-primeira-receita-5-minutos)
3. [Receita para software Autotools](#3-receita-para-software-autotools)
4. [Receita para software CMake](#4-receita-para-software-cmake)
5. [Receita para software Meson](#5-receita-para-software-meson)
6. [Receita para software Make puro](#6-receita-para-software-make-puro)
7. [Receita para software custom (Rust, Go, etc.)](#7-receita-para-software-custom-rust-go-etc)
8. [Dependências com versão](#8-dependências-com-versão)
9. [Patches e sources múltiplos](#9-patches-e-sources-múltiplos)
10. [Hooks: pre_build, post_install, pre_remove, post_remove](#10-hooks)
11. [Variáveis de ambiente por receita](#11-variáveis-de-ambiente-por-receita)
12. [Metadados completos (v0.4+)](#12-metadados-completos-v04)
13. [Publicar a receita em um repositório](#13-publicar-a-receita-em-um-repositório)
14. [Testar a receita antes de publicar](#14-testar-a-receita-antes-de-publicar)
15. [Troubleshooting](#15-troubleshooting)
16. [Templates prontos para copiar](#16-templates-prontos-para-copiar)

---

## 1. Anatomia de uma receita

Uma receita é um arquivo TOML. Exemplo mínimo:

```toml
name    = "hello"
version = "1.0"
source  = "https://example.org/hello-1.0.tar.gz"
```

Salvo como `/etc/thornspkg/recipes/hello.toml`, isso já é suficiente para
`thorn install hello` funcionar (assumindo que o source é um tarball
autotools padrão).

### Campos obrigatórios

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome canônico do pacote (sem espaços, sem acentos) |
| `version` | string | Versão (qualquer formato: `1.0`, `3.12.4`, `2.40-1`) |

### Campos de source

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `source` | string \| lista | URL (http/https/ftp) ou caminho local; pode ser lista |
| `sources` | lista | Mesmo que `source` em formato lista |
| `sha256` | string \| lista | Checksum SHA256 do tarball (recomendado) |

### Campos de dependência

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `depends` | lista | Dependências obrigatórias (suporta `openssl>=3.0`) |
| `optional_deps` | lista | Só instala se já estiverem presentes |
| `provides` | lista | Nomes virtuais que este pacote satisfaz |

### Campos de build

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `build_system` | string | `autotools` | `autotools` \| `make` \| `cmake` \| `meson` \| `custom` |
| `configure_args` | lista | `[]` | Args extras para configure/cmake/meson |
| `prefix` | string | (do config) | Sobrescreve `--prefix` global só para este pacote |
| `steps` | lista | `[]` | Comandos de build (ignora `build_system` se presente) |
| `install_steps` | lista | `["make install"]` | Comandos de install |

### Campos de hooks

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `pre_build` | lista | Comandos shell antes do build (ex: `autoreconf -fi`) |
| `post_install` | lista | Comandos shell após install (ex: `ldconfig`) |
| `pre_remove` | lista | Comandos shell antes de remover |
| `post_remove` | lista | Comandos shell após remover |

### Campos de metadados (v0.4+)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `description` | string | Descrição curta de uma linha |
| `homepage` | string | URL do projeto |
| `license` | string | Licença (SPDX ou nome) |
| `maintainer` | string | Nome/email do mantenedor da receita |
| `repository` | string | Nome do repositório de origem |
| `architecture` | string | `x86_64`, `aarch64`, `any` |
| `build_date` | string | ISO 8601 (preenchido em binários) |
| `install_size` | int | Tamanho instalado em bytes |
| `download_size` | int | Tamanho do download em bytes |

---

## 2. Sua primeira receita (5 minutos)

Vamos criar uma receita para o `hello` da GNU — um programa trivial que
imprime "Hello, world!".

### Passo 1: descobrir o source

O `hello` da GNU está em `https://ftp.gnu.org/gnu/hello/`. Vamos usar a
versão 2.12.1:

```sh
# Baixar para descobrir o SHA256
curl -LO https://ftp.gnu.org/gnu/hello/hello-2.12.1.tar.gz
sha256sum hello-2.12.1.tar.gz
# Saída: 8d99142afd930639263a3f7a0fcd1819d3c8e2e2f3e8a6c8c8c8c8c8c8c8c8c8  hello-2.12.1.tar.gz
```

### Passo 2: criar o arquivo de receita

Crie `/etc/thornspkg/recipes/hello.toml`:

```toml
name        = "hello"
version     = "2.12.1"
description = "Programa de exemplo que imprime 'Hello, world!'"
homepage    = "https://www.gnu.org/software/hello/"
license     = "GPL-3.0-or-later"

source  = "https://ftp.gnu.org/gnu/hello/hello-2.12.1.tar.gz"
sha256  = "8d99142afd930639263a3f7a0fcd1819d3c8e2e2f3e8a6c8c8c8c8c8c8c8c8c8"

build_system = "autotools"
```

### Passo 3: testar a resolução de dependências

```sh
$ thorn deps hello
Ordem de build/instalação:
    1.  hello    2.12.1    [pendente]
```

### Passo 4: testar o dry-run

```sh
$ thorn install hello --dry-run
Pacotes a instalar (1):
  hello
[dry-run] nenhum pacote foi instalado.
```

### Passo 5: instalar de verdade

```sh
$ sudo thorn install hello
[1/1] ==> hello-2.12.1
  ↓  https://ftp.gnu.org/gnu/hello/hello-2.12.1.tar.gz
  ✓  checksum OK
  ⚙  compilando
  📦 staging (DESTDIR)
  →  /
  ✓  3 arquivos instalados

✓ 1 pacote(s) instalado(s).

$ hello
Hello, world!
```

Parabéns! Você criou sua primeira receita. 

---

## 3. Receita para software Autotools

A maioria dos projetos GNU/Linux usa Autotools (`./configure && make`).

### Caso simples

```toml
name         = "zlib"
version      = "1.3.1"
description  = "Biblioteca de compressão de uso geral"
homepage     = "https://zlib.net/"
license      = "Zlib"

source  = "https://zlib.net/zlib-1.3.1.tar.gz"
sha256  = "9a93b2b7dfdac77ceba5a558a580e74667dd6fede4585b91eefb60f03b72df23"

build_system   = "autotools"
configure_args = ["--shared"]
```

O thornspkg executa, nesta ordem:
1. `./configure --prefix=/usr --shared`
2. `make -j$(nproc)`
3. `make install` (com `DESTDIR=$DESTDIR`)

### Com dependências e post_install

```toml
name         = "curl"
version      = "8.8.0"
description  = "Ferramenta e biblioteca de transferência de dados por URL"
homepage     = "https://curl.se/"
license      = "curl"
maintainer   = "Daniel Stenberg <daniel@haxx.se>"

# depends com operadores de versão (v0.4+)
depends       = ["zlib>=1.2", "openssl>=3.0"]
source        = "https://curl.se/download/curl-8.8.0.tar.gz"
# sha256 = "preencha com: sha256sum curl-8.8.0.tar.gz"

build_system   = "autotools"
configure_args = [
    "--with-openssl",
    "--disable-static",
    "--enable-versioned-symbols",
]
post_install   = ["ldconfig"]
```

### Com `pre_build` (ex: autoreconf)

Alguns projetos precisam de `autoreconf` antes do `configure`:

```toml
name         = "libpng"
version      = "1.6.43"
description  = "Biblioteca de manipulação de PNG"
homepage     = "https://www.libpng.org/"
license      = "libpng-2.0"

depends       = ["zlib"]
source        = "https://download.sourceforge.net/libpng/libpng-1.6.43.tar.gz"

build_system   = "autotools"
pre_build      = ["autoreconf -fi"]
configure_args = ["--disable-static"]
```

### Com `prefix` customizado

Algumas receitas precisam de prefix diferente (ex: `/` em vez de `/usr`):

```toml
name         = "glibc"
version      = "2.40"
description  = "Biblioteca C GNU"

prefix        = "/"
build_system  = "custom"
# glibc não é autotools padrão — precisa de steps customizados
steps = [
    "mkdir -p build",
    "cd build && ../configure --prefix=/usr --enable-kernel=4.19 --enable-stack-protector=strong",
    "cd build && make",
]
install_steps = [
    "cd build && make DESTDIR=$DESTDIR install",
]
```

---

## 4. Receita para software CMake

```toml
name         = "ninja"
version      = "1.12.1"
description  = "Sistema de build pequeno e rápido focado em velocidade"
homepage     = "https://ninja-build.org/"
license      = "Apache-2.0"

source        = "https://github.com/ninja-build/ninja/archive/refs/tags/v1.12.1.tar.gz"

build_system   = "cmake"
configure_args = [
    "-DCMAKE_BUILD_TYPE=Release",
]
```

O thornspkg executa:
1. `cmake -B _build -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release`
2. `cmake --build _build -j$(nproc)`
3. `cmake --install _build`

### Com dependência que precisa ser encontrada via pkg-config

```toml
name         = "htop"
version      = "3.3.0"
description  = "Visualizador de processos interativo"
homepage     = "https://htop.dev/"
license      = "GPL-2.0-or-later"

depends       = ["ncurses>=6.0"]
source        = "https://github.com/htop-dev/htop/releases/download/3.3.0/htop-3.3.0.tar.xz"

build_system   = "autotools"  # htop ainda usa autotools
configure_args = ["--enable-unicode"]
```

---

## 5. Receita para software Meson

```toml
name         = "systemd"
version      = "256"
description  = "Sistema de init e gerenciador de serviços"
homepage     = "https://systemd.io/"
license      = "LGPL-2.1-or-later"

depends       = ["glibc>=2.36", "libcap", "util-linux", "dbus"]

source        = "https://github.com/systemd/systemd/archive/refs/tags/v256.tar.gz"

build_system   = "meson"
configure_args = [
    "-Drootprefix=/usr",
    "-Dsplit-usr=false",
    "-Db_lto=true",
    "-Dselinux=disabled",
]
```

O thornspkg executa:
1. `meson setup _build --prefix=/usr -Drootprefix=/usr ...`
2. `ninja -C _build -j$(nproc)`
3. `ninja -C _build install`

---

## 6. Receita para software Make puro

Projetos que usam apenas `make` (sem `./configure`):

```toml
name         = "bin86"
version      = "0.16.21"
description  = "Assembler e linker para x86 real-mode"
homepage     = "https://v3.sk/~lkundrak/dev86/"

source        = "https://v3.sk/~lkundrak/dev86/bin86-0.16.21.tar.gz"

build_system   = "make"
configure_args = ["PREFIX=/usr"]  # vira: make PREFIX=/usr
```

O thornspkg executa:
1. `make -j$(nproc) PREFIX=/usr`
2. `make install PREFIX=/usr` (com `DESTDIR=$DESTDIR`)

---

## 7. Receita para software custom (Rust, Go, etc.)

Use `build_system = "custom"` e forneça `steps` explícitos:

### Rust (cargo)

```toml
name         = "ripgrep"
version      = "14.1.0"
description  = "Busca recursiva rápida (alternativa ao grep)"
homepage     = "https://github.com/BurntSushi/ripgrep"
license      = "MIT"
maintainer   = "Andrew Gallant <jamslam@gmail.com>"
architecture = "x86_64"

source        = "https://github.com/BurntSushi/ripgrep/archive/refs/tags/14.1.0.tar.gz"

build_system  = "custom"
steps = [
    "cargo build --release --locked --features 'pcre2'",
]
install_steps = [
    "install -Dm755 target/release/rg $DESTDIR/usr/bin/rg",
    "install -Dm644 complete/_rg $DESTDIR/usr/share/zsh/site-functions/_rg",
    "install -Dm644 doc/rg.1 $DESTDIR/usr/share/man/man1/rg.1",
]

post_install = ["mandb -q || true"]
```

### Go

```toml
name         = "caddy"
version      = "2.8.4"
description  = "Servidor web com HTTPS automático"
homepage     = "https://caddyserver.com/"
license      = "Apache-2.0"
architecture = "x86_64"

source        = "https://github.com/caddyserver/caddy/archive/refs/tags/v2.8.4.tar.gz"

build_system  = "custom"
steps = [
    "CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o caddy ./cmd/caddy",
]
install_steps = [
    "install -Dm755 caddy $DESTDIR/usr/bin/caddy",
    "install -Dm644 README.md $DESTDIR/usr/share/doc/caddy/README.md",
    "mkdir -p $DESTDIR/etc/caddy",
    "install -Dm644 dist/config/Caddyfile $DESTDIR/etc/caddy/Caddyfile",
]

post_install = [
    "getent passwd caddy > /dev/null || useradd -r -d /var/lib/caddy -s /usr/sbin/nologin caddy",
    "systemctl daemon-reload || true",
]

pre_remove = [
    "systemctl stop caddy 2>/dev/null || true",
    "systemctl disable caddy 2>/dev/null || true",
]
```

### Python (pip install direto no source)

```toml
name         = "pip"
version      = "24.2"
description  = "Instalador de pacotes Python"
homepage     = "https://pip.pypa.io/"
license      = "MIT"

source        = "https://files.pythonhosted.org/packages/source/p/pip/pip-24.2.tar.gz"

build_system  = "custom"
steps = [
    "python3 setup.py build",
]
install_steps = [
    "python3 setup.py install --prefix=/usr --root=$DESTDIR",
]
```

---

## 8. Dependências com versão

Desde v0.4+, o campo `depends` aceita operadores de versão:

```toml
depends = [
    "openssl>=3.0",         # no mínimo 3.0
    "python<3.15",          # qualquer versão abaixo de 3.15
    "glibc>=2.40",          # no mínimo 2.40
    "curl=8.9.1",           # exatamente 8.9.1
    "bash!=5.0",            # qualquer bash exceto 5.0
    "zlib",                 # qualquer versão
]
```

### Operadores suportados

| Operador | Significado |
|----------|-------------|
| `>` | maior que |
| `>=` | maior ou igual |
| `<` | menor que |
| `<=` | menor ou igual |
| `=` | exatamente igual |
| `!=` | diferente de |
| `==` | alias de `=` |

### `provides` (nomes virtuais)

Para pacotes que substituem outros:

```toml
# /etc/thornspkg/recipes/bash.toml
name    = "bash"
version = "5.2.21"
provides = ["sh"]   # bash satisfaz qualquer dependência de "sh"
```

Agora, se outra receita tem `depends = ["sh"]`, o thornspkg sabe que
instalar `bash` satisfaz a dependência.

### `optional_deps`

Dependências instaladas **só se já estiverem presentes no sistema**. Útil
para features opcionais:

```toml
name         = "ffmpeg"
version      = "7.0"
description  = "Conjunto de ferramentas para áudio e vídeo"

# Estas dependências só são incluídas se já estiverem instaladas.
# Se não estiverem, o build prossegue sem elas (recursos desabilitados).
optional_deps = ["libx264", "libx265", "libvpx", "fdk-aac"]
```

---

## 9. Patches e sources múltiplos

### Aplicar patches

Crie o diretório `/etc/thornspkg/patches/<nome-do-pacote>/` e coloque
os patches lá:

```
/etc/thornspkg/
├── recipes/
│   └── bash.toml
└── patches/
    └── bash/
        ├── bash52-001.patch
        ├── bash52-002.patch
        └── bash52-003.patch
```

Na receita:

```toml
name         = "bash"
version      = "5.2.21"
provides     = ["sh"]
depends      = ["readline", "ncurses"]

source       = "https://ftp.gnu.org/gnu/bash/bash-5.2.21.tar.gz"
patches      = [
    "bash52-001.patch",
    "bash52-002.patch",
    "bash52-003.patch",
]

build_system   = "autotools"
configure_args = ["--without-bash-malloc"]
install_steps  = [
    "make install",
    "ln -sfv bash $DESTDIR/usr/bin/sh",  # cria symlink /bin/sh → bash
]

post_install = ["ldconfig"]
```

Os patches são aplicados via `patch -p1` antes do build.

### Caminho absoluto para patches

Para patches em local não-padrão:

```toml
patches = [
    "/home/user/my-patches/bash/custom.patch",
    "/etc/thornspkg/patches/bash/bash52-001.patch",
]
```

### Múltiplos sources

Alguns pacotes precisam de mais de um tarball:

```toml
name    = "gcc"
version = "14.2.0"

# Lista de sources — todos são baixados e extraídos no mesmo diretório
sources = [
    "https://ftp.gnu.org/gnu/gcc/gcc-14.2.0/gcc-14.2.0.tar.xz",
    "https://ftp.gnu.org/gnu/gcc/gcc-14.2.0/mpfr-4.2.1.tar.xz",
    "https://ftp.gnu.org/gnu/gcc/gcc-14.2.0/gmp-6.3.0.tar.xz",
    "https://ftp.gnu.org/gnu/gcc/gcc-14.2.0/mpc-1.3.1.tar.xz",
]

# sha256 alinhado com sources (lista tem mesmo comprimento)
sha256 = [
    "abc123...",   # gcc
    "def456...",   # mpfr
    "ghi789...",   # gmp
    "jkl012...",   # mpc
]

build_system   = "custom"
steps = [
    # Renomeia diretórios para os nomes esperados pelo gcc build
    "mv mpfr-4.2.1 mpfr",
    "mv gmp-6.3.0 gmp",
    "mv mpc-1.3.1 mpc",
    "mkdir -p build",
    "cd build && ../configure --prefix=/usr --enable-languages=c,c++ --disable-multilib",
    "cd build && make",
]
install_steps = ["cd build && make DESTDIR=$DESTDIR install"]
```

---

## 10. Hooks

Hooks são comandos shell executados em momentos específicos do ciclo de
vida do pacote.

### Quando cada hook roda

| Hook | Quando roda | Diretório atual |
|------|-------------|-----------------|
| `pre_build` | Antes do build | Diretório do source extraído |
| `post_install` | Após instalar no root | `/` (root real) |
| `pre_remove` | Antes de remover arquivos | `/` (root real) |
| `post_remove` | Após remover arquivos | `/` (root real) |

### Variáveis de ambiente disponíveis

| Variável | Valor |
|----------|-------|
| `DESTDIR` | Caminho do staging (em `install_steps`); vazio em `post_install` |
| `MAKEFLAGS` | `-j$(nproc)` por default |
| `PKG_CONFIG_PATH` | `$ROOT/usr/lib/pkgconfig:$ROOT/usr/share/pkgconfig` |
| Variáveis de `[env]` | Definidas na receita |

### Exemplos práticos

**Rodar `ldconfig` após instalar libs:**

```toml
post_install = ["ldconfig"]
post_remove  = ["ldconfig"]
```

**Reiniciar serviço após upgrade:**

```toml
post_install = [
    "systemctl daemon-reload",
    "systemctl restart myservico 2>/dev/null || true",
]
```

**Criar usuário antes de instalar:**

```toml
pre_build = [
    "getent group myservice >/dev/null || groupadd -r myservice",
    "getent passwd myservice >/dev/null || useradd -r -g myservice -d /var/lib/myservice -s /usr/sbin/nologin myservice",
]
```

**Atualizar banco de dados de manpages:**

```toml
post_install = ["mandb -q"]
post_remove  = ["mandb -q"]
```

**Limpar arquivos temporários antes de remover:**

```toml
pre_remove = [
    "rm -rf /var/cache/myservice",
    "systemctl stop myservice 2>/dev/null || true",
]
```

---

## 11. Variáveis de ambiente por receita

Defina `CFLAGS`, `LDFLAGS`, etc. específicos para cada pacote:

```toml
name         = "python"
version      = "3.12.4"
description  = "Linguagem de programação interpretada e de alto nível"

depends       = ["zlib", "bzip2", "xz", "ncurses", "readline", "openssl", "libffi", "sqlite"]

source        = "https://www.python.org/ftp/python/3.12.4/Python-3.12.4.tgz"

build_system   = "autotools"
configure_args = [
    "--enable-shared",
    "--with-system-expat",
    "--enable-optimizations",
]

[env]
CFLAGS  = "-O3 -pipe"
LDFLAGS = "-Wl,-O1"
```

Essas variáveis são mescladas com o ambiente do shell (variáveis da
receita têm prioridade sobre as do shell).

---

## 12. Metadados completos (v0.4+)

Use todos os campos opcionais para uma receita "profissional":

```toml
name          = "vim"
version       = "9.1"
description   = "Vi Improved — editor de texto programável"
homepage      = "https://www.vim.org/"
license       = "Vim"
maintainer    = "Bram Moolenaar <Bram@vim.org>"
repository    = "core"
architecture  = "x86_64"
build_date    = "2024-04-02"
install_size  = 44040192     # ~42 MB
download_size = 11000000     # ~11 MB

depends       = ["ncurses>=6.0"]
optional_deps = ["python", "ruby", "lua"]

source        = "https://github.com/vim/vim/archive/refs/tags/v9.1.0.tar.gz"
sha256        = "6ed6f7ec343d8a3a27e2b6a3d8d4e2a0f4a0b3d3c2e1f4a3b2c1d0e9f8a7b6c5"

build_system   = "make"
configure_args = [
    "CFLAGS=-O2 -pipe",
    "FEATURES=huge",
    "MULTI_UNICODE=yes",
]

post_install = [
    "ldconfig",
    "update-alternatives --install /usr/bin/editor editor /usr/bin/vim 50 || true",
]

[env]
CFLAGS  = "-O2 -pipe"
LDFLAGS = "-Wl,-O1"
```

---

## 13. Publicar a receita em um repositório

Receitas podem ser servidas por um repositório remoto para que outros
sistemas as usem sem precisar copiar arquivos manualmente.

### Estrutura no servidor

```
/var/www/thornspkg/
├── index.json
└── recipes/
    ├── htop.toml
    ├── tmux.toml
    └── ripgrep.toml
```

### A entrada no `index.json`

```json
{
    "schema_version": 1,
    "packages": {
        "htop": {
            "version": "3.3.0",
            "type": "recipe",
            "recipe": "recipes/htop.toml",
            "sha256": "<hex SHA256 do arquivo htop.toml>",
            "size": 916,
            "description": "Visualizador de processos interativo",
            "homepage": "https://htop.dev/",
            "license": "GPL-2.0-or-later",
            "maintainer": "Htop Authors <htop@example.org>",
            "architecture": "any",
            "depends": ["ncurses>=6.0"]
        }
    }
}
```

### Como o cliente baixa e usa

```sh
# Cliente configura o repo uma vez
sudo thorn repo add meu-repo https://meu-servidor.org/thornspkg/

# Sincroniza índices
sudo thorn sync

# Agora pode instalar receitas remotas
sudo thorn install htop
```

O thornspkg:
1. Baixa `https://meu-servidor.org/thornspkg/recipes/htop.toml`
2. Verifica SHA256 contra o `index.json`
3. Carrega a receita como se fosse local
4. Baixa o `source` da receita (URL externa)
5. Compila e instala

### Script para gerar `index.json`

Veja `examples/repo-example/scripts/gen_index.py` — ele percorre um
diretório de receitas e gera o `index.json` automaticamente com SHA256.

---

## 14. Testar a receita antes de publicar

### Teste local (sem repositório)

```sh
# 1. Coloque a receita em /etc/thornspkg/recipes/meupacote.toml
sudo cp meupacote.toml /etc/thornspkg/recipes/

# 2. Verifique dependências (sem instalar nada)
thorn deps meupacote

# 3. Veja a árvore de deps
thorn tree meupacote

# 4. Simule a instalação (não compila nada)
sudo thorn install meupacote --dry-run

# 5. Use --suggest-deps para descobrir dependências que faltam
thorn suggest-deps meupacote

# 6. Instale de verdade em um root de teste (sem afetar o sistema)
sudo thorn --root /tmp/test-root install meupacote

# 7. Verifique os arquivos instalados
find /tmp/test-root -type f
thorn --root /tmp/test-root files meupacote

# 8. Teste remover
sudo thorn --root /tmp/test-root remove meupacote
find /tmp/test-root -type f  # deve estar vazio
```

### Testar a receita remota antes de publicar

```sh
# Sirva o diretório local via HTTP
cd /path/to/repo-example
python -m http.server 8099 &

# Em outro terminal, teste como cliente
TEST_DB=/tmp/thorn-test-db
sudo thorn --db-dir $TEST_DB --repos-config /tmp/test-repos.json \
    repo add test http://127.0.0.1:8099/

sudo thorn --db-dir $TEST_DB --repos-config /tmp/test-repos.json sync

# Tente instalar
sudo thorn --db-dir $TEST_DB --repos-config /tmp/test-repos.json \
    --root /tmp/test-root install meupacote
```

---

## 15. Troubleshooting

### "pacote desconhecido 'X'"

Verifique:
- O arquivo `.toml` está em `/etc/thornspkg/recipes/`?
- O campo `name` dentro do TOML bate com o nome do arquivo?
- O TOML é válido? Teste: `python -c "import tomllib; tomllib.load(open('X.toml','rb'))"`

### "sha256 diverge para 'X'"

O SHA256 no campo `sha256` não bate com o tarball baixado. Recalcule:

```sh
curl -LO <url-do-source>
sha256sum <arquivo-baixado>
# Cole o hash no campo sha256 da receita
```

### "falhou (exit 2): ./configure"

Provavelmente faltam dependências de build (headers, libs). Use
`thorn suggest-deps <pacote>` para ver sugestões:

```sh
$ thorn suggest-deps meupacote
Dependências sugeridas (obrigatórias):
  libfoo      de: configure.ac
  libbar      de: meson.build
```

Adicione-as em `depends` e instale-as primeiro.

### "no rule to make target 'install'"

O build system não é autotools. Mude `build_system` para `make`, `cmake`,
`meson` ou `custom`.

### "permission denied" ao instalar

Use `sudo`:

```sh
sudo thorn install meupacote
```

Ou use `--root` para instalar em diretório não-sistema:

```sh
sudo thorn --root /tmp/test-root install meupacote
```

### "conflito de arquivos ao instalar 'X'"

O pacote tenta instalar um arquivo que já pertence a outro. Veja:

```sh
thorn owns /caminho/do/arquivo
```

Se for sobreposição legítima (ex: dois pacotes que fornecem o mesmo
binário), use `--force-overwrite`:

```sh
sudo thorn install meupacote --force-overwrite
```

### Patches não são aplicados

- O patch está em `/etc/thornspkg/patches/<nome>/`?
- O patch aplica com `patch -p1`? Teste manualmente:
  ```sh
  cd /tmp/source-extracted
  patch -p1 --dry-run < /etc/thornspkg/patches/meupacote/meu.patch
  ```

### `post_install` falha

`post_install` roda no root real (não no staging), com `DESTDIR=` vazio.
Se o comando precisa do DESTDIR, mova para `install_steps`.

---

## 16. Templates prontos para copiar

### Template mínimo (autotools)

```toml
name         = "PACOTE"
version      = "VERSAO"
description  = "DESCRICAO"
homepage     = "HOMEPAGE"
license      = "LICENCA"

source       = "URL_DO_TARBALL"
sha256       = "SHA256_AQUI"

build_system = "autotools"
```

### Template completo (autotools com deps e hooks)

```toml
name          = "PACOTE"
version       = "VERSAO"
description   = "DESCRICAO"
homepage      = "HOMEPAGE"
license       = "LICENCA"
maintainer    = "Seu Nome <voce@email.com>"
repository    = "core"
architecture  = "x86_64"

depends       = ["dep1>=1.0", "dep2"]
optional_deps = ["dep3"]

source        = "URL_DO_TARBALL"
sha256        = "SHA256_AQUI"

patches       = ["patch1.patch"]

build_system   = "autotools"
configure_args = ["--enable-foo", "--disable-bar"]

pre_build      = ["autoreconf -fi"]
post_install   = ["ldconfig"]

[env]
CFLAGS  = "-O2 -pipe"
LDFLAGS = "-Wl,-O1"
```

### Template CMake

```toml
name         = "PACOTE"
version      = "VERSAO"
description  = "DESCRICAO"
homepage     = "HOMEPAGE"
license      = "LICENCA"

depends       = ["dep1", "dep2"]
source        = "URL_DO_TARBALL"
sha256        = "SHA256_AQUI"

build_system   = "cmake"
configure_args = [
    "-DCMAKE_BUILD_TYPE=Release",
    "-DBUILD_SHARED_LIBS=ON",
]
```

### Template Meson

```toml
name         = "PACOTE"
version      = "VERSAO"
description  = "DESCRICAO"
homepage     = "HOMEPAGE"
license      = "LICENCA"

depends       = ["dep1", "dep2"]
source        = "URL_DO_TARBALL"
sha256        = "SHA256_AQUI"

build_system   = "meson"
configure_args = [
    "-Dfeature_a=enabled",
    "-Dfeature_b=disabled",
]
```

### Template custom (Rust/Go/etc.)

```toml
name         = "PACOTE"
version      = "VERSAO"
description  = "DESCRICAO"
homepage     = "HOMEPAGE"
license      = "LICENCA"
architecture = "x86_64"

source        = "URL_DO_TARBALL"
sha256        = "SHA256_AQUI"

build_system  = "custom"
steps = [
    "cargo build --release --locked",
]
install_steps = [
    "install -Dm755 target/release/PACOTE $DESTDIR/usr/bin/PACOTE",
    "install -Dm644 README.md $DESTDIR/usr/share/doc/PACOTE/README.md",
]

post_install = ["mandb -q || true"]
```

### Template para daemon (systemd)

```toml
name          = "meudaemon"
version       = "1.0"
description   = "Meu serviço de sistema"
homepage      = "https://meusite.com/"
license       = "GPL-3.0-or-later"
maintainer    = "Seu Nome <voce@email.com>"

depends       = ["glibc", "dbus"]

source        = "https://meusite.com/downloads/meudaemon-1.0.tar.gz"
sha256        = "SHA256_AQUI"

build_system  = "custom"
steps = [
    "make",
]
install_steps = [
    "install -Dm755 meudaemon $DESTDIR/usr/bin/meudaemon",
    "install -Dm644 meudaemon.service $DESTDIR/usr/lib/systemd/system/meudaemon.service",
    "install -Dm644 config.toml $DESTDIR/etc/meudaemon/config.toml",
    "install -d -m 0750 $DESTDIR/var/lib/meudaemon",
]

pre_build = [
    "getent group meudaemon >/dev/null || groupadd -r meudaemon",
    "getent passwd meudaemon >/dev/null || useradd -r -g meudaemon -d /var/lib/meudaemon -s /usr/sbin/nologin meudaemon",
]

post_install = [
    "systemctl daemon-reload || true",
    "systemctl enable meudaemon 2>/dev/null || true",
]

pre_remove = [
    "systemctl stop meudaemon 2>/dev/null || true",
    "systemctl disable meudaemon 2>/dev/null || true",
]

post_remove = [
    "systemctl daemon-reload || true",
    "getent passwd meudaemon >/dev/null && userdel meudaemon 2>/dev/null || true",
    "getent group meudaemon >/dev/null && groupdel meudaemon 2>/dev/null || true",
]
```

---

## Checklist final antes de publicar

- [ ] O `name` bate com o nome do arquivo `.toml`
- [ ] O `version` bate com a versão do source baixado
- [ ] O `sha256` foi calculado a partir do tarball real (não copiado de outro lugar)
- [ ] Testei com `thorn deps PACOTE`
- [ ] Testei com `sudo thorn install PACOTE --dry-run`
- [ ] Testei com `sudo thorn --root /tmp/test-root install PACOTE`
- [ ] Verifiquei os arquivos instalados com `find /tmp/test-root -type f`
- [ ] Testei remover com `sudo thorn --root /tmp/test-root remove PACOTE`
- [ ] Se publica em repo: rodei `python scripts/gen_index.py` para regenerar `index.json`
- [ ] Se publica em repo: testei com `thorn sync && thorn install PACOTE` de um cliente

---

## Referência rápida dos build systems

| `build_system` | Comando de build | Comando de install |
|----------------|------------------|--------------------|
| `autotools` (default) | `./configure --prefix=X && make -jN` | `make install` |
| `make` | `make -jN PREFIX=X` | `make install PREFIX=X` |
| `cmake` | `cmake -B _build -DCMAKE_INSTALL_PREFIX=X && cmake --build _build -jN` | `cmake --install _build` |
| `meson` | `meson setup _build --prefix=X && ninja -C _build -jN` | `ninja -C _build install` |
| `custom` | Comandos em `steps[]` | Comandos em `install_steps[]` (default: `["make install"]`) |
