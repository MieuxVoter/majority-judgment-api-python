
# Natural Language Processing tools


from tools_i18n import guess_language


def parse_amount(context, amount_string):
    """
    - Probably Not Invented Here ; help us find where it's at
    - Multilingual (hopefully) EN - FR - …
    - Tailored for Gherkin features and behave
    :param context: Context object from behave step def
    :param string amount_string:
    :return int|float:
    """

    # TODO: find the lib(s) implementing what we want here
    # - num2words odes it the other way around
    # - word2number looks ok, but for english only
    # - spacy ? or our very own tensorflow experiment

    if 'fr' in context.tags:
        if amount_string.startswith('aucun'):
            return 0
        if 'un' == amount_string:
            return 1
        # :(|)
        raise NotImplemented()

    from word2number import w2n
    return w2n.word_to_num(amount_string)


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
            'fr': {
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
