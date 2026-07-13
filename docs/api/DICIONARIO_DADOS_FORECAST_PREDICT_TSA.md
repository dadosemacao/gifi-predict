# Dicionário de Dados — APIs Forecast e Predict-TSA

**Autor:** Emerson Antônio  
**Data:** 2026-07-13  
**Versão:** 1.1  
**Escopo:** `POST/GET /api/forecast` e `POST/GET /api/predict-tsa`  
**Fonte de verdade (código):** `src/serving/schemas.py`, `src/serving/routes/`, `src/serving/services/`

---

## 1. Visão geral

| Aspecto | `/api/forecast` (Produto A) | `/api/predict-tsa` (Produto B) |
|---------|-------------------------------|--------------------------------|
| **Produto** | `forecast_operacional` | `what_if_direct` |
| **Objetivo** | Prever TSA do **próximo turno** com histórico recente | What-if **direto**: TSA só a partir das variáveis de processo |
| **Histórico TSA** | **Obrigatório** (`tsa_history`, mín. 7 valores) | **Não usado** |
| **Modelo campeão** | ExtraTrees residual sobre âncora `TSA_roll3` | Lasso direto (13 preditores) |
| **Saída principal** | `tsa_dia` + intervalo (`tsa_dia_lo`, `tsa_dia_hi`) + baselines | `tsa_dia` pontual |
| **MAE holdout (ref.)** | ~67 t/dia | ~89 t/dia |
| **Artefato** | `models/primeira_base/current_forecast.json` | `models/primeira_base/current_tsa.json` |
| **Content-Type** | `application/json` | `application/json` |

Ambas as APIs compartilham o mesmo **corpo de variáveis de processo** (`ProcessVariablesInput`), resolvidas pela camada `resolve_process_fields()` antes da inferência.

---

## 2. Convenções

### 2.1 Nomenclatura

| Camada | Padrão | Exemplo |
|--------|--------|---------|
| API (JSON) | `snake_case` | `carga_alcalina`, `db_sgf` |
| Modelo / L2 | `PascalCase` ou legado | `Carga_Alcalina`, `DB_SGF` |
| Alvo | — | `TSA_dia` (toneladas de polpa seca por dia) |

### 2.2 Origem dos campos (`field_origins`)

Após resolução, cada variável de processo informada ou derivada recebe uma origem:

| Valor | Significado |
|-------|-------------|
| `medido` | Valor enviado explicitamente no request |
| `proxy` | Derivado por regra Tier A (sem modelo ML) |
| `estimado` | Preenchido por imputer Tier B (RandomForest serving) |

Campos ausentes no request e não resolvidos geram erro `422`.

### 2.3 Tiers de imputação no serving

| Tier | Campos | Regra |
|------|--------|-------|
| **Obrigatório** | `carga_alcalina`, `kappa`, `prod_alcali_class`, `db_sgf`, `casca_pct`, `tpc`, `idade` | Devem estar no request; sem fallback |
| **Tier A — proxy** | `pct_ab`, `pct_dmg`, `vmi_le_021`, `vmi_021_025`, `vmi_gt_025` | Derivados se insumos auxiliares existirem |
| **Tier B — estimado** | `extrativo_at` | RF serving (`mix + idade`) se ausente |
| **Auxiliar (imputer)** | `pct_c` | Usado só na imputação Tier B; **não** entra no modelo TSA |

### 2.4 Regras Tier A (detalhe)

| Campo destino | Condição | Fórmula / regra |
|---------------|----------|-----------------|
| `pct_ab` | `pct_ab` ausente | `pct_a + pct_b` (requer ambos) |
| `pct_dmg` | `pct_dmg` ausente | `pct_d + pct_mg` (requer ambos) |
| `vmi_*` | flags ausentes | A partir de `vmi` contínuo: `≤0.21` → `vmi_le_021=1`; `0.21<v≤0.25` → `vmi_021_025=1`; `>0.25` → `vmi_gt_025=1` (one-hot) |
| `prod_alcali_class` | string ou número | Ordinal: `baixo`/`0` → 0; `normal`/`1` → 1 |

### 2.5 Regra Tier B (detalhe)

