
# Natural language processing tools


def parse_amount(context, amount_string):

    # TODO: find the lib(s) implementing what we want here
    # - num2words odes it the other way around
    # - word2number looks ok, but for english only
    # - spacy ? or our very own tensorflow experiment

    if 'fr' in context.tags:
        # :(|)
        if 'un' == amount_string:
            return 1
        raise NotImplemented()

    from word2number import w2n
    return w2n.word_to_num(amount_string)
