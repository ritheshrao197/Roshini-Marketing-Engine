# Daily Marketing Engine

**For:** Roshini's Home Products  
**Platform:** Google Antigravity 2.0  

---

## Trigger
Run every day at **9:00 AM** (local time)  
Scheduled prompt for Antigravity:
```text
Run the Daily Marketing Engine for Roshini's Home Products using .antigravity/daily-content-engine.md
```

---

## Step 1 – Load Knowledge
Before generating any content, load all required context databases to ensure strict alignment with brand rules and product facts:
- **Brand Identity & Style:**
  - `brand-kit/color-guidelines.md`
  - `brand-kit/style-guide.md`
- **Product & Nutritional Core:**
  - `knowledge-base/company.md`
  - All files in `knowledge-base/products/`
  - All files in `knowledge-base/ingredients/`
  - All files in `knowledge-base/nutrition/`
  - All files in `knowledge-base/recipes/`
- **Calendar & History:**
  - `calendar/festivals.md`
  - `history/previous-posts.md`
- **Scraping Sources:**
  - `sources.md`

*Understand:* Brand voice, product information, ingredients, nutrition, recipes, festivals, previous posts, and current offers. Ensure no claim violates FSSAI guidelines (from `health-claims.md`) and that **Roshini's Nutrimix** is never referred to as sprouted.

---

## Step 2 – Daily Research & Trend Discovery
Collect today's information from trusted sources.

### 1. Nutrition & Industry Research
- Latest nutrition research.
- Healthy recipes.
- Millet-related news.
- Seasonal fruits and vegetables.
- Festival and seasonal events.
- Competitor content.
- Health awareness days.

### 2. Social Media Trend Discovery
Search Instagram, Google Trends, Pinterest, and YouTube Shorts for:
- Trending food reels.
- Trending healthy recipes.
- Trending Instagram audio.
- Viral food photography styles.
- Trending carousel formats.
- Trending memes related to food, family, mornings, fitness, or healthy living.

### 3. Trend Validation
Before using any trend, verify that it:
- Fits Roshini's Home Products' brand voice (warm, trustworthy, educational, friendly).
- Is family-friendly.
- Is positive and educational.
- Does not reference politics or controversial topics (avoid political topics, controversial news, celebrity gossip, or unprofessional memes).
- Does not contain offensive or copyrighted content.
- Can naturally promote healthy eating or homemade foods.
*Reject any trends that do not satisfy these conditions.*

### 4. Meme & Viral Content
If a suitable trend or meme is found, generate:
- One meme-based Instagram post.
- One humorous carousel idea.
- One relatable Reel concept.
*Examples include:* Monday motivation + healthy breakfast, "POV" style videos, "Expectation vs Reality", "Nobody:" meme format, "Things that just make sense", Before vs After breakfast, Parent & child relatable moments, Office lunch humor, Gym nutrition humor. The humor must remain wholesome and aligned with the brand.

### 5. Save Research
Store the collected information as `today-research.md`, including:
- Today's nutrition topic.
- Trending recipe.
- Trending reel/audio.
- Trending meme (if applicable).
- Festival or seasonal event.
- Competitor insights.
- Recommended content angle.

---

## Step 3 – Generate Daily Marketing Package
Choose today's featured product, target customer persona, content theme, and active campaign (if applicable). Generate the following core marketing components:

### 1. Instagram
- **Caption:** Warm, engaging copy (80-150 words) with relevant hashtags and a clear call to action (CTA).
- **Post Content:** Main post copy.
- **Carousel Content (5 Slides):** Short, readable copy optimized for 5 carousel slides.
- **Story Content:** Text/visual ideas for stories.
- **Reel Caption:** Engaging, short caption for video.

### 2. Blog
- **SEO Title:** Under 60 characters.
- **Meta Description:** 140-160 characters.
- **URL Slug:** Clean, hyphenated slug.
- **Target Keywords:** 3-5 primary search terms.
- **SEO Article:** A 600–1000 word search-optimized article explaining the day's trend or ingredient profile.