| Campo | Modelo | Features do imputer | Clamp |
|-------|--------|---------------------|-------|
| `extrativo_at` | `models/ingest/extrativo_serving_imputer.joblib` | `pct_AB`, `pct_C`, `pct_DMG`, `Idade` | `[range_min, range_max]` do artefato (default 1.0–3.5) |

---

## 3. Catálogo de campos de entrada (processo)

Campos comuns a **Forecast** e **Predict-TSA**. Tipos JSON: `number` (float).

### 3.1 Variáveis obrigatórias no request

| Campo API | Coluna L2 | Unidade | Descrição | Validação rígida da API |
|-----------|-----------|---------|-----------|-------------------------|
| `carga_alcalina` | `Carga_Alcalina` | % Na₂O* | Carga alcalina efetiva do digestor | **17,5 ≤ valor ≤ 21,0** |
| `kappa` | `Kappa` | adimensional | Índice kappa do licor | **15,0 ≤ valor ≤ 18,5** |
| `prod_alcali_class` | `Prod_alcali_class` | ordinal {0,1} | Classe produção álcali: 0=baixo, 1=normal | Aceita `0`/`1` ou `"baixo"`/`"normal"` |
| `db_sgf` | `DB_SGF` | **kg/m³** | Densidade básica medida no SGF | **465 ≤ valor ≤ 515** |
| `casca_pct` | `Casca_pct` | **%** | Percentual de casca nos cavacos | **valor ≤ 1,5** |
| `tpc` | `TPC` | **dias** | Tempo de permanência no cozimento | **valor ≥ 45** |
| `idade` | `Idade` | **anos** | Idade média da madeira | Sem faixa normativa |

\* Unidades de processo conforme planilha QM × Processo.

Valores fora dos limites oficiais retornam HTTP `422`. Limites inclusivos.

### 3.2 Variáveis opcionais (imputáveis Tier A/B)

| Campo API | Coluna L2 | Obrigatório final | Tier | Descrição |
|-----------|-----------|-------------------|------|-----------|
| `extrativo_at` | `Extrativo_AT` | Sim | B | Extrativo álcool-tolueno; imputado se omitido |
| `pct_ab` | `pct_AB` | Sim* | A | Fração A+B no mix |
| `pct_dmg` | `pct_DMG` | Sim* | A | Fração D+MG no mix |
| `vmi_le_021` | `vmi_le_021` | Sim* | A | VMI ≤ 0,21 |
| `vmi_021_025` | `vmi_021_025` | Sim* | A | 0,21 < VMI ≤ 0,25 |
| `vmi_gt_025` | `vmi_gt_025` | Sim* | A | VMI > 0,25 |

\* Após resolução, os **13** campos de `PROCESS_COLUMNS` devem estar completos. Mix e VMI podem ser informados diretamente ou via campos auxiliares.

### 3.3 Campos auxiliares (somente derivação / imputer; não vão ao modelo TSA)

| Campo API | Tipo | Descrição |
|-----------|------|-----------|
| `vmi` | number | VMI contínuo; deriva as três flags `vmi_*` |
| `pct_a` | number | Componente A do mix (para derivar `pct_ab`) |
| `pct_b` | number | Componente B do mix |
| `pct_c` | number | Componente C — **auxiliar do imputer** `Extrativo_AT` |
| `pct_d` | number | Componente D (para derivar `pct_dmg`) |
| `pct_mg` | number | Componente MG |

**Restrição de mix:** é necessário informar `(pct_ab, pct_c, pct_dmg)` **ou** insumos suficientes para derivá-los.  
**Restrição de VMI:** informar as três flags **ou** o campo `vmi` contínuo.

### 3.4 Campo exclusivo do Forecast

| Campo API | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `tsa_history` | `array[number]` | **Sim** | Histórico de `TSA_dia` por turno, **ordem cronológica** (índice 0 = mais antigo, último = turno mais recente) |

| Regra | Valor |
|-------|-------|
| Tamanho mínimo | **7** valores |
| Uso interno | Gera `TSA_lag1`, `TSA_roll3` (âncora default), `TSA_roll7` |
| Unidade | t/dia (toneladas polpa seca / dia) |
| Faixa típica | 3 001 – 3 650 (base histórica) |

---

## 4. API — Forecast operacional

### 4.1 `POST /api/forecast`

Previsão do próximo turno: **TSA_pred = âncora + resíduo_ML**, com âncora default `TSA_roll3`.

