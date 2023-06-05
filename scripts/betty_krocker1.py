#!/usr/bin/env python3

import secrets
import krock32

encoder = krock32.Encoder(checksum=False)
encoder.update(secrets.token_bytes(10))
encoding = encoder.finalize().upper()
print(encoding)
