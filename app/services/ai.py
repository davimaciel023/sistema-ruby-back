"""Geração de ideias de conteúdo com a API da Anthropic (Claude)."""

import json

from anthropic import AsyncAnthropic

from app.core.config import settings

SYSTEM_PROMPT = """Você é estrategista de conteúdo digital especializado em música brasileira, \
com foco em forró, piseiro e vaneirão. Você trabalha para a banda Forró Ruby, um trio \
(sanfona, teclado e duas vozes) que quer crescer no Instagram e TikTok para fechar mais \
contratos de show.

Quando receber uma ideia inicial da banda, gere ideias de conteúdo concretas e prontas para \
executar. Baseie-se no que comprovadamente engaja para artistas de forró no Brasil: trechos \
de música ao vivo com boa captação de áudio, bastidores e intimidade da banda, participação \
do público, trends adaptadas ao forró, cortes verticais de 15-40s com gancho nos 2 primeiros \
segundos, legendas que puxam comentário e postagem nos horários de pico do público nordestino \
e das casas de forró (fim de tarde e noite, quinta a domingo).

Para cada ideia explique de forma direta por que ela tende a engajar esse público. \
Responda sempre em português do Brasil."""

IDEAS_SCHEMA = {
    "type": "object",
    "properties": {
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Nome curto da ideia"},
                    "format": {
                        "type": "string",
                        "description": "Formato: Reels, Carrossel, Stories, TikTok, Live…",
                    },
                    "hook": {
                        "type": "string",
                        "description": "Gancho dos 2 primeiros segundos do vídeo",
                    },
                    "description": {
                        "type": "string",
                        "description": "Roteiro resumido: o que gravar e como montar",
                    },
                    "caption": {"type": "string", "description": "Sugestão de legenda"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                    "best_time": {
                        "type": "string",
                        "description": "Melhor dia/horário para postar",
                    },
                    "why_it_works": {
                        "type": "string",
                        "description": "Por que essa ideia engaja o público de forró",
                    },
                },
                "required": [
                    "title",
                    "format",
                    "hook",
                    "description",
                    "caption",
                    "hashtags",
                    "best_time",
                    "why_it_works",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["ideas"],
    "additionalProperties": False,
}


def ai_configured() -> bool:
    return bool(settings.anthropic_api_key)


async def generate_content_ideas(prompt: str) -> list[dict]:
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": IDEAS_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": (
                    "Ideia inicial da banda: "
                    f"{prompt}\n\n"
                    "Gere de 4 a 6 ideias de conteúdo desenvolvendo essa ideia."
                ),
            }
        ],
    )
    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)["ideas"]
