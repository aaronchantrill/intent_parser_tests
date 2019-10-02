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
from pprint import pprint


def weight(count, examples):
    weight = 0
    if count == examples:
        weight = 1
    elif count < examples:
        weight = .5
    return weight


def makeindex(num):
    char = []
    while num>0:
        char.insert(0, chr(97 + (num % 26)))
        num = num // 26
    return "".join(char)


class Brain(object):
    intent_map = {'intents': {}}
    keywords = {}
    keyword_index = 0
    words = {}
    trained = False
    tokenizer = EnglishTokenizer()
    trie = Trie()
    tagger = EntityTagger(trie, tokenizer)
    parser = Parser(tokenizer, tagger)
    engine = IntentDeterminationEngine()

    def add_word(self, intent, word):
        # Check if this is a collection
        if word[:1]+word[-1:]=="{}":
            keyword_name = "{}_{}".format(intent,word[1:][:-1])
            # print("Registering words for '{}'".format(keyword_name))
            # This doesn't have to exist:
            if keyword_name in self.keywords:
                for keyword_word in self.keywords[keyword_name]['words']:
                    # print("Registering '{}'".format(keyword_word))
                    self.engine.register_entity(keyword_word, keyword_name)
        else:
            # Just register the word as a required word
            self.keyword_index+=1
            keyword_name = "{}_{}".format(intent, makeindex(self.keyword_index))
            # print("Registering word '{}' as {}".format(word,keyword_name))
            self.engine.register_entity(word, keyword_name)
        return keyword_name

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
            if('keywords' in intents[intent_base]):
                for keyword in intents[intent_base]['keywords']:
                    keyword_token = "{}_{}".format(intent,keyword)
                    self.keywords[keyword_token]={
                        'words': intents[intent_base]['keywords'][keyword],
                        'name': keyword
                    }
            self.intent_map['intents'][intent] = {
                'action': intents[intent_base]['action'],
                'words': {},
                'templates': []
            }
            for phrase in intents[intent_base]['templates']:
                # Save the phrase so we can search for undefined keywords
                self.intent_map['intents'][intent]['templates'].append(phrase)
                # Make a count of word frequency. The fact that small connector
                # type words sometimes appear multiple times in a single
                # sentence while the focal words usually only appear once is
                # giving too much weight to those connector words.
                words = list(set(phrase.split()))
                for word in words:
                    # Count the number of times the word ap
                    try:
                        self.intent_map['intents'][intent]['words'][word]['count'] += 1
                    except KeyError:
                        self.intent_map['intents'][intent]['words'][word] = {'count': 1, 'weight': None, 'required': False}
                    # A
                    try:
                        self.words[word].update({intent: True})
                    except KeyError:
                        self.words[word]={intent: True}
            # for each word in each intent, divide the word frequency by the number of examples.
            # Since a word is only counted once per example, regardless of how many times it appears,
            # if the number of times it was counted matches the number of examples, then
            # this is a "required" word.
            phrase_count = len(intents[intent]['templates'])
            for word in self.intent_map['intents'][intent]['words']:
                # print("Word: '{}' Count: {} Phrases: {} Weight: {}".format(word, self.intent_map['intents'][intent]['words'][word], phrase_count, weight(self.intent_map['intents'][intent]['words'][word], phrase_count)))
                Weight = weight(self.intent_map['intents'][intent]['words'][word]['count'], phrase_count)
                self.intent_map['intents'][intent]['words'][word]['weight'] = Weight
                if Weight == 1:
                    self.intent_map['intents'][intent]['words'][word]['required'] = True

    # Call train after loading all the intents.
    def train(self):
        # print("Words:")
        # pprint(self.words)
        # print("")
        # print("Intents:")
        # pprint(self.intent_map['intents'])
        # print("Keywords:")
        # pprint(self.keywords)
        for intent in self.intent_map['intents']:
            required_words = []
            optional_words = []
            print("Training {}".format(intent))
            # pprint(self.keywords)
            for word in self.intent_map['intents'][intent]['words']:
                weight = self.intent_map['intents'][intent]['words'][word]
                intents_count = len(self.intent_map['intents'])
                word_appears_in = len(self.words[word])
                # print("Word: {} Weight: {} Intents: {} Appears in: {}".format(word, weight, intents_count, word_appears_in))
                self.intent_map['intents'][intent]['words'][word]['weight'] = self.intent_map['intents'][intent]['words'][word]['weight']*(intents_count - word_appears_in) / intents_count
                if(self.intent_map['intents'][intent]['words'][word]['required']):
                    # add the word as required.
                    print("adding '{}' as required".format(word))
                    required_words.append(self.add_word(intent,word))
                else:
                    # if the word is a keyword list, add it
                    if(word[:1] + word[-1:] == "{}"):
                        optional_words.append(self.add_word(intent,word))
                    else:
                        if(self.intent_map['intents'][intent]['words'][word]['weight'] > 0.35):
                            print("adding '{}' as optional".format(word))
                            optional_words.append(self.add_word(intent,word))
            a=None
            for keyword in required_words:
                if(a):
                    a=a.require(keyword)
                else:
                    a=IntentBuilder(intent).require(keyword)
            for keyword in optional_words:
                if(a):
                    a=a.optionally(keyword)
                else:
                    a=IntentBuilder(intent).optionally(keyword)
            if(a):
                print("Building {}".format(intent))
                self.engine.register_intent_parser(a.build())
        
        # pprint(self.intent_map['intents'])
        print("")
        self.trained = True

    def determine_intent(self, phrase):
        response = {}
        try:
            for intent in self.engine.determine_intent(phrase):
                if intent and intent.get("confidence")>0:
                    keywords = {}
                    for keyword in intent:
                        if keyword not in ['confidence','intent_type','target']:
                            if keyword in self.keywords:
                                # Since the Naomi parser can return a list of matching words,
                                # this needs to be a list
                                keywords[self.keywords[keyword]['name']] = [intent[keyword]]
                    response.update(
                        {
                            intent['intent_type']: {
                                'action': self.intent_map['intents'][intent['intent_type']]['action'],
                                'input': phrase,
                                'matches': keywords,
                                'score': intent['confidence']
                            }
                        }
                    )
        except ZeroDivisionError:
            print("Could not determine an intent")
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
