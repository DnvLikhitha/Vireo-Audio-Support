import pandas as pd
import numpy as np

tickets = pd.read_csv('data/tickets.csv')

# Stratify by category (intake bot category) - completely independent of any model prediction
# 150 tickets across 11 categories
# Let's see category counts:
cat_counts = tickets['category'].value_counts()
print(cat_counts)

# Stratified sampling: proportional allocation with minimum of 6 per category
target_sample_size = 150
proportions = cat_counts / len(tickets)
sample_sizes = (proportions * target_sample_size).round().astype(int)
# Ensure sum is 150 and minimum per category
sample_sizes = sample_sizes.clip(lower=6)
diff = target_sample_size - sample_sizes.sum()
if diff != 0:
    # Adjust largest categories
    for cat in sample_sizes.nlargest(abs(diff)).index:
        sample_sizes[cat] += int(np.sign(diff))

print('Target sample sizes per category:')
print(sample_sizes)
print('Total samples:', sample_sizes.sum())

# Perform sampling with a fixed random seed for reproducibility (seed=42)
sampled_list = []
for cat, size in sample_sizes.items():
    cat_df = tickets[tickets['category'] == cat]
    sampled_cat = cat_df.sample(n=size, random_state=42)
    sampled_list.append(sampled_cat)

sampled_df = pd.concat(sampled_list).sample(frac=1, random_state=42).reset_index(drop=True)
print(f'Final sampled rows: {len(sampled_df)}')

# Prepare columns for the user
output_cols = [
    'ticket_id', 'created_at', 'channel', 'product_sku', 'category',
    'customer_message', 'agent_notes', 'hand_label', 'user_notes'
]

# Ensure hand_label and user_notes are empty
sampled_df['hand_label'] = ''
sampled_df['user_notes'] = ''

print('\nSample rows:')
print(sampled_df[['ticket_id', 'product_sku', 'category', 'hand_label']].head(10))
