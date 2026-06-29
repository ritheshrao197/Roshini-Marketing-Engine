# Roshini's Home Products AI Marketing System
**Platform: Google Antigravity 2.0**

A production-grade, multi-agent AI marketing and automation engine customized for **Roshini's Home Products** (Homemade Millet, Dry Fruit & Seeds Mix). This system runs daily content creation, tracks calendar-driven campaigns, validates FDA/FSSAI compliance, incorporates content memory loops, and produces ready-to-run graphics briefs and SEO assets.

---

## Complete Folder Structure

```
roshini-content-engine/
├── README.md                          ← You are here
├── sources.md                         ← Daily monitored keywords, URLs, and RSS feeds
├── brand-kit/
│   ├── color-guidelines.md            ← Brand values, voice and tone, platform rules
│   ├── skills.md                      ← Operational skill capabilities catalog
│   └── style-guide.md                 ← Typography pairing, colors, Canva briefs
├── knowledge-base/
│   ├── company.md                     ← Mission, vision, values, USPs, and tone
│   ├── brand-story.md                 ← Brand origin story and narrative
│   ├── certifications.md              ← Hygiene protocols, sourcing standards, FSSAI rules
│   ├── manufacturing-process.md       ← Step-by-step small batch preparation
│   ├── shipping.md                    ← Delivery times, rates, and dispatch timelines
│   ├── faq.md                         ← Age guidance, allergens, usage, and health FAQs
│   ├── pricing.md                     ← Pricing, pack sizes, combos, and shipping rates
│   ├── customer-personas.md           ← Restructured personas (Anjali, Rahul, Mr. Rao, Meera, Vikram)
│   ├── product-comparison.md          ← Roshini's vs. Commercial health mixes comparison
│   ├── health-claims.md               ← Always Say / Never Say compliance guidelines
│   │
│   ├── products/
│   │   └── nutrimix.md                ← Flagship product profiles, prep, storage, and details
│   │
│   ├── ingredients/
│   │   ├── millets.md                 ← Finger, pearl, sorghum, foxtail millets, etc.
│   │   ├── dry-fruits.md              ← Almonds, walnuts, pistachios, dates, peanuts, etc.
│   │   ├── seeds.md                   ← Pumpkin, flax, chia, and watermelon seeds
│   │   ├── spices.md                  ← Premium Kerala cardamom details
│   │   └── sweeteners.md              ← Natural sugar alternatives and sweetening policies
│   │
│   ├── nutrition/
│   │   ├── vitamins.md                ← Vitamin E, B-Complex, Vitamin C details
│   │   ├── minerals.md                ← Bioavailability, calcium, iron, zinc, magnesium
│   │   ├── protein.md                 ← Plant-protein sources and benefits
│   │   ├── fiber.md                   ← Soluble and insoluble dietary fiber profiles
│   │   └── antioxidants.md            ← Polyphenols, lignans, carotenoids
│   │
│   └── recipes/
│       ├── breakfast.md               ← Classic porridge (malt), dry fruit malt, protein oats
│       ├── smoothies.md               ← Banana & date smoothie, mango shake
│       ├── desserts.md                ← Sweet treats, kids' laddus, chocolate pudding
│       ├── snacks.md                  ← Savory buttermilk porridge, baked crackers
│       └── kids.md                    ← Sweet porridge, laddus, kids' chocolate pudding
├── calendar/
│   ├── festivals.md                   ← 2026 Indian festival triggers and copy hooks
│   └── campaigns.md                   ← Promotional schemes and campaign frameworks
├── history/
│   ├── previous-posts.md              ← Content memory log to prevent repetition
│   └── hashtags.md                    ← Categorized hashtag library and platform guidelines
├── templates/
│   ├── instagram.md                   ← Instagram carousel layouts & Canva styling briefs
│   ├── reels.md                       ← Video scripting grid (Visuals, VO, Text, timing)
│   ├── blogs.md                       ← Blog SEO rules, FAQ JSON-LD schema layouts
│   ├── newsletters.md                 ← Weekly newsletter newsletter templates
│   └── product-launch.md              ← Teaser, pre-order, and launch copywriting frames
├── outputs/                           ← Generated daily content batches land here
├── research/                          ← Raw scraped news summaries and raw text cache
└── .antigravity/
    ├── daily-content-engine.md        ← Daily scheduled 7-agent Instagram-focused pipeline
    ├── weekly-report.md               (Weekly analytics loop scheduler - Sundays)
    └── monthly-report.md              (Monthly strategic review scheduler - 1st of month)
```

---

## How the 7-Agent Instagram Engine Works

Daily at **9:00 AM**, Google Antigravity spawns and orchestrates 7 specialized agents to run the marketing engine:

```
                  9:00 AM Daily Trigger
                            │
                            ▼
             Step 1: Load Context Databases
    (Loads Brand Kit, Product Knowledge, Calendar & History)
                            │
                            ▼
             Step 2: Scrape & Research Sources
        (Executes Google Search & url_context extraction)
                            │
                            ▼
            Step 3: Run 7-Agent Orchestration
┌──────────────────────────┬──────────────────────────┐
│  1. Research Agent       │  2. Product Knowledge    │
│  3. Instagram Writer     │  4. Canva & Image Gen    │
│  5. Campaign Manager     │  6. QA & Compliance      │
│  7. Memory & Analytics   │                          │
└──────────────────────────┴──────────────────────────┘
                            │
                            ▼
                Step 4: Output Assembly
(Topic rotated by calendar, compiled into YYYY-MM-DD-multi-source-content.md)
```

---

## Quick Start Setup

### 1. Load Workspace
Open Google Antigravity, click `File → Open Folder`, and select your `roshini-content-engine` workspace folder (i.e. `e:\Roshinis\AI_Content`).

### 2. Set Up the Daily Scheduled Task
- Go to the **Schedule** tab in Antigravity.
- Create a new scheduled task set for **9:00 AM, Daily**.
- Paste the following prompt:
  ```
  Read .antigravity/daily-content-engine.md and execute the Daily Content Engine for Roshini's Home Products.
  ```

### 3. Set Up the Weekly Reporting Task (Sundays)
- Create a new scheduled task set for **6:00 PM, Weekly on Sunday**.
- Paste the following prompt:
  ```
  Read .antigravity/weekly-report.md and execute the Weekly Report Engine.
  ```

### 4. Set Up the Monthly Review Task (1st of the Month)
- Create a new scheduled task set for **9:00 AM, Monthly on the 1st**.
- Paste the following prompt:
  ```
  Read .antigravity/monthly-report.md and execute the Monthly Review.
  ```

### 5. Running a Manual Test
In the Antigravity Manager view, launch a new agent and command it:
```
Read .antigravity/daily-content-engine.md and run a manual test for today.
```
Watch the agents fetch live research, consult the history log to avoid repetition, reference the ingredient guides, compile the Canva graphics layouts, and write the output files into `/outputs/`.
