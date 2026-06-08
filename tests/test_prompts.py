"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any

@pytest.fixture(scope="session")
def prompts_dir() -> Path:
    """Return the prompts directory."""
    return Path(__file__).parent.parent / "prompts"

@pytest.fixture(scope="session")
def prompt_v2_data(prompts_dir: Path) -> Dict[str, Any]:
    """Load and return bug_to_user_story_v2.yml data."""
    file_path = prompts_dir / "bug_to_user_story_v2.yml"
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    # The file has a top-level key matching the prompt ID
    return data['bug_to_user_story_v2']

def test_prompt_has_system_prompt(prompt_v2_data: Dict[str, Any]):
    """Verifica se o campo 'system_prompt' existe e não está vazio."""
    assert 'system_prompt' in prompt_v2_data, "O prompt deve conter o campo 'system_prompt'"
    assert prompt_v2_data['system_prompt'].strip(), "O campo 'system_prompt' não pode estar vazio"

def test_prompt_has_role_definition(prompt_v2_data: Dict[str, Any]):
    """Verifica se o prompt define uma persona (ex: 'Você é um ...')."""
    system_prompt = prompt_v2_data['system_prompt']
    # Check for persona definition keywords
    persona_keywords = ["Você é um", "Você é uma", "As a ", "Role:", "Papel:"]
    assert any(keyword.lower() in system_prompt.lower() for keyword in persona_keywords), \
        "O prompt deve definir uma persona ou papel (ex: 'Você é um ...')"

def test_prompt_mentions_format(prompt_v2_data: Dict[str, Any]):
    """Verifica se o prompt exige formato Markdown ou User Story padrão."""
    system_prompt = prompt_v2_data['system_prompt']
    format_keywords = ["Markdown", "User Story", "Como [persona]", "Critérios de Aceitação"]
    assert any(keyword.lower() in system_prompt.lower() for keyword in format_keywords), \
        "O prompt deve mencionar o formato de saída (Markdown ou User Story)"

def test_prompt_has_few_shot_examples(prompt_v2_data: Dict[str, Any]):
    """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
    system_prompt = prompt_v2_data['system_prompt']
    # Check for few-shot example markers
    example_keywords = ["Exemplo", "Few-shot", "Entrada:", "Saída esperada:"]
    assert any(keyword.lower() in system_prompt.lower() for keyword in example_keywords), \
        "O prompt deve conter exemplos de poucas passagens (Few-shot)"

def test_prompt_no_todos(prompt_v2_data: Dict[str, Any]):
    """Garante que não existem marcações [TODO] no texto."""
    system_prompt = prompt_v2_data['system_prompt']
    # Check for [TODO], TODO:, or similar placeholders
    assert "[TODO]" not in system_prompt, "O prompt contém uma marcação '[TODO]'"
    assert "TODO:" not in system_prompt, "O prompt contém uma marcação 'TODO:'"

def test_minimum_techniques(prompt_v2_data: Dict[str, Any]):
    """Verifica se pelo menos 2 técnicas foram listadas nos metadados."""
    techniques = prompt_v2_data.get('techniques_applied', [])
    assert isinstance(techniques, list), "O campo 'techniques_applied' deve ser uma lista"
    assert len(techniques) >= 2, f"O prompt deve listar pelo menos 2 técnicas, mas encontrou {len(techniques)}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
