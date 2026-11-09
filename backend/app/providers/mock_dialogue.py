"""Mock dialogue engine — deterministic, no external calls.

REPLACEMENT POINT (plan Phase 3 / Task 4): swap this class for an
LLM-backed engine implementing the same DialogueEngine protocol; the API
routes stay unchanged.
"""

from typing import Mapping

from app.models.dialogue import (
    MAX_TURNS,
    STATE_GREETING,
    STATE_LISTENING,
    STATE_PRAISE,
    Session,
    Turn,
)

_PRAISES: tuple[str, ...] = (
    "Great job!",
    "Well done!",
    "Awesome!",
    "You are doing great!",
)

FINISH_PRAISE: str = (
    "Amazing talking with you! You did a wonderful job! See you next time!"
)

_TOPIC_INTROS: Mapping[str, str] = {
    "animals": "Let's talk about animals!",
    "colors": "Let's talk about colors!",
    "fruits": "Let's talk about fruits!",
    "sports": "Let's talk about sports!",
    "hobbies": "Let's talk about hobbies!",
}

# Per topic -> per age group -> exactly MAX_TURNS questions.
_QUESTIONS: Mapping[str, Mapping[str, tuple[str, ...]]] = {
    "animals": {
        "4-6": (
            "Do you like dogs?",
            "Do you like cats?",
            "What does a cat say?",
            "Do you like big animals or small animals?",
        ),
        "7-9": (
            "What is your favorite animal?",
            "Do you have a pet at home?",
            "What animal do you think is funny?",
            "Do you like pandas or tigers more?",
        ),
        "10-12": (
            "If you could have any pet, what would you choose and why?",
            "What animal would you like to be for one day?",
            "Which animal do you think is the smartest?",
            "Have you ever seen a really big animal? Where?",
        ),
    },
    "colors": {
        "4-6": (
            "Do you like red?",
            "What color is the sky?",
            "Do you like yellow or blue?",
            "What color is your shirt?",
        ),
        "7-9": (
            "What is your favorite color?",
            "What color do you see around you now?",
            "Do you like bright colors or dark colors?",
            "What color is your school bag?",
        ),
        "10-12": (
            "If your room could be any color, what color would you pick?",
            "What color makes you feel happy? Why?",
            "Do you think colors change how we feel? How?",
            "If you designed a sports team shirt, what colors would you use?",
        ),
    },
    "fruits": {
        "4-6": (
            "Do you like apples?",
            "Do you like bananas?",
            "What fruit is red?",
            "Do you like sweet fruits?",
        ),
        "7-9": (
            "What is your favorite fruit?",
            "Do you like fruit or ice cream more?",
            "What fruit do you eat in the morning?",
            "Have you ever tried a mango?",
        ),
        "10-12": (
            "What fruit would you bring to a picnic, and why?",
            "What is the strangest fruit you have ever tried?",
            "If you could grow one fruit at home, which one?",
            "Do you think fruit is a good snack after sport? Why?",
        ),
    },
    "sports": {
        "4-6": (
            "Do you like running?",
            "Can you jump high?",
            "Do you like football?",
            "Do you like to swim?",
        ),
        "7-9": (
            "What sport do you like?",
            "Do you play any sport at school?",
            "Do you like football or basketball more?",
            "Who do you play sport with?",
        ),
        "10-12": (
            "What sport would you like to learn next? Why?",
            "Do you prefer team sports or solo sports? Why?",
            "Who is your favorite athlete?",
            "If you could join the Olympics one day, which sport would you pick?",
        ),
    },
    "hobbies": {
        "4-6": (
            "Do you like drawing?",
            "Do you like singing?",
            "Do you like dancing?",
            "Do you like story books?",
        ),
        "7-9": (
            "What do you like to do after school?",
            "Do you like drawing or reading more?",
            "What do you do on the weekend?",
            "Do you play any games with your friends?",
        ),
        "10-12": (
            "What hobby would you love to try one day?",
            "What do you like to do after school, and why?",
            "If you had a free afternoon, how would you spend it?",
            "What is something you learned to do by yourself?",
        ),
    },
}


class MockDialogueEngine:
    """Scripted engine: praise + next question, finish after MAX_TURNS."""

    def start(self, age_group: str, topic: str) -> Turn:
        intro = _TOPIC_INTROS[topic]
        question = _QUESTIONS[topic][age_group][0]
        return Turn(
            assistant_text=f"Hello! I'm Coco! {intro} {question}",
            state=STATE_GREETING,
            turn=0,
            finished=False,
        )

    def respond(self, session: Session, child_text: str) -> Turn:
        last = session.last
        if last is None:
            raise ValueError("Session has no greeting turn; it is uninitialized.")
        if last.finished:
            return last

        next_index = last.turn + 1
        if next_index >= MAX_TURNS:
            return Turn(
                assistant_text=FINISH_PRAISE,
                state=STATE_PRAISE,
                turn=MAX_TURNS,
                finished=True,
            )

        praise = _PRAISES[(next_index - 1) % len(_PRAISES)]
        question = _QUESTIONS[session.topic][session.age_group][next_index]
        return Turn(
            assistant_text=f"{praise} {question}",
            state=STATE_LISTENING,
            turn=next_index,
            finished=False,
        )
