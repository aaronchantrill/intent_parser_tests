#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import sys
from adapt.entity_tagger import EntityTagger
from adapt.tools.text.tokenizer import EnglishTokenizer
from adapt.tools.text.trie import Trie
from adapt.intent import IntentBuilder
from adapt.parser import Parser
from adapt.engine import IntentDeterminationEngine

tokenizer = EnglishTokenizer()
trie = Trie()
tagger = EntityTagger(trie, tokenizer)
parser = Parser(tokenizer, tagger)
engine = IntentDeterminationEngine()

# Hello
for word in ['hi', 'hello']:
    engine.register_entity(word, "HelloKeyword")
engine.register_intent_parser(
    IntentBuilder("HelloIntent")
        .require("HelloKeyword")
        .build()
)
# Goodbye
for word in ['see you', 'goodbye', 'bye']:
    engine.register_entity(word, "GoodbyeKeyword")
engine.register_intent_parser(
    IntentBuilder("GoodbyeIntent")
        .require("GoodbyeKeyword")
        .build()
)
# Search
for word in ['search']:
    engine.register_entity(word, "SearchKeyword")
for word in ['google', 'youtube', 'instagram']:
    engine.register_entity(word, "EngineKeyword")
engine.register_regex_entity("for (?P<Query>) on")
engine.register_regex_entity("for (?P<Query>.*)$")
engine.register_intent_parser(
    IntentBuilder("SearchIntent")
        .require("SearchKeyword")
        .require("Query")
        .optionally("EngineKeyword")
        .build()
)
# Game
for word in ['game', 'play', 'playing']:
    engine.register_entity(word, "GameKeyword")
for word in ['seahawks', 'bengals']:
    engine.register_entity(word, "TeamKeyword")
engine.register_intent_parser(
    IntentBuilder("GameIntent")
        .optionally("GameKeyword")
        .optionally("TeamKeyword")
        .optionally("LocationKeyword")
        .optionally("TimeKeyword")
        .build()
)
# Weather
for word in ['weather', 'forecast']:
    engine.register_entity(word, "WeatherKeyword")
for word in ['snowing', 'raining', 'windy',  'sleeting', 'sunny', 'clear']:
    engine.register_entity(word, "WeatherPresentKeyword")
for word in ['snow', 'rain', 'wind', 'sleet']:
    engine.register_entity(word, "WeatherFutureKeyword")
for word in ['seattle', 'san francisco', 'tokyo']:
    engine.register_entity(word, "LocationKeyword")
for word in ['today', 'tomorrow', 'this weekend']:
    engine.register_entity(word, "TimeKeyword")
engine.register_intent_parser(
    IntentBuilder("WeatherIntent")
        .optionally("WeatherKeyword")
        .optionally("WeatherPresentKeyword")
        .optionally("WeatherFutureKeyword")
        .optionally("LocationKeyword")
        .optionally("TimeKeyword")
        .build()
)
# Music
for word in ["listen", "hear", "play"]:
    engine.register_entity(word, "MusicVerb")
for word in ["music", "song"]:
    engine.register_entity(word, "MusicKeyword")
for word in ["third eye blind", "the who", "the clash"]:
    engine.register_entity(word, "ArtistKeyword")
engine.register_intent_parser(
    IntentBuilder("MusicIntent")
        .require("MusicVerb")
        .optionally("MusicKeyword")
        .optionally("ArtistKeyword")
        .build()
)

# Test
test_phrases = [
    "hello",
    "are the seahawks playing the bengals tomorrow",
    "what's happening tomorrow",
    "weather",
    "what's the forecast for today",
    "when will it rain in san francisco",
    "what's the weather like in san francisco today",
    "play some music by the who",
    "play some music",
    "play music",
    "play the who",
    "play third eye blind",
    "see you"
]
for phrase in test_phrases:
    print()
    print(phrase)
    for intent in engine.determine_intent(phrase):
        if intent and intent.get("confidence")>0:
            print(json.dumps(intent,indent=4))
