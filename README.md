# Seminário PySUS: do terminal ao show de gestos

Seminário sobre a biblioteca **PySUS**, apresentado em duas versões:

1. **O começo (versão 1):** um menu no terminal que explora dados epidemiológicos.
2. **A evolução (versão 2):** o mesmo menu, agora controlado pela mão diante da câmera,
   com os dados desenhados em pontos de luz.

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

Para evitar que a imagem "trema", cada gesto passa por uma votação entre os últimos 5
quadros da câmera antes de valer.

---

## Como rodar (Windows)

Os dois programas usam ambientes separados, porque pedem versões diferentes do `numpy`.

**Terminal (versão 1):**

```
py -3.12 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

Depois, dois cliques em `abrir_terminal.bat`.

**Show de gestos (versão 2):**

```
py -3.12 -m venv venv_gestos
venv_gestos\Scripts\python.exe -m pip install -r gestos\requirements.txt
```

Depois, dois cliques em `abrir_show.bat`. Na primeira vez o show baixa o modelo da mão,
então precisa de internet.

### Roteiro do show

1. **O terminal vira luz:** o menu antigo aparece em pontos verdes. Feche o punho e ele se desfaz.
2. **Enxame da dengue:** os pontos seguem a mão como mosquitos. Punho junta, mão aberta solta.
   Depois de alguns segundos, aponte para **ABRIR MENU** no canto.
3. **Menu de gestos:** as mesmas opções do terminal. Aponte e segure, ou faça a pinça:
   `1` Sobre · `2` Comparação por doença · `3` Evolução temporal · `4` Distribuição geográfica ·
   `5` Internações (SIH) · `6` Mortalidade (SIM) · `7` Pegar doença no ar · `0` Encerrar

**Teclas de emergência:** `ESPAÇO` avança ou volta ao menu · `1` a `7` e `0` abrem as telas ·
`BACKSPACE` volta ao menu · `M` troca mão/mouse · `F` tela cheia · `H` esconde as dicas ·
`R` recomeça · `ESC` sai.
