import pandas as pd
import numpy as np
import re

tickets = pd.read_csv('data/tickets.csv')

print('=== 1. IDENTIFY JUNK IVR TRANSCRIPTS (~40 tickets) ===')
# In email-thread.txt:
# "About forty tickets have junk in the customer message (IVR transcripts that failed), that's the phone system, not the agents."
# Let's inspect voice tickets customer messages
voice = tickets[tickets['channel'] == 'voice'].copy()
print(f'Total voice tickets: {len(voice)}')

# Let's look for transcript failure patterns
# Check bracketed audio errors like [inaudible], [crosstalk], [line dropped], [static], [noise], etc.
patterns = [
    r'\[inaudible\]',
    r'\[crosstalk\]',
    r'\[line dropped\]',
    r'\[static\]',
    r'\[noise\]',
    r'\[garbled\]',
    r'\[unintelligible\]',
    r'\[silence\]',
    r'\[audio cut\]',
    r'transcription error',
    r'failed transcript'
]
regex_junk = '|'.join(patterns)
junk_matches = voice[voice['customer_message'].str.contains(regex_junk, case=False, na=False)]
print(f'Bracketed/failure keywords in voice customer messages: {len(junk_matches)}')
print(junk_matches['customer_message'].value_counts())

# What about messages where the transcript failed completely or is just noise?
# Let's check very short voice transcripts or transcripts with specific text
print('\nVoice messages with len < 25:')
short_voice = voice[voice['customer_message'].str.len() < 25]
print(f'Count: {len(short_voice)}')
print(short_voice['customer_message'].value_counts())

# Let's check if there are around 40 tickets with specific junk/failed patterns across all channels or voice:
# Let's look at all voice customer messages:
print('\nSample voice customer messages that look like failed transcripts:')
for msg in voice['customer_message'].dropna().unique():
    if any(p in msg.lower() for p in ['inaudible', 'crosstalk', 'dropped', 'static', 'unintelligible', 'garbled', '...']):
        print(f'  • {msg[:100]}')
