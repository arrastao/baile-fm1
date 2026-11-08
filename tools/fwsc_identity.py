#!/usr/bin/env python3
"""Re-encode only FWSC version markers for M-UPGRADE's 3-digit parser.
The encrypted update image, OTA loader and all inner flash bytes stay identical.
"""
from pathlib import Path
import hashlib,json,re
def identity(data):
 chars=[];ended=False
 for i in range(20):
  marker=data[i*48+47]
  if marker==125:ended=True
  else:
   if ended:raise ValueError('identity after terminator')
   c=(marker-i-1)&255
   if not 32<=c<=126:raise ValueError('bad identity byte')
   chars.append(chr(c))
 return ''.join(chars)
def unwrap(data):
 if len(data)<960:raise ValueError('short FWSC')
 return b''.join(data[i*48:i*48+47] for i in range(20))+data[960:]
def reidentify(data,product):
 if not re.fullmatch(r'FM-1_[0-9]{3}',product):raise ValueError('M-UPGRADE requires 3 digits')
 output=bytearray(data)
 for i in range(20):output[i*48+47]=(ord(product[i])+i+1)&255 if i<len(product) else 125
 assert identity(output)==product
 assert unwrap(output)==unwrap(data)
 return bytes(output)
