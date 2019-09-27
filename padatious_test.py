#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from padatious import IntentContainer

container = IntentContainer('intent_cache')
# Hello
container.add_intent('HelloIntent', [
    'hi', 
    'hello.'
])
# Goodbye
container.add_intent('GoodbyeIntent', [
    'see you', 
    'goodbye',
    'bye'
])
# Search
container.add_entity('EngineKeyword', ["google", "youtube", "instagram"])
container.add_intent('SearchIntent', [
    'search for {Query} (using|on) {EngineKeyword}',
    'search {EngineKeyword} for {Query}'
])
# Weather
container.add_entity('WeatherTypePresentKeyword', ['snowing', 'raining', 'windy', 'sleeting', 'sunny'])
container.add_entity('WeatherTypeFutureKeyword', ['snow', 'rain', 'sleet'])
container.add_entity('LocationKeyword', ['seattle', 'san francisco', 'tokyo'])
container.add_entity('TimeKeyword', ["morning", "afternoon", "evening", "night"])
container.add_entity('DayKeyword', ["today", "tomorrow", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"])
container.add_intent('WeatherIntent', [
    "what's the weather in {LocationKeyword}",
    "is it {WeatherTypePresentKeyword} in {LocationKeyword}",
    "will it {WeatherTypeFutureKeyword} this {TimeKeyword}",
    "will it {WeatherTypeFutureKeyword} {DayKeyword}",
    "will it {WeatherTypeFutureKeyword} {DayKeyword} {TimeKeyword}"
])
# Music
container.add_entity('ArtistKeyword', ['third eye blind', 'the who', 'the clash'])
container.add_intent('MusicIntent', [
    "play music by {ArtistKeyword}",
    "play something by {ArtistKeyword}",
    "play a song by {ArtistKeyword}",
    "play music"
    "play {ArtistKeyword}",
])
#container.add_intent('UnknownIntent', ['{Unknown}'])
container.train()

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
    intent = container.calc_intent(phrase)
    print(json.dumps(intent.__dict__,indent=4))
