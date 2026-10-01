import pandas as pd
import numpy as np

tickets = pd.read_csv('data/tickets.csv')

# Let's inspect voice tickets:
voice = tickets[tickets['channel'] == 'voice'].copy()
print(f'Total voice tickets: {len(voice)}')

# Let's see what agent_notes say for voice tickets:
ivr_agent_notes = voice[voice['agent_notes'].str.contains('ivr|transcript|call|audio|garbled|inaudible|junk|phone|empty|blank', case=False, na=False)]
print(f'Voice tickets with transcript/audio/call mentioned in agent_notes: {len(ivr_agent_notes)}')
print(ivr_agent_notes['agent_notes'].value_counts().head(20))

# Let's check across ALL tickets for agent_notes mentioning IVR or failed call:
all_ivr_notes = tickets[tickets['agent_notes'].str.contains('ivr.*fail|failed.*ivr|junk.*ivr|corrupt|unintelligible|dropped call|blank call|silent call', case=False, na=False)]
print(f'Tickets with failed IVR mentioned in agent_notes: {len(all_ivr_notes)}')

# Let's check customer message patterns across all voice tickets
# Let's check customer messages with "[IVR transcript]"
ivr_prefix = tickets[tickets['customer_message'].str.startswith('[IVR transcript]', na=False)]
print(f'Tickets starting with [IVR transcript]: {len(ivr_prefix)}')

# Check for junk: messages that have garbled text, or test, or unintelligible, or very low quality:
# Let's see all unique customer messages in voice channel:
print('\nUnique customer messages in voice channel:', voice['customer_message'].nunique())
# Let's look for repetitive short strings or non-informative transcripts:
vc = voice['customer_message'].value_counts()
print('\nMost frequent customer messages in voice channel:')
print(vc.head(30))

# What about messages where the intake bot categorized as "Other" or "Technical Support"?
print('\nCategory distribution for voice tickets:')
print(voice['category'].value_counts())