#### Query parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `run_id` | string | Não | ID do run de forecast; default lido de `current_forecast.json` |

#### Request body — `ForecastRequest`

Herda todos os campos de `ProcessVariablesInput` + `tsa_history`.

#### Response body — `ForecastResponse` (HTTP 200)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `product` | string | Sim | Constante `"forecast_operacional"` |
| `model_id` | string | Sim | Run ID do artefato bindado (ex.: `2026-07-13T104544Z`) |
| `family` | string | Sim | Família do modelo (ex.: `extratrees`) |
| `anchor_name` | string | Sim | Nome da coluna âncora (default `TSA_roll3`) |
| `tsa_dia` | number | Sim | TSA prevista para o próximo turno (t/dia) |
| `tsa_dia_lo` | number | Sim | Limite inferior intervalo ~80% (t/dia) |
| `tsa_dia_hi` | number | Sim | Limite superior intervalo ~80% (t/dia) |
| `anchor` | number | Sim | Valor numérico da âncora usada na predição |
| `residual` | number | Sim | Resíduo predito pelo ML (`tsa_dia - anchor`) |
| `baselines` | object | Sim | Baselines do histórico (ver abaixo) |
| `metrics` | object | Sim | Métricas de holdout do modelo bindado |
| `field_origins` | object | Sim | Origem de cada campo de processo resolvido |
| `warnings` | array[string] | Sim | Avisos de proxy/estimado (pode ser `[]`) |

**Objeto `baselines`:**

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `lag1` | number | Último valor de `tsa_history` |
| `roll3` | number | Média dos últimos 3 turnos |
| `roll7` | number | Média dos últimos 7 turnos |

**Objeto `metrics` (`HoldoutMetricsResponse`):**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `mae_holdout` | number | MAE no holdout temporal (t/dia) |
| `r2_holdout` | number | R² no holdout |
| `interval_80_coverage` | number | Cobertura empírica do intervalo 80% [0–1] |

**Objeto `field_origins`:** mapa campo → `"medido"` \| `"proxy"` \| `"estimado"` (somente campos presentes na resolução).

#### Lógica de predição (referência)

```text
1. resolve_process_fields(body)
2. compute_lags(tsa_history) → TSA_lag1, TSA_roll3, TSA_roll7
3. engineer_features → interações (DB_c, TPC_crit, Extr_x_Carga, …)
4. residual = pipe.predict(X)
5. tsa_dia = anchor + residual
6. tsa_dia_lo/hi = tsa_dia + quantis do artefato
```

---

### 4.2 `GET /api/forecast/status`

Metadados do modelo de forecast bindado (sem inferência).

#### Query parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `run_id` | string | Não | Override do run; default via `current_forecast.json` |

#### Response body — `ForecastStatusResponse` (HTTP 200)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `run_id` | string | Run ID do artefato |
| `family` | string | Família (ex.: `extratrees`) |
| `anchor` | string | Nome da âncora (ex.: `TSA_roll3`) |
| `product` | string | `"forecast_operacional"` |
| `holdout_mae` | number | MAE holdout (t/dia) |
| `holdout_r2` | number | R² holdout |
| `interval_80_coverage` | number | Cobertura intervalo 80% |
| `artifact_path` | string | Caminho absoluto do `.joblib` |

---

## 5. API — Predict-TSA (what-if direto)

### 5.1 `POST /api/predict-tsa`

Predição **direta** de TSA a partir das **13** variáveis de processo oficiais, **sem** histórico TSA.

#### Query parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `run_id` | string | Não | ID do run; default via `current_tsa.json` |

#### Request body — `PredictTsaRequest`

Idêntico a `ProcessVariablesInput` (sem `tsa_history`).

#### Response body — `PredictTsaResponse` (HTTP 200)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `product` | string | Sim | Constante `"what_if_direct"` |
| `model_id` | string | Sim | Run ID do modelo bindado |
| `family` | string | Sim | Família (ex.: `lasso`) |
| `tsa_dia` | number | Sim | TSA predita (t/dia) |
| `disclaimer` | string | Sim | Aviso de MAE superior ao forecast operacional |
| `metrics` | object | Sim | Métricas holdout (`HoldoutMetricsResponse`) |
| `field_origins` | object | Sim | Origens após resolução |
| `warnings` | array[string] | Sim | Avisos de imputação |

