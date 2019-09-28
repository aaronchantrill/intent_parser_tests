#!/usr/bin/env python3
import re
from jiwer import wer
from pprint import pprint


# Replace the nth occurrance of sub
# based on an answer by aleskva at 
# https://stackoverflow.com/questions/35091557/replace-nth-occurrence-of-substring-in-string
def replacenth(search_for, replace_with, string, n):
    try:
        where = [m.start() for m in re.finditer(search_for, string)][n]
        before = string[:where]
        after = string[where:]
        after = after.replace(search_for, replace_with, 1)
        string = before + after
    except IndexError:
        pass
    return string


class Brain(object):
    intent_map = {'intents': {}}
    keywords = {}
    words = {}
    def add_intent(self, intents):
        for intent in intents:
            # this prevents collisions between intents
            intent_base = intent
            intent_inc = 0
            while intent in self.intent_map['intents']:
                intent_inc += 1
                intent = "{}{}".format(intent_base, intent_inc)
            if('keywords' in intents[intent]):
                try:
                    self.keywords[intent].update(intents[intent]['keywords'])
                except KeyError:
                    self.keywords[intent]=intents[intent]['keywords']
            self.intent_map['intents'][intent] = {
                'action': intents[intent]['action'],
                'words': {},
                'templates': []
            }
            for phrase in intents[intent]['templates']:
                # Save the phrase so we can search for undefined keywords
                self.intent_map['intents'][intent]['templates'].append(phrase)
                for word in phrase.split():
                    try:
                        self.intent_map['intents'][intent]['words'][word] += 1
                    except KeyError:
                        self.intent_map['intents'][intent]['words'][word] = 1
                    # keep a list of the intents a word appears in
                    try:
                        self.words[word].update({intent: True})
                    except KeyError:
                        self.words[word]={intent: True}
        # for each word in each intent, divide the word frequency by the number of examples
        for intent in intents:
            phrase_count = len(intents[intent]['templates'])
            for word in self.intent_map['intents'][intent]['words']:
                self.intent_map['intents'][intent]['words'][word]/=phrase_count

    def determine_intent(self, phrase):
        # print(phrase)
        score = {}
        allvariants = {phrase: {}}
        for intent in self.keywords:
            variants = {phrase: {}}
            for keyword in self.keywords[intent]:
                for word in self.keywords[intent][keyword]:
                    count=0  # count is the index of the match we are looking for
                    countadded=0  # keep track of variants added for this count
                    while True:
                        added = 0 # if we get through all the variants without adding any new variants, then increase the count.
                        for variant in variants:
                            #print("Count: {} Added: {} CountAdded: {}".format(count, added, countadded))
                            #print()
                            #print("word: '{}' variant: '{}'".format(word,variant))
                            # subs is a list of substitutions
                            subs = dict(variants[variant])
                            # check and see if we can make a substitution and
                            # generate a new variant.
                            new = replacenth(word, '{'+keyword+'}', variant, count)
                            #print(new)
                            if new not in variants:
                                #print(new)
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
                        # check if we were able to loop over all the variants
                        # without creating any new ones
                        if added == 0:
                            if countadded == 0:
                                break
                            else:
                                count+=1
                                countadded=0
            allvariants.update(variants)
        # Now calculate a total score for each variant
        variantscores = {}
        for variant in allvariants:
            # print("************VARIANT**************")
            # print(variant)
            variantscores[variant]={}
            words = variant.split()
            intentscores={}
            for intent in self.intent_map['intents']:
                score = 0
                for word in words:
                    if word in self.intent_map['intents'][intent]['words']:
                        weight = self.intent_map['intents'][intent]['words'][word]
                        intents_count = len(self.intent_map['intents'])
                        word_appears_in = len(self.words[word])
                        # print("Word: {} Weight: {} Intents: {} Appears in: {}".format(word, weight, intents_count, word_appears_in))
                        score += self.intent_map['intents'][intent]['words'][word]*(intents_count-word_appears_in)/intents_count
                intentscores[intent] = score / len(words)
            # Take the intent with the highest score
            # print("==========intentscores============")
            # pprint(intentscores)
            bestintent = max(intentscores, key=lambda key:intentscores[key])
            variantscores[variant]={
                'intent': bestintent, 
                'input': phrase, 
                'variant': variant,
                'score': intentscores[bestintent],
                'matches': allvariants[variant],
                'action': self.intent_map['intents'][bestintent]['action']
            }
        bestvariant = max(variantscores, key=lambda key:variantscores[key]['score'])
        # print("BEST: {}".format(bestvariant))
        # find the template with the smallest levenshtein distance
        templates={}
        for template in brain.intent_map['intents'][bestintent]['templates']:
            templates[template]=wer(template,variant)
            # print("distance from '{}' to '{}' is {}".format(variant,template,templates[template]))
        besttemplate = min(templates, key=lambda key:templates[key])
        # The next thing we have to do is match up all the substitutions
        # that have been made between the template and the current variant
        # This is so that if there are multiple match indicators we can eliminate
        # the ones that have matched.
        # Consider the following:
        #   Team: ['bengals','patriots']
        #   Template: will the {Team} play the {Team} {Day}
        #   Input: will done browns play the bengals today
        #   Input with matches: will done browns play the {Team} {Day}
        #   Matches: {Team: bengals, Day: today}
        # Obviously there is a very low Levenshtein distance between the template
        # and the input with matches, but it's not that easy to figure out which
        # Team in the template has been matched. So loop through the matches and
        # words and match the word with each possible location in the template
        # and take the best as the new template.
        #   Template1: will the bengals play the {Team} {Day}
        #   input: will done browns play the bengals {Day}
        #   distance: .42
        #
        #   Template2: will the {Team} play the bengals {Day}
        #   input: will done browns play the bengals {Day}
        #   distance: .28
        #
        # since we are looking for the smallest distance, Template2 is obviously
        # a better choice.
        # print("Best variant: {}".format(bestvariant))
        # print("Best template: {}".format(besttemplate))
        currentvariant = bestvariant
        currenttemplate = besttemplate
        for matchlist in variantscores[bestvariant]['matches']:
            for word in variantscores[bestvariant]['matches'][matchlist]:
                # Substitute word into the variant (we know this matches the first
                # occurrance of {matchlist})
                # print("Matchlist: {} Word: {}".format(matchlist, word))
                currentvariant = bestvariant.replace('{'+matchlist+'}', word, 1)
                # print("Bestvariant with substitutions: {}".format(currentvariant))
                templates = {}
                # Get a count of the number of matches for the current matchlist in template
                possiblesubstitutions = currenttemplate.count('{'+matchlist+'}')
                # We don't actually know if there are actually any substitutions in the template
                if(possiblesubstitutions>0):
                    for i in range(possiblesubstitutions):
                        currenttemplate=replacenth('{'+matchlist+'}', word, currenttemplate, i)
                        templates[currenttemplate]=wer(currentvariant,currenttemplate)
                    currenttemplate = min(templates, key=lambda key: templates[key])
                    # print(currenttemplate)
                # print("{}: {}".format(word,currenttemplate))
            # print("{}: {}".format(matchlist,currenttemplate))
        # Now that we have a matching template, run through a list of all
        # substitutions in the template and see if there are any we have not
        # identified yet.
        substitutions = re.findall('\{(.*?)\}',currenttemplate)
        if(substitutions):
            for substitution in substitutions:
                subvar = '{'+substitution+'}'
                # print("Searching for {}".format(subvar))
                # So now we know that we are missing the variable contained in substitution.
                # What we have to do now is figure out where in the string to insert that
                # variable in order to minimize the levenshtein distance between
                # bestvariant and besttemplate
                # print("Minimizing distance from '{}' to '{}' by substituting in '{}'".format(currentvariant,currenttemplate,subvar))
                # print("Variant: {}".format(currentvariant))
                variant=currentvariant.split()
                # print("Template: {}".format(currenttemplate))
                template=currenttemplate.split()
                m=len(variant)+1
                n=len(template)+1
                # Find out which column contains the first instance of substitution
                s=template.index(subvar)+1
                # print("subvar={} s={}".format(subvar,s))
                match=[]
                a=[]
                for i in range(n+1):
                    a.append([0]*(m+1))
                    a[i][0]=i
                    a[i][m]=1
                for j in range(m):
                    a[0][j]=j
                    a[n][j]=1
                for i in range(1,n):
                    for j in range(1,m):
                        if(template[i-1] == variant[j-1]):
                            c=0
                        else:
                            c=1
                        a[i][j]=min(
                            a[i-1][j]+1,
                            a[i][j-1]+1,
                            a[i-1][j-1]+c
                        )
                        a[i][j]=c
                # pprint(a)
                # examine the resulting list of matched words
                # to locate the position of the unmatched keyword
                matched = ""
                for i in range(1,m):
                    # print("s: {} i: {}".format(s,i))
                    if(a[s-1][i-1]==0):
                        # the previous item was a match
                        # so start here and work to the right until there is another match
                        k=i-1
                        start = k
                        compare = [k]
                        compare.extend([1]*m)
                        # print("Comparing {} to {}".format(a[k],compare))
                        while(a[k]==compare):
                            match.append(variant[k])
                            k+=1
                            compare = [k]
                            compare.extend([1]*m)
                            # print("Comparing {} to {}".format(a[k],compare))
                            end = k
                        matched = " ".join(match)
                        # print("Variant:")
                        # pprint(variant)
                        # print("Start: {} End: {}".format(start,end))
                        substitutedvariant = variant[:start]
                        substitutedvariant.append('{'+substitution+'}')
                        substitutedvariant.extend(variant[end:])
                        # print("SubstitutedVariant: {}".format(substitutedvariant))
                    elif(a[s+1][i+1]==0):
                        # the next item is a match, so start working backward
                        k=i
                        end = k
                        compare = [k]
                        compare.extend([1]*m)
                        # print("Comparing {} to {}".format(a[k],compare))
                        while(a[k]==compare):
                            match.append(variant[k-1])
                            k-=1
                            compare = [k]
                            compare.extend([1]*m)
                            # print("Comparing {} to {}".format(a[k],compare))
                            start = k
                        matched = " ".join(reversed(match))
                        # print("Variant:")
                        # pprint(variant)
                        # print("Start: {} End: {}".format(start,end))
                        substitutedvariant = variant[:start]
                        substitutedvariant.append('{'+substitution+'}')
                        substitutedvariant.extend(variant[end:])
                        # print("SubstitutedVariant: {}".format(substitutedvariant))
                if(len(matched)):
                    # print("Match: '{}' to '{}'".format(substitution, matched))
                    try:
                        variantscores[bestvariant]['matches'][substitution].append(matched)
                    except KeyError:
                        variantscores[bestvariant]['matches'][substitution]=[matched]
        variantscores[bestvariant]['template']=besttemplate
        return variantscores[bestvariant]
        

