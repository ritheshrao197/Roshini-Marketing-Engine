Daily Marketing Engine For: Roshini's Home Products
Platform: Google Antigravity 2.0

Trigger

Run every day at 9:00 AM (Local Time)

Execute

.antigravity/daily-content-engine.md

---

## STEP 1 - LOAD KNOWLEDGE

Before generating any content, load all required knowledge.

Brand Identity

brand-kit/color-guidelines.md
brand-kit/style-guide.md

Brand Assets

brand-kit/logo/
brand-kit/products/
brand-kit/posters/
brand-kit/fonts/

Product Knowledge

knowledge-base/company.md
knowledge-base/products/
knowledge-base/ingredients/
knowledge-base/nutrition/
knowledge-base/recipes/

Compliance

knowledge-base/health-claims.md

Calendar

calendar/festivals.md

history/previous-posts.md

Sources

sources.md

Understand

• Brand voice
• Product information
• Ingredients
• Nutrition
• Recipes
• Previous content
• Festivals
• Seasonal trends
• Brand assets

Never violate FSSAI guidelines.

Never refer to Nutrimix as Sprouted.

---

## STEP 2 - DAILY RESEARCH

Collect today's information.

Research

• Nutrition News
• Health News
• Healthy Recipes
• Millet News
• Seasonal Fruits
• Seasonal Vegetables
• Festivals
• Awareness Days
• Government Health Updates
• Food Industry News

Only use trusted sources.

Reject

• Politics
• Celebrity News
• Controversial Topics
• Medical Claims
• Copyrighted Content

Save research as

today-research.md

Include

• Today's Trends
• Recommended Topics
• Recommended Products
• Recommended Keywords

---

## STEP 3 - CONTENT GENERATION

Select

• Featured Product
• Customer Persona
• Content Theme

Generate

## Instagram

Generate exactly ONE premium Instagram post.

Include

• Caption
• Post Text
• Hashtags
• CTA
• One detailed production-ready image prompt

---

## Website Content

Generate between 2 and 5 website articles every day.

Choose automatically from

• Blog Article
• Health Tip
• Nutrition News
• Healthy Recipe
• Ingredient Spotlight
• Product Guide
• Myth vs Fact
• Seasonal Article
• FAQ
• Healthy Lifestyle

Avoid duplicate topics.

Prioritize evergreen content.

For every article generate

• Title
• Slug
• Category
• Tags
• Excerpt
• SEO Title
• SEO Description
• Target Keywords
• Featured Image Prompt
• Related Products
• References
• Complete Article
• Status = DRAFT

---

## Step 4 – Generate Image Prompts

Every day, generate descriptive prompts for Featured Image and Instagram Image concepts (including carousel slides on Mon/Thu, and 16:9 featured blog image on Wed).
Do NOT generate binary image files or call Imagen/Pillow. The prompts will be consumed by the separate image generation pipeline.

Image Style Rules:
Mood: Wholesome, rustic, warm, family-oriented.
Lighting: Natural light, soft morning shadows.
Visual elements: Scattered raw ingredients (almonds, whole millets, cardamoms) on linen or wooden backdrops.
Color consistency: Natural greens (#4E7A2E), millet gold (#D98C2B), and warm sand backgrounds (#FFF8EE).

Always include the image prompt text in the output markdown package.

Step 5 – Duplicate Prevention & Quality Check
1. Duplicate Prevention: Before generating the marketing package, search existing blogs on the backend via GET /api/vlogs/search?query={keyword}.
   Verify title similarity <= 80%, slug uniqueness, and keyword freshness.
   If duplicate is detected, query LLM for an alternative topic and re-check.
2. Quality Check validation:
   FSSAI Compliance: Cross-reference against knowledge-base/health-claims.md. Verify NO medical cure claims are made.
   Accuracy Check: Ensure millets in Nutrimix are never called sprouted.
   Spelling & Grammar: Clean, professional copy.
   Tone Consistency: Warm, trustworthy, educational, friendly.
   SEO Check (blog days only): Target keywords are logically distributed.
   Update Memory: Automatically append today's metadata to history/previous-posts.md.

Step 6 – Export & Upload
1. Parse & Upload Draft Blog: If a blog post is generated, map its category dynamically by fetching vlog categories via GET /api/vlog-categories. Import the post as a Draft to POST /api/blogs/import.
2. Merge all verified copy and metadata into a single markdown file named:
   outputs/YYYY-MM-DD-marketing-package.md
   Include:
   Daily Summary: Featured product, customer persona, theme.
   Instagram Copy: Caption (+ carousel slides on Mon/Thu).
   Blog Article: SEO article & metadata (if applicable).
   Healthy Recipe (if applicable).
   Image Prompt(s): Structured visual concept prompt descriptions.
   Upload Status: Draft ID and upload time (if uploaded).

Step 7 – Send to Telegram
Automatically deliver the complete content package summary to the Telegram channel/group:

Telegram Text Message:
📅 Daily Content Package

✅ Featured Product: [Product Name]
✅ Theme: [Theme Topic]
✅ Instagram Caption
✅ Carousel Content (Mon/Thu only)
✅ Blog Article (Wed only)
✅ Healthy Recipe (if applicable)
✅ Backend Draft Upload Status (with Draft ID)

📄 Content Package (.md) Attached

Attachments:
The exported outputs/YYYY-MM-DD-marketing-package.md document.

Fail-Safe Mechanism: If sending fails, retry up to 3 times, log the error in outputs/telegram_errors.log, and ensure all files are saved locally.

---

## STEP 8 - TELEGRAM

Send

• Daily Summary
• Instagram Caption
• Website Articles
• Image Prompts
• Markdown Package

Retry three times if sending fails.

Log failures.

---

## STEP 9 - HISTORY

Append to

history/previous-posts.md

Store

• Date
• Topics
• Products
• Keywords
• Categories
• Instagram Theme
• Website Articles
• Image Prompts
• Article IDs

---

## SUCCESS CRITERIA

Every day generate

✓ 1 Premium Instagram Post

✓ 2–5 Website Articles

✓ SEO Metadata

✓ Production-ready Image Prompt for Instagram

✓ Production-ready Featured Image Prompt for every article

✓ Upload every article as DRAFT

✓ Export Markdown Package

✓ Telegram Notification

✓ Update History

Never generate images.

Only generate detailed prompts.

Admin approval is always required before publishing.
