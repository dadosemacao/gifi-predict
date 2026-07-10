# Skill — Cientista de Dados Sênior Especialista em Análise Preditiva

## 1. Objetivo desta Skill
Este documento descreve, de forma estruturada e detalhada, o conjunto de conhecimentos, competências, práticas, ferramentas e critérios de maturidade esperados de um **Cientista de Dados Sênior com especialização em Análise Preditiva**.

O objetivo é servir como **guia de estudo, avaliação de senioridade, checklist de contratação, matriz de evolução profissional e referência para projetos corporativos**.

---

# 2. Definição do Papel

## 2.1. O que é um Cientista de Dados Sênior especialista em análise preditiva
É o profissional capaz de:

- entender um problema de negócio ambíguo e traduzi-lo em um problema analítico;
- definir corretamente o **alvo preditivo**, o horizonte temporal e a estratégia de modelagem;
- construir datasets robustos e features com sinal preditivo real;
- treinar, avaliar, comparar e selecionar modelos com rigor estatístico;
- operacionalizar o modelo em produção com governança, monitoramento e plano de evolução;
- transformar previsão em **decisão prática de negócio**, não apenas em score técnico;
- liderar tecnicamente a solução ponta a ponta.

---

# 3. Escopo de Conhecimento da Skill

A skill está organizada em **10 pilares de competência**:

1. Fundamentos matemáticos e estatísticos  
2. Programação e manipulação de dados  
3. Machine Learning supervisionado  
4. Séries temporais e previsão  
5. Engenharia de features e preparação de dados  
6. Avaliação, validação e seleção de modelos  
7. Negócio, framing analítico e decisão  
8. MLOps, produção e monitoramento  
9. Interpretabilidade, risco e governança  
10. Comunicação, liderança técnica e senioridade operacional  

---

# 4. Pilar 1 — Fundamentos Matemáticos e Estatísticos

## 4.1. Objetivo
Dar sustentação conceitual para modelagem, avaliação, inferência e tomada de decisão baseada em evidência.

## 4.2. Conhecimentos obrigatórios

### 4.2.1. Probabilidade
- Probabilidade clássica e condicional
- Teorema de Bayes
- Variáveis aleatórias
- Distribuições discretas e contínuas
- Esperança, variância, covariância
- Independência e dependência
- Lei dos grandes números
- Intuição de risco e incerteza

### 4.2.2. Estatística descritiva e inferencial
- Média, mediana, moda, percentis
- Variância, desvio padrão, IQR
- Assimetria, curtose
- Testes de hipótese
- p-valor e significância
- Intervalo de confiança
- Poder estatístico
- Bootstrap e reamostragem
- Inferência aplicada a experimentos e modelos

### 4.2.3. Regressão e análise estatística
- Regressão linear
- Interpretação de coeficientes
- Multicolinearidade
- Resíduos e diagnóstico
- Regularização (L1/L2)
- Relação entre inferência e previsão

### 4.2.4. Álgebra linear
- Vetores e matrizes
- Produto matricial
- Transformações lineares
- autovalores/autovetores
- decomposições (SVD)
- PCA em nível conceitual e prático

### 4.2.5. Otimização
- Gradiente descendente
- Função de perda
- Derivadas parciais
- Noções de convexidade
- Overfitting vs underfitting sob a ótica da otimização

## 4.3. Evidência de senioridade
O profissional consegue explicar:
- por que o modelo está superajustando;
- por que uma métrica aparentemente boa pode ser enganosa;
- por que um ganho observado pode não ser estatisticamente confiável;
- como a distribuição dos dados afeta a validade da modelagem.

---

# 5. Pilar 2 — Programação e Manipulação de Dados

## 5.1. Objetivo
Capacitar o profissional a construir pipelines analíticos reprodutíveis, limpos, performáticos e auditáveis.

## 5.2. Linguagens e ferramentas essenciais

## 5.2.1. Python
Conhecimento forte em:
- Python idiomático
- estruturas de dados
- funções, classes e modularização
- tratamento de exceções
- logging
- tipagem quando aplicável
- organização de projeto

