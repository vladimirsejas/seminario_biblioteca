# Relatório de análise — Projeto MISM
**Mapa de internações oncológicas de mulheres — Rio Claro (SP), 2021–2025**

Data da análise: 06/10/2026
Material analisado: `MISM-main.zip` (3 scripts Python + README)
Natureza do trabalho: **somente leitura**. Nenhum arquivo do projeto foi alterado ou executado.

---

## 1. Resumo executivo

- O MISM é um pipeline em Python que transforma o **CEP** de cada internação oncológica feminina (SIH/SUS, via PySUS) em **bairro + coordenada**, e gera um **mapa web interativo** (um único HTML com Leaflet).
- A ideia está bem estruturada e o mapa tem bons recursos (filtros, heatmap, ranking, legenda). Porém, a **ligação entre CEP, bairro e polígono do bairro é o ponto mais frágil**: ela depende de nomes escritos de forma idêntica e de apenas 21 polígonos.
- Há um **risco de privacidade (LGPD)** que contradiz o próprio README: o HTML gerado embute dados por caso, incluindo CEP e coordenadas.
- O ZIP **não contém os dados nem os GeoJSON**, então nada pôde ser executado nem medido. Tudo abaixo vem da leitura do código.
- O texto sobre o mapa oficial da Prefeitura, os Correios/DNE e a lista de 182 bairros **não foi verificado** (não foi possível abrir as fontes). O raciocínio é coerente, mas os fatos precisam ser conferidos.

---

## 2. O que existe no repositório

| Arquivo | Linhas | Função |
|---|---|---|
| `readme.md` | 108 | Planejamento: objetivo, fontes, arquitetura prevista, LGPD, roadmap |
| `georreferenciar_dados.py` | 220 | Junta os CSVs por doença e converte CEP em bairro/logradouro/lat/lon |
| `gerar_clusters_bairro.py` | 159 | Agrupa casos por bairro e obtém um ponto "cluster" por bairro |
| `gerar_mapa.py` | 1341 | Gera o HTML do mapa (CSS, HTML e JS dentro de uma f-string) |

**Arquivos que os scripts esperam, mas não vieram no ZIP:**
- `dados/brutos/*.csv` (7 arquivos, um por tipo de câncer)
- `dados/referencia/municipio_rio_claro.geojson`
- `bairros_rio_claro_21_bairros.geojson` (polígonos dos bairros)
- caches e saídas intermediárias em `dados/cache/` e `dados/processados/`

---

## 3. Como o pipeline funciona

```
CSVs do PySUS (1 por doença, coluna CEP)
        │
        ▼  georreferenciar_dados.py
CEP → logradouro + bairro + latitude/longitude   (cache: ceps_rio_claro.json)
        │
        ▼  gerar_clusters_bairro.py
casos agrupados por bairro + estatísticas + ponto "cluster"
        │
        ▼  gerar_mapa.py
HTML único: polígonos, clusters, heatmap, filtros, ranking
```

### 3.1 `georreferenciar_dados.py`
1. Lê os 7 CSVs, marca cada linha com o tipo de doença e junta tudo.
2. Normaliza o CEP (só dígitos, 8 posições com zero à esquerda).
3. Para cada CEP único, consulta em cascata (até 6 requisições simultâneas):
   1. **BrasilAPI v2**: rua, bairro e coordenadas.
   2. **AwesomeAPI**: coordenadas, se faltarem.
   3. **ViaCEP**: bairro, se ainda estiver vazio.
   4. **Nominatim/OSM**: coordenada pelo nome do bairro.
   5. **Fallback**: ponto perto do centro da cidade, com deslocamento calculado por `hash(cep)`.
4. Descarta coordenadas fora de uma caixa em torno de Rio Claro.
5. Grava o CSV unificado, com `BAIRRO`, `LOGRADOURO`, `LATITUDE`, `LONGITUDE`, `FONTE_GEO`.

### 3.2 `gerar_clusters_bairro.py`
- Agrupa os registros pelo texto da coluna `BAIRRO`.
- Calcula, por bairro: nº de casos, idade média/mínima/máxima, casos por ano, valor SUS total e lista de CEPs.
- Para posicionar o "cluster", busca o nome do bairro (e a rua do primeiro CEP) no **Photon** (geocodificador do OSM). Um filtro por termos distintivos tenta evitar resultados de outras cidades.
- Resultado: o ponto do cluster vem de **busca por nome**, não do centro de um polígono.

