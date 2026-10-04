# Seminário PySUS: do terminal ao show de gestos

Seminário sobre a biblioteca **PySUS**, apresentado em duas versões:

1. **O começo (versão 1):** um menu no terminal que explora dados epidemiológicos.
2. **A evolução (versão 2):** o mesmo menu, agora controlado pela mão diante da câmera,
   com os dados desenhados em pontos de luz.

---

## Duas formas de ver os mesmos dados: a antiga e a nova

As duas versões têm as mesmas opções de menu e usam a mesma simulação de dados. O que muda
é **como você escolhe** e **como os dados aparecem**.

| | Antiga: terminal (versão 1) | Nova: show de gestos (versão 2) |
|---|---|---|
| **Como escolher** | Digitar o número da opção e o código da doença ou do estado | Apontar com o indicador e segurar, ou fazer a pinça |
| **Como os dados aparecem** | Texto, tabelas e barras de caracteres (`▮▮▮`), feitos com a biblioteca Rich | Gráficos feitos de milhares de pontos de luz que voam até o lugar |
| **[1] Sobre PySUS** | Painel de texto com a versão e as bases | "PySUS" em pontos de luz e a lista das bases |
| **[2] Comparação por Doença** | Uma doença por vez, num ano sorteado: resumo, sexo e estados | As 10 doenças lado a lado em barras (ano 2026); apontar uma barra abre a evolução dela |
| **[3] Evolução Temporal** | Ano a ano (2020–2026), em texto com barras `▮` | Gráfico de linha; apontar um ano mostra os detalhes |
| **[4] Distribuição Geográfica** | Tabela dos estados mais afetados (2026) | Mapa do Brasil em bolhas de luz, mais o ranking |
| **[5] Internações (SIH)** | Digitar o estado; mês e ano sorteados | Botões de estados; mês fixo (06/2026) |
| **[6] Mortalidade (SIM)** | Digitar o estado; ano sorteado | Botões de estados; ano fixo (2026) |
| **Só na versão nova** | | Enxame da dengue, pegar doença no ar, aceno de tchau |

**Os números batem quando o ano e o mês são os mesmos.** A Evolução (2020–2026) e a
Distribuição Geográfica (2026) mostram exatamente os mesmos valores nas duas versões. Nas
opções 2, 5 e 6, o terminal **sorteia** o ano (e o mês, no SIH) a cada consulta, enquanto
o show usa um ano fixo. Por isso, ali, os valores só coincidem quando o terminal sorteia o
mesmo ano e mês do show.

**No cantinho da tela do show** fica o crédito das duas bibliotecas principais: **PySUS** em
destaque, porque é o tema do seminário, e, menor, embaixo, **MediaPipe | Google**, a
biblioteca que enxerga a mão.

---

## O que é o PySUS

