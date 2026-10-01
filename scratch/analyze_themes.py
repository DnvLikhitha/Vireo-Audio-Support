import pandas as pd
from collections import Counter
import re

tickets = pd.read_csv('data/tickets.csv')

print('=== INTAKE BOT CATEGORIES ===')
print(tickets['category'].value_counts())

# Let's inspect customer messages and agent notes for frequent keywords
def get_tokens(text_series):
    tokens = []
    for text in text_series.dropna():
        words = re.findall(r'[a-zA-Z]{3,}', text.lower())
        tokens.extend(words)
    return Counter(tokens)

cust_words = get_tokens(tickets['customer_message'])
notes_words = get_tokens(tickets['agent_notes'])

print('\nTop 40 customer words:')
print(cust_words.most_common(40))

print('\nTop 40 agent notes words:')
print(notes_words.most_common(40))

# Let's check common phrases in customer messages:
# e.g. "one earbud", "left earbud", "right earbud", "charging case", "not charging", "battery", "drain", "pair", "bluetooth", "refund", "delivered", "tracking", "warranty", "rma", "firmware", "app"
phrases = [
    'left earbud', 'right earbud', 'left bud', 'right bud', 'one earbud', 'one side', 'single side',
    'charging case', 'case dead', 'case not charging', 'case led',
    'not charging', 'won\'t charge', 'taking charge',
    'battery drain', 'battery life', 'backup', 'drain',
    'pairing', 'bluetooth', 'connect', 'cutting out', 'disconnect',
    'delivery', 'delivered', 'tracking', 'courier', 'dispatch', 'pincode', 'wrong product', 'damaged',
    'refund', 'money debited', 'payment', 'double payment', 'price',
    'warranty', 'repair', 'rma', 'inspection',
    'firmware', 'app crash', 'update', 'login', 'otp'
]

print('\nFrequency of key phrases in customer_message:')
for p in phrases:
    c = tickets['customer_message'].str.contains(p, case=False, na=False).sum()
    print(f'  {p:25s}: {c}')
