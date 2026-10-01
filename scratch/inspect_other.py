import pandas as pd

tickets = pd.read_csv('data/tickets.csv')
other = tickets[tickets['category'] == 'Other'].copy()

print(f'Total tickets tagged Other: {len(other)}')
print('\nSample 25 customer messages tagged Other:')
for i, r in other.sample(25, random_state=42).iterrows():
    print(f"[{r['product_sku']}] Msg: {r['customer_message'][:80]} | Note: {str(r['agent_notes'])[:80]}")
