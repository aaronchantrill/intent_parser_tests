#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from padatious import IntentContainer
from pprint import pprint


class Brain(object):
    intent_map = {'intents': {}}
    keywords = {}
    keyword_index = 0
    words = {}
    trained = False
    container = IntentContainer('intent_cache')

    def add_intent(self, intent):
        self.add_intents(intent)
        
    def add_intents(self, intents):
        for intent in intents:
            # print("Adding intent {}".format(intent))
            # this prevents collisions between intents
            intent_base = intent
            intent_inc = 0
            while intent in self.intent_map['intents']:
                intent_inc += 1
                intent = "{}{}".format(intent_base, intent_inc)
            self.intent_map['intents'][intent] = {
                'action': intents[intent_base]['action'],
                'name': intent_base,
                'templates': []
            }
            templates = intents[intent_base]['templates']
            if('keywords' in intents[intent_base]):
                for keyword in intents[intent_base]['keywords']:
                    keyword_token = "{}_{}".format(intent,keyword)
                    self.keywords[keyword_token]={
                        'words': intents[intent_base]['keywords'][keyword],
                        'name': keyword
                    }
                    # print("Adding keyword '{}': {}".format(keyword_token,intents[intent_base]['keywords'][keyword]))
                    # map the keywords into the intents
                    templates = [t.replace(keyword,keyword_token) for t in templates]
                    self.container.add_entity(keyword_token, intents[intent_base]['keywords'][keyword])
            self.container.add_intent(intent, templates)
            # pprint({intent: templates})

    # Call train after loading all the intents.
    def train(self):
        print("Training")
        self.container.train()
        self.trained = True

    def determine_intent(self, phrase):
        response = {}
        intent = self.container.calc_intent(phrase)
        # pprint(intent)
        if(intent):
            intent_name = self.intent_map['intents'][intent.name]['name']
            matches = {}
            for match in intent.matches:
                if match in self.keywords:
                    matches.update({self.keywords[match]['name']: [intent[match]]})
                else:
                    matches.update({match: [intent[match]]})
            response = {
                intent.name: {
                    'action': self.intent_map['intents'][intent.name]['action'],
                    'input': phrase,
                    'matches': [{self.keywords[match]['name'] if match in self.keywords else match: [intent[match]]} for match in intent.matches],
                    'score': intent.conf
                }
            }
        return response
        

