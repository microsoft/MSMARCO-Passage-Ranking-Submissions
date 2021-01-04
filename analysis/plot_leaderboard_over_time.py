# MS MARCO Passage: Script for plotting leaderboard over time scatter plots

import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
plt.switch_backend('agg')

import pandas as pd

df = pd.read_csv('../leaderboard/leaderboard.csv')
df['date']= pd.to_datetime(df['date'])

# Plot all the runs
ax = df.plot(x='date',y='eval',marker='o',linestyle='none',label='Submission')

# Overlay all the runs that have 'BERT' in their names, in orange
bert = df[df['description'].str.contains('BERT', case=False)]
bert.plot(ax=ax, x='date',y='eval',marker='o',color = 'orange',linestyle='none',label='"BERT" technique')

# Overlay all SOTA runs, in red.
sota = df[df['Unnamed: 0'] == '🏆']
sota.plot(ax=ax, x='date',y='eval',marker='o',color = 'red',linestyle='none',label='SOTA')

ax.set_xlim([datetime.date(2018, 10, 1), datetime.date(2021, 1, 1)])

plt.title('MS MARCO Passage Leaderboard')
plt.xlabel('Date')
plt.ylabel('MRR@10')

plt.savefig('leaderboard.pdf', bbox_inches='tight', format='pdf')