### 3.3 `gerar_mapa.py`
- Monta uma lista de registros (um por internação) e **a embute inteira no HTML**.
- Carrega o limite municipal e o GeoJSON de bairros (21 polígonos).
- Camadas: polígonos coloridos por nº de casos, clusters, heatmap e limite municipal.
- Filtros: doença, ano, faixa etária. Ranking de bairros com busca. Quatro mapas-base.
- **A ligação dado ↔ polígono é feita por comparação exata de texto** entre `BAIRRO` e `feature.properties.bairro`.

---

## 4. Pontos de melhoria (do mais grave ao menos grave)

### 4.1 CRÍTICO — Privacidade e LGPD
- **Onde:** `gerar_mapa.py`, linhas 84–98 (montagem dos registros) e 899 (`const rawData = ...`).
- **O que acontece:** cada internação é gravada no HTML com **CEP, rua, latitude/longitude, idade, ano, valor, dias de internação e óbito**. Quem abrir o arquivo e inspecionar o código consegue ler tudo.
- **Contradição:** o README afirma que o CEP não é armazenado no que alimenta o site, que só dados agregados são expostos e que haveria supressão de números pequenos. Hoje nada disso é cumprido.
- **Agravante:** a legenda mostra faixas "1–2 casos", e em bairros pequenos isso aumenta o risco de reidentificação (dado de saúde é dado sensível).
- **Correção sugerida:** publicar apenas bairro × ano × contagem, aplicar regra de supressão (por exemplo, "< 5 casos") e nunca embutir CEP, rua ou coordenada individual.

### 4.2 ALTO — Ligação por nome entre bairro e polígono
- **Onde:** `gerar_mapa.py`, linhas 1112 e 1156–1158 (comparação exata de texto).
- **Problema:** o bairro dos casos vem do CEP (Correios/ViaCEP) e o polígono tem outro nome. Qualquer diferença de grafia, acento, "II" ou "Jardim" faz o bairro aparecer com **0 casos**, mesmo havendo casos reais.
- **Cobertura:** o GeoJSON se chama "21_bairros". Se o município tem na ordem de 182 bairros postais, a maioria dos casos **não tem polígono**.
- **Correção sugerida:** ligar por **geografia** (ponto dentro do polígono) e manter uma tabela de equivalência `nome_correios → nome_prefeitura`, com lista de revisão manual para os que não casarem.

### 4.3 ALTO — Coordenadas falsas misturadas com as reais
- **Onde:** `georreferenciar_dados.py`, linhas 135–143 (fallback) e 55 (cache).
- **Problemas:**
  1. O fallback grava um ponto aleatório no centro como se fosse coordenada real. Esses pontos entram no heatmap e formam uma "mancha" artificial no centro.
  2. A linha 55 só refaz a consulta se `lat` for `None`. Como o fallback preenche `lat`, o CEP fica **para sempre** com a coordenada falsa no cache.
  3. `hash(cep_str)` de texto muda a cada execução do Python (aleatorização por processo), então o mapa **não é reprodutível**.
  4. O bairro vira "Rio Claro (Geral)", que aparece como se fosse um bairro.
- **Correção sugerida:** guardar a **qualidade** do ponto (CEP exato, só bairro, sem localização) e **excluir** os sem localização do heatmap e dos clusters. Não inventar coordenadas.

### 4.4 MÉDIO — Erros silenciosos
- **Onde:** `georreferenciar_dados.py` (vários `except Exception: pass`) e `gerar_clusters_bairro.py` (linha 66).
- **Problema:** falha de internet, limite de uso da API ou bloqueio viram simplesmente "sem resultado". O usuário não sabe se o CEP não existe ou se a API falhou.
- **Correção sugerida:** registrar o erro (log) e contar quantos CEPs falharam, por fonte.

### 4.5 MÉDIO — Uso das APIs públicas
- **Nominatim** (política pública) permite no máximo cerca de 1 requisição por segundo. O código usa 6 tarefas simultâneas, e o Photon em `ThreadPoolExecutor(max_workers=6)`.
- **Risco:** bloqueio de IP e dados incompletos.
- **Sugestão:** reduzir a concorrência nesses serviços e manter o cache.

### 4.6 MÉDIO — Cluster por nome em vez de centroide
- O ponto de cada bairro vem de uma busca por texto no OSM, que pode devolver uma rua, uma loja ou um bairro homônimo.
- Quando houver polígono oficial, usar o **centroide do polígono**.

### 4.7 MÉDIO — O que o dado realmente mede
- O README já alerta, mas o mapa ainda diz "casos". São **internações (AIH)**, e não pessoas nem incidência. Uma mesma paciente pode gerar várias internações.
- Sem **população por bairro** não dá para calcular taxa por 100 mil. Comparar bairros só por contagem favorece os mais populosos.
- A confirmação da fonte exata do PySUS (SIH/SISCAN/SIM) continua pendente no README, embora o painel já diga "SIH/SUS SP".

### 4.8 BAIXO — Organização e manutenção
- `Path(__file__).resolve().parents[2]` exige que os scripts fiquem duas pastas abaixo da raiz. No ZIP, solto na raiz, apontaria para fora do repositório.
- Os limites de latitude/longitude são diferentes entre os scripts (`-22.60..-22.20` e `-22.51..-22.31`).
- `gerar_mapa.py` mistura Python, CSS, HTML e JavaScript numa **f-string de 1.200 linhas**, com chaves duplicadas (`{{ }}`). Fica difícil de editar. Melhor separar em template HTML + arquivos de dados.
- O texto "Todas (7)" e o dicionário de CID estão fixos no código.
- Não há `requirements.txt` neste ZIP, testes automatizados nem documentação de como rodar.
- Bibliotecas por CDN (Leaflet.heat, Phosphor) sem verificação de integridade; nomes de bairro entram no HTML via `innerHTML`.
- O README está desatualizado: diz "ainda não há implementação de código" e que a Prefeitura não tem malha de bairros.

---

## 5. Sobre o texto recebido (mapa da Prefeitura, Correios/DNE, 182 bairros)

| Afirmação | Situação |
|---|---|
| Existe um mapa municipal oficial com bairros, em escala 1:12.500, SIRGAS 2000 / UTM | **Não verificado.** Provavelmente PDF ou imagem. |
| Os Correios cadastram bairros, logradouros e CEPs no DNE; o DNE é a base oficial | Plausível. O DNE é **licenciado**, e terceiros podem ter cópias incompletas. |
| Existe lista de 182 bairros de Rio Claro com faixas de CEP | **Não verificado.** Vem de site de terceiros; conferir antes de usar. |
| CEP ≠ limite geográfico de bairro | **Correto.** Faixas se cruzam e variam por trecho de rua. |
| O caminho é Prefeitura (geometria) + Correios (endereço) + SIG/QGIS (junção) | **Correto** como método. |
| É preciso procurar a versão vetorial (SHP/GPKG/DWG/GeoJSON) | **Correto.** Sem ela, é preciso georreferenciar o PDF e redesenhar. |

---

## 6. Plano recomendado

1. **Resolver a privacidade primeiro** (4.1): trocar dados por caso por dados agregados com supressão.
2. **Obter polígonos reais de bairro**: pedir o arquivo vetorial à Secretaria de Planejamento da Prefeitura; consultar também a Malha de Bairros do Censo 2022 (IBGE) e o OpenStreetMap; se só houver PDF, georreferenciar no QGIS (SIRGAS 2000 / UTM 23S, EPSG:31983).
3. **Ligar CEP → bairro por geografia** (ponto dentro do polígono), usando a tabela de faixas de CEP apenas como apoio.
4. **Criar a tabela de equivalência de nomes** e a lista de revisão manual.
5. **Marcar a qualidade de cada ponto** e remover o fallback do heatmap (4.3).
6. **Trocar o cluster por centroide** do polígono (4.6).
7. **Adicionar população por bairro** (Censo 2022) para calcular taxas.
8. **Organizar o código** (4.8) e atualizar o README.

---

## 7. Informações que ainda faltam

- Existe o arquivo **vetorial** do mapa da Prefeitura, ou só o PDF?
- O mapa será só para uso interno/seminário ou será **publicado**?
- Serão usados os 21 bairros do GeoJSON ou toda a lista (cerca de 182)?
- Podem enviar os **CSVs e GeoJSON** que faltam? Com eles seria possível medir quantos CEPs casam com bairro e quantos ficam sem correspondência.

---

*Relatório baseado apenas na leitura do código do ZIP. Nenhuma fonte externa foi verificada.*