O [PySUS](https://github.com/AlertaDengue/PySUS) é uma biblioteca Python de código aberto,
mantida pela equipe do projeto **AlertaDengue**. Ela baixa os dados públicos do
**DATASUS**, o departamento de informática do SUS, e os entrega prontos para análise
como tabelas do `pandas`.

Sem o PySUS, quem quer esses dados precisa entrar no servidor do DATASUS, baixar arquivos
num formato antigo e compactado (`.dbc`) e convertê-los por conta própria. O PySUS faz isso
em poucas linhas de código.

### As bases de dados que o PySUS acessa

| Base | Nome completo | O que registra |
|---|---|---|
| **SINAN** | Sistema de Informação de Agravos de Notificação | Doenças de notificação obrigatória: dengue, zika, chikungunya, tuberculose, hanseníase, malária, meningite, hepatites... |
| **SIH** | Sistema de Informações Hospitalares | Internações pagas pelo SUS: diagnóstico, dias de permanência, valor pago |
| **SIM** | Sistema de Informações sobre Mortalidade | Óbitos e suas causas (pela CID-10) |
| **SINASC** | Sistema de Informações sobre Nascidos Vivos | Nascimentos: peso, tipo de parto, idade da mãe |
| **CNES** | Cadastro Nacional de Estabelecimentos de Saúde | Hospitais, postos, leitos e equipamentos |
| **SIA** | Sistema de Informações Ambulatoriais | Atendimentos e procedimentos fora da internação |
| **PNI** | Programa Nacional de Imunizações | Doses de vacina aplicadas |

### Os campos que aparecem neste projeto

- **SINAN:** estado da notificação (`SG_UF_NOT`), ano (`NU_ANO`), doença (`ID_AGRAVO`),
  idade (`NU_IDADE_N`), sexo (`CS_SEXO`) e evolução do caso (`EVOLUCAO`).
- **SIH:** diagnóstico principal pela CID-10 (`DIAG_PRINC`), valor total (`VAL_TOT`),
  dias de permanência (`DIAS_PERM`), idade e sexo.
- **SIM:** causa básica do óbito pela CID-10 (`CAUSABAS`), data do óbito (`DTOBITO`),
  idade e sexo.

A **CID-10** é a Classificação Internacional de Doenças. Cada doença tem um código:
`A90` é dengue, `A15` é tuberculose, `J18` é pneumonia, `I21` é infarto, e assim por diante.

### Um aviso honesto sobre os números

Os arquivos reais do DATASUS são muito grandes. Um único ano de dengue tem milhões de
linhas, e baixá-lo durante uma apresentação seria lento e arriscado. Por isso o projeto
**simula** os dados com a mesma estrutura de colunas das bases reais
(`src/epidemiology_service.py`). A chamada ao PySUS de verdade está no código, comentada,
no ponto exato onde ela entraria.

A simulação usa uma "semente" fixa: o mesmo pedido gera sempre os mesmos números. O show
de gestos repete exatamente os mesmos sorteios (`gestos/dados.py`), então **o terminal e o
show mostram os mesmos valores**. São números ilustrativos, não dados oficiais.

---

## As bibliotecas usadas

### Versão 1: o terminal

| Biblioteca | Para que serve aqui |
|---|---|
| **PySUS** | O tema do seminário: a ponte entre o Python e os dados do SUS |
| **pandas** | Organiza os dados em tabelas (DataFrames) e faz as contagens: casos por estado, por sexo, por faixa de idade |
| **Rich** | Deixa o terminal bonito: painéis com borda, tabelas coloridas e barras feitas de caracteres |

### Versão 2: o show de gestos

| Biblioteca | Para que serve aqui |
|---|---|
| **MediaPipe** (Google) | Uma rede neural que encontra a mão na imagem da câmera e devolve 21 pontos: punho, juntas e pontas dos dedos |
| **OpenCV** | Abre a câmera, cria a janela e desenha tudo: textos, botões, círculos e o brilho neon |
| **NumPy** | Move milhares de pontos de luz ao mesmo tempo. Cada ponto é puxado para o seu lugar como por uma mola com atrito, e o NumPy calcula todos de uma vez, sem um laço por ponto |

### Como os gestos são reconhecidos

O MediaPipe só entrega os 21 pontos da mão. O gesto é decidido pelo nosso código, apenas
com distâncias entre esses pontos:

- **Punho fechado:** nenhum dos quatro dedos tem a ponta mais longe do pulso do que a junta do meio.
- **Pinça:** a ponta do polegar fica perto da ponta do indicador, em relação ao tamanho da mão.
- **Apontar e segurar:** a ponta do indicador fica parada sobre um botão por cerca de 1 segundo.
- **Tchau:** a mão aberta vai e volta para os lados pelo menos três vezes em 1,6 segundo.

Para evitar que a imagem "trema", cada gesto passa por uma votação entre os últimos 5
quadros da câmera antes de valer.

---

## Como rodar (Windows)

Tudo por dois cliques, sem digitar comandos:

| Atalho | O que faz |
|---|---|
| `Abrir Terminal PySUS.bat` | Abre o menu do terminal (versão 1) |
| `Abrir Show PySUS.bat` | Abre o show de gestos (versão 2) |
| `Atualizar do GitHub.bat` | Traz as novidades do GitHub para o computador |

Na primeira vez em um computador, cada atalho prepara o seu ambiente sozinho (`venv` para o
terminal, `venv_gestos` para o show). Isso leva alguns minutos e precisa de internet e do
Python 3.12. Os dois ambientes são separados porque os programas pedem versões diferentes
do `numpy`. Na primeira vez, o show também baixa o modelo da mão.

### O que é um `.bat`

Um `.bat` é **um arquivo cheio de comandos guardados**, que o Windows executa sozinho, na
ordem, quando você dá dois cliques. A janela preta que aparece é o Windows trabalhando (o
**cmd**, o intérprete de comandos antigo do Windows): não é preciso digitar nada nela.

- O `.bat` só existe no **Windows**. No Mac e no Linux, o equivalente é um arquivo `.sh`.
- O show em si é Python e funciona em qualquer sistema; só o atalho muda.
- Para ver o que um `.bat` faz antes de rodar: botão direito > **Editar**.

### Usando pelo VS Code

Tudo pode ser feito pelo VS Code, sem abrir o cmd:

1. **Abra a pasta certa:** File > Open Folder... > `C:\seminario_biblioteca`. Assim o terminal
   do VS Code já abre nela e mostra `PS C:\seminario_biblioteca>` (o `PS` é o **PowerShell**,
   o terminal moderno do Windows).
2. **Abra o terminal:** menu Terminal > New Terminal.
3. **Rode um atalho pelo terminal:** digite `.\Abrir` e aperte **Tab** até aparecer o atalho
   desejado (o VS Code completa com `& '.\Abrir Show PySUS.bat'`), depois **Enter**.
4. **Ou sem digitar:** botão direito no `.bat` na lista à esquerda > **Reveal in File Explorer**,
   e dois cliques no arquivo.

### Roteiro do show

1. **O terminal vira luz:** o menu antigo aparece em pontos verdes. Feche o punho e ele se desfaz.
2. **Enxame da dengue:** os pontos seguem a mão como mosquitos. Punho junta, mão aberta solta.
   Depois de alguns segundos, aponte para **ABRIR MENU** no canto.
3. **Menu de gestos:** as mesmas opções do terminal. Aponte e segure, ou faça a pinça:
   `1` Sobre · `2` Comparação por doença · `3` Evolução temporal · `4` Distribuição geográfica ·
   `5` Internações (SIH) · `6` Mortalidade (SIM) · `7` Pegar doença no ar · `0` Encerrar
4. **Tchau:** acene com a mão aberta (para os lados, umas duas vezes) e aparece a tela final.
   Nela, aponte **SAIR** e segure para fechar o show.

**Teclas de emergência:** `ESPAÇO` avança ou volta ao menu · `1` a `7` e `0` abrem as telas ·
`BACKSPACE` volta ao menu · `M` troca mão/mouse · `F` tela cheia · `H` esconde as dicas ·
`R` recomeça · `ESC` sai.