if __name__ == "__main__":
    brain = Brain()
    brain.add_intent(
        {
            'HelloIntent': {
                'keywords': {
                    'HelloKeyword': [
                        'hi',
                        'hello'
                    ]
                },
                'templates': [
                    '{HelloKeyword}'
                ],
                'action': lambda intent: print("{} : HelloIntent".format(intent['input']))
            }
        }
    )
    brain.add_intent(
        {
            'GoodbyeIntent': {
                'keywords': {
                    'GoodbyeKeyword': [
                        "so long",
                        "farewell",
                        "later",
                        "see you",
                        "goodbye",
                        "bye"
                    ]
                },
                'templates': [
                    '{GoodbyeKeyword}'
                ],
                'action': lambda intent: print("{} : GoodbyeIntent".format(intent['input']))
            }
        }
    )
    brain.add_intent(
        {
            'SearchIntent': {
                'keywords': {
                    'EngineKeyword': [
                        "google",
                        "youtube",
                        "instagram"
                    ]
                },
                'regex': {
                    'Query': [
                        "for (?P<Query>) on",
                        "for (?P<Query>.*)$"
                    ]
                },
                'templates': [
                    'search for {Query} using {EngineKeyword}',
                    'search for {Query} on {EngineKeyword}',
                    'search {EngineKeyword} for {Query}'
                ],
                'action': lambda intent: print("{} : SearchIntent : {}".format(intent['input'],intent['matches']))
            }
        }
    )
    brain.add_intent(
        {
            'GameIntent': {
                'keywords': {
                    'TeamKeyword': [
                        'seahawks',
                        'bengals'
                    ],
                    'LocationKeyword': [
                        'seattle', 
                        'san francisco', 
                        'tokyo'
                    ],
                    'TimeKeyword': [
                        "morning", 
                        "afternoon",
                        "evening",
                        "night"
                    ],
                    'DayKeyword': [
                        "today", 
                        "tomorrow", 
                        "sunday", 
                        "monday", 
                        "tuesday", 
                        "wednesday", 
                        "thursday", 
                        "friday", 
                        "saturday"
                    ]
                },
                'templates': [
                    'is there a game {DayKeyword}',
                    'is there a game on {DayKeyword}',
                    'will the {TeamKeyword} play the {TeamKeyword} {DayKeyword}',
                    'will the {TeamKeyword} play {DayKeyword}',
                    "who's playing {DayKeyword}",
                    "when is the {TeamKeyword} game",
                    "when are the {TeamKeyword} playing"
                ],
                'action': lambda intent: print("{} : GameIntent : {}".format(intent['input'], intent['matches']))
            }
        }
    )
    brain.add_intent(
        {
            'WeatherIntent': {
                'keywords': {
                    'WeatherTypePresentKeyword': [
                        'snowing', 
                        'raining',
                        'windy',
                        'sleeting',
                        'sunny'
                    ],
                    'WeatherTypeFutureKeyword': [
                        'snow', 
                        'rain', 
                        'be windy',
                        'sleet',
                        'be sunny'
                    ],
                    'LocationKeyword': [
                        'seattle', 
                        'san francisco', 
                        'tokyo'
                    ],
                    'TimeKeyword': [
                        "morning", 
                        "afternoon",
                        "evening",
                        "night"
                    ],
                    'DayKeyword': [
                        "today", 
                        "tomorrow", 
                        "sunday", 
                        "monday", 
                        "tuesday", 
                        "wednesday", 
                        "thursday", 
                        "friday", 
                        "saturday"
                    ]
                },
                'templates': [
                    "what's the weather in {LocationKeyword}",
                    "what's the forecast for {DayKeyword}",
                    "what's the forecast for {LocationKeyword}",
                    "what's the forecast for {LocationKeyword} on {DayKeyword}",
                    "what's the forecast for {LocationKeyword} on {DayKeyword} {TimeKeyword}",
                    "is it {WeatherTypePresentKeyword} in {LocationKeyword}",
                    "will it {WeatherTypeFutureKeyword} this {TimeKeyword}",
                    "will it {WeatherTypeFutureKeyword} {DayKeyword}",
                    "will it {WeatherTypeFutureKeyword} {DayKeyword} {TimeKeyword}",
                    "when will it {WeatherTypeFutureKeyword}",
                    "when will is {WeatherTypeFutureKeyword} in {LocationKeyword}"
                ],
                'action': lambda intent: print("{} : WeatherIntent : {}".format(intent['input'], intent['matches']))
            }
        }
    )
    brain.add_intent(
        {
            'MusicIntent': {
                'keywords': {
                    'ArtistKeyword': [
                        'third eye blind',
                        'the who',
                        'the clash'
                    ]
                },
                'regex': {
                    'ArtistKeyword': [
                        "by (?P<ArtistKeyword>.*)$"
                    ]
                },
                'templates': [
                    "play music by {ArtistKeyword}",
                    "play something by {ArtistKeyword}",
                    "play a song by {ArtistKeyword}",
                    "play music"
                ],
                'action': lambda intent: print("{} : MusicIntent : {}".format(intent['input'], intent['matches']))
            }
        }
    )
    brain.train()
    # print("******Intent_map***********")
    # pprint(brain.intent_map['intents']['SearchIntent'])
    # print("******Words****************")
    # pprint(brain.keywords)
    # print("***************************")
    test_phrases = [
        "hello",
        "are the seahawks playing the bengals tomorrow",
        "will the dallas cowboys play the seahawks tomorrow",
        "what's happening tomorrow",
        "please search for cats on youtube",
        "look up cats on google",
        "weather",
        "what's the forecast for today",
        "when will it rain in san francisco",
        "what's the weather like in san francisco today",
        "play some music by the who",
        "play some music by janis joplin",
        "play some music",
        "play music",
        "play the who",
        "play third eye blind",
        "see you"
    ]
    for phrase in test_phrases:
        print("Phrase: {}".format(phrase))
        intent = brain.determine_intent(phrase)
        #intent['action'](intent)
        # print(phrase)
        pprint(intent)
        # We can pass a "handle" method with the intent,
        # and call it directly when we get our result.
        # I'm just passing lambda functions above, but
        # you can see how this could be used to pass
        # a method from your plugin to be handled
        #intent['action'](intent)
        print()
