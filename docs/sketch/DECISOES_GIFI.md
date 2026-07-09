# Registro de Decisões — Projeto GIFI

**Autor:** Emerson Antônio (Cientista de Dados)  
**Data:** 2026-07-09  
**Stakeholder:** Thiago Taglialegna Salles  
**Objetivo:** rastrear decisões de escopo e método que destravam a construção do MVP.

Status possíveis: **Confirmada** (aprovada pelo stakeholder) · **Assumida (CD)** · **Encaminhada** (depende de terceiro).

---

## D-A — Janela de validação (holdout temporal)

| Campo | Conteúdo |
|---|---|
| Decisão | Holdout = **2025-05-01 a 2025-10-30**; treino = histórico até **2025-04-30** |
| Status | **Confirmada** pelo stakeholder (2026-07-09) |
| Motivo | Meta original citava 2026 (inexistente na base, que vai até out/2025); últimos 6 meses de 2025 são o proxy honesto de “dados não vistos”, sem leakage temporal |
| Impacto | Define partição da Matriz A (MAE ≤ 56) e a partição `holdout_features` no Ingest (I4) |
| Documentos afetados | `analytical-backbone.md` §6; `ingest-engine.md` §9; `PRD_GIFI_v1.1.md` §4.3 |

---

## D-B — Estimativa de % Casca (Elo 1b)

| Campo | Conteúdo |
|---|---|
| Decisão | **NO-GO no MVP** — não incluir estimativa automática de casca (Elo 1b) |
| Status | **Confirmada** pelo stakeholder (2026-07-09) |
| Motivo | Correlação fraca com TSA (ρ ≈ −0,15) e cobertura parcial (~64%); somar elo à cascata elevaria o erro composto com baixo ganho, ameaçando o MAE ≤ 56 |
| Ressalva | Casca segue como **feature opcional do Elo 3 quando medida**; estimativa automática reavaliável na Fase 2 |
| Documentos afetados | `PRD_GIFI_v1.1.md` §2/§4.1; `RESUMO_TECNICO_GIFI_v1.1.md` §3/§5; `analytical-backbone.md` §6 |

---

## Decisões operacionais (CD) — assumidas

| ID | Decisão | Status |
|---|---|---|
| D-C | Agregação turno→dia: média ponderada por volume (qualidade), soma (volume), TSA meta diária | Assumida (CD) |
| D-D | Formato de artefatos: Parquet (datasets) + JSON (manifesto) | Assumida (CD) |
| D-E | Template de cenário `template_cenario_v0` como artefato da Camada 1 (Domínio) | Assumida (CD) |

---

## Encaminhamentos (dependem de terceiros)

| ID | Item | Responsável | Bloqueia build? |
|---|---|---|---|
| D-F | Entrega da base interpolada | TI Veracel/Keyrus | Não (fallback: Excel consolidado) |
| D-G | SLA de reprocesso quando TI republicar base (proposta: ≤ 2 dias úteis) | TI + CD | Não |

---

*Registro vivo. Alterações às decisões confirmadas exigem solicitação formal de mudança (change request).*
