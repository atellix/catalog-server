#!/usr/bin/env python3

import sys
sys.path.append('..')

from util import *

webkey = JWKey.generate()

print(webkey.to_custom(private=True))
print(webkey.to_custom(private=False))

