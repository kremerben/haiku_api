import random

# from botocore.vendored import requests
import requests
import time
import json


DATAMUSE_APIBASE = "https://api.datamuse.com/words?md=sp&sp=s*"
DATAMUSE_APIBASE = "https://api.datamuse.com/words?md=sp"
# DATAMUSE_LIMIT_ARG = "&max={}"
DATAMUSE_STARTSWITH_ARG = "&sp={}*"
LINE_SPACE = "\n"


def respond(err, res=None):
    print(res)
    return {
        "statusCode": 400 if err else 200,
        "body": err.message if err else json.dumps(res),
        "headers": {"Content-Type": "application/json"},
    }


def lambda_handler(event, context):
    qs_params = event["queryStringParameters"]
    if "keyword" not in qs_params:
        return respond(
            None,
            "Please add a keyword parameter ex: https://haiku.kremer.dev/?keyword=potato "
            "- starts_with parameter is optional ex: https://haiku.kremer.dev/?keyword=potato&starts_with=v",
        )
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
    def __init__(self, word: str = "", starts_with: str = ""):
        self.word = word
        self.starts_with = starts_with

        self.nouns = []
        self.verbs = []
        self.adjectives = []
        self.adverbs = []
        self.associated_words = []
        self.synonyms = []
        self.kindof_words = []
        self.preceding_words = []
        self.following_words = []

        self.all_verbs = []
        self.all_nouns = []
        self.all_adverbs = []
        self.all_adjectives = []

        self.prime_word_lists(self.word)

    def prime_word_lists(self, word):
        start_time = time.time()
        self.get_nouns(word)
        self.get_verbs(word)
        self.get_adjectives(word)
        #         self.get_adverbs(word)
        # print('time0001:: ', time.time() - start_time)
        self.get_associated_words(word)
        self.get_synonyms(word)
        self.get_kindof_words(word)
        self.get_preceding_words(word)
        self.get_following_words(word)
        # print('time0002:: ', time.time() - start_time)

        self.get_all_nouns(word)
        self.get_all_verbs(word)
        self.get_all_adjectives(word)
        # print('time0003:: ', time.time() - start_time)

    def request_words(self, url, starts_with: str = "") -> list:
        """
            Simple request generator with limit
            :param url: request url
            :param limit: number of values to return, 0 for no limit
            Return:
                [{'word': 'level', 'score': 31451, 'numSyllables': 2},
                 {'word': 'water', 'score': 16450, 'numSyllables': 2}]
        """
        if starts_with:
            url += DATAMUSE_STARTSWITH_ARG.format(starts_with)
        elif self.starts_with:
            url += DATAMUSE_STARTSWITH_ARG.format(self.starts_with)

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
        self.nouns = self.request_words(f"{DATAMUSE_APIBASE}&rel_jja={word}")
        return self.nouns

    def get_verbs(self, word: str) -> list:
        related_words = self.get_related_words(word)
        self.verbs = [word for word in related_words if "tags" in word and "v" in word["tags"]]
        return self.verbs

    def get_adjectives(self, word: str) -> list:
        self.adjectives = self.request_words(f"{DATAMUSE_APIBASE}&rel_jjb={word}")
        return self.adjectives

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

    def get_all_nouns(self, word: str = "") -> list:
        word = word if word else self.word
        nouns = self.nouns
        nouns.extend(self.synonyms)
        nouns.extend(self.associated_words)
        nouns.extend(self.kindof_words)
        nouns.extend(self.preceding_words)
        nouns.extend(self.following_words)
        nouns = [word for word in nouns if "tags" in word and "n" in word["tags"]]
        self.all_nouns = list({noun["word"]: noun for noun in nouns}.values())
        return self.all_nouns

    def get_all_verbs(self, word: str = "") -> list:
        word = word if word else self.word
        verbs = self.verbs
        verbs.extend(self.synonyms)
        verbs.extend(self.associated_words)
        verbs.extend(self.kindof_words)
        verbs.extend(self.preceding_words)
        verbs.extend(self.following_words)
        verbs = [word for word in verbs if "tags" in word and "v" in word["tags"]]
        self.all_verbs = list({verb["word"]: verb for verb in verbs}.values())
        return self.all_verbs

    def get_all_adjectives(self, word: str = "") -> list:
        word = word if word else self.word
        adjectives = self.adjectives
        adjectives.extend(self.synonyms)
        adjectives.extend(self.associated_words)
        adjectives.extend(self.kindof_words)
        adjectives.extend(self.preceding_words)
        adjectives.extend(self.following_words)
        adjectives = [word for word in adjectives if "tags" in word and "adj" in word["tags"]]
        self.all_adjectives = list(
            {adjective["word"]: adjective for adjective in adjectives}.values()
        )
        return self.all_adjectives