### Bibliotecas esperadas
- pandas
- numpy
- scikit-learn
- xgboost
- lightgbm
- catboost
- statsmodels
- scipy
- matplotlib
- plotly
- pyarrow / parquet
- joblib / pickle com cautela
- MLflow (quando aplicável)

## 5.2.2. SQL
Domínio forte em:
- joins
- CTEs
- subqueries
- window functions
- agregações complexas
- data quality checks
- tuning básico de consulta
- construção de datasets analíticos
- reconciliação de dados

## 5.2.3. Ambientes distribuídos
Para ambientes enterprise, espera-se domínio de:
- Spark DataFrames
- PySpark
- particionamento
- otimização de leitura/escrita
- Delta Lake
- notebooks e jobs
- ingestão e transformação em escala

## 5.3. Evidência de senioridade
- consegue sair do notebook exploratório e transformar em pipeline robusto;
- sabe organizar dados por camadas ou responsabilidades;
- consegue construir dataset analítico sem depender totalmente de terceiros;
- pensa em performance, custo e reprodutibilidade.

---

# 6. Pilar 3 — Machine Learning Supervisionado

## 6.1. Objetivo
Resolver problemas preditivos com método, consistência e capacidade de comparação entre abordagens.

## 6.2. Tipos de problema
O profissional deve dominar:
- classificação binária
- classificação multiclasse
- regressão
- scoring / propensão
- ranking orientado a decisão
- detecção de anomalias como apoio preditivo

## 6.3. Algoritmos esperados

### 6.3.1. Modelos lineares
- regressão linear
- regressão logística
- elastic net, ridge, lasso

### 6.3.2. Modelos baseados em árvore
- Decision Trees
- Random Forest
- Gradient Boosting
- XGBoost
- LightGBM
- CatBoost

### 6.3.3. Outros modelos relevantes
- SVM
- kNN
- Naive Bayes
- ensembles
- stacking/blending
- redes neurais quando houver justificativa real

## 6.4. Temas obrigatórios
- bias-variance tradeoff
- overfitting e underfitting
- regularização
- hiperparâmetros
- feature importance
- pipelines de treino
- comparação entre modelos simples e complexos

## 6.5. Evidência de senioridade
- sabe começar por baseline e não por modismo;
- escolhe o algoritmo pelo problema, dados, custo e necessidade de explicabilidade;
- sabe quando um modelo simples é mais valioso que um sofisticado;
- sabe defender tecnicamente a escolha do modelo.

---

# 7. Pilar 4 — Séries Temporais e Forecast

## 7.1. Objetivo
Modelar fenômenos com dependência temporal, sazonalidade, tendência e necessidade de previsão futura.

## 7.2. Conhecimentos esperados
- estrutura de séries temporais
- tendência, sazonalidade, ruído
- estacionariedade em nível conceitual
- autocorrelação
- lags e janelas móveis
- backtesting temporal
- forecast horizon
- features de calendário
- validação respeitando o tempo

## 7.3. Modelos e abordagens
- baseline naïve e sazonal
- regressão com features temporais
- ARIMA/SARIMA em nível de repertório
- Prophet em nível crítico, sem dependência cega
- boosting para forecast
- modelos por janela deslizante
- previsão hierárquica quando aplicável

## 7.4. Cuidados obrigatórios
- vazamento temporal
- treino usando informação futura
- splits incorretos
- métricas incompatíveis com a decisão
- comparação injusta entre horizontes

## 7.5. Evidência de senioridade
- sabe montar backtesting correto;
- sabe explicar se o erro piora por horizonte, segmento ou sazonalidade;
- sabe traduzir forecast em capacidade, estoque, escala ou receita.

---

# 8. Pilar 5 — Engenharia de Features e Preparação de Dados

## 8.1. Objetivo
Transformar dados brutos em variáveis com valor preditivo real, consistência temporal e aderência ao negócio.

