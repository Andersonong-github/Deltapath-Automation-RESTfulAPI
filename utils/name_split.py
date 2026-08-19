def split_name(name):
    name = name.strip()
    name = name.title()
    for substring in [' Bin ', ' Binti ', ' & ', '&', ' Bini ', ' Bt ', ' bin ', ' binti ', ' bini ', ' bt ',
                      ' A/L ', ' A/P ', ' a/l ', ' a/p ']:
        name = name.replace(substring, ' ')
    words = name.split()

    if len(words) == 1:
        first_name = words[0].strip()[:20]
        last_name = ''
    else:
        split_index = len(words) // 2
        first_name = ' '.join(words[:split_index]).strip()[:20]
        last_name = ' '.join(words[split_index:]).strip()[:20]

    return first_name, last_name