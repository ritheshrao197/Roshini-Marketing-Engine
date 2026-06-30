Daily Marketing Engine
For: Roshini's Home Products
Platform: Google Antigravity 2.0

Trigger
Run every day at 9:00 AM (local time)
Scheduled prompt for Antigravity:

Run the Daily Marketing Engine for Roshini's Home Products using .antigravity/daily-content-engine.md

Step 1 – Load Knowledge
Before generating any content, load all required context databases to ensure strict alignment with brand rules and product facts:

Brand Identity & Style:
brand-kit/color-guidelines.md
brand-kit/style-guide.md
Product & Nutritional Core:
knowledge-base/company.md
All files in knowledge-base/products/
All files in knowledge-base/ingredients/
All files in knowledge-base/nutrition/
All files in knowledge-base/recipes/
Calendar & History:
calendar/festivals.md
history/previous-posts.md
Scraping Sources:
sources.md

Understand: Brand voice, product information, ingredients, nutrition, recipes, festivals, previous posts, and current offers. Ensure no claim violates FSSAI guidelines (from health-claims.md) and that Roshini's Nutrimix is never referred to as sprouted.

Step 2 – Daily Research & Trend Discovery
Collect today's information from trusted sources.

1. Nutrition & Industry Research
   Latest nutrition research.
   Healthy recipes.
   Millet-related news.
   Seasonal fruits and vegetables.
   Festival and seasonal events.
   Health awareness days.

2. Trend Validation
   Before using any trend, verify that it:
   Fits Roshini's Home Products' brand voice (warm, trustworthy, educational, friendly).
   Is family-friendly, positive, and educational.
   Does not reference politics, controversial topics, or celebrity gossip.
   Does not contain offensive or copyrighted content.
   Can naturally promote healthy eating or homemade foods.
   Reject any trends that do not satisfy these conditions.

3. Save Research
   Store the collected information as today-research.md, including:
   Today's nutrition topic.
   Trending recipe (if relevant).
   Festival or seasonal event.
   Recommended content angle.

Step 3 – Generate Daily Content Package

Choose today's featured product, target customer persona, and content theme.

1. Daily Instagram Post (every day)
   Caption: Warm, engaging copy (80-150 words) with relevant hashtags and a clear CTA.
   Post Content: Main post copy.

2. Carousel Post (Mon & Thu only, 2x per week)
   5-slide carousel, short readable copy per slide, built around the week's theme/product.

3. Blog Post (1x per week, Wednesday)
   SEO Title: Under 60 characters.
   Meta Description: 140-160 characters.
   URL Slug: Clean, hyphenated slug.
   Target Keywords: 3-5 primary search terms.
   SEO Article: A 600–1000 word search-optimized article explaining the day's trend or ingredient profile.

4. Healthy Recipe (only on days a recipe naturally fits the theme)
   One easy healthy recipe using today's featured product.

Step 4 – Generate Image

Every day, generate exactly ONE image to accompany the daily Instagram post (and, on carousel days, the 5 carousel images; on blog days, 1 additional blog featured image).

Write a descriptive image prompt and use the generate_image tool to create the image.

Daily Image: 1 image (1:1 / 4:5 square, product-focused shot).
Carousel Days (Mon & Thu): 5 images for the carousel slides (replaces the single daily image that day).
Blog Day (Wed): 1 additional 16:9 blog featured image.

Image Style Rules:
Mood: Wholesome, rustic, warm, family-oriented.
Sourcing reference: Check brand-kit/brand-ambassador/, brand-kit/products-photos/, and brand-kit/Posters/. If reference assets exist, pass up to 3 paths to the ImagePaths parameter of generate_image.
Lighting: Natural light, soft morning shadows.
Visual elements: Scattered raw ingredients (almonds, whole millets, cardamoms) on linen or wooden backdrops.
Color consistency: Natural greens (#4E7A2E), millet gold (#D98C2B), and warm sand backgrounds (#FFF8EE).

Always include the image prompt text alongside the generated image in the output.

Step 5 – Quality Check
Validate the daily package using our validation layers:
FSSAI Compliance: Cross-reference against knowledge-base/health-claims.md. Verify NO medical cure claims are made.
Accuracy Check: Ensure millets in Nutrimix are never called sprouted.
Spelling & Grammar: Clean, professional copy.
Tone Consistency: Warm, trustworthy, educational, friendly.
SEO Check (blog days only): Target keywords are logically distributed.
Image Quality: Ensure correct branding elements.
Update Memory: Automatically append today's metadata to the end of history/previous-posts.md:
Product featured
Topic/Theme
Target keywords (blog days)
Hashtags used

Step 6 – Export
Merge all verified copy and files into a single markdown file named:
outputs/YYYY-MM-DD-marketing-package.md

Include:
Daily Summary: Featured product, customer persona, theme.
Instagram Copy: Caption (+ carousel slides on Mon/Thu).
Blog Article (Wed only): SEO article & metadata.
Healthy Recipe (if applicable).
Image Prompt(s) & Generated Image(s): Prompt text and embedded absolute local file links to the generated PNG image(s) under outputs/images/.

Step 7 – Send to Telegram
Automatically deliver the complete content package to the Telegram channel/group:

Telegram Text Message:
📅 Daily Content Package

✅ Featured Product: [Product Name]
✅ Theme: [Theme Topic]
✅ Instagram Caption
✅ Carousel Content (Mon/Thu only)
✅ Blog Article (Wed only)
✅ Healthy Recipe (if applicable)

📷 Generated Image(s) Attached
📄 Content Package (.md) Attached

Attachments:
The exported outputs/YYYY-MM-DD-marketing-package.md document.
The generated PNG image(s) from /outputs/images/.

Fail-Safe Mechanism: If sending fails, retry up to 3 times, log the error in outputs/telegram_errors.log, and ensure all files are saved locally.
