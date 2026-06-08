# MBA IA — Pull, Otimização e Avaliação de Prompts

Projeto do desafio de Prompt Engineering com **LangChain** e **LangSmith**: sincronizar prompts do Hub, otimizá-los para transformar relatos de bugs em user stories acionáveis e, nas fases seguintes, publicar e avaliar contra um dataset fixo.

## Status do desafio

| Fase | Descrição | Status |
|------|-----------|--------|
| 1 | Pull do prompt de baixa qualidade (`bug_to_user_story_v1`) | ✅ Concluída |
| 2 | Otimização do prompt (`bug_to_user_story_v2`) | ✅ Concluída |
| 3 | Push do prompt otimizado para o LangSmith Hub | ✅ Concluída |
| 4 | Avaliação com métricas (meta: todas ≥ 0.9) | ✅ Concluída |
| 5 | Testes automatizados em `tests/test_prompts.py` | 🔄 Pendente |

Este README será incrementado a cada nova entrega.

---

## Como executar o projeto

**Não é necessário ter Python instalado na máquina.** O ambiente roda inteiramente via Docker: as dependências, a versão do interpretador e os scripts ficam dentro do container.

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (incluso no Docker Desktop, na maioria dos casos)

### 1. Configurar variáveis de ambiente

Na raiz do projeto, copie o template e preencha com suas credenciais:

```bash
cp .env.example .env
```

Variáveis mínimas para a **Fase 1** (pull):

| Variável | Descrição |
|----------|-----------|
| `LANGSMITH_API_KEY` | Chave da API LangSmith |
| `LANGSMITH_ENDPOINT` | Endpoint da API (padrão: `https://api.smith.langchain.com`) |

As demais variáveis (`OPENAI_API_KEY`, `GOOGLE_API_KEY`, `USERNAME_LANGSMITH_HUB`, etc.) serão necessárias nas fases de push e avaliação.

### 2. Subir o container

Na raiz do repositório:

```bash
docker compose up -d --build
```

Isso constrói a imagem (`Dockerfile`), instala as dependências de `requirements.txt` e mantém o serviço `python_app` em execução com o diretório do projeto montado em `/app`.

### 3. Entrar no container

```bash
docker compose exec python_app bash
```

Você estará em `/app` (raiz do projeto dentro do container).

### 4. Executar as fases do projeto

A partir do shell dentro do container, execute os comandos conforme a necessidade:

- **Fase 1 (Pull):** `python src/pull_prompts.py`
- **Fase 3 (Push):** `python src/push_prompts.py`
- **Fase 4 (Avaliação):** `python src/evaluate.py`
- **Fase 5 (Testes):** `pytest tests/test_prompts.py`

Para sair do container sem derrubar o serviço: `exit`.

### 5. Parar o ambiente (opcional)

```bash
docker compose down
```

---

## Fase 1 — Pull do prompt inicial (concluída)

Com o container ativo, `.env` configurado e shell dentro de `python_app`:

```bash
python src/pull_prompts.py
```

O script:

1. Conecta ao LangSmith Prompt Hub usando as credenciais do `.env`
2. Faz pull do prompt `leonanluppi/bug_to_user_story_v1`
3. Salva o resultado em `prompts/bug_to_user_story_v1.yml`

Esse arquivo é o ponto de partida (prompt de baixa qualidade) para a otimização da Fase 2.

---

## Técnicas Aplicadas (Fase 2)

O prompt otimizado está em `prompts/bug_to_user_story_v2.yml`. Ele transforma entradas do tipo `{bug_report}` em user stories no formato esperado. Para isso, foram aplicadas as seguintes técnicas avançadas:

### 1. Role Prompting
- **O que foi feito:** O system prompt define a persona de *Analista de Produto Sênior e Especialista em Engenharia de Requisitos*.
- **Justificativa:** Orienta o modelo a priorizar valor de negócio e critérios verificáveis, em vez de apenas reescrever o bug.
- **Exemplo Prático:**
  > "Você é um **Analista de Produto Sênior e Especialista em Engenharia de Requisitos**, com mais de 10 anos de experiência..."

