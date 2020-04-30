"""
Natural Language Processing tools
"""

import re
from text_to_num import text2num

from tools_i18n import guess_language


def parse_amount(context, amount_string):
    """
    - Multilingual (hopefully) EN - FR - …
    - Tailored for Gherkin features and behave
    :param context: Context object from behave step def
    :param string amount_string:
    :return int|float:
    """
    language = guess_language(context)[0:2]
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
        language = guess_language(context)
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
