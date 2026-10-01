import pandas as pd

tickets = pd.read_csv('data/tickets.csv')

# Let's inspect all voice customer messages by length
voice = tickets[tickets['channel'] == 'voice'].copy()

# Print messages with len < 50 in voice channel:
short_msgs = voice[voice['customer_message'].str.len() < 50][['ticket_id', 'customer_message', 'category', 'agent_notes']]
print(f'Voice messages < 50 chars: {len(short_msgs)}')
print(short_msgs.to_string())

# Also check for junk patterns across all tickets:
# Is there any message with nonsense characters or gibberish?
# Let's check:
for i, r in tickets.iterrows():
    msg = str(r['customer_message'])
    if any(k in msg.lower() for k in ['inaudible', 'crosstalk', 'garbled', 'transcript fail', 'transcription fail', 'static noise', 'line dropped']):
        pass

# Check messages with bracketed text [ ... ]
bracketed = tickets[tickets['customer_message'].str.contains(r'\[.*\]', na=False)]
print(f'Messages containing brackets: {len(bracketed)}')
# Exclude the literal prefix '[IVR transcript]'
non_standard_brackets = bracketed[~bracketed['customer_message'].str.startswith('[IVR transcript]', na=False)]
print(f'Non-[IVR transcript] brackets: {len(non_standard_brackets)}')
print(non_standard_brackets[['ticket_id', 'channel', 'customer_message']].head(20))

# Also inside [IVR transcript], what has brackets inside?
ivr_internal_brackets = bracketed[bracketed['customer_message'].str.replace('[IVR transcript]', '', regex=False).str.contains(r'\[.*\]', regex=True)]
print(f'IVR transcripts with internal brackets: {len(ivr_internal_brackets)}')
print(ivr_internal_brackets[['ticket_id', 'customer_message']])
