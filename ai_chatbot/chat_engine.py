import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

from scripted_chat import BANKS, PERSONAS, detect_topic

PERSONA_ORDER = ["FREEzzzy", "RakNaDne", "mamkinBlogger", "zadr0t", "tipoFUN"]

PERSONA_AFFINITY = {
    "greet": ["FREEzzzy", "RakNaDne", "tipoFUN", "mamkinBlogger", "zadr0t"],
    "game": ["zadr0t", "RakNaDne", "tipoFUN", "FREEzzzy", "mamkinBlogger"],
    "live": ["mamkinBlogger", "tipoFUN", "RakNaDne", "FREEzzzy", "zadr0t"],
    "tech": ["zadr0t", "FREEzzzy", "RakNaDne", "mamkinBlogger", "tipoFUN"],
    "fun": ["tipoFUN", "RakNaDne", "mamkinBlogger", "FREEzzzy", "zadr0t"],
    "portal": ["FREEzzzy", "zadr0t", "mamkinBlogger", "RakNaDne", "tipoFUN"],
    "mood": ["RakNaDne", "FREEzzzy", "tipoFUN", "mamkinBlogger", "zadr0t"],
    "chat": ["RakNaDne", "FREEzzzy", "tipoFUN", "mamkinBlogger", "zadr0t"],
}

DIALOGUE_BANKS = {
    "FREEzzzy": [
        "Согласен. А что остальные думают?",
        "Хорошее начало. Я бы продолжил эту мысль.",
        "Вот теперь разговор становится интереснее.",
        "Поддержу. Только без лишней суеты.",
        "Мне нравится направление. Кто ещё подключится?",
        "Окей, это уже похоже на нормальный разговор.",
        "Я бы на этом не останавливался.",
        "Так, теперь интересно услышать остальных.",
    ],
    "RakNaDne": [
        "Вот, уже пошёл нормальный разговор.",
        "Я бы тоже так сказал.",
        "Ну всё, теперь подключились серьёзно.",
        "Интересно, а кто думает иначе?",
        "Вот это уже можно обсудить.",
        "Поддерживаю. Двигаемся дальше.",
        "Нормально начали, продолжайте.",
        "Я слушаю, что скажут остальные.",
    ],
    "mamkinBlogger": [
        "О, вот это уже хороший сюжет для чата. 📹",
        "Фиксируем эту мысль.",
        "Так, это становится интереснее.",
        "Вот теперь есть о чём поговорить.",
        "Чат, внимание: начинается дискуссия.",
        "Хороший поворот. Продолжаем.",
        "Из этого уже можно сделать отдельную тему.",
        "О, остальные подключаются — отлично.",
    ],
    "zadr0t": [
        "Логично. Теперь проверим следующую мысль.",
        "Есть такое. Но я бы уточнил один момент.",
        "Окей, аргумент принят.",
        "Теперь интересен контраргумент.",
        "Нормально. Давайте не терять логику.",
        "С этим можно работать.",
        "Хорошо, цепочка рассуждений продолжается.",
        "Теперь посмотрим, что скажет следующий.",
    ],
    "tipoFUN": [
        "Опа, дискуссия пошла 😂",
        "Так, это уже становится весело.",
        "Я за продолжение этого сериала.",
        "Чат, не расходимся 😂",
        "Вот теперь мне интересно.",
        "О, пошла движуха.",
        "Ставлю этому разговору лайк.",
        "Так-так, кто следующий?",
    ],
}


@dataclass
class ChatState:
    last_persona: Optional[str] = None
    last_topic: Optional[str] = None
    recent_personas: Deque[str] = field(default_factory=lambda: deque(maxlen=8))
    recent_replies: Dict[str, Deque[str]] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=80))
    )
    recent_messages: Deque[str] = field(default_factory=lambda: deque(maxlen=24))


@dataclass(frozen=True)
class BotTurn:
    persona: str
    text: str
    delay: float = 0.0