### 3. Healthy Recipe
- Generate one easy healthy recipe using today's featured product.

### 4. Instagram Reel Script
- **Hook:** Under 3 seconds.
- **Voiceover Script:** Verbal narration.
- **Shot List:** Scene-by-scene visual descriptions.
- **On-screen Text:** Font overlays.
- **Ending CTA:** Clear conversion prompt.

### 5. Trending Content (Optional)
If a validated trend or meme is available from Step 2, generate:
- 1 Trending Instagram Post
- 1 Trending Reel Idea
- 1 Meme Image Prompt
- 1 Viral Hook
Otherwise, continue with the standard marketing content.

---

## Step 4 – Generate Images
Based on the generated text, write descriptive prompts and use the `generate_image` tool to create the following **10 visual assets**:
1. **Instagram Post Image** (1:1 / 4:5 square product-focused shot)
2. **Instagram Carousel Images (5)** (Sequence of 5 styled slides)
3. **Blog Featured Image** (16:9 landscape visual)
4. **Product Hero Image** (High-quality mockup showing packaging sitting on a kitchen counter)
5. **Lifestyle Image** (A family enjoying warm millet porridge)
6. **Recipe Image** (Plated close-up of the prepared recipe)

*Image Style Rules:*
- Mood: Wholesome, rustic, warm, family-oriented.
- Sourcing reference: Check `brand-kit/brand-ambassador/`, `brand-kit/products-photos/`, and `brand-kit/Posters/`. If reference assets exist, pass up to 3 paths to the `ImagePaths` parameter of `generate_image`.
- Lighting: Natural light, soft morning shadows.
- Visual elements: Scattered raw ingredients (almonds, whole millets, cardamoms) on linen or wooden backdrops.
- Color consistency: Natural greens (`#4E7A2E`), millet gold (`#D98C2B`), and warm sand backgrounds (`#FFF8EE`).

---

## Step 5 – Quality Check
Validate the daily package using our validation layers:
1. **FSSAI Compliance:** Cross-reference against `knowledge-base/health-claims.md`. Verify NO medical cure claims are made.
2. **Accuracy Check:** Ensure millets in Nutrimix are never called sprouted.
3. **Spelling & Grammar:** Clean, professional copy.
4. **Tone Consistency:** Warm, trustworthy, educational, friendly.
5. **SEO Check:** Target keywords are logically distributed.
6. **Image Quality:** Ensure correct branding elements.

*Update Memory:*
Automatically append today's metadata to the end of `history/previous-posts.md`:
- Product featured
- Topic/Theme
- Target keywords
- Hashtags used

---

## Step 6 – Export
Merge all verified copy and files into a single markdown file named:
```text
outputs/YYYY-MM-DD-marketing-package.md
```
Include:
- **Daily Summary:** Featured product, customer persona, theme, and active festival (if applicable).
- **Instagram Copy:** Caption, carousel slides, stories, reel caption.
- **Blog Article:** SEO article & metadata.
- **Healthy Recipe**
- **Reel Script**
- **AI Image Prompts & Generated Images:** List of prompts and embedded absolute local file links to the 10 generated PNG images under `outputs/images/`.

---

## Step 7 – Send to Telegram
Automatically deliver the complete marketing package to the Telegram channel/group:
- **Telegram Text Message:**
  ```text
  📅 Daily Marketing Package

  ✅ Featured Product: [Product Name]
  ✅ Theme: [Theme Topic]
  ✅ Instagram Caption
  ✅ Carousel Content
  ✅ Blog Article
  ✅ Healthy Recipe
  ✅ Reel Script
  ✅ SEO Keywords

  📷 Generated Images Attached
  📄 Marketing Package (.md) Attached
  ```
- **Attachments:**
  - The exported `outputs/YYYY-MM-DD-marketing-package.md` document.
  - The 10 generated PNG images from `/outputs/images/`.
- **Fail-Safe Mechanism:** If sending fails, retry up to 3 times, log the error in `outputs/telegram_errors.log`, and ensure all files are saved locally.
