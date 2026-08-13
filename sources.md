# Target Content Sources
> Edit this file to control what Roshini's Home Products content engine monitors daily.

## Web Search Keywords
These are searched every morning to discover the latest health, nutrition, and food trends.

- "Millet health benefits"
- "Healthy breakfast ideas India"
- "Superfoods nutrition research"
- "Child nutrition India"
- "Women's health nutrition"
- "Protein rich vegetarian foods"
- "Healthy snacks for office"
- "Natural immunity boosting foods"
- "FSSAI food updates"
- "Organic food trends India"
- "Millet recipes"
- "Dry fruits health benefits"
- "Nutrition tips for working professionals"
- "Healthy pregnancy nutrition"
- "Kids breakfast nutrition"

## Industry News URLs
These are fetched to extract raw article/news text.

- https://www.fssai.gov.in
- https://www.nin.res.in
- https://www.nhp.gov.in
- https://www.eatrightindia.gov.in
- https://www.healthline.com/nutrition
- https://www.medicalnewstoday.com/nutrition

## Competitor / Inspiration Websites
Monitor content from:

- Slurrp Farm
- True Elements
- Yogabar
- Tata Soulfull
- Nourish Organics
- Millet Amma
- Organic India

## Recipe Inspiration
- Hebbars Kitchen
- Archana's Kitchen
- Dassana's Veg Recipes
- Indian Healthy Recipes

## Daily Food News (automated)
`collectors/food_news.py` pulls 5 real, current stories every day via Google News RSS
search feeds (no API key needed) and feeds them into the "food_news" article type,
which is generated alongside the usual 5-article campaign. Edit the query list in
`collectors/food_news.py` (`DEFAULT_QUERIES`) to change what it covers - each query
also sets the suggested category for its stories:

- "food and nutrition news India" -> Nutrition News
- "nutrition research superfoods" -> Nutrition Research
- "FSSAI food safety" -> Food Safety
- "millets OR dry fruits health benefits" -> Nutrition
- "healthy eating trends India" -> Lifestyle

Each generated article is required to cite its real source (name + link) in the
article body and in `references` - the writer prompt is instructed not to invent
facts beyond the collected headline/summary.

---
_Tip: For sites with heavy JavaScript or anti-bot blocks, Antigravity will automatically fall back to a headless Playwright browser script to extract clean HTML text._