class ChatEngine:
    """Pure scripted conversation engine. Telegram transport stays outside this class."""

    def __init__(self, dialogue_probability=0.35, max_dialogue_turns=2, rng=None):
        self.dialogue_probability = max(0.0, min(1.0, dialogue_probability))
        self.max_dialogue_turns = max(0, min(2, max_dialogue_turns))
        self.rng = rng or random.Random()
        self.states = defaultdict(ChatState)

    def state(self, chat_id):
        return self.states[chat_id]

    def _topic(self, text, state):
        return detect_topic(text) or state.last_topic or "chat"

    def _candidate_personas(self, topic, state):
        order = PERSONA_AFFINITY.get(topic, PERSONA_ORDER)
        recent = list(state.recent_personas)
        fresh = [p for p in order if p not in recent[-2:]]
        if not fresh:
            fresh = [p for p in order if p != state.last_persona]
        return fresh or [p for p in PERSONA_ORDER if p != state.last_persona] or PERSONA_ORDER[:1]

    def _pick_primary(self, topic, state):
        candidates = self._candidate_personas(topic, state)
        return self.rng.choice(candidates[:3])

    def _pick_text(self, persona, topic, state):
        bank = BANKS.get(persona, {}).get(topic)
        if not bank:
            topics = list(BANKS.get(persona, {}))
            bank = BANKS[persona][self.rng.choice(topics)]
        used = state.recent_replies[persona]
        available = [x for x in bank if x not in used]
        if not available:
            available = list(bank)
            used.clear()
        text = self.rng.choice(available)
        used.append(text)
        return text

    def user_turn(self, chat_id, text):
        state = self.state(chat_id)
        state.recent_messages.append(text)
        topic = self._topic(text, state)

        persona = self._pick_primary(topic, state)
        answer = self._pick_text(persona, topic, state)
        state.last_persona = persona
        state.last_topic = topic
        state.recent_personas.append(persona)

        turns = [BotTurn(persona, answer, 0.0)]

        if (
            self.max_dialogue_turns
            and topic != "greet"
            and self.rng.random() < self.dialogue_probability
        ):
            turns.extend(self._dialogue_turns(chat_id, topic, persona))

        return turns

    def _dialogue_turns(self, chat_id, topic, previous):
        state = self.state(chat_id)
        turns = []
        used_cycle = {previous}

        for index in range(self.max_dialogue_turns):
            candidates = [
                p for p in PERSONA_AFFINITY.get(topic, PERSONA_ORDER)
                if p not in used_cycle
            ]
            if not candidates:
                break

            persona = candidates[0]
            pool = [
                x for x in DIALOGUE_BANKS[persona]
                if x not in state.recent_replies[persona]
            ]
            if not pool:
                pool = DIALOGUE_BANKS[persona]
                state.recent_replies[persona].clear()

            answer = self.rng.choice(pool)
            state.recent_replies[persona].append(answer)
            state.recent_personas.append(persona)
            state.last_persona = persona
            turns.append(BotTurn(persona, answer, 2.5 * (index + 1)))
            used_cycle.add(persona)

        return turns

    def self_test(self):
        engine = ChatEngine(
            dialogue_probability=1.0,
            max_dialogue_turns=2,
            rng=random.Random(7),
        )

        turns = engine.user_turn(100, "Во что играем?")
        assert 1 <= len(turns) <= 3
        personas = [t.persona for t in turns]
        assert len(personas) == len(set(personas)), personas
        assert personas[0] == "zadr0t"
        assert all(t.text for t in turns)

        turns2 = engine.user_turn(100, "Есть стрим?")
        assert turns2[0].persona == "mamkinBlogger"
        assert len({t.persona for t in turns2}) == len(turns2)

        return {
            "first_cycle": len(turns),
            "second_cycle": len(turns2),
            "personas": personas,
        }
