"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HUB_PROMPT_IDENTIFIER = "leonanluppi/bug_to_user_story_v1"
DESTINATION_FILE = PROJECT_ROOT / "prompts" / "bug_to_user_story_v1.yml"

def _message_template_text(msg) -> str:
    """Recupera o conteúdo textual de um item de mensagem do LangChain."""
    inner = getattr(msg, "prompt", None)
    if inner is not None:
        raw = getattr(inner, "template", None)
        if isinstance(raw, str):
            return raw

    direct = getattr(msg, "template", None)
    if isinstance(direct, str):
        return direct

    raise TypeError(f"Formato de mensagem não suportado: {type(msg).__name__}")


def _parse_hub_template(hub_object) -> dict:
    """Separa instruções de sistema e entrada do usuário de um ChatPromptTemplate."""
    system_prompt_text = ""
    user_prompt_text = ""

    for item in getattr(hub_object, "messages", []) or []:
        content = _message_template_text(item).strip()

        if isinstance(item, SystemMessagePromptTemplate) and not system_prompt_text:
            system_prompt_text = content
        elif isinstance(item, HumanMessagePromptTemplate) and not user_prompt_text:
            user_prompt_text = content

    return {
        "system_prompt": system_prompt_text,
        "user_prompt": user_prompt_text,
    }


def pull_prompts_from_langsmith() -> bool:
    """
    Obtém o template remoto e grava a versão local em formato YAML.

    Retorno:
        Verdadeiro quando a operação conclui com êxito; falso em qualquer falha.
    """
    print_section_header("SINCRONIZAÇÃO DE TEMPLATE — LANGSMITH HUB")

    mandatory_env_keys = [
        "LANGSMITH_API_KEY",
        "LANGSMITH_ENDPOINT",
    ]

    if not check_env_vars(mandatory_env_keys):
        return False

    try:
        print(f"Recuperando template remoto: {HUB_PROMPT_IDENTIFIER}")
        hub_object = hub.pull(HUB_PROMPT_IDENTIFIER)
        extracted = _parse_hub_template(hub_object)

        if not extracted["system_prompt"]:
            print("Falha: instrução de sistema ausente após análise do template.")
            return False

        user_prompt = extracted["user_prompt"]
        if not user_prompt:
            print("Aviso: user_prompt ausente no Hub; usando fallback '{bug_report}'.")
            user_prompt = "{bug_report}"

        yaml_data = {
            "bug_to_user_story_v1": {
                "description": "Template base obtido via LangSmith Prompt Hub",
                "system_prompt": extracted["system_prompt"],
                "user_prompt": user_prompt,
                "version": "v1",
                "source": HUB_PROMPT_IDENTIFIER,
                "tags": [
                    "bug-analysis",
                    "user-story",
                    "langsmith-import",
                ],
            }
        }

        save_ok = save_yaml(yaml_data, str(DESTINATION_FILE))
        if not save_ok:
            print("Falha: não foi possível persistir o arquivo YAML localmente.")
            return False

        print(f"Template armazenado com sucesso em: {DESTINATION_FILE}")
        return True

    except Exception as exc:
        print(f"Falha durante a sincronização do template: {exc}")
        return False


def main():
    """Ponto de entrada da rotina de sincronização."""
    success = pull_prompts_from_langsmith()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
