from typing import TypedDict, Optional, List


class StreakInfo(TypedDict):
    daily_goal: int
    site_streak: int
    streak_extended_today: bool


class LanguageDetails(TypedDict):
    streak: int
    language_string: str
    points: int
    learning: bool
    language: str
    level: int
    current_learning: bool
    sentences_translated: int
    to_next_level: int


class UserDetails(TypedDict):
    username: str
    bio: str
    id: int
    learning_language_string: str
    created: str
    admin: bool
    fullname: str
    avatar: str
    ui_language: str


class LanguageProgress(TypedDict):
    language_string: str
    streak: int
    level_progress: int
    num_skills_learned: int
    level_percent: int
    level_points: int
    next_level: int
    level_left: int
    language: str
    points: int
    fluency_score: float
    level: int


class FriendInfo(TypedDict):
    username: str
    id: int
    points: int
    avatar: str
    displayName: str


class WordInfo(TypedDict):
    text: str
    translations: List[str]
    audioURL: Optional[str]
    isNew: bool