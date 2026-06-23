"""
FSM holatlari — Savol qo'shish va Reklama yuborish.
"""
from aiogram.fsm.state import State, StatesGroup


class LangState(StatesGroup):
    choosing = State()


class QuestionAdd(StatesGroup):
    subject = State()
    text = State()
    opt_a = State()
    opt_b = State()
    opt_c = State()
    opt_d = State()
    correct = State()
    difficulty = State()
    confirm = State()


class BroadcastState(StatesGroup):
    text = State()
    confirm = State()


class CategoryAdd(StatesGroup):
    name = State()
    time_limit = State()
    confirm = State()


class ClassAdd(StatesGroup):
    name = State()
    confirm = State()
