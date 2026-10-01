import pandas as pd
import re

tickets = pd.read_csv('data/tickets.csv')

# Check all customer messages for junk/test/garbage patterns:
print('Customer messages length describe:')
print(tickets['customer_message'].str.len().describe())

# Check shortest 100 customer messages across the entire dataset:
tickets['msg_len'] = tickets['customer_message'].str.len()
shortest = tickets.sort_values('msg_len').head(60)
print('\nShortest 60 customer messages overall:')
print(shortest[['ticket_id', 'channel', 'category', 'customer_message']].to_string())
