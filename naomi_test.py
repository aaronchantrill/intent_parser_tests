#!/usr/bin/env python3
from pprint import pprint
import re


def replacenth(sub, wanted, string, n):
    try:
        where = [m.start() for m in re.finditer(sub, string)][n]
        before = string[:where]
        after = string[where:]
        after = after.replace(sub, wanted, 1)
        # print("Before: {} After: {}".format(before,after))
        string = before + after
    except IndexError:
        pass
    return string


class Brain(object):
    intent_map = {}
    keywords = {}
    def add_intent(self, keywords, intents):
        self.keywords.update(keywords)
        for intent in intents:
            # this prevents collisions between intents
            intent_base = intent
            intent_inc = 0
            while intent in self.intent_map:
                intent_inc += 1
                intent = "{}{}".format(intent_base, intent_inc)
            self.intent_map[intent] = {
                'action': intents[intent]['action'],
                'words': {}
            }
            for phrase in intents[intent]['templates']:
                for word in phrase.split():
                    try:
                        self.intent_map[intent]['words'][word] += 1
                    except KeyError:
                        self.intent_map[intent]['words'][word] = 1
        # for each word in each intent, divide the word frequency by the number of examples
        for intent in intents:
            phrase_count = len(intents[intent]['templates'])
            for word in self.intent_map[intent]['words']:
                self.intent_map[intent]['words'][word]/=phrase_count

    def determine_intent(self, phrase):
        # print(phrase)
        score = {}
        variants = {phrase: {}}
        for keyword in self.keywords:
            for word in self.keywords[keyword]:
                count=0  # count is the index of the match we are looking for
                countadded=0  # keep track of variants added for this count
                while True:
                    added = 0 # if we get throut all the variants without adding any new variants, then increase the count.
                    for variant in variants:
                        #print("Count: {} Added: {} CountAdded: {}".format(count, added, countadded))
                        #print()
                        #print("word: '{}' variant: '{}'".format(word,variant))
                        subs = dict(variants[variant])
                        new = replacenth(word, '{'+keyword+'}', variant, count)
                        #print(new)
                        if new not in variants:
                            try:
                                subs[keyword].append(word)
                            except KeyError:
                                subs[keyword] = [word]
                            # print(subs[keyword])
                            # print()
                            variants[new]=subs
                            # pprint(variants)
                            added += 1
                            countadded += 1
                            # start looping over variants again
                            break
                    if added == 0:
                        if countadded == 0:
                            break
                        else:
                            count+=1
                            countadded=0
        # Now calculate a total score for each variant
        variantscores = {}
        for variant in variants:
            variantscores[variant]={}
            words = variant.split()
            intentscores={}
            for intent in self.intent_map:
                score = 0
                for word in words:
                    if word in self.intent_map[intent]['words']:
                        score += self.intent_map[intent]['words'][word]
                intentscores[intent] = score / len(words)
            # Take the intent with the highest score
            # pprint(intentscores)
            best = max(intentscores, key=lambda key:intentscores[key])
            variantscores[variant]={
                'intent': best, 
                'input': phrase, 
                'template': variant, 
                'score': intentscores[best], 
                'matches': variants[variant],
                'action': self.intent_map[best]['action']
            }
        # pprint(variantscores)
        # now take the best score out of scores
        best = max(variantscores, key=lambda key:variantscores[key]['score'])
        return variantscores[best]
        #print(best)
        #pprint(variantscores[best])
        #print("")
        # score = {best: variantscores[best]
        

if __name__ == "__main__":
    brain = Brain()
    brain.add_intent(
        {},
        {
            'HelloIntent': {
                'templates': [
                    "hi",
                    "hello"
                ],
                'action': lambda: print("HelloIntent")
            }
        }
    )
    brain.add_intent(
        {},
        {
            'GoodbyeIntent': {
                'templates': [
                    "so long",
                    "see you later",
                    "goodbye",
                    "bye"
                ],
                'action': lambda: print("GoodbyeIntent")
            }
        }
    )
    brain.add_intent(
        {
            'EngineKeyword': [
                "google",
                "youtube",
                "instagram"
            ]
        },
        {
            'SearchIntent': {
                'templates': [
                    'search for {Query} using {EngineKeyword}',
                    'search for {Query} on {EngineKeyword}',
                    'search {EngineKeyword} for {Query}'
                ],
                'action': lambda: print("SearchIntent")
            }
        }
    )
    brain.add_intent(
        {
            'TeamKeyword': [
                'seahawks',
                'bengals'
            ]
        },
        {
            'GameIntent': {
                'templates': [
                    'is there a game {DayKeyword}',
                    'is there a game on {DayKeyword}',
                    'will the {TeamKeyword} play the {TeamKeyword} {DayKeyword}',
                    'will the {TeamKeyword} play {DayKeyword}'
                ],
                'action': lambda: print("GameIntent")
            }
        }
    )
    brain.add_intent(
        {
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
                'sleet'
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
        {
            'WeatherIntent': {
                'templates': [
                    "what's the weather in {LocationKeyword}",
                    "is it {WeatherTypePresentKeyword} in {LocationKeyword}",
                    "will it {WeatherTypeFutureKeyword} this {TimeKeyword}",
                    "will it {WeatherTypeFutureKeyword} {DayKeyword}",
                    "will it {WeatherTypeFutureKeyword} {DayKeyword} {TimeKeyword}"
                ],
                'action': lambda: print("WeatherIntent")
            }
        }
    )
    brain.add_intent(
        {
            'ArtistKeyword': [
                'third eye blind',
                'the who',
                'the clash'
            ]
        },
        {
            'MusicIntent':{
                'templates': [
                    "play music by {ArtistKeyword}",
                    "play something by {ArtistKeyword}",
                    "play a song by {ArtistKeyword}",
                    "play music"
                ],
                'action': lambda: print("MusicIntent")
            }
        }
    )
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
        intent = brain.determine_intent(phrase)
        print(phrase)
        pprint(intent)
        intent['action']()
        print()