## 8.2. Conhecimentos obrigatórios
- imputação de missing
- tratamento de outliers
- encoding de categóricas
- discretização quando fizer sentido
- agregações históricas
- janelas temporais
- features de recência, frequência, intensidade e tendência
- padronização de granularidade
- criação de variáveis derivadas de negócio
- feature selection
- redução de dimensionalidade quando necessário

## 8.3. Boas práticas
- toda feature deve respeitar a data de corte do problema;
- features não podem usar informação que não existiria no momento da predição;
- a criação da feature deve ser reproduzível em produção;
- feature boa é a que gera sinal, estabilidade e viabilidade operacional.

## 8.4. Exemplos de features típicas
### Churn
- dias desde última compra
- frequência de uso nos últimos 7/30/90 dias
- tendência de queda de engajamento
- número de tickets recentes

### Inadimplência
- atraso médio
- dias em atraso máximos
- variabilidade do pagamento
- concentração de compras

### Operação / atendimento
- volume recente
- tempo médio
- reincidência
- perfil do agente, canal, fila, horário

## 8.5. Evidência de senioridade
- sabe onde o ganho de performance realmente nasce;
- entende a semântica das features;
- sabe construir feature útil em vez de despejar centenas de colunas aleatórias;
- consegue defender por que determinada feature é válida ou inválida.

---

# 9. Pilar 6 — Avaliação, Validação e Seleção de Modelos

## 9.1. Objetivo
Garantir que o modelo seja comparado de forma honesta, estável e alinhada ao uso de negócio.

## 9.2. Métricas para classificação
- accuracy com critério
- precision
- recall
- F1-score
- ROC-AUC
- PR-AUC
- log loss
- matriz de confusão
- lift / gain
- KS / Gini em cenários de risco

## 9.3. Métricas para regressão
- MAE
- RMSE
- MAPE / WAPE / sMAPE com cuidado
- R² com leitura crítica
- erro por segmento

## 9.4. Métricas para forecast
- MAE
- RMSE
- MAPE/WAPE
- erro por horizonte
- comparação contra baseline temporal

## 9.5. Estratégias de validação
- holdout
- cross-validation
- stratified split quando aplicável
- validação temporal
- nested CV em cenários específicos
- avaliação por coortes, segmentos ou janelas

## 9.6. Temas críticos
- threshold tuning
- custo de falso positivo vs falso negativo
- calibration
- drift de performance
- estabilidade fora do período de treino
- análise de erro

## 9.7. Evidência de senioridade
- escolhe a métrica em função da decisão de negócio;
- rejeita validação mal feita;
- não se deixa seduzir por métrica única;
- consegue explicar por que um modelo “melhor” em AUC pode ser pior na prática.

---

# 10. Pilar 7 — Negócio, Framing Analítico e Tomada de Decisão

## 10.1. Objetivo
Transformar problema de negócio em problema analítico correto, útil e acionável.

## 10.2. Competências essenciais
- entender contexto operacional
- identificar KPI de valor
- definir o que precisa ser previsto
- definir horizonte preditivo
- mapear restrições de uso
- alinhar o modelo à ação operacional

## 10.3. Perguntas que o sênior precisa fazer
- qual decisão será tomada com essa previsão?
- o que acontece se o modelo errar?
- qual é o custo do falso positivo e do falso negativo?
- com quanto tempo de antecedência a previsão precisa existir?
- quem vai agir em cima do score?
- qual processo operacional será alterado por esse modelo?

## 10.4. Exemplos de framing correto
### Errado
“Vamos prever churn.”

### Certo
“Vamos prever, com 30 dias de antecedência, quais clientes B2B com ticket acima de X têm maior probabilidade de cancelar, para acionar retenção com capacidade operacional limitada a Y clientes por semana.”

## 10.5. Evidência de senioridade
- consegue refinar problema mal formulado;
- evita projeto sem ação operacional possível;
- fala a linguagem do negócio sem perder rigor técnico;
- mede impacto esperado e impacto realizado.

