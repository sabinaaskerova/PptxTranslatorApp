import re
def is_russian_text(text):
    return bool(re.search('[а-яА-ЯёЁ]', text))


def split_languages(text):
    text = re.sub(r'\s+', ' ', text).strip() # remove extra spaces 

    segments = []
    current_segment = ''
    current_lang = None

    tokens = re.findall(r'\S+|\s+|[^\w\s]+', text)

    for token in tokens:
        if token.isspace():
            current_segment += token
        elif re.match(r'[^\w\s]+', token):
            if current_segment:
                segments.append((current_segment, current_lang))
                current_segment = ''
                current_lang = None
            segments.append((token, 'punct'))
        else:
            token_lang = 'ru' if is_russian_text(token) else 'en'
            if current_lang is None or token_lang == current_lang:
                current_segment += token
                current_lang = token_lang
            else:
                if current_segment:
                    segments.append((current_segment, current_lang))
                current_segment = token
                current_lang = token_lang

    # Add the last segment if it exists
    if current_segment:
        segments.append((current_segment, current_lang))

    # Merge segments of the same language
    merged_segments = []
    for segment, lang in segments:
        if merged_segments and merged_segments[-1][1] == lang and lang != 'punct':
            merged_segments[-1] = (merged_segments[-1][0] + segment, lang)
        else:
            merged_segments.append((segment, lang))

    return merged_segments



