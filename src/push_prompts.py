"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langsmith import Client

from pull_prompts import _parse_hub_template
from utils import (
    load_yaml,
    check_env_vars,
    print_section_header,
    validate_prompt_structure,
)

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"
HUB_PROMPT_SUFFIX = "bug_to_user_story_v2"

PUBLIC_VISIBILITY_HINT = (
    "Aviso: caso o prompt não fique público automaticamente, "
    "abra o Prompt Hub e ajuste para Public manualmente."
)


def _local_prompt_texts(prompt_data: dict) -> dict[str, str]:
    """Extrai textos de system e user do YAML local para comparação."""
    system_prompt = prompt_data.get("system_prompt", "").strip()
    user_prompt = prompt_data.get("user_prompt", "").strip()

    if not user_prompt:
        user_prompt = "{bug_report}"

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


def _build_chat_prompt_template(prompt_data: dict) -> ChatPromptTemplate:
    """Monta ChatPromptTemplate com as mesmas classes usadas no pull."""
    texts = _local_prompt_texts(prompt_data)

    return ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(texts["system_prompt"]),
            HumanMessagePromptTemplate.from_template(texts["user_prompt"]),
        ]
    )


def _build_push_metadata(prompt_data: dict) -> dict:
    """Metadados do prompt (versão e técnicas aplicadas)."""
    return {
        "version": prompt_data.get("version", "v2"),
        "techniques_applied": prompt_data.get("techniques_applied", []),
        "source": prompt_data.get("source", "local-optimized"),
    }


def _build_push_readme(prompt_data: dict) -> str:
    """Formata metadados como readme para o LangSmith Hub."""
    metadata = _build_push_metadata(prompt_data)
    techniques = metadata.get("techniques_applied", [])

    lines = [
        f"Versão: {metadata.get('version', 'v2')}",
        f"Fonte: {metadata.get('source', 'local-optimized')}",
    ]
    if techniques:
        lines.append("Técnicas aplicadas:")
        lines.extend(f"- {technique}" for technique in techniques)

    return "\n".join(lines)


def _hub_remote_status(hub_identifier: str, local_texts: dict) -> str:
    """
    Compara o template remoto com o conteúdo local.

    Retorna:
        "equal"    — conteúdo idêntico; push não é necessário
        "different" — prompt existe no Hub mas difere do local
        "missing"  — prompt ainda não existe no Hub
    """
    try:
        hub_object = hub.pull(hub_identifier)
    except Exception as exc:
        error_text = str(exc).lower()
        if "not found" in error_text or "404" in error_text:
            return "missing"
        raise

    remote_texts = _parse_hub_template(hub_object)
    if not remote_texts["user_prompt"]:
        remote_texts["user_prompt"] = "{bug_report}"

    remote_system = remote_texts["system_prompt"].strip()
    remote_user = remote_texts["user_prompt"].strip()

    if (
        remote_system == local_texts["system_prompt"]
        and remote_user == local_texts["user_prompt"]
    ):
        return "equal"

    return "different"


def _is_nothing_to_commit_error(error: Exception) -> bool:
    """Detecta resposta da API quando não há diff para commitar."""
    error_text = str(error)
    return "Nothing to commit" in error_text or (
        "409" in error_text and "Nothing to commit" in error_text
    )


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    return validate_prompt_structure(prompt_data)


def push_prompt_to_langsmith(hub_identifier: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        hub_identifier: Identificador no Hub (ex.: javielrezende/bug_to_user_story_v2)
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    local_texts = _local_prompt_texts(prompt_data)

    try:
        remote_status = _hub_remote_status(hub_identifier, local_texts)
    except Exception as exc:
        print(f"Falha ao comparar template local com o Hub: {exc}")
        return False

    if remote_status == "equal":
        print("O template no LangSmith Hub já está igual ao arquivo local.")
        print(f"Nenhuma alteração enviada. Prompt: {hub_identifier}")
        print(
            "Para publicar uma nova versão, altere prompts/bug_to_user_story_v2.yml "
            "e execute este script novamente."
        )
        print(PUBLIC_VISIBILITY_HINT)
        return True

    chat_prompt = _build_chat_prompt_template(prompt_data)
    description = prompt_data.get("description", "").strip()
    tags = prompt_data.get("tags") or []
    metadata = _build_push_metadata(prompt_data)
    readme = _build_push_readme(prompt_data)

    client = Client()

    try:
        print(f"Publicando template no Hub: {hub_identifier}")
        print(f"   Descrição: {description or '(não informada)'}")
        print(f"   Tags: {', '.join(tags) if tags else '(nenhuma)'}")
        print(f"   Técnicas: {', '.join(metadata.get('techniques_applied', [])) or '(nenhuma)'}")

        result = client.push_prompt(
            hub_identifier,
            object=chat_prompt,
            description=description or None,
            tags=tags,
            readme=readme,
            is_public=True,
        )

        result_text = str(result)
        print("Template publicado com sucesso.")
        print(f"   Prompt: {hub_identifier}")
        print(f"   Metadados: {metadata}")
        if result_text and result_text != "None":
            print(f"   Resposta da API: {result_text}")
        print(PUBLIC_VISIBILITY_HINT)
        return True

    except Exception as exc:
        if _is_nothing_to_commit_error(exc):
            print("O template no LangSmith Hub já está igual ao conteúdo local.")
            print(f"Nenhuma alteração enviada. Prompt: {hub_identifier}")
            print(PUBLIC_VISIBILITY_HINT)
            return True

        print(f"Falha durante o push do template: {exc}")
        return False


def push_prompts_to_langsmith() -> bool:
    """
    Carrega o YAML local, valida e publica no LangSmith Prompt Hub.

    Retorno:
        Verdadeiro quando a operação conclui com êxito; falso em qualquer falha.
    """
    print_section_header("PUBLICAÇÃO DE TEMPLATE — LANGSMITH HUB")

    mandatory_env_keys = [
        "LANGSMITH_API_KEY",
        "LANGSMITH_ENDPOINT",
        "USERNAME_LANGSMITH_HUB",
    ]

    if not check_env_vars(mandatory_env_keys):
        return False

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    hub_identifier = f"{username}/{HUB_PROMPT_SUFFIX}"

    prompt_data_raw = load_yaml(str(SOURCE_FILE))
    if not prompt_data_raw:
        print(f"Falha: não foi possível carregar o arquivo {SOURCE_FILE}.")
        return False

    prompt_data = prompt_data_raw.get(PROMPT_KEY)
    if not prompt_data:
        print(f"Falha: chave '{PROMPT_KEY}' ausente em {SOURCE_FILE}.")
        return False

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("Falha: prompt inválido.")
        for error in errors:
            print(f"   - {error}")
        return False

    print(f"Arquivo local: {SOURCE_FILE}")
    print(f"Destino no Hub: {hub_identifier}")

    return push_prompt_to_langsmith(hub_identifier, prompt_data)


def main():
    """Ponto de entrada da rotina de publicação."""
    success = push_prompts_to_langsmith()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
