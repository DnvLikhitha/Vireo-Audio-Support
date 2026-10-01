import pandas as pd

tickets = pd.read_csv('data/tickets.csv')

# Check combinations that give ~40 tickets
# 1. Voice channel with short or audio artifacts
c1 = (tickets['channel'] == 'voice') & (tickets['customer_message'].str.contains(r'\[inaudible\]|\[crosstalk\]|\[line dropped\]', regex=True, case=False))
print('Audio bracket artifacts in voice:', c1.sum())

# 2. Voice channel customer message len <= 35
c2 = (tickets['channel'] == 'voice') & (tickets['customer_message'].str.len() <= 35)
print('Voice customer message len <= 35:', c2.sum())

# 3. Customer message contains bracket artifacts or punctuation only or test across all channels
c3 = tickets['customer_message'].str.contains(r'\[inaudible\]|\[crosstalk\]|\[line dropped\]', regex=True, case=False) | (tickets['customer_message'].str.strip().isin(['.', '-', '??', '...', 'test', 'call me', 'urgent']))
print('Artifacts + uninformative tokens:', c3.sum())

# 4. Check IVR transcript with length < 40 or bracket artifacts:
ivr = tickets['customer_message'].str.startswith('[IVR transcript]', na=False)
c4 = ivr & (tickets['customer_message'].str.contains(r'\[inaudible\]|\[crosstalk\]|\[line dropped\]', regex=True, case=False) | (tickets['customer_message'].str.len() <= 45))
print('IVR transcript bracket artifacts or len <= 45:', c4.sum())

c5 = (tickets['channel'] == 'voice') & (tickets['customer_message'].str.contains(r'\[inaudible\]|\[crosstalk\]|\[line dropped\]', regex=True, case=False) | (tickets['customer_message'].str.len() <= 40))
print('Voice artifacts or len <= 40:', c5.sum())
