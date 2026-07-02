from __future__ import annotations

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

CARD_BG = (255, 231, 238)
PANEL = (255, 250, 252)
ROSE = (215, 95, 127)
INK = (69, 48, 60)
GOLD = (232, 169, 76)


class CardService:
    """Generates consistently styled relationship image cards with Pillow."""

    async def couple_card(self, title: str, lines: list[str]) -> BytesIO:
        return self._card(title, lines, accent=ROSE)

    async def profile_card(self, name: str, lines: list[str]) -> BytesIO:
        return self._card(f"{name}'s Relationship Profile", lines, accent=GOLD)

    async def memory_card(self, text: str, tags: list[str]) -> BytesIO:
        return self._card("A Memory Worth Keeping", [text, f"Tags: {', '.join(tags)}"], accent=ROSE)

    async def anniversary_card(self, title: str, days: int) -> BytesIO:
        return self._card("Anniversary", [title, f"{days} days of choosing each other."], accent=GOLD)

    async def achievement_card(self, title: str, description: str) -> BytesIO:
        return self._card(f"Achievement: {title}", [description], accent=ROSE)

    async def milestone_card(self, title: str, lines: list[str]) -> BytesIO:
        return self._card(f"Milestone: {title}", lines, accent=GOLD)

    async def mood_summary_card(self, average: float, entries: int, latest: int | None) -> BytesIO:
        latest_text = "No latest mood yet" if latest is None else f"Latest mood: {latest}/10"
        return self._card("Mood Summary", [f"Average mood: {average}/10", f"Entries: {entries}", latest_text], accent=ROSE)

    def _card(self, title: str, lines: list[str], *, accent: tuple[int, int, int]) -> BytesIO:
        image = Image.new("RGB", (1000, 560), CARD_BG)
        draw = ImageDraw.Draw(image)
        title_font = ImageFont.load_default(size=34)
        body_font = ImageFont.load_default(size=22)
        draw.rounded_rectangle((34, 34, 966, 526), radius=38, fill=PANEL, outline=accent, width=5)
        draw.ellipse((782, -110, 1110, 218), fill=(255, 220, 230), outline=None)
        draw.ellipse((-90, 390, 180, 660), fill=(255, 238, 202), outline=None)
        draw.text((82, 74), "♡", fill=accent, font=title_font)
        draw.text((132, 80), title[:58], fill=INK, font=title_font)
        y = 158
        for raw in lines[:9]:
            for line in self._wrap(raw, 74):
                draw.text((96, y), line, fill=INK, font=body_font)
                y += 34
            y += 8
        draw.text((96, 482), "ntm × Kosi • made with care", fill=accent, font=body_font)
        output = BytesIO()
        image.save(output, "PNG")
        output.seek(0)
        return output

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 > width:
                lines.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
        if current:
            lines.append(current)
        return lines or [""]