---

# 11. Pilar 8 — MLOps, Produção e Monitoramento

## 11.1. Objetivo
Fazer o modelo sobreviver fora do notebook, com rastreabilidade, reprodutibilidade e governança operacional.

## 11.2. Conhecimentos esperados
- versionamento de código
- versionamento de dados
- tracking de experimentos
- registro de modelos
- pipeline de treino
- pipeline de inferência
- batch scoring
- scoring near real time / real time quando necessário
- automação de retreino
- monitoramento de métricas de produção
- monitoramento de drift
- observabilidade mínima

## 11.3. Ferramentas e conceitos comuns
- Git
- MLflow
- orquestração de jobs
- artefatos de modelo
- ambientes dev/homolog/prod
- testes de pipeline
- validação de schema
- feature store quando aplicável

## 11.4. O que um sênior precisa saber desenhar
- como o modelo será treinado periodicamente;
- onde as features serão calculadas;
- como garantir consistência entre treino e produção;
- como monitorar queda de performance;
- quando e como retreinar;
- como auditar versões.

## 11.5. Evidência de senioridade
- sabe discutir deploy e não só treino;
- considera operação desde o início;
- entende que sem monitoramento não existe modelo corporativo confiável.

---

# 12. Pilar 9 — Interpretabilidade, Risco e Governança

## 12.1. Objetivo
Garantir que o modelo seja compreensível, defensável, monitorável e utilizável em ambiente corporativo.

## 12.2. Conhecimentos esperados
- feature importance
- SHAP / interpretabilidade local e global
- análise de sensibilidade
- limitações do modelo
- viés e fairness em nível aplicado
- estabilidade por segmento
- documentação de premissas
- rastreabilidade de dados e versões

## 12.3. O que deve ser documentado
- objetivo do modelo
- variável-alvo
- janela de observação
- janela de previsão
- features usadas
- exclusões e filtros
- métrica principal
- limitações conhecidas
- risco de uso indevido
- plano de monitoramento

## 12.4. Evidência de senioridade
- consegue explicar o comportamento do modelo para negócio, auditoria ou gestão;
- deixa claro onde o modelo funciona e onde ele não é confiável;
- documenta risco em vez de vender certeza falsa.

---

# 13. Pilar 10 — Comunicação, Liderança Técnica e Senioridade Operacional

## 13.1. Objetivo
Garantir que o profissional não seja apenas um executor técnico, mas um condutor de solução analítica de alto impacto.

## 13.2. Competências esperadas
- estruturar problema ambíguo
- conduzir discovery analítico
- revisar trabalho de plenos e juniores
- orientar boas práticas
- negociar escopo e prioridade
- apresentar resultado para executivo
- transformar análise em recomendação objetiva
- dizer “não” para solução ruim

## 13.3. Entregáveis típicos de um sênior
- framing do problema
- desenho da variável-alvo
- estratégia de dados e features
- baseline e critérios de comparação
- plano de validação
- recomendação do modelo
- plano de produção
- leitura executiva do impacto
- roadmap de evolução

## 13.4. Evidência de senioridade
- assume responsabilidade por decisões técnicas;
- antecipa risco antes de virar incidente;
- sabe simplificar sem empobrecer;
- influencia o negócio com clareza e precisão.

---

# 14. Competências Complementares Desejáveis

## 14.1. Engenharia e arquitetura de dados
- modelagem de dados analíticos
- camadas bronze/silver/gold ou equivalentes
- qualidade de dados
- governança
- lineage

## 14.2. Cloud e plataformas
- Databricks
- Azure / AWS / GCP
- notebooks + jobs + storage + catálogo
- custos e performance

## 14.3. Experimentação e causalidade
- A/B test
- desenho experimental
- uplift quando aplicável
- leitura crítica de causalidade vs associação

## 14.4. Domínio setorial
- finanças
- atendimento/call center
- supply
- varejo
- indústria
- agro
- risco e crédito

---

# 15. O que NÃO caracteriza senioridade

Não é suficiente:
- saber usar XGBoost;
- montar notebook bonito;
- fazer gráfico elegante;
- decorar bibliotecas;
- ter jargão de IA;
- usar deep learning sem necessidade;
- ter boa AUC em base com vazamento;
- depender de terceiros para qualquer etapa de produção.

---

# 16. O que caracteriza senioridade de verdade

## 16.1. Sinais fortes de senioridade
- transforma problema de negócio em problema preditivo bem definido;
- evita leakage e erros metodológicos;
- escolhe métricas e validações corretas;
- sabe balancear performance, interpretabilidade e operação;
- pensa no deploy antes de o projeto travar;
- documenta limitações e riscos;
- mede impacto real do modelo;
- lidera a solução ponta a ponta.

---

# 17. Matriz Resumida de Conhecimentos Esperados

| Pilar | Conhecimento esperado |
|---|---|
| Matemática e Estatística | Probabilidade, inferência, regressão, álgebra linear, otimização |
| Programação | Python, SQL, organização de código, Spark em contexto enterprise |
| ML Supervisionado | Classificação, regressão, ensembles, tuning, pipelines |
| Forecast | Séries temporais, backtesting, horizon, sazonalidade |
| Features | Missing, outliers, encoding, lags, agregações, seleção |
| Avaliação | Métricas, validação, threshold, análise de erro |
| Negócio | Framing, KPI, custo de erro, horizonte, ação operacional |
| MLOps | Versionamento, treino, inferência, monitoramento, retreino |
| Governança | SHAP, limitações, fairness, documentação |
| Liderança | Comunicação executiva, revisão técnica, priorização, autonomia |

---

# 18. Checklist de Autoavaliação do Profissional

## 18.1. Modelagem
- [ ] Sei definir corretamente a variável-alvo e o horizonte preditivo.
- [ ] Sei construir baseline antes de testar modelos mais complexos.
- [ ] Sei tratar desbalanceamento e evitar vazamento.
- [ ] Sei comparar modelos com validação adequada.

## 18.2. Dados e features
- [ ] Sei construir datasets analíticos confiáveis.
- [ ] Sei criar features temporais sem contaminar o futuro.
- [ ] Sei justificar por que uma feature tem valor de negócio.

## 18.3. Negócio
- [ ] Consigo traduzir demanda vaga em caso preditivo claro.
- [ ] Consigo explicar impacto de falso positivo e falso negativo.
- [ ] Sei conectar score a uma ação operacional real.

## 18.4. Produção
- [ ] Sei como o modelo será implantado e monitorado.
- [ ] Sei como retreinar e versionar o pipeline.
- [ ] Sei discutir drift e degradação de performance.

## 18.5. Senioridade
- [ ] Consigo defender minhas decisões técnicas para negócio e engenharia.
- [ ] Consigo revisar trabalho de outros cientistas.
- [ ] Consigo assumir um problema ambíguo e conduzir até entrega.

---

# 19. Níveis de maturidade

## 19.1. Júnior
- executa análises com supervisão;
- usa modelos conhecidos;
- depende de direcionamento para framing e validação.

## 19.2. Pleno
- conduz modelagens com autonomia moderada;
- entende métricas e pipelines;
- começa a conversar melhor com o negócio.

## 19.3. Sênior
- define a estratégia analítica;
- lidera a modelagem ponta a ponta;
- decide método, validação, produção e comunicação;
- responde pelo resultado e pelo risco técnico.

---

# 20. Conclusão

Um **Cientista de Dados Sênior especialista em Análise Preditiva** não é um operador de algoritmo.  
É um profissional que combina:

- **rigor estatístico**
- **capacidade de modelagem**
- **engenharia de dados e features**
- **leitura de negócio**
- **operacionalização de modelos**
- **governança**
- **liderança técnica**

Se uma dessas camadas faltar, o profissional pode ser forte em partes do processo, mas ainda não atingiu a senioridade robusta exigida para projetos preditivos críticos em ambiente corporativo.
