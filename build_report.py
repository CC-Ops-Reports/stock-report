import json
import os
import re

# Read scan data
with open('daily_scan.json') as f:
    scan = json.load(f)

report_date = scan['report_date']
market_tone = scan.get('market_tone', 'N/A')
key_themes = ', '.join(scan.get('key_themes', []))
sp500 = scan.get('sp500', {})
nasdaq = scan.get('nasdaq', {})
sp500_str = f"{sp500.get('value', 'N/A')} ({sp500.get('change', 'N/A')})"
nasdaq_str = f"{nasdaq.get('value', 'N/A')} ({nasdaq.get('change', 'N/A')})"
nasdaq_note = nasdaq.get('note', '')
if nasdaq_note:
    nasdaq_str += f" — {nasdaq_note}"

# Read batch files
all_stocks = []
for batch_file in ['research_batch1.json', 'research_batch2.json', 'research_batch3.json']:
    if os.path.exists(batch_file):
        with open(batch_file) as f:
            batch = json.load(f)
        if 'error' not in batch and batch.get('stocks'):
            all_stocks.extend(batch['stocks'])

if not all_stocks:
    print('ERROR: No stock data available from any batch')
    exit(1)

# Read stock history
history = {}
if os.path.exists('stock_history.json'):
    with open('stock_history.json') as f:
        history = json.load(f)

# Read old archive from README
old_archive = ''
if os.path.exists('README.md'):
    with open('README.md') as f:
        content = f.read()
    match = re.search(r'## REPORT ARCHIVE\n(.*?)(?=\n---\n\n\*DISCLAIMER)', content, re.DOTALL)
    if match:
        old_archive = match.group(1).strip()

# Determine recurring stocks
def is_recurring(ticker):
    dates = history.get(ticker, [])
    count = len(dates)
    if report_date not in dates:
        count += 1
    return count >= 2

# Update history
for stock in all_stocks:
    ticker = stock['ticker']
    if ticker not in history:
        history[ticker] = []
    if report_date not in history[ticker]:
        history[ticker].append(report_date)

with open('stock_history.json', 'w') as f:
    json.dump(history, f, indent=2)

# Build report
lines = []
lines.append('# DAILY STOCK SENTIMENT REPORT')
lines.append('')
lines.append(f'**DATE:** {report_date}')
lines.append(f'**TOTAL STOCKS TRACKED:** {len(all_stocks)}')
lines.append(f'**MARKET TONE:** {market_tone}')
lines.append(f'**KEY THEMES:** {key_themes}')
lines.append('')
lines.append(f'**S&P 500:** {sp500_str} • **NASDAQ:** {nasdaq_str}')
lines.append('')
lines.append('---')

for stock in all_stocks:
    ticker = stock['ticker']
    company = stock['company']
    star = ' ⭐' if is_recurring(ticker) else ''
    lines.append('')
    lines.append(f'## {company.upper()} ({ticker}){star}')
    lines.append('')
    lines.append(f"**Discussion Driver:** {stock.get('discussion_driver', 'N/A')}")
    lines.append('')
    lines.append('**Bull Case:**')
    for b in stock.get('bull_case', []):
        lines.append(f'- {b}')
    lines.append('')
    lines.append('**Bear Case:**')
    for b in stock.get('bear_case', []):
        lines.append(f'- {b}')
    lines.append('')
    lines.append(f"**Recommendation:** {stock.get('recommendation', 'N/A')}")
    lines.append('')
    lines.append('**Metrics:**')
    lines.append('| Metric | Value |')
    lines.append('|--------|-------| ')
    lines.append(f"| Current Price | {stock.get('current_price', 'N/A')} |")
    lines.append(f"| Price Target | {stock.get('price_target', 'N/A')} |")
    lines.append(f"| P/E Ratio | {stock.get('pe_ratio', 'N/A')} |")
    lines.append(f"| RSI | {stock.get('rsi', 'N/A')} |")
    lines.append(f"| vs 52-Wk High | {stock.get('vs_52wk_high', 'N/A')} |")
    lines.append(f"| Analyst Rating | {stock.get('analyst_rating', 'N/A')} |")
    lines.append(f"| Sector | {stock.get('sector', 'N/A')} |")
    lines.append('')
    sources = ', '.join(stock.get('sources', []))
    lines.append(f'**Sources:** {sources}')
    lines.append('')
    lines.append('---')

# Daily insights
lines.append('')
lines.append('## DAILY INSIGHTS')
lines.append('')

# Determine sectors
buy_sectors = {}
sell_sectors = {}
for s in all_stocks:
    sector = s.get('sector', 'Unknown')
    rec = s.get('recommendation', '').lower()
    if rec in ['buy', 'strong buy', 'speculative buy']:
        buy_sectors[sector] = buy_sectors.get(sector, 0) + 1
    elif rec in ['sell', 'hold']:
        sell_sectors[sector] = sell_sectors.get(sector, 0) + 1

bullish = max(buy_sectors, key=buy_sectors.get) if buy_sectors else 'N/A'
bearish = max(sell_sectors, key=sell_sectors.get) if sell_sectors else 'N/A'

# Most mentioned
most_sources = max(all_stocks, key=lambda s: len(s.get('sources', [])))

lines.append(f'- **Most Bullish Sector:** {bullish}')
lines.append(f'- **Most Bearish Sector:** {bearish}')
lines.append(f"- **Most Mentioned Stock:** {most_sources['ticker']} — appeared in {len(most_sources.get('sources', []))} sources")
lines.append(f'- **Sentiment Shift:** Market tone is {market_tone}')
lines.append('')
lines.append('---')

# Archive
lines.append('')
lines.append('## REPORT ARCHIVE')
lines.append('')

# Today's archive entry
lines.append(f'### {report_date} | {market_tone} | {key_themes}')
lines.append('')
lines.append('| Stock | Rec | Price | Target | vs 52-Wk High |')
lines.append('|-------|-----|-------|--------|---------------|')
for s in all_stocks:
    t = s['ticker']
    star_t = ' ⭐' if is_recurring(t) else ''
    rec = s.get('recommendation', 'N/A')
    if rec == 'Speculative Buy':
        rec = 'Spec. Buy'
    price = s.get('current_price', 'N/A')
    target = s.get('price_target', 'N/A')
    high = s.get('vs_52wk_high', 'N/A')
    lines.append(f'| {t}{star_t} | {rec} | {price} | {target} | {high} |')
lines.append('')

# Old archive
if old_archive:
    lines.append(old_archive)
    lines.append('')

lines.append('---')
lines.append('')
lines.append('*DISCLAIMER: This report is for informational purposes only and does not constitute financial advice. All data sourced from publicly available analyst reports and financial media. Metrics marked N/A were unavailable at time of publication. Always conduct your own research before making investment decisions.*')
lines.append('')
lines.append('*⭐ = Stock has appeared in 2 or more daily reports*')

with open('README.md', 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f'Report built successfully with {len(all_stocks)} stocks')
