# Monthly Strategic Marketing Review Engine
**For: Roshini's Home Products | Platform: Google Antigravity 2.0**

---

## Trigger
**Scheduled Task** — Monthly, on the 1st of every month at 9:00 AM
Set up in Antigravity via: `Schedule → New → Monthly 1st 9:00 AM`

Paste the following as your scheduled task prompt:
```
Run the Monthly Strategic Review for Roshini's Home Products. Read `.antigravity/monthly-report.md` and generate the report.
```

---

## Step 1 — Load Monthly Aggregates
The monthly review agent aggregates the last 4 weekly reports and parses the sales invoice sheet / Google Analytics data:
- Total website sessions & conversion rate (%).
- Total packs sold (250g vs 500g).
- Highest-performing promotional campaign (e.g. `EARLYBIRD` vs `FIRST10`).
- Month-on-month search impressions growth.

---

## Step 2 — Competitive Strategy Evaluation
- The agent reviews `/sources.md` competitor websites (Slurrp Farm, Yogabar, Millet Amma) to extract changes in their pricing, new product launches, or packaging shifts.
- Compiles a list of "Opportunities to Differentiate" for Roshini's Home Products (e.g. creating custom diabetic-friendly blends if competitors focus only on kids).

---

## Step 3 — Output Format
Create a report under `/outputs/monthly-reports/YYYY-MM-report.md`:

```markdown
# Monthly Marketing Review — [Month, Year]

## 1. Executive Summary
- Total Sales Generated: ₹[Amount]
- Total Traffic Growth: [Impressions / Sessions % change]
- Best Performing Campaign: [Campaign Code]

## 2. Product Sourcing & Inventory Recommendations
- High-demand pack size: [250g / 500g]
- Suggested ingredient pre-orders (based on popular recipes generated this month).

## 3. Competitor Movements & Counter-Strategy
- Summary of competitor offers.
- Recommended price adjustments or packaging hooks.

## 4. Next Month's Content Strategy Adjustments
- Calendar modifications (festivals to target next month).
- Suggested blog topics to improve organic ranking.
```
