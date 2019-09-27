# intent_parser_tests
Comparison of the Adapt, Padatious and Naomi intent parsers

This repository contains three python3 scripts:
* adapt_test.py
* naomi_test.py
* padatious_test.py

Running the adapt_test.py script requires that you have Adapt installed on your system.
You can install this from PyPI using
`$ pip3 install adapt-parser`

Running the padatious_test.py script requires that you have Padatious installed on your system.
Padatious requires that you have FANN (Fast Artificial Neural Net) installed on your system
You can install FANN in Debian/Raspbian Buster with
`# apt install libfann2`
or just install both the python3 module and C library with
`# apt install python3-fann2`
You can install the python module with
`$ pip3 install fann2`

Running the naomi_test.py script does not require anything other than the standard modules
(it requires re for the parsing, and pprint for the test output)

These scripts demonstrate what I am thinking about as far as writing an intent parser
specifically for Naomi, and also the start of writing plugins to allow a user to
use Adapt or Padatious in place of the Naomi intent parser.
