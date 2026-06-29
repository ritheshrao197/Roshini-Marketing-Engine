# Weekly Marketing Analytics & Report Engine
**For: Roshini's Home Products | Platform: Google Antigravity 2.0**

---

## Trigger
**Scheduled Task** — Weekly, every Sunday at 6:00 PM
Set up in Antigravity via: `Schedule → New → Weekly Sunday 6:00 PM`

Paste the following as your scheduled task prompt:
```
Run the Weekly Report Engine for Roshini's Home Products. Read `.antigravity/weekly-report.md` and generate the report.
```

---

## Step 1 — Load Metrics Context
The Analytics Agent reads metrics files placed by the website or manual input under a temporary folder `/metrics/weekly-raw.json`:
- **Instagram:** Top 3 posts by reach/engagement, reel views, comments.
- **Facebook:** Post engagement, comment rates, groups shares.
- **Google Search Console (GSC):** Top 5 ranking blog pages, total impressions, top keywords.
- **WhatsApp:** Click-through rates on broadcasts, number of orders converted.

---

## Step 2 — Analytics Feedback Loop (The AI Learning Layer)
The Analytics Agent runs an evaluation prompt to adjust the daily engine:
1. **Analyze Engagement Patterns:**
   - *Example:* If video reels showing step-by-step cooking are getting 3x more views than ingredient dry-roasting, recommend prioritizing recipe reels.
   - *Example:* If "Working Mother" persona posts convert 40% higher on WhatsApp than "Gym Trainer" posts, suggest increasing the frequency of mother-focused hooks.
2. **Flag Repetitive or Low-Performing Styles:**
   - If posts beginning with "Did you know..." are showing declining engagement, mark it in the history ledger as a "Muted Hook Style".

---

## Step 3 — Output Format
Create a report under `/outputs/weekly-reports/YYYY-W[WeekNumber]-report.md`:

```markdown
# Weekly Performance Report — [Date Range]

## 1. Key Performance Indicators (KPIs)
- **Top Instagram Post:** (Link & visual style used)
- **Top GSC Keywords:** (Search queries that drove traffic)
- **WhatsApp Broadcast Conversions:** (Orders generated / Click rate)

## 2. What Worked (Create More of This)
- List 3 content themes or hooks that drove high conversion.

## 3. What Didn't Work (Avoid Next Week)
- List 2 angles that fell flat or had high bounce rates.

## 4. Updates to Automation Config
- Recommend keywords to add/remove in `sources.md`.
- Recommended topic rotation weights (e.g. increase Millet Monday focus).
```