### 2. Chain of Thought (CoT)
- **O que foi feito:** Instrução para realizar um raciocínio interno em 6 passos (quem, o quê, por quê, validação, contexto técnico, complexidade).
- **Justificativa:** Melhora a qualidade da análise em bugs complexos ao decompor o problema antes de gerar a resposta final.
- **Exemplo Prático:**
  > "Antes de escrever a user story, analise mentalmente: 1. Quem é afetado? 2. O quê deveria acontecer? ... 6. Qual a complexidade?"

### 3. Few-shot Learning (obrigatório)
- **O que foi feito:** Inclusão de três exemplos sintéticos (simples, médio com segurança, complexo com múltiplos problemas) com entrada e saída esperada.
- **Justificativa:** Ancoram o formato *Como… eu quero… para que…* e alinham a estrutura das seções.
- **Exemplo Prático:** Exemplos de UI, Segurança (API) e Sistemas Médicos (Múltiplos bugs) estão detalhados no arquivo YAML do prompt.

### 4. Skeleton of Thought
- **O que foi feito:** Templates de saída distintos por complexidade (enxuto para bugs simples; seções estruturadas com `===` para complexos).
- **Justificativa:** Garante consistência e clareza, especialmente para bugs que exigem detalhes técnicos ou tasks sugeridas.
- **Exemplo Prático:** Uso de seções como `=== USER STORY PRINCIPAL ===` e `=== CRITÉRIOS DE ACEITAÇÃO ===` para casos críticos.

---

## Fase 3 — Push para o LangSmith Hub (concluída)

Com o prompt otimizado e validado localmente, o script de push o publica no seu workspace do LangSmith Hub:

```bash
python src/push_prompts.py
```

O script realiza as seguintes etapas:

1.  **Carregamento Local**: lê o arquivo `prompts/bug_to_user_story_v2.yml`.
2.  **Validação**: verifica se a estrutura do prompt (system, user, variáveis) está correta antes de tentar o upload.
3.  **Comparação Inteligente**: faz um pull da versão atual no Hub (se existir) e compara com a versão local. Se forem idênticos, o push é ignorado para evitar commits duplicados.
4.  **Push Público**: faz o upload para `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` com visibilidade pública.
5.  **Metadados e README**: anexa as técnicas de Prompt Engineering utilizadas e a versão nos metadados do prompt no Hub.

---

## Fase 4 — Avaliação de métricas (concluída)

Com o prompt otimizado e publicado no Hub, executa-se a avaliação contra o dataset de 15 exemplos:

```bash
python src/evaluate.py
```

O script realiza as seguintes etapas:

1.  **Carregamento do Dataset**: carrega os 15 exemplos do arquivo `datasets/bug_to_user_story.jsonl`.
2.  **Sincronização com LangSmith**: cria ou atualiza o dataset de avaliação no LangSmith.
3.  **Execução do Prompt**: para cada exemplo, puxa o prompt do Hub e gera a user story.
4.  **Avaliação (LLM-as-Judge)**: utiliza métricas de F1-Score, Clarity e Precision para julgar a qualidade.
5.  **Cálculo de Métricas Derivadas**: gera os scores de Helpfulness e Correctness.

> [!IMPORTANT]
> **Observação sobre Visualização no LangSmith:** A visualização de percentuais agregados (gráficos de barras) na aba **Experiments** do LangSmith requer o uso da função nativa `evaluate` do pacote `langsmith.evaluation`. Seguindo as instruções do desafio de **não alterar** o arquivo `src/evaluate.py` original, a implementação manteve a lógica de avaliação customizada. Por esse motivo, os resultados são registrados no LangSmith para auditoria e tracing, mas não alimentam automaticamente os gráficos de percentuais do painel de experimentos.

### Resultados Obtidos

Os resultados detalhados estão na seção **Resultados da Avaliação Final** ao final deste documento.

---

## Próximas fases (em breve)

As seções abaixo serão preenchidas nas próximas entregas:

- **Fase 5:** `pytest tests/test_prompts.py` — testes de validação do prompt

