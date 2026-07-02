from pathlib import Path
from openai import AsyncOpenAI
from config import Settings


class AIService:
    """OpenAI-powered neutral counselor, mediator, and prompt generator."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.system_prompt = Path('prompts/counselor.md').read_text(encoding='utf-8')

    async def counsel(self, message: str, context: list[str]) -> str:
        if self.client is None:
            return 'AI counseling is not configured yet. Set OPENAI_API_KEY to enable private counselor responses.'
        messages = [{'role': 'system', 'content': self.system_prompt}]
        messages.extend({'role': 'user', 'content': item} for item in context[-self.settings.counselor_max_history:])
        messages.append({'role': 'user', 'content': message})
        response = await self.client.chat.completions.create(model=self.settings.openai_model, messages=messages, temperature=0.4, max_tokens=450)
        return response.choices[0].message.content or 'I am here with you, but I could not form a response.'

    async def mediate(self, complaint: str, context: list[str]) -> str:
        prompt = (
            "Mediate this concern neutrally. Never take sides. Identify misunderstandings, "
            "summarize both possible viewpoints, ask clarifying questions, recommend a compromise, "
            f"and encourage kind direct communication. Concern: {complaint}"
        )
        return await self.counsel(prompt, context)

    async def appreciation_prompt(self, context: list[str]) -> str:
        prompt = "Create one sweet, specific appreciation prompt for a long-distance couple. Make it easy to answer in under two minutes."
        return await self.counsel(prompt, context)

    async def weekly_review(self, context: list[str]) -> str:
        prompt = "Create a weekly relationship review: wins, hard moments, mood pattern, one repair suggestion, one date idea, and one question for each partner."
        return await self.counsel(prompt, context)
