# MBA IA — Pull, Otimização e Avaliação de Prompts

Projeto do desafio de Prompt Engineering com **LangChain** e **LangSmith**: sincronizar prompts do Hub, otimizá-los para transformar relatos de bugs em user stories acionáveis e, nas fases seguintes, publicar e avaliar contra um dataset fixo.

## Status do desafio

| Fase | Descrição | Status |
|------|-----------|--------|
| 1 | Pull do prompt de baixa qualidade (`bug_to_user_story_v1`) | Concluída |
| 2 | Otimização do prompt (`bug_to_user_story_v2`) | Concluída |
| 3 | Push do prompt otimizado para o LangSmith Hub | Concluída |
| 4 | Avaliação com métricas (meta: todas ≥ 0.9) | Pendente |
| 5 | Testes automatizados em `tests/test_prompts.py` | Pendente |

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

Você estará em `/app` (raiz do projeto dentro do container). Todos os comandos Python abaixo devem ser executados **a partir desse shell**.

Para sair do container sem derrubar o serviço: `exit`.

### 4. Parar o ambiente (opcional)

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

## Fase 2 — Otimização do prompt (concluída)

O prompt otimizado está em `prompts/bug_to_user_story_v2.yml`. Ele transforma entradas do tipo `{bug_report}` (usadas pelo dataset `datasets/bug_to_user_story.jsonl`) em user stories no formato esperado pela avaliação.

### Separação System vs User

- **`system_prompt`**: persona, regras, formato de saída, few-shots e edge cases
- **`user_prompt`**: apenas `{bug_report}` — variável que o dataset e o `evaluate.py` injetam em cada execução

### Técnicas aplicadas e justificativa

#### 1. Role Prompting

**O que foi feito:** o system prompt abre com a persona de *Analista de Produto Sênior e Especialista em Engenharia de Requisitos*, com competências explícitas (persona, critérios testáveis, contexto técnico).

**Por quê:** relatos de bug costumam ser vagos ou técnicos demais. Uma persona especializada orienta o modelo a priorizar valor de negócio, clareza para desenvolvedores e critérios verificáveis — em vez de apenas reescrever o bug.

#### 2. Chain of Thought (CoT)

**O que foi feito:** seção de raciocínio em 6 passos (quem, o quê, por quê, como validar, contexto técnico, complexidade), com instrução explícita para **não** expor esse raciocínio na resposta final.

**Por quê:** converter bug em user story exige decomposição (persona, comportamento esperado, cenários de teste). O CoT melhora a qualidade da análise em bugs médios e complexos sem poluir a saída entregue ao time.

#### 3. Few-shot Learning (obrigatório)

**O que foi feito:** três exemplos sintéticos (simples, médio com segurança, complexo com múltiplos problemas), cada um com entrada e saída esperada.

**Por quê:** o desafio exige few-shot; exemplos ancoram o formato *Como… eu quero… para que…*, critérios Dado/Quando/Então e seções estruturadas para casos críticos.

**Importante:** os exemplos **não** foram tirados do dataset de avaliação (`datasets/bug_to_user_story.jsonl`). Usar casos do próprio dataset no prompt seria vazamento de dados (*data leakage*) e inflaria as métricas artificialmente. Os few-shots são ilustrativos e independentes do conjunto de teste.

#### 4. Skeleton of Thought

**O que foi feito:** templates de saída distintos por complexidade — formato enxuto para bugs simples/médios e seções `=== USER STORY PRINCIPAL ===`, `=== CRITÉRIOS DE ACEITAÇÃO ===`, etc., para bugs complexos.

**Por quê:** o dataset mistura bugs simples (5), médios (7) e complexos (3). Um esqueleto explícito reduz respostas inconsistentes e alinha a estrutura às referências de avaliação.

### Outros elementos do prompt v2

- **Regras de comportamento** explícitas (foco no comportamento esperado, preservar dados técnicos, não inventar informação)
- **Tratamento de edge cases** (relato vago, múltiplos bugs, ambiente específico, steps to reproduce)
- Metadados em `techniques_applied` no YAML para rastreabilidade

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

## Próximas fases (em breve)

As seções abaixo serão preenchidas nas próximas entregas:

- **Fase 4:** `python src/evaluate.py` — avaliar contra o dataset e iterar até métricas ≥ 0.9
- **Fase 5:** `pytest tests/test_prompts.py` — testes de validação do prompt
- **Resultados finais:** link do LangSmith, screenshots e tabela v1 vs v2

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
