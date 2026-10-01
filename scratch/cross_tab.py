import pandas as pd
import numpy as np

# Load test predictions
import sys
sys.path.append('scratch')
from test_classifier import clean_tickets

print('=== COMPARISON: INTAKE BOT CATEGORY vs PREDICTED THEME ===')
ct = pd.crosstab(clean_tickets['category'], clean_tickets['predicted_theme'], margins=True)
print(ct.to_string())

print('\n=== WHERE BOT TAG DISAGREES ===')
# How often does bot category disagree with predicted theme?
# For example, what did the bot tag for tickets classified as one_earbud_dead_or_not_charging?
earbud_tickets = clean_tickets[clean_tickets['predicted_theme'] == 'one_earbud_dead_or_not_charging']
print('\nBot category for tickets classified as "one_earbud_dead_or_not_charging":')
print(earbud_tickets['category'].value_counts())

# What about battery drain?
battery_tickets = clean_tickets[clean_tickets['predicted_theme'] == 'battery_drain']
print('\nBot category for tickets classified as "battery_drain":')
print(battery_tickets['category'].value_counts())

# What was inside bot category "Charging & Battery"?
charging_cat = clean_tickets[clean_tickets['category'] == 'Charging & Battery']
print('\nPredicted themes for bot category "Charging & Battery":')
print(charging_cat['predicted_theme'].value_counts())

# What was inside bot category "Other"?
other_cat = clean_tickets[clean_tickets['category'] == 'Other']
print('\nPredicted themes for bot category "Other":')
print(other_cat['predicted_theme'].value_counts())