#     def get_all_adverbs(self, word: str="") -> list:
#         word = word if word else self.word
#         verbs = self.verbs
#         verbs.extend(self.associated_words)
#         verbs.extend(self.kindof_words)
#         verbs.extend(self.preceding_words)
#         verbs.extend(self.following_words)
#         verbs = [word for word in verbs if "tags" in word and "v" in word["tags"]]
#         self.all_verbs = list({verb["word"]:verb for verb in verbs}.values())
#         return self.all_verbs


#     def get_all_nouns(self, word: str="") -> list:
#         word = word if word else self.word
#         nouns = self.get_nouns(word)
#         nouns.extend([word for word in self.get_associated_words(word) if "tags" in word and "n" in word["tags"]])
#         nouns.extend([word for word in self.get_synonyms(word) if "tags" in word and "n" in word["tags"]])
#         nouns.extend([word for word in self.get_kindof_words(word) if "tags" in word and "n" in word["tags"]])
#         nouns.extend([word for word in self.get_preceding_words(word) if "tags" in word and "n" in word["tags"]])
#         nouns.extend([word for word in self.get_following_words(word) if "tags" in word and "n" in word["tags"]])
#         return list({noun["word"]:noun for noun in nouns}.values())


class HaikuGenerator(PoemGenerator):
    def build_haiku(self, word=None) -> list:

        if not word:
            word = self.word

        haiku_syllables = [5, 7, 5]
        haiku_result = []

        current_wordtype = random.choice(["adj", "n", "v"])

        prevWord = ""

        #         nouns = self.all_nouns
        #         verbs = self.get_verbs(word)
        #         adjectives = self.get_adjectives(word)

        #         structure_mapping = {
        #             "noun": {"next": ["verb"]},
        #             "verb": {"next": ["noun", "adjective", "adverb"]},
        #             "adjective": {"next": ["noun"]},
        #             "adverb": {"next": ["verb", "adjective", "adverb"]},
        #         }

        structure_mapping = {
            # removed adverbs for now
            "n": {"next": "v", "wordlist": self.get_all_nouns(word)},
            "v": {"next": "adj", "wordlist": self.get_all_verbs(word)},
            "adj": {"next": "n", "wordlist": self.get_adjectives(word)},
            #             "adverb": {"next": random.choice(["verb", "adjective"]),
            #                     "wordlist": get_all_adverbs(word)},
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
                #                 current_words = structure_mapping[current_wordtype]["wordlist"]
                word_to_add = random.choice(current_words) if current_words else None

                if word_to_add and word_to_add["word"] in used_words and error_count < 10:
                    # no duplicates please
                    continue

                elif word_to_add:
                    used_words.append(word_to_add["word"])
                    #                     current_line.append(word_to_add["word"]+":"+current_wordtype)
                    current_line.append(word_to_add["word"])
                    syllable_target -= word_to_add["numSyllables"]

                current_wordtype = structure_mapping[current_wordtype]["next"]

                # print(current_line)
            haiku_result.append(current_line)

        #     print(haiku_result)
        # print(haiku_result)

        return " ".join(haiku_result[0]), " ".join(haiku_result[1]), " ".join(haiku_result[2])


def main():
    # This command-line parsing code is provided.
    # Make a list of command line arguments, omitting the [0] element
    # which is the script itself.
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

    # pg.get_preceding_words("carrot")

    print(pg.build_haiku())

    # n = int(sys.stdin.readline())
    # for line in sys.stdin:
    #     db.ingest_boms(line)

    # result = db.to_json(n)
    # sys.stdout.write(result)

    # # very basic tests
    # assert isinstance(result, str)
    # result_as_list = json.loads(result)
    # assert isinstance(result_as_list, list)
    # assert isinstance(result_as_list[0], dict)
    # assert len(result_as_list) == n


if __name__ == "__main__":
    main()
