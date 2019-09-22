
## HAIKU API V1 WIKI
-------------
This Haiku REST API provides simple access to read data in JSON format via HTTP GET requests over http(s).


### Base URL

https://haiku.kremer.dev


### API Root

Accessing the root of the API, /, without parameters, will return an object describing the usage of the API.

"Please add a keyword parameter ex: https://haiku.kremer.dev/?keyword=potato - starts_with parameter is optional ex: https://haiku.kremer.dev/?keyword=potato&starts_with=f"


### Query Parameters

| Name          | Type                            | Description |
|---------------|---------------------------------|-------------|
| `keyword`     | string (required)               | Keyword that the entire haiku will be built on. |
| `starts_with` | single letter string (optional) | If given, all the words in the haiku will start with that letter. Caveat, depending on the letter given, there may be a lot of word repetition. |

### Response
The Response is a json list object containing the three lines of the generated haiku.

### Examples:

Request: https://haiku.kremer.dev/?keyword=potato

Response:
```json
[
    "russet transgenic",
    "puree fried raw yields sliced grains",
    "has cooked flesh leaves peach"
]
```


Request: https://haiku.kremer.dev/?keyword=potato&starts_with=f

Response:
```json
[
    "farm french-fry frozen",
    "fruits flakes fresh fish fried frozen",
    "fruit forked fried flour"
]
```
