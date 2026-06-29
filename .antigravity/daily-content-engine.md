# Daily Multi-Agent Marketing Engine (12-Agent Production Setup)
**For: Roshini's Home Products | Platform: Google Antigravity 2.0**

---

## Trigger
**Scheduled Task** — Daily at 9:00 AM (local time)
Set this up in Antigravity via: `Schedule → New → Daily 9:00 AM`

Paste the following as your scheduled task prompt:
```
Run the Daily Content Engine for Roshini's Home Products. Follow the steps in `.antigravity/daily-content-engine.md` exactly.
```

---

## Step 1 — Load System Assets & Context

The orchestration engine reads and loads the following resources:
1. **Brand Voice & Style Rules:** `/brand-kit/color-guidelines.md` and `/brand-kit/style-guide.md`.
2. **Product Knowledge Base:** All files under `/knowledge-base/` (USP, ingredients, nutrition, recipes, faq, pricing).
3. **Calendar Triggers:** `/calendar/festivals.md` and `/calendar/campaigns.md` (detects if a festival is within the next 7 days or if a campaign is active).
4. **History Ledger:** `/history/previous-posts.md` (to ensure the hooks, recipes, and personas are rotated and not repeated from the last 30 days).

---

## Step 2 — Fetch Daily Sources

Scrape and collect raw research context from `/sources.md` (Web search keywords and target URLs).
1. Execute `google_search` for today's keywords (past 24h).
2. Fetch clean text from target industry and recipe URLs.
3. Save raw context locally to `today_raw_research.txt`.

---

## Step 3 — Orchestrate the 7-Agent Instagram Engine

To produce high-conversion, brand-safe, and visually consistent daily posts, Antigravity coordinates **7 specialized agents** in a structured sequence:

```mermaid
graph TD
    A[Start: Load Assets & Sources] --> B[Agent 1: Research Agent]
    B --> C[Agent 2: Product Knowledge Agent]
    C --> D[Generation Layer]
    subgraph Generation Layer
        E[Agent 3: Instagram Agent]
        F[Agent 4: Canva & Image Gen Agent]
        G[Agent 5: Campaign Agent]
    end
    D --> H[Agent 6: QA & Compliance Agent]
    H --> I[Agent 7: Analytics & Memory Agent]
    I --> J[End: Export Daily Output]
```

### 1. Research Agent
- **Responsibility:** Parses the raw scraping folder, extracts the top 3 health/nutrition trends from today's sources, and provides a summarized daily research brief.

### 2. Product Knowledge Agent
- **Responsibility:** Validates the research brief against the modular `/knowledge-base/` (USPs, ingredients, and nutrition). It translates raw science into simple family benefits, ensuring no false nutritional claims are made.

### 3. Instagram Agent
- **Responsibility:** Injects daily topic rotations (e.g. Millet Monday) and drafts:
  - 1 Instagram Caption (80-150 words).
  - Carousel copy (Slide 1 to 5).
  - Target call to action (CTA).

### 4. Canva & Image Gen Agent
- **Responsibility:**
  - **Design Layouts:** Generates exact styling briefs for the Instagram carousel slides (font sizing, hex codes, layouts, and icons).
  - **Visual Prompts:** Formulates specific visual image prompts based on the drafted Instagram post/carousel content.
  - **Image Generation:** Executes the `generate_image` tool to create 2 high-quality marketing images for the Instagram post or carousel (saved under `e:\Roshinis\AI_Content\outputs\images\YYYY-MM-DD_post_1.png` and `e:\Roshinis\AI_Content\outputs\images\YYYY-MM-DD_post_2.png`).
  - **Reference Image Integration:** The agent has the option to use reference images to maintain consistent branding. It must check the folders `/brand-kit/brand-ambassador/`, `/brand-kit/products-photos/`, and the newly added `/brand-kit/Posters/` (which contains 79 previously generated high-quality brand posters). If any reference images are present in these folders (such as packaging mockups, ambassador portraits, or established style poster templates), the agent must pass their absolute paths (up to 3) in the `ImagePaths` parameter of the `generate_image` tool to guide the generation (e.g., matching the product pouch, the face of the ambassador, or the rustic design/lighting style of the brand posters).

### 5. Campaign Agent
- **Responsibility:** Checks `/calendar/festivals.md` and `/calendar/campaigns.md`. If a promotion or festival is active, it modifies CTAs and posts to include custom discount codes (e.g. `FIRST10`) and seasonal copy hooks.

### 6. QA & Compliance Agent (Validation Layer)
- **Responsibility:** Reviews the output of all preceding agents:
  - Checks for grammar and spelling.
  - Ensures voice consistency (warm, educational, honest).
  - Verifies FSSAI compliance (flags any medical cure claims using `/knowledge-base/health-claims.md`).
  - Checks history database to ensure no hook, recipe, or target persona is duplicated.

### 7. Analytics & Memory Agent
- **Responsibility:** Adjusts final post hook styles based on previous week's performance data. At the end of the run, it automatically appends today's hooks and tags to `/history/previous-posts.md`.

---

## Step 4 — Export & Log
1. **Merge** all verified output segments into a single markdown file named `YYYY-MM-DD-multi-source-content.md` under `/outputs/`.
2. **Embed Generated Images:** Insert absolute local paths/markdown links of the generated images from `/outputs/images/` directly into the Instagram caption and carousel slides sections of the merged markdown file.
3. **Include summary metadata** at the beginning: Active rotation day, target customer persona chosen for today, campaign codes used, and links to the generated image files.
4. **Purge** the temporary research briefs and cache files.
