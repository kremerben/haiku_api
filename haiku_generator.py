import json
import random
# from botocore.vendored import requests  # for AWS lambda
import requests  # for local development
from typing import Tuple


DATAMUSE_FULL_APIBASE = "https://api.datamuse.com/words?md=sp&sp=s*"
DATAMUSE_APIBASE = "https://api.datamuse.com/words?md=sp"
DATAMUSE_STARTSWITH_ARG = "&sp={}*"
LINE_SPACE = "\n"


def respond(err, res=None):
    print(res)  # adds the generated Haiku to the CloudWatch logs
    return {
        "statusCode": 400 if err else 200,
        "body": err.message if err else json.dumps(res),
        "headers": {"Content-Type": "application/json"},
    }


def lambda_handler(event, context):
    if (
        not event
        or event.get("queryStringParameters")
        or "keyword" not in event["queryStringParameters"]
    ):
        return respond(
            None,
            "Please add a keyword parameter ex: https://haiku.kremer.dev/?keyword=potato "
            "- starts_with parameter is optional ex: https://haiku.kremer.dev/?keyword=potato&starts_with=v",
        )
    qs_params = event["queryStringParameters"]
    keyword = qs_params["keyword"]

    if "starts_with" in qs_params:
        starts_with = qs_params["starts_with"][:1]
        print(f"The keyword is {keyword}, and starts_with letter is {starts_with}.")
    else:
        print(f"The keyword is {keyword}.")
        starts_with = ""

    pg = HaikuGenerator(word=keyword, starts_with=starts_with)

    return respond(None, pg.build_haiku())


class PoemGenerator:
    """ Parent Class that gathers all the words """

    def __init__(self, word: str = "", starts_with: str = ""):
        self.word = word
        self.starts_with = starts_with

        # prime the word lists
        self.nouns = self.get_nouns(word)
        self.verbs = self.get_verbs(word)
        self.adjectives = self.get_adjectives(word)
        # self.adverbs =  self.get_adverbs(word)
        self.associated_words = self.get_associated_words(word)
        self.synonyms = self.get_synonyms(word)
        self.kindof_words = self.get_kindof_words(word)
        self.preceding_words = self.get_preceding_words(word)
        self.following_words = self.get_following_words(word)

        self.all_nouns = self.get_all_nouns(word)
        self.all_verbs = self.get_all_verbs(word)
        self.all_adjectives = self.get_all_adjectives(word)
        # self.all_adverbs = []


    def request_words(self, url, starts_with: str = "") -> list:
        """
            Simple request generator with limit
            :param url: request url
            :param limit: number of values to return, 0 for no limit
            Return:
                [{'word': 'level', 'score': 31451, 'numSyllables': 2},
                 {'word': 'water', 'score': 16450, 'numSyllables': 2}]
        """
        if starts_with or self.starts_with:
            url += DATAMUSE_STARTSWITH_ARG.format(starts_with or self.starts_with)

        return requests.get(url).json()

    def get_related_words(self, word: str) -> list:
        """ Returns related words with syllable count

            Arg: word == string
            Return:
                [{'word': 'level', 'score': 31451, 'numSyllables': 2},
                 {'word': 'water', 'score': 16450, 'numSyllables': 2}]
        """
        related_words_url = f"{DATAMUSE_APIBASE}&ml={word}"
        return self.request_words(related_words_url)

    def get_nouns(self, word: str) -> list:
        return self.request_words(f"{DATAMUSE_APIBASE}&rel_jja={word}")

    def get_verbs(self, word: str) -> list:
        related_words = self.get_related_words(word)
        return [word for word in related_words if "tags" in word and "v" in word["tags"]]

    def get_adjectives(self, word: str) -> list:
        return self.request_words(f"{DATAMUSE_APIBASE}&rel_jjb={word}")

    def get_associated_words(self, word: str) -> list:
        """ Trigger words """
        self.associated_words = self.request_words(f"{DATAMUSE_APIBASE}&rel_trg={word}")
        return self.associated_words

    def get_synonyms(self, word: str) -> list:
        self.synonyms = self.request_words(f"{DATAMUSE_APIBASE}&rel_syn={word}")
        return self.synonyms

    def get_kindof_words(self, word: str) -> list:
        self.kindof_words = self.request_words(f"{DATAMUSE_APIBASE}&rel_spc={word}")
        return self.kindof_words

    def get_preceding_words(self, word: str) -> list:
        self.preceding_words = self.request_words(f"{DATAMUSE_APIBASE}&rel_bgb={word}")
        return self.preceding_words

    def get_following_words(self, word: str) -> list:
        self.following_words = self.request_words(f"{DATAMUSE_APIBASE}&rel_bga={word}")
        return self.following_words

    def indirectly_extend_word_lists(self, word_type_identifier="n"):
        extra_words = []
        extra_words.extend(self.associated_words)
        extra_words.extend(self.synonyms)
        extra_words.extend(self.kindof_words)
        extra_words.extend(self.preceding_words)
        extra_words.extend(self.following_words)
        return [
            word for word in extra_words if "tags" in word and word_type_identifier in word["tags"]
        ]

    def get_all_nouns(self, word: str = "") -> list:
        self.nouns.extend(self.indirectly_extend_word_lists("n"))
        self.all_nouns = list({noun["word"]: noun for noun in self.nouns}.values())
        return self.all_nouns

    def get_all_verbs(self, word: str = "") -> list:
        self.verbs.extend(self.indirectly_extend_word_lists("v"))
        self.all_verbs = list({verb["word"]: verb for verb in self.verbs}.values())
        return self.all_verbs

    def get_all_adjectives(self, word: str = "") -> list:
        self.adjectives.extend(self.indirectly_extend_word_lists("adj"))
        self.all_adjectives = list(
            {adjective["word"]: adjective for adjective in self.adjectives}.values()
        )
        return self.all_adjectives

    def get_all_adverbs(self, word: str = "") -> list:
        """ Not yet in use """
        self.adverbs.extend(self.indirectly_extend_word_lists("v"))
        self.all_adverbs = list({adverb["word"]: adverb for adverb in self.adverbs}.values())
        return self.all_adverbs