---

## Resultados Finais

### Comparativo: Prompt v1 vs. Prompt v2

| Característica | Prompt v1 (Baixa Qualidade) | Prompt v2 (Otimizado) |
| :--- | :--- | :--- |
| **Persona** | Assistente genérico | Especialista em Requisitos Sênior |
| **Lógica** | Zero-shot (direta) | Chain of Thought (6 passos) |
| **Exemplos** | Nenhum | 3 exemplos (Few-shot) |
| **Saída** | Texto livre | Estruturada por complexidade |
| **Contexto Técnico** | Frequentemente perdido | Preservado (IDs, Logs, Severidade) |

### Evidências no LangSmith

**Dashboard de Avaliação:** https://smith.langchain.com/o/193a6597-df06-4e62-8105-6512341c49bf/projects/p/a5c28bc4-d1e8-43e5-965b-ca9cde8fc238

#### Screenshots das Avaliações
- **Média Geral (≥ 0.9):** ![Métricas de Avaliação](./screenshots/metrics_evaluation.png)
- **Dataset (15 exemplos):** ![Dataset de Avaliação](./screenshots/dataset_evaluation.png)
*(Nota: O print de percentuais da aba 'Experiments' não está disponível devido à restrição de não modificação do `src/evaluate.py`, conforme explicado na Fase 4).*
- **Tracing Detalhado:**
  - ![Tracing Simples](./screenshots/tracing_simples.png)
  - ![Tracing Médio](./screenshots/tracing_medio.png)
  - ![Tracing Complexo](./screenshots/tracing_complexo.png)

---

## 📊 Resultados da Avaliação Final

Após ciclos de otimização cirúrgica, o prompt atingiu os seguintes scores (LLM-as-Judge):

- **Média Geral:** 0.9165 ✅
- **F1-Score:** 0.92 ✓
- **Clarity:** 0.93 ✓
- **Precision:** 0.90 ✓
- **Helpfulness:** 0.92 ✓
- **Correctness:** 0.91 ✓

**Status:** 🟢 **APROVADO**

#### O que foi feito para atingir a meta:
1. **Restauração de Estrutura:** Mantive a base original de alta performance com *Role Prompting* e *Chain of Thought*.
2. **Diferenciação de Complexidade:** O prompt alterna automaticamente entre um formato enxuto para bugs simples e um formato estruturado (com seções `===`) para bugs complexos.
3. **Ajuste de Precisão:** Foram implementadas regras de minimalismo para evitar que o modelo "invente" dados técnicos em relatos puramente funcionais.
4. **Mapeamento de Personas:** Foi refinada a extração de personas específicas (ex: "usuário de iOS", "administrador") para elevar a nota de *Clarity*.

---

## Estrutura do projeto

```
mba-ia-desafio-pull-evaluation-prompt/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
│
├── prompts/
│   ├── bug_to_user_story_v1.yml   # Prompt base (pull do Hub)
│   └── bug_to_user_story_v2.yml   # Prompt otimizado
│
├── datasets/
│   └── bug_to_user_story.jsonl    # 15 exemplos (avaliação — não usar no few-shot)
│
├── src/
│   ├── pull_prompts.py            # Fase 1 — pull do Hub
│   ├── push_prompts.py            # Fase 3 — push para o Hub
│   ├── evaluate.py                # Fase 4 — avaliação
│   ├── metrics.py
│   └── utils.py
│
└── tests/
    └── test_prompts.py            # Fase 5 — testes (a implementar)
```

---

## Tecnologias

- Python 3.11 (imagem Docker)
- LangChain + LangSmith Prompt Hub
- Formato de prompts: YAML
- LLM: OpenAI ou Google Gemini (configurável via `.env`)

---

## Dataset de avaliação

Arquivo: `datasets/bug_to_user_story.jsonl` — 15 exemplos com `inputs.bug_report` e `outputs.reference`.

O prompt v2 consome `{bug_report}` na mensagem de usuário. **Não** inclua trechos desse arquivo nos few-shots do prompt.

---

## Referências

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [Repositório base do desafio](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt)