**Features do modelo (13):**  
`Carga_Alcalina`, `Kappa`, `Prod_alcali_class`, `DB_SGF`, `Idade`, `TPC`, `pct_AB`, `pct_DMG`, `vmi_le_021`, `vmi_021_025`, `vmi_gt_025`, `Extrativo_AT`, `Casca_pct`.

**Removidos da Camada 3 (v1.0):** `DB_LAB`, `Secura_pct`, `Extrativo_Total`, `Extrativo_SGF`, `pct_C` (este último permanece auxiliar do imputer).

---

### 5.2 `GET /api/predict-tsa/status`

Metadados do modelo what-if direto.

#### Query parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `run_id` | string | Não | Override do run |

#### Response body — `PredictTsaStatusResponse` (HTTP 200)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `run_id` | string | Run ID |
| `family` | string | Família (ex.: `catboost`) |
| `product` | string | `"what_if_direct"` |
| `holdout_mae` | number | MAE holdout (~104 t/dia ref.) |
| `holdout_r2` | number | R² holdout |
| `interval_80_coverage` | number | Cobertura (0.0 para modelo direto) |
| `artifact_path` | string | Caminho do pipeline `.joblib` |
| `features` | array[string] | Lista das 17 features de entrada |

---

## 6. Códigos HTTP e erros

| Código | Situação | Corpo típico |
|--------|----------|--------------|
| **200** | Sucesso | Response schema completo |
| **404** | Artefato ou `current_*.json` ausente | `{"detail": "..."}` |
| **422** | Validação Pydantic ou regra de negócio | `{"detail": "..."}` ou array de erros de campo |

**Exemplos de mensagens 422 (negócio):**

| Causa | Mensagem (padrão) |
|-------|-------------------|
| Campo obrigatório ausente | `campos obrigatórios ausentes: carga_alcalina, ...` |
| Valor fora da faixa oficial | Pydantic: `greater_than_equal` ou `less_than_equal` no campo |
| Resolução incompleta | `campos ausentes após resolução: pct_ab, vmi_le_021, ...` |
| Histórico curto (forecast) | Pydantic: `tsa_history` min_length=7 |
| Features ausentes pós-resolução | `features ausentes após resolução: [...]` |

---

## 7. Exemplos

### 7.1 Forecast — request completo

```json
{
  "tsa_history": [3420, 3435, 3440, 3450, 3445, 3455, 3460],
  "carga_alcalina": 18.71,
  "kappa": 15.96,
  "db_sgf": 486.80,
  "db_lab": 475.00,
  "secura_pct": 61.75,
  "casca_pct": 0.84,
  "extrativo_total": 3.50,
  "extrativo_at": 1.87,
  "extrativo_sgf": 3.96,
  "tpc": 59.38,
  "idade": 6.69,
  "vmi_le_021": 0.0,
  "vmi_021_025": 0.0,
  "vmi_gt_025": 1.0,
  "pct_ab": 0.658,
  "pct_c": 0.103,
  "pct_dmg": 0.146
}
```

### 7.2 Forecast — request mínimo com derivações Tier A/B

```json
{
  "tsa_history": [3450, 3450, 3450, 3450, 3450, 3450, 3450],
  "carga_alcalina": 18.71,
  "kappa": 15.96,
  "db_sgf": 486.80,
  "secura_pct": 61.75,
  "casca_pct": 0.84,
  "extrativo_total": 3.50,
  "extrativo_sgf": 3.96,
  "tpc": 59.38,
  "idade": 6.69,
  "vmi": 0.30,
  "pct_a": 0.40,
  "pct_b": 0.26,
  "pct_c": 0.103,
  "pct_d": 0.10,
  "pct_mg": 0.046
}
```

Resposta incluirá `field_origins.db_lab = "proxy"`, `field_origins.extrativo_at = "estimado"`, etc., e `warnings` descritivos.

### 7.3 Forecast — response (estrutura)