class HaikuGenerator(PoemGenerator):
    def build_haiku(self, word=None) -> Tuple[str, str, str]:

        haiku_syllables = [5, 7, 5]
        haiku_result = []

        if not word and self.word:
            word = self.word

        current_wordtype = random.choice(["adj", "n", "v"])

        structure_mapping = {
            # removed adverbs for now
            "n": {"next": "v", "wordlist": self.get_all_nouns(word)},
            "v": {"next": "adj", "wordlist": self.get_all_verbs(word)},
            "adj": {"next": "n", "wordlist": self.get_adjectives(word)},
            # "adverb": {"next": random.choice(["v", "adj"]),
            #            "wordlist": get_all_adverbs(word)
            #            },
        }

        used_words = []

        for syllable_count in haiku_syllables:
            syllable_target = syllable_count
            current_line = []
            error_count = 0

            while syllable_target > 0:
                error_count += 1

                current_words = [
                    _word
                    for _word in structure_mapping[current_wordtype]["wordlist"]
                    if ("numSyllables" in _word and _word["numSyllables"] <= syllable_target)
                ]
                word_to_add = random.choice(current_words) if current_words else None

                if word_to_add and word_to_add["word"] in used_words and error_count < 10:
                    # no duplicates please
                    continue

                elif word_to_add:
                    used_words.append(word_to_add["word"])
                    current_line.append(word_to_add["word"])
                    syllable_target -= word_to_add["numSyllables"]

                current_wordtype = structure_mapping[current_wordtype]["next"]

            haiku_result.append(current_line)

        return " ".join(haiku_result[0]), " ".join(haiku_result[1]), " ".join(haiku_result[2])


def main():
    # Make a list of command line arguments, omitting the [0] element which is the script itself.
    import sys

    args = sys.argv[1:]
    starts_with = ""

    if not args:
        print("usage: <keyword>")
        sys.exit(1)

    keyword = args[0]
    if len(args) > 1:
        starts_with = args[1]

    pg = HaikuGenerator(word=keyword, starts_with=starts_with)

    print(pg.build_haiku())

    # # very basic tests
    # assert isinstance(result, str)
    # result_as_list = json.loads(result)
    # assert isinstance(result_as_list, list)
    # assert isinstance(result_as_list[0], dict)
    # assert len(result_as_list) == n


if __name__ == "__main__":
    main()
