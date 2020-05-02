"""
Natural Language Processing tools
"""

import re
from text_to_num import text2num

from tools_i18n import guess_locale


def parse_amount(context, amount_string):
    """
    - Multilingual (hopefully) EN - FR - …
    - Tailored for Gherkin features and behave
    :param context: Context object from behave step def
    :param string amount_string:
    :return int|float:
    """
    language = guess_locale(context)[0:2]
    if 'fr' == language:
        if re.match("^aucun(?:[⋅.-]?e)?$", amount_string):
            return 0
    elif 'en' == language:
        if re.match("^no(?:ne)?$", amount_string):
            return 0

    return text2num(text=amount_string, lang=language, relaxed=True)


def parse_yaml(context, with_i18n=True):
    """
    :param context: Context object from behave step def
    :param bool with_i18n:
    :return: The step pystring contents as dictionary from YAML
    """
    from yaml import safe_load
    data = safe_load(context.text)

    if with_i18n:
        language = guess_locale(context)
        # Eventually, load these maps from files, perhaps
        yaml_keys_map = {
            'fr_FR': {
                'titre': 'title',
                'candidats': 'candidates',
                'candidates': 'candidates',
                'candidat⋅es': 'candidates',
            },
        }
        # Naive mapping, not collision-resilient, but it's ok for now
        if language in yaml_keys_map:
            for key in [k for k in data.keys()]:
                if key in yaml_keys_map[language]:
                    data[yaml_keys_map[language][key]] = data[key]

    return data


def parse_grades(context, data, poll):
    grades = []

    for candidate in poll.candidates:
        if candidate not in data:
            raise AssertionError("Candidate `%s' not found in `%s'." % (candidate, data))
        grade_text = data[candidate]

        grades_database = {  # TBD
            'fr_FR': {
                'quality': {
                    '7': [
                        ['à rejeter'],
                        ['insuffisant', 'insuffisante', 'insuffisant⋅e', 'insuffisant-e', 'insuffisant.e'],
                        ['passable'],
                        ['assez bien'],
                        ['bien'],
                        ['très bien'],
                        ['excellent', 'excellente', 'excellent⋅e', 'excellent-e', 'excellent.e'],
                    ],
                },
            }
        }
        locale = guess_locale(context)
        grades_in_order = grades_database[locale]['quality']['7']
        for k, matching_grades in enumerate(grades_in_order):
            if grade_text in matching_grades:
                grades.append(k)
                break

    return grades