```json
{
  "product": "forecast_operacional",
  "model_id": "2026-07-13T104544Z",
  "family": "extratrees",
  "anchor_name": "TSA_roll3",
  "tsa_dia": 3468.5,
  "tsa_dia_lo": 3390.2,
  "tsa_dia_hi": 3546.8,
  "anchor": 3455.0,
  "residual": 13.5,
  "baselines": {
    "lag1": 3460.0,
    "roll3": 3455.0,
    "roll7": 3450.7
  },
  "metrics": {
    "mae_holdout": 67.6,
    "r2_holdout": 0.252,
    "interval_80_coverage": 0.71
  },
  "field_origins": {
    "carga_alcalina": "medido",
    "db_lab": "medido",
    "extrativo_at": "medido"
  },
  "warnings": []
}
```

### 7.4 Predict-TSA — request (sem histórico)

```json
{
  "carga_alcalina": 18.71,
  "kappa": 15.96,
  "db_sgf": 486.80,
  "secura_pct": 61.75,
  "casca_pct": 0.84,
  "extrativo_total": 3.50,
  "extrativo_sgf": 3.96,
  "tpc": 59.38,
  "idade": 6.69,
  "vmi_gt_025": 1.0,
  "vmi_le_021": 0.0,
  "vmi_021_025": 0.0,
  "pct_ab": 0.658,
  "pct_c": 0.103,
  "pct_dmg": 0.146
}
```

### 7.5 Predict-TSA — response (estrutura)

```json
{
  "product": "what_if_direct",
  "model_id": "2026-07-13T102553Z",
  "family": "catboost",
  "tsa_dia": 3512.3,
  "disclaimer": "Previsão sem histórico TSA — MAE holdout ~104 t/dia. Use /api/forecast para forecast operacional.",
  "metrics": {
    "mae_holdout": 103.7,
    "r2_holdout": -0.092,
    "interval_80_coverage": 0.0
  },
  "field_origins": {
    "db_lab": "proxy",
    "extrativo_at": "estimado"
  },
  "warnings": [
    "db_lab estimado via proxy DB_SGF × 0.985",
    "extrativo_at estimado via imputer serving (mix + idade)"
  ]
}
```

---

## 8. Bind de modelos e configuração

| API | Pointer | Config YAML | Query override |
|-----|---------|-------------|----------------|
| Forecast | `models/primeira_base/current_forecast.json` | `default_forecast_run_id` | `?run_id=` |
| Predict-TSA | `models/primeira_base/current_tsa.json` | `default_tsa_run_id` | `?run_id=` |

**Prioridade do `run_id`:** query param > pointer JSON > erro 404 se ausente.

**Métricas holdout:** resolvidas de `reports/TSA_FORECAST_OPERACIONAL.json` (forecast) e `reports/TSA_PRIMEIRA_BASE_MODELING.json` (predict-tsa), com fallback no pointer do artefato.

---

## 9. Matriz de decisão — qual API usar?

| Cenário | API recomendada |
|---------|-----------------|
| Operação turno a turno com histórico recente de TSA | `POST /api/forecast` |
| Simulação what-if sem histórico (Postman, UI “What-if direto”) | `POST /api/predict-tsa` |
| Verificar MAE / artefato bindado | `GET .../status` |
| Cenário completo multi-linha (CSV) | `POST /api/simulate` (fora deste documento) |

---

## 10. Auditoria (observabilidade)

Chamadas a `/api/forecast` e `/api/predict-tsa` são registradas em `logs/serving_audit.db` (middleware ASGI), incluindo `request_json`, `response_json`, `field_origins_json`, `metrics_json` e `warnings_json`. Consulta: `scripts/audit_query.py --last 10`.

---

## 11. Referências

| Documento / código | Conteúdo |
|--------------------|----------|
| `src/serving/schemas.py` | Contratos Pydantic |
| `src/serving/services/resolve_process_fields.py` | Tiers A/B |
| `src/simulation/forecast/specs.py` | Features + `MIN_TSA_HISTORY=7` |
| `src/simulation/forecast/features.py` | Lags e feature engineering |
| `src/simulation/tsa_direct/specs.py` | 17 features what-if |
| `docs/sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md` | Faixas operacionais |
| `docs/kb/gifi-ingest/concepts/feature-column-contract.md` | Contrato L2 |
| `config/serving.yaml` | Defaults de serving |

---

## Histórico de revisões

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 2026-07-13 | Emerson Antônio | Versão inicial — dicionário completo forecast + predict-tsa |