if __name__ == "__main__":
    brain = Brain()
    brain.add_intent(
        {
            'HelloIntent': {
                'templates': [
                    "hi",
                    "hello"
                ],
                'action': lambda intent: print("{} : HelloIntent".format(intent['input']))
            }
        }
    )
    brain.add_intent(
        {
            'GoodbyeIntent': {
                'templates': [
                    "so long",
                    "see you later",
                    "goodbye",
                    "bye"
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
                'action': lambda intent: print("{} : SearchIntent".format(intent['input']))
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
                'templates': [
                    "what's the weather in {LocationKeyword}",
                    "what's the forecast for {DayKeyword}",
                    "what's the forecast for {LocationKeyword}",
                    "what's the forecast for {LocationKeyword} on {DayKeyword}",
                    "what's the forecast for {LocationKeyword} on {DayKeyword} {TimeKeyword}",
                    "is it {WeatherTypePresentKeyword} in {LocationKeyword}",
                    "will it {WeatherTypeFutureKeyword} this {TimeKeyword}",
                    "will it {WeatherTypeFutureKeyword} {DayKeyword}",
                    "will it {WeatherTypeFutureKeyword} {DayKeyword} {TimeKeyword}"
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
    # print("******Intent_map***********")
    # pprint(brain.intent_map['intents']['SearchIntent'])
    # print("******Words****************")
    # pprint(brain.keywords)
    # print("***************************")
    test_phrases = [
        "hello",
        "are the seahawks playing the bengals tomorrow",
        "what's happening tomorrow",
        "please search for cats on youtube",
        "look up cats on google",
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
        print("Phrase: {}".format(phrase))
        intent = brain.determine_intent(phrase)
        # print(phrase)
        # pprint(intent)
        # We can pass a "handle" method with the intent,
        # and call it directly when we get our result.
        # I'm just passing lambda functions above, but
        # you can see how this could be used to pass
        # a method from your plugin to be handled
        intent['action'](intent)
        print()
