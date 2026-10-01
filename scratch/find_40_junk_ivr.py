import pandas as pd

tickets = pd.read_csv('data/tickets.csv')
ivr = tickets[tickets['customer_message'].str.startswith('[IVR transcript]', na=False)].copy()

# Look at short IVR transcripts:
ivr['clean_text'] = ivr['customer_message'].str.replace('[IVR transcript]', '', regex=False).str.strip()
ivr['word_count'] = ivr['clean_text'].apply(lambda x: len(x.split()))
ivr['char_count'] = ivr['clean_text'].apply(len)

print('Word count distribution of IVR transcripts:')
print(ivr['word_count'].value_counts().sort_index().head(15))

# What messages have word_count <= 8?
short_ivr = ivr[ivr['word_count'] <= 6]
print(f'\nIVR transcripts with <= 6 words: {len(short_ivr)}')
print(short_ivr[['ticket_id', 'clean_text', 'word_count']])

# What about messages where the customer message is very short or repetitive across voice?
# Let's check voice tickets that don't have IVR prefix vs with IVR prefix
voice_all = tickets[tickets['channel'] == 'voice'].copy()
voice_all['char_count'] = voice_all['customer_message'].str.len()
print('\nVoice tickets with char_count < 30:')
print(len(voice_all[voice_all['char_count'] < 30]))
print(voice_all[voice_all['char_count'] < 30]['customer_message'].value_counts())

# What about tickets across all channels with customer_message containing test, blank, or junk?
junk_words = ['[line dropped]', '[inaudible]', '[crosstalk]', 'test', 'call me', 'hello??', 'pls reply']
# Let's inspect tickets where agent notes say customer disconnected or silent call:
silent = tickets[tickets['agent_notes'].str.contains('silent|dropped|disconnected|no response from cx|blank call|hang up|hung up', case=False, na=False)]
print(f'\nAgent notes mentioning silent/disconnected/dropped: {len(silent)}')
print(silent[['ticket_id', 'channel', 'customer_message', 'agent_notes']].head(20))
