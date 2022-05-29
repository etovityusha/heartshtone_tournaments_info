class DeckStringCleaner:
    @classmethod
    def clean_deck_string(cls, deck_string: str):
        deck_string_lst = deck_string.split('\n')
        return ''.join([x for x in deck_string_lst if len(x) and x[0] != "#"])
