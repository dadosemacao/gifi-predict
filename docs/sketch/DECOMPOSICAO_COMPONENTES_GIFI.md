# Decomposição de Componentes de Nível Superior — Projeto GIFI

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 1.0  
**Tipo:** Decomposição estrutural (sem planejamento de tarefas)  
**Base:** `PRD_GIFI_v1.1.md`, `MAPA_COMPONENTES_GIFI.md`, documentos v1.1 alinhados  

---

## 1. Propósito

Apresentar a divisão do sistema GIFI em **componentes de nível superior**, justificar **por que a fronteira ocorre exatamente ali**, agrupar as camadas sob cada componente e explicar as **dependências** entre eles.

Este documento **não** define backlog, estimativas nem cronograma de execução.

---

## 2. Princípio da divisão

A decomposição de nível superior do GIFI cabe em **cinco componentes**. A divisão não é por tecnologia (Python vs. UI), e sim por **contrato de responsabilidade**: o que cada parte pode mudar sem forçar o redesenho das outras.

---

## 3. Visão dos cinco componentes

```
┌─────────────────────────────┐
│ 1. Domínio e Contrato       │  L0 (docs + faixas + schema)
└──────────────┬──────────────┘
               │ define regras
               ▼
┌─────────────────────────────┐
│ 2. Dados e Representação    │  L1 (limpeza + features)
└──────────────┬──────────────┘
               │ alimenta
               ▼
┌─────────────────────────────┐
│ 3. Motor de Simulação       │  L2 (Elo 1 → 1b → 2 → 3)
│    (Caminho da Ida)         │
└──────────────┬──────────────┘
               │ produz scores + artefatos
               ▼
┌─────────────────────────────┐
│ 4. Confiança e Aceite       │  L3 (+ explicabilidade)
│    (Matrizes A/B/C)         │
└──────────────┬──────────────┘
               │ libera uso
               ▼
┌─────────────────────────────┐
│ 5. Superfície de Uso        │  L4 (UI + relatório de desvios)
└─────────────────────────────┘
```

---

## 4. Componente 1 — Domínio e Contrato

**O que é:** a definição do problema e as regras que não são código — PRD, Resumo, Casos de Teste, faixas operacionais, unidades, KPIs, o que é MVP e o que não é.

**Camadas agrupadas:** L0.

**Por que a fronteira fica aqui:**  
Mudar um limiar (Extrativos > 2,45%, fator 0,985, MAE ≤ 56) não deve exigir reescrever o modelo; mudar o modelo não deve redefinir o problema. Esta é a **fonte única de verdade semântica**. Sem ela, Features, Motor e Testes divergem de novo (foi exatamente o que aconteceu entre os PDFs v1.0).

**Não inclui:** pipelines, treino, UI.

**Artefatos típicos:** `PRD_GIFI_v1.1.md`, `RESUMO_TECNICO_GIFI_v1.1.md`, `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md`, `sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md`.

---

## 5. Componente 2 — Dados e Representação

**O que é:** transformar a base QM×Processo em um dataset analítico estável — limpeza, schema, imputação DB, mix A/B/C, ponderação por volume, agregação turno→dia.

**Camadas agrupadas:** L1 (C1 limpeza + C2 features).

**Por que a fronteira fica aqui:**  
A física do abastecimento (mix, densidade, TPC, VMI) é **independente** de como se estima Extrativos ou TSA. O Elo 1, o Elo 3 e os testes de monotonicidade devem consumir a **mesma representação**. Se features ficarem dentro do “modelo”, cada elo inventa o seu mix e a Camada C (entropia/HHI) deixa de ser auditável.

**Depende de:** Domínio (faixas, unidades, regras de filtro).  
**Alimenta:** Motor e, indiretamente, Confiança (TC-08, TC-P01).

---

## 6. Componente 3 — Motor de Simulação (Caminho da Ida)

**O que é:** a cascata preditiva encadeada — Elo 1 (Extrativos), Elo 1b opcional (Casca), Elo 2 (Carga), Elo 3 (TSA) — nos Modos A (integração) e B (isolamento).

**Camadas agrupadas:** L2.

**Por que a fronteira fica aqui:**  
O produto de negócio não é “um regressor de TSA”; é um **sistema de estimação em cadeia** que existe porque o longo prazo não tem Lab. A fronteira agrupa tudo o que **gera previsão**. Separar Elo 1/2/3 em “produtos” diferentes quebraria o contrato do Caminho da Ida; misturar validação ou UI aqui misturaria treino com aceite.

