"""Unofficial API for duolingo.com"""
from typing import List
from datetime import datetime, timedelta

import requests

from .jwt import decode
from .response_types import StreakInfo, LanguageDetails, UserDetails, LanguageProgress, FriendInfo, WordInfo


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class DuolingoException(Exception):
    pass


class Duolingo(object):
    _USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 " \
                  "Safari/537.36"

    def __init__(self, *, jwt):
        """
        Create a connection to the Duolingo server, providing your JWT for authentication.

        >>> from duolingo import Duolingo
        >>> lingo = duolingo.Duolingo(jwt=MY_DUOLINGO_JWT)
        >>>
        >>> lingo.get_languages()  # Issue an arbitrary command
        ['...', 'High Valyrian'...]
        """
        self.jwt = jwt

        self.session = requests.Session()
        self.session.cookies.set_cookie(
            requests.cookies.create_cookie("jwt_token", self.jwt)
        )

        self._set_username()

        if not self._check_authentication():
            raise DuolingoException(
                "The Duolingo API was unable to authenticate your credentials. Please check your JWT and try again."
            )

        self.user_data = Struct(**self._get_data())

    def _set_username(self):
        """
        AFTER setting `self.jwt` and `self.session`, call this method to retrieve and set `self.username`
        """
        if (not getattr(self, 'jwt', None)) or (not getattr(self, 'session', None)):
            raise RuntimeError("You must set `self.jwt` and `self.session` before calling this method.")

        decoded_jwt = decode(self.jwt, algorithms=["HS256"], options={"verify_signature": False})
        uuid = decoded_jwt["sub"]

        url = "https://www.duolingo.com/2017-06-30/users/{}?fields=username"
        url = url.format(uuid)
        request = self._make_req(url)

        try:
            self.username = request.json()['username']
        except:
            raise Exception('Could not get username')

    def _make_req(self, url, data=None):
        headers = {}
        if self.jwt is not None:
            headers['Authorization'] = 'Bearer ' + self.jwt
        headers['User-Agent'] = self._USER_AGENT
        req = requests.Request('POST' if data else 'GET',
                               url,
                               json=data,
                               headers=headers,
                               cookies=self.session.cookies)
        prepped = req.prepare()

        return self.session.send(prepped)

    def _check_authentication(self):
        resp = self._make_req(self._get_user_url())
        return resp.status_code == 200

    def _get_user_url_by_id(self, fields=None):
        if fields is None:
            fields = []
        url = 'https://www.duolingo.com/2017-06-30/users/{}'.format(self.user_data.id)
        fields_params = requests.utils.requote_uri(','.join(fields))
        if fields_params:
            url += '?fields={}'.format(fields_params)
        return url

    def _get_user_url(self):
        return "https://duolingo.com/users/%s" % self.username

    def _switch_language(self, abbr):
        """
        Change the learned language with
        ``https://www.duolingo.com/switch_language``.

        :param abbr: Wanted language abbreviation (example: ``'fr'``)
        :type abbr: str
        """
        data = {"learning_language": abbr}
        url = "https://www.duolingo.com/switch_language"
        response = self._make_req(url, data)
        response.raise_for_status()

        self.user_data = Struct(**self._get_data())

        if not self._is_current_language(abbr):
            raise DuolingoException('Failed to switch language')

    def _get_data_by_user_id(self, fields=None):
        """
        Get user's data from ``https://www.duolingo.com/2017-06-30/users/<user_id>``.
        """
        if fields is None:
            fields = []
        get = self._make_req(self._get_user_url_by_id(fields))
        if get.status_code == 404:
            raise DuolingoException('User not found')
        else:
            return get.json()

    def _get_data(self):
        """
        Get user's data from ``https://www.duolingo.com/users/<username>``.
        """
        get = self._make_req(self._get_user_url())
        if get.status_code == 404:
            raise Exception('User not found')
        else:
            return get.json()

    @staticmethod
    def _make_dict(keys, array):
        data = {}

        for key in keys:
            if type(array) == dict:
                data[key] = array[key]
            else:
                data[key] = getattr(array, key, None)

        return data

    @staticmethod
    def _compute_dependency_order_func(skills):
        # Create dictionary:
        skills_dict = {}
        for skill in skills:
            skills_dict[skill['name']] = skill
        # Get ordinal for all dependencies
        for skill in skills:
            skill['dependency_order'] = Duolingo._get_skill_ordinal(skills_dict, skill, [])

    @staticmethod
    def _get_skill_ordinal(skills_dict, skill, breadcrumbs):
        # If name is already in breadcrumbs, we've found a loop
        if skill['name'] in breadcrumbs:
            raise DuolingoException("Loop encountered: {}".format(breadcrumbs + [skill['name']]))
        # If order already set for this skill, return it
        if "dependency_order" in skill:
            return skill["dependency_order"]
        # If no dependencies, set order on this skill to 1
        if not skill['dependencies_name']:
            skill['dependency_order'] = 1
            return 1
        # Calculate order based on order of dependencies
        new_breadcrumbs = breadcrumbs + [skill['name']]
        order = 1 + max(
            [
                Duolingo._get_skill_ordinal(
                    skills_dict,
                    skills_dict[name],
                    new_breadcrumbs
                )
                for name in skill['dependencies_name']
            ]
        )
        skill["dependency_order"] = order
        return order

    def get_languages(self, abbreviations: bool = False) -> List[str]:
        """
        Get practiced languages.

        >>> lingo.get_languages()
        ['...', 'High Valyrian'...]

        >>> lingo.get_languages(abbreviations=True)
        ['...', 'hv'...]
        """
        data = []

        for lang in self.user_data.languages:
            if lang['learning']:
                if abbreviations:
                    data.append(lang['language'])
                else:
                    data.append(lang['language_string'])
        return data

    def get_language_from_abbr(self, abbr: str) -> str:
        """
        Get language full name from abbreviation.

        >>> lingo.get_language_from_abbr(abbr='hv')
        'High Valyrian'
        """
        for language in self.user_data.languages:
            if language['language'] == abbr:
                return language['language_string']
        return None

    def get_abbreviation_of(self, lang: str) -> str:
        """
        Get abbreviation of a language.

        >>> lingo.get_abbreviation_of(lang='High Valyrian')
        'hv'
        """
        for language in self.user_data.languages:
            if language['language_string'].lower() == lang.lower():
                return language['language']
        return None

    def get_language_details(self, language) -> LanguageDetails:
        """
        Get user's status about a language.

        >>> lingo.get_language_details(language='High Valyrian')
        {'streak': ..., ..., 'to_next_level': ...}
        """
        for lang in self.user_data.languages:
            if language == lang['language_string']:
                return lang

        raise ValueError(f"Language {language} not found for this user.")

    def get_user_info(self) -> UserDetails:
        """
        Get user's information.

        >>> lingo.get_user_info()
        {'username': ..., ..., 'ui_language': ...}
        """
        fields = ['username', 'bio', 'id', 'learning_language_string',
                  'created', 'admin', 'fullname', 'avatar', 'ui_language']

        return self._make_dict(fields, self.user_data)

    def get_streak_info(self) -> StreakInfo:
        """
        Get user's streak information.

        >>> lingo.get_streak_info()
        {'daily_goal': ..., ..., 'streak_extended_today': ...}
        """
        fields = ['daily_goal', 'site_streak', 'streak_extended_today']
        return self._make_dict(fields, self.user_data)

    def _is_current_language(self, abbr: str) -> bool:
        """Get if user is learning a language."""
        return abbr in self.user_data.language_data.keys()

    def get_language_progress(self, abbr: str) -> LanguageProgress:
        """
        Get information about user's progression in a language.

        >>> lingo.get_language_progress(abbr='hv')
        {'language_string': 'High Valyrian', ..., 'level': ...}
        """
        if not self._is_current_language(abbr):
            self._switch_language(abbr)

        fields = ['language_string', 'streak', 'level_progress',
                  'num_skills_learned', 'level_percent', 'level_points', 'next_level', 'level_left', 'language',
                  'points', 'fluency_score', 'level']

        return self._make_dict(fields, self.user_data.language_data[abbr])

    def _get_following(self):
        return self._make_req(f"https://www.duolingo.com/2017-06-30/friends/users/{self.user_data.id}/following").json()['following']['users']

    def get_friends(self) -> List[FriendInfo]:
        """
        Get user's friends.

        >>> lingo.get_friends()
        [{'username': '...', ..., 'displayName': '...'}...]
        """
        following = self._get_following()
        friends = []
        for follower in following:
            if follower["isFollowing"]:
                friends.append(
                    {"username": follower["username"], "id": follower["userId"],"points": follower["totalXp"],"avatar": follower["picture"],"displayName": follower["displayName"]})

        return friends

    def get_known_words(self, abbr) -> List[str]:
        """
        Get a list of all words learned by user in a language.

        >>> lingo.get_known_words(abbr=MY_FAVORITE_LANGUAGE_ABBREVIATION)
        [...]
        """
        words = []
        for topic in self.user_data.language_data[abbr]['skills']:
            if topic['learned']:
                words += topic['words']
        return list(set(words))

    def get_known_topics(self, abbr) -> List[str]:
        """
        Return the topics learned by a user in a language.

        >>> lingo.get_known_topics(abbr=MY_FAVORITE_LANGUAGE_ABBREVIATION)
        ['...', '...', ...]
        """
        if not self._is_current_language(abbr):
            self._switch_language(abbr)

        return [topic['title']
                for topic in self.user_data.language_data[abbr]['skills']
                if topic['learned']]

    def get_unknown_topics(self, abbr) -> List[str]:
        """
        Return the topics learned by a user in a language.

        >>> lingo.get_unknown_topics(abbr=MY_FAVORITE_LANGUAGE_ABBREVIATION)
        ['...', '...', ...]
        """
        if not self._is_current_language(abbr):
            self._switch_language(abbr)

        return [topic['title']
                for topic in self.user_data.language_data[abbr]['skills']
                if not topic['learned']]

    def get_golden_topics(self, abbr) -> List[str]:
        """
        Return the topics mastered ("golden") by a user in a language.

        >>> lingo.get_golden_topics(abbr=MY_FAVORITE_LANGUAGE_ABBREVIATION)
        [...]
        """
        if not self._is_current_language(abbr):
            self._switch_language(abbr)

        return [topic['title']
                for topic in self.user_data.language_data[abbr]['skills']
                if topic['learned'] and topic['strength'] == 1.0]

    def get_reviewable_topics(self, abbr):
        """
        Return the topics learned but not golden by a user in a language.

        >>> lingo.get_reviewable_topics(abbr=MY_FAVORITE_LANGUAGE_ABBREVIATION)
        ['...', '...', ...]
        """
        if not self._is_current_language(abbr):
            self._switch_language(abbr)

        return [topic['title']
                for topic in self.user_data.language_data[abbr]['skills']
                if topic['learned'] and topic['strength'] < 1.0]

    def get_vocabulary(self, abbr: str, source_language_abbr=None) -> List[WordInfo]:
        """Get overview of user's vocabulary in a language.

        >>> lingo.get_vocabulary(abbr=MY_FAVORITE_LANGUAGE_ABBREVIATION)
        [{'text': ..., ...}, ...]

        :param abbr: Language abbreviation of learning language
        :param source_language_abbr: Language abbreviation of source language (default: user's UI language)
        """
        if abbr and not self._is_current_language(abbr):
            self._switch_language(abbr)

        current_courses = self._get_data_by_user_id()["currentCourse"]["pathSectioned"]
        progressed_skills = []
        for section in current_courses:
            completedUnits = section["completedUnits"]
            units = section["units"]
            for i in range(completedUnits):
                unit = units[i]
                levels = unit["levels"]
                for l in levels:
                    level_type = l["type"]
                    # unit review doesnt contain new words
                    if level_type in ["chest", "unit_review"]:
                        continue
                    pathLevelClientData = l["pathLevelClientData"]
                    finishedSessions = l["finishedSessions"]
                    if "skillId" in pathLevelClientData:
                        skillId = pathLevelClientData["skillId"]
                        new_obj = {
                            "finishedLevels": 1,
                            "finishedSessions": finishedSessions,
                            "skillId": {
                                "id": skillId
                            }
                        }
                        progressed_skills.append(new_obj)
                    elif "skillIds" in pathLevelClientData:
                        skillIds = pathLevelClientData["skillIds"]
                        for skillId in skillIds:
                            new_obj = {
                                "finishedLevels": 1,
                                "finishedSessions": finishedSessions,
                                "skillId": {
                                    "id": skillId
                                }
                            }
                            progressed_skills.append(new_obj)

        # updated URL, default language to be english,
        current_index = 0
        data = []
        if source_language_abbr is None:
            source_language_abbr = self.user_data.ui_language
        while True:
            overview_url = f"https://www.duolingo.com/2017-06-30/users/{self.user_data.id}/courses/{abbr}/{source_language_abbr}/learned-lexemes?sortBy=ALPHABETICAL&startIndex={current_index}"
            overview_request = self._make_req(overview_url, data={
                "lastTotalLexemeCount": 0,
                "progressedSkills": progressed_skills
            })
            overview = overview_request.json()
            learnedLexemes = overview['learnedLexemes']
            data.extend(learnedLexemes)
            pagination = overview['pagination']
            totalLexemes = pagination['totalLexemes']
            if len(data) >= totalLexemes:
                break

            nextStartIndex = pagination['nextStartIndex']
            current_index = nextStartIndex
        return data

    def get_daily_xp_progress(self):
        """
        Return the topics learned but not golden by a user in a language.

        >>> lingo.get_daily_xp_progress()
        {'xp_goal': ..., ..., 'xp_today': ...}
        """
        daily_progress = self._get_data_by_user_id(["xpGoal", "xpGains", "streakData"])

        if not daily_progress:
            raise DuolingoException(
                "Could not get daily XP progress for user \"{}\". Are you logged in as that user?".format(self.username)
            )

        # xpGains lists the lessons completed on the last day where lessons were done.
        # We use the streakData.updatedTimestamp to get the last "midnight", and get lessons after that.
        reported_timestamp = daily_progress['streakData']['updatedTimestamp']
        reported_midnight = datetime.fromtimestamp(reported_timestamp)
        midnight = datetime.fromordinal(datetime.today().date().toordinal())

        # Sometimes the update is marked into the future. When this is the case
        # we fall back on the system time for midnight.
        time_discrepancy = min(midnight - reported_midnight, timedelta(0))
        update_cutoff = round((reported_midnight + time_discrepancy).timestamp())

        lessons = [lesson for lesson in daily_progress['xpGains'] if
                   lesson['time'] > update_cutoff]

        return {
            "xp_goal": daily_progress['xpGoal'],
            "lessons_today": lessons,
            "xp_today": sum(x['xp'] for x in lessons)
        }
