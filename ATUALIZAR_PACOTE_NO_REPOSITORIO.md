# Como atualizar um pacote no repositório

Este guia mostra o workflow completo para atualizar um pacote no repositório
thornspkg — desde a construção do novo tarball até a propagação para os
clientes.

## Visão geral do fluxo

```
[mantenedor do repo]                      [clientes]

  1. Construir novo tarball v2                 |
  2. Atualizar entrada em gen_index.py        |
  3. Rodar gen_index.py (regenera index.json) |
  4. Publicar no servidor HTTP                |
                                              |
                                          5. thorn sync        ← baixa novo index.json
                                          6. thorn list-upgrades ← vê que v1 → v2
                                          7. thorn upgrade pkg  ← instala v2, remove arquivos obsoletos
```

## Pré-requisitos

- O repositório já existe (ver `examples/repo-example/README.md` para criar um novo)
- Você tem acesso de escrita ao diretório do repositório no servidor
- O `gen_index.py` está configurado com a entrada do pacote

## Passo a passo

### Exemplo: atualizar `hello` de 1.0 para 1.1

#### 1. Construir o novo tarball binário

```sh
cd examples/repo-example

# A versão é controlada pela variável VERSION
VERSION=1.1 bash scripts/build_hello_pkg.sh
```

Saída esperada:
```
✓ Criado: packages/hello-1.1-x86_64.tar.gz
  Tamanho: 478 bytes
  SHA256:  378bf67d062d1e53884c71c27e120ae282f851f5d06a3bf94470972e1f305d98
```

> **Importante**: o tarball deve conter a estrutura **completa** a partir do
> root (ex: `usr/bin/hello`, `usr/share/man/man1/hello.1`). NÃO inclua um
> diretório pai — o thornspkg extrai direto no root.

#### 2. Atualizar a entrada em `scripts/gen_index.py`

Abra `scripts/gen_index.py` e localize a entrada do pacote na lista `PKGS`:

```python
PKGS = [
    {
        "name": "hello",
        "version": "1.0",                          # ← mudar para "1.1"
        "type": "binary",
        "url": "packages/hello-1.0-x86_64.tar.gz", # ← mudar para hello-1.1-...
        "depends": [],
        "description": "Programa de exemplo: imprime 'hello'",
        "homepage": "https://example.org/hello",
        "license": "MIT",
        "maintainer": "Example <dev@example.org>",
        "architecture": "x86_64",
        "build_date": "2026-06-25",                # ← atualizar data
    },
    # ... outros pacotes
]
```

Mude `version`, `url` e `build_date` para a nova versão:

```python
        "version": "1.1",
        "type": "binary",
        "url": "packages/hello-1.1-x86_64.tar.gz",
        "build_date": "2026-06-26",
```

#### 3. Regenerar o `index.json`

```sh
python scripts/gen_index.py
```

O script recalcula o SHA256 do novo tarball automaticamente e reescreve
`index.json`:

```
✓ Gerado: /path/to/repo-example/index.json
  5 pacote(s) no índice:
    goodbye      1.0        [binary] sha256=5581b9f3afff3ee1…
    hello        1.1        [binary] sha256=378bf67d062d1e53…  ← novo
    htop         3.3.0      [recipe] sha256=671e70579e457d71…
    ripgrep      14.1.0     [recipe] sha256=519eefa1dae82697…
    tmux         3.4        [recipe] sha256=4996c757966830dc…
```

#### 4. Publicar no servidor

Se você já está servindo o diretório via HTTP estático (`python -m http.server`
ou nginx/caddy), não precisa fazer nada — o novo `index.json` e o novo tarball
já estão visíveis imediatamente.

#### 5. No cliente: sincronizar

```sh
sudo thorn sync
```

Saída:
```
  ↓  local: http://127.0.0.1:8099/index.json
  ✓  local: 5 pacote(s) no índice
✓ refresh concluído.
```

#### 6. Verificar atualizações disponíveis

```sh
thorn list-upgrades
```

Saída:
```
Pacotes desatualizados (1):
  Pacote          Instalado     → Disponível    Origem
  ──────────────── ──────────────   ────────────── ────────
  hello            1.0           → 1.1           repo
```

#### 7. Atualizar

```sh
sudo thorn upgrade hello
```

Saída:
```
Pacotes a atualizar (1):
  hello                    1.0 → 1.1
  ↓  http://127.0.0.1:8099/packages/hello-1.1-x86_64.tar.gz
  ✓  checksum OK

[1/1] ==> hello-1.1 (binário)
  →  /
  ✓  2 arquivos instalados (binário)
  ♻  0 arquivo(s) obsoleto(s) removido(s) da versão anterior

✓ 1 pacote(s) atualizado(s).
```

## Casos especiais

### Remover arquivos na nova versão

Se a nova versão do pacote **removeu** arquivos que existiam na versão antiga
(ex: `legacy.txt` foi removido em v2), o thornspkg remove esses arquivos
automaticamente do root durante o upgrade:

```
[1/1] ==> demo-2.0 (binário)
  →  /
  ✓  2 arquivos instalados (binário)
  ♻  1 arquivo(s) obsoleto(s) removido(s) da versão anterior  ← legacy.txt limpo
```

Isso é feito pelo helper `cleanup_obsolete_files()` em `commands/common.py`,
chamado tanto por `thorn install` (em reinstalações) quanto por `thorn upgrade`.

### Adicionar dependências na nova versão

Se a nova versão adicionou dependências novas, basta incluí-las no campo
`depends` do `index.json`. O resolvedor do thornspkg vai instalá-las
automaticamente antes do pacote principal:

```python
# Em gen_index.py, entrada do hello v1.1:
{
    "name": "hello",
    "version": "1.1",
    "type": "binary",
    "url": "packages/hello-1.1-x86_64.tar.gz",
    "depends": ["ncurses>=6.0"],   # ← nova dependência
    ...
}
```

### Mudar dependências com versão

O thornspkg v0.4+ suporta operadores de versão em `depends`. Se a nova versão
exige uma versão mínima diferente:

```python
"depends": ["openssl>=3.0"]   # era "openssl>=1.1" antes
```

Se o cliente tem `openssl 2.9` instalado, o upgrade vai falhar com
`VersionConflictError`:
```
erro: versão instalada de 'openssl' (2.9) não satisfaz constraint 'openssl>=3.0'
```

O cliente precisa fazer `thorn upgrade openssl` primeiro.

### Atualizar uma receita remota (type=recipe)

Para receitas que são compiladas localmente, o processo é similar:

1. Edite o arquivo `.toml` em `recipes/` (mude `version`, `source`, `sha256`,
   `depends`, etc.)
2. Rode `python scripts/gen_index.py` (recalcula SHA256 do `.toml`)
3. Publique
4. No cliente: `thorn sync && thorn upgrade <pkg>`

O thornspkg vai baixar a nova receita, verificar SHA256, e recompilar
localmente.

### Atualizar múltiplos pacotes de uma vez

Se vários pacotes mudaram, basta regenerar `index.json` uma vez. O cliente
roda `thorn sync && thorn upgrade` e todos os pacotes desatualizados são
atualizados na ordem correta (respeitando dependências).

### Rollback para versão anterior

O thornspkg não tem comando nativo de rollback, mas você pode simular:

```sh
# 1. No repositório, mantenha o tarball da versão anterior
#    (não apague packages/hello-1.0-x86_64.tar.gz)

# 2. Mude a entrada em gen_index.py de volta para 1.0
# 3. Rode gen_index.py
# 4. Publique

# 5. No cliente:
sudo thorn sync
sudo thorn upgrade hello --reinstall   # força reinstalação
```

> **Atenção**: o comparador de versões do thornspkg trata 1.0 < 1.1, então
> `thorn list-upgrades` não mostra 1.0 como "atualização". Use
> `thorn upgrade hello --reinstall` para forçar o downgrade.

## Boas práticas

1. **Sempre inclua SHA256 no index.json** — protege contra adulteração e
   downloads corrompidos. O `gen_index.py` faz isso automaticamente.

2. **Versione os tarballs no nome do arquivo** — `hello-1.0-x86_64.tar.gz`
   em vez de `hello.tar.gz`. Permite manter múltiplas versões lado a lado
   para rollback.

3. **Não apague tarballs antigos imediatamente** — mantenha pelo menos a
   versão anterior por algumas semanas para permitir rollback.

4. **Teste localmente antes de publicar** — use `python -m http.server`
   para servir o repositório localmente e teste `thorn sync && thorn upgrade`
   antes de propagar para produção.

5. **Bump em `generated_at`** — o `gen_index.py` atualiza automaticamente
   o timestamp, mas vale confirmar que o `index.json` mudou.

6. **Use `thorn upgrade --atomic` em produção** — em caso de erro, faz
   rollback automático dos arquivos instalados.

7. **Migre `depends` gradualmente** — se vai adicionar uma constraint de
   versão nova (ex: `openssl>=3.0`), primeiro publique a nova versão do
   `openssl`, depois a dos pacotes que dependem dele.

## Troubleshooting

### "Nada a fazer — todos os pacotes já estão na versão mais recente"

Mas você sabe que há uma versão nova. Verifique:
1. Você rodou `thorn sync`? (baixa o novo índice)
2. O `index.json` no servidor tem a versão nova? (`curl http://servidor/index.json`)
3. O SHA256 no `index.json` bate com o tarball real?

### "sha256 diverge para binário 'hello'"

O `index.json` tem um SHA256 que não bate com o tarball no servidor. Rode
`python scripts/gen_index.py` no servidor para regenerar.

### "conflito de arquivos ao instalar 'hello'"

A nova versão tenta instalar um arquivo que pertence a outro pacote. Ou:
- O tarball inclui um arquivo que não deveria (verifique com `tar -tzf`)
- Você precisa usar `--force-overwrite` (não recomendado)

### Após upgrade, arquivos antigos permanecem no root

Isso era um bug em versões anteriores do thornspkg (pré-v0.4.1). A partir
da v0.4.1, o helper `cleanup_obsolete_files()` remove automaticamente
arquivos do manifest antigo que não estão no novo. Se você ainda vê esse
problema, verifique que está usando a versão mais recente do thornspkg.

### Verificar integridade após upgrade

```sh
sudo thorn check hello    # verifica SHA256 de cada arquivo instalado
sudo thorn files hello    # lista os arquivos atuais
sudo thorn owns /usr/bin/hello   # confirma ownership
```