**Depende de:** Dados e Representação (e Domínio para o desenho dos elos).  
**Alimenta:** Confiança (candidatos + saídas por elo) e Superfície (inferência).

**Dentro do motor, a ordem interna é rígida:** Elo 1 → Elo 2 → Elo 3. Isso é dependência **interna**, não componente de nível superior.

---

## 7. Componente 4 — Confiança e Aceite

**O que é:** o mecanismo que decide se o motor é liberável — Matriz A (MAE), Matriz B (física), Matriz C (top-3 detratores), política de campeão, relatório de métricas por elo.

**Camadas agrupadas:** L3 + a parte de explicabilidade necessária ao aceite (não a tela).

**Por que a fronteira fica aqui:**  
Aceite é **ortogonal** ao treino. Um modelo com MAE bom que viola DB↓→TSA↓ não pode ir para a UI. Se validação viver “dentro do notebook do Elo 3”, a homologação vira subjetiva de novo. Explicabilidade entra neste componente porque, no GIFI, ela é **critério de aceite** (Matriz C), não um extra de dashboard.

**Depende de:** Motor (artefatos treinados) + Domínio (protocolo TC / KPIs) + Dados (cenários e features corretas).  
**Libera:** Superfície de Uso.

---

## 8. Componente 5 — Superfície de Uso

**O que é:** onde o negócio opera o sistema — upload de cenário, curvas de TSA/Carga/Extrativos, painel de detratores, fluxo assistido de desvios, relatório de aderência para encerramento.

**Camadas agrupadas:** L4.

**Por que a fronteira fica aqui:**  
A UI não define física nem métrica; ela **consome** um motor já aceito. Misturar UI com o Motor faria o prazo de 31/08 depender de redesenho de features a cada experimento. O relatório final também é superfície (consumo/comunicação), não parte do algoritmo.

**Depende de:** Confiança (release) + Motor (inferência) + Domínio (template de planilha).  
**Não alimenta** os outros no MVP (sem retreino na UI).

---

## 9. Dependências entre componentes

| De → Para | Tipo de dependência |
|---|---|
| Domínio → Dados | Regras de schema, unidades, filtros, faixas |
| Domínio → Motor | Desenho da cascata, alvos, política de modelos |
| Domínio → Confiança | Contratos MAE / TC / Matrizes |
| Domínio → Superfície | Template de cenário, o que mostrar |
| Dados → Motor | Features de treino e inferência |
| Dados → Confiança | Massa dos testes e pipeline checks |
| Motor → Confiança | Predições, erros por elo, modelo candidato |
| Confiança → Superfície | Autorização de uso + artefato de explicabilidade |
| Motor → Superfície | API/artefato de inferência (após aceite) |

### Fluxo único de construção lógica

**Domínio → Dados → Motor → Confiança → Superfície**

Não há atalho seguro:

- UI sem Confiança homologa o errado;
- Motor sem Dados estável não é reproduzível;
- Dados sem Domínio reabre as divergências D-01…D-17.

---

## 10. O que ficou de fora (de propósito)

Não são componentes de nível superior porque não mudam a fronteira do MVP:

| Item | Onde vive |
|---|---|
| Elo 1b, Redes Neurais | Variação interna do **Motor** |
| Caminho da Volta, cloud, RCA automática | Fora do MVP / fase futura |
| ElasticNet vs Random Forest | Escolha interna do **Motor**, arbitrada pela **Confiança** |

---

## 11. Resumo da justificativa das fronteiras

| Corte | Motivo |
|---|---|
| Domínio ∥ resto | Semântica separada de implementação |
| Dados ∥ Motor | Representação física reutilizável por todos os elos e testes |
| Motor ∥ Confiança | Treinar ≠ aceitar |
| Confiança ∥ Superfície | Usar só o que passou A+B+C |
| Cascata inteira num Motor | O valor do GIFI é a cadeia, não um modelo isolado |

---

## 12. Relação com o mapa detalhado

O documento `sketch/MAPA_COMPONENTES_GIFI.md` detalha C0…C9 e a ordem de construção. Este documento **agrupa** esses elementos nos cinco componentes de nível superior:

| Componente de nível superior | Elementos do mapa detalhado |
|---|---|
| Domínio e Contrato | C0 |
| Dados e Representação | C1, C2 |
| Motor de Simulação | C3, C3b, C4, C5 |
| Confiança e Aceite | C6, C7 (aceite) |
| Superfície de Uso | C8, C9 |

---

*Documento de decomposição estrutural. Serve como base para definição posterior de tarefas, sem antecipar o plano de execução.*
