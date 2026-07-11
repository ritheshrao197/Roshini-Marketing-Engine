import os
import datetime
import glob
import json
import requests
from google import genai
from google.genai import types

# Ensure script runs from its own directory so relative paths resolve correctly
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir:
    os.chdir(base_dir)

# Load local .env file if it exists relative to script directory
def load_dotenv():
    filepath = os.path.join(base_dir, ".env")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip().strip("'").strip('"')

load_dotenv()

# Setup Gemini API client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables. Gemini/Imagen calls will fail.")

# Setup Telegram API
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def load_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return ""

def load_knowledge_base():
    kb_content = {}
    kb_files = [
        "knowledge-base/company.md",
        "knowledge-base/brand-story.md",
        "knowledge-base/certifications.md",
        "knowledge-base/manufacturing-process.md",
        "knowledge-base/shipping.md",
        "knowledge-base/faq.md",
        "knowledge-base/pricing.md",
        "knowledge-base/customer-personas.md",
        "knowledge-base/product-comparison.md",
        "knowledge-base/health-claims.md",
    ]
    for filepath in kb_files:
        if os.path.exists(filepath):
            kb_content[filepath] = load_file(filepath)
            
    # Include all product, ingredient, nutrition, and recipe files
    for folder in ["products", "ingredients", "nutrition", "recipes"]:
        for filepath in glob.glob(f"knowledge-base/{folder}/*.md"):
            kb_content[filepath] = load_file(filepath)
            
    return kb_content

def call_gemini(prompt, system_instruction=None, model_name=None):
    """
    Redirects legacy pipeline calls to the unified multi-provider LLM routing layer.
    """
    import asyncio
    from llm import call_llm
    
    requires_json = False
    
    try:
        return asyncio.run(call_llm(
            prompt=prompt,
            system_instruction=system_instruction,
            json_format=requires_json,
            version="v2"
        ))
    except Exception as e:
        print(f"[LEGACY WRAPPER] Error calling LLM: {e}")
        return f"Error executing LLM call: {e}"


def create_pillow_placeholder(prompt, output_path):
    """
    Creates a premium, designer-style visual card with rich typography,
    a modern layout, and clean geometric accents to wow the user.
    Uses official brand colors and loads the brand logo from the brand kit.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os
        
        # Dimensions
        w, h = 800, 800
        
        # Create image with premium warm background (#FFF8EE - Warm Sand)
        img = Image.new('RGB', (w, h), color=(255, 248, 238))
        draw = ImageDraw.Draw(img)
        
        # Load fonts from standard Windows System font directories
        try:
            font_brand = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26) # Segoe UI Bold
            font_body = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 22)   # Georgia Regular
            font_meta = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)    # Segoe UI Regular
            font_badge = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 14)  # Segoe UI Bold
        except Exception:
            font_brand = font_body = font_meta = font_badge = None

        # 1. Accent shapes (modern geometric layout)
        # Forest green header card block (#4E7A2E)
        draw.rectangle([0, 0, w, 160], fill=(78, 122, 46))
        
        # Gold accent thin divider line (#D98C2B)
        draw.rectangle([0, 160, w, 168], fill=(217, 140, 43))
        
        # Attempt to load and paste the official brand logo white version
        logo_loaded = False
        logo_path = "brand-kit/Logo white version.png"
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path)
                aspect = logo_img.width / logo_img.height
                logo_h = 100
                logo_w = int(logo_h * aspect)
                logo_img = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                
                paste_x = (w - logo_w) // 2
                paste_y = (160 - logo_h) // 2
                
                if logo_img.mode == 'RGBA':
                    img.paste(logo_img, (paste_x, paste_y), logo_img)
                else:
                    img.paste(logo_img, (paste_x, paste_y))
                logo_loaded = True
            except Exception as e:
                print(f"Failed to paste brand logo: {e}")
                
        if not logo_loaded:
            # Fallback to drawing text brand name in header
            draw.text((w // 2, 50), "ROSHINI'S HOME PRODUCTS", fill=(255, 255, 255), font=font_brand, anchor="mm")
            draw.text((w // 2, 95), "Wholesome Blend for a Healthier You", fill=(245, 235, 220), font=font_meta, anchor="mm")
        
        # 2. Main Content Card Area (clean centered white box with borders)
        card_margin = 50
        card_y_start = 220
        card_y_end = 700
        
        # Draw a beautiful card with border
        draw.rounded_rectangle(
            [card_margin, card_y_start, w - card_margin, card_y_end],
            radius=15,
            fill=(255, 255, 255),
            outline=(230, 225, 215),
            width=2
        )
        
        # Section category badge inside the card
        badge_w, badge_h = 180, 30
        badge_x = (w - badge_w) // 2
        badge_y = card_y_start + 30
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=10,
            fill=(245, 240, 230),
            outline=(217, 140, 43),
            width=1
        )
        draw.text((w // 2, badge_y + 15), "VISUAL CONCEPT", fill=(217, 140, 43), font=font_badge, anchor="mm")
        
        # Wrapped Prompt Body Text (Charcoal color #4A4A4A)
        y_text = badge_y + 80
        
        max_chars = 48
        words = prompt.split()
        lines = []
        current_line = []
        for word in words:
            if len(" ".join(current_line + [word])) > max_chars:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        if current_line:
            lines.append(" ".join(current_line))
            
        for line in lines[:10]:
            draw.text((w // 2, y_text), line, fill=(74, 74, 74), font=font_body, anchor="mm")
            y_text += 35
            
        # Draw Footer accents
        draw.text(
            (w // 2, 750),
            "[ Imagen 3 API unavailable • Fallback Production Card ]",
            fill=(140, 140, 140),
            font=font_meta,
            anchor="mm"
        )
        
        # Save image
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        print(f"Created fallback placeholder image at {output_path}")
        return output_path
    except Exception as e:
        print(f"Failed to create Pillow placeholder: {e}")
        return None

def generate_image_asset(prompt, output_path):
    """
    Generates an image using Google's Imagen model and saves it.
    If the API model is unavailable, falls back to a Pillow visual card.
    """
    if not GEMINI_API_KEY:
        print(f"Skipping image generation for '{output_path}' (No API Key).")
        return create_pillow_placeholder(prompt, output_path)
        
    try:
        print(f"Generating image: {output_path} with prompt: {prompt}")
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Decide aspect ratio based on output path
        aspect_ratio = "1:1"
        if "blog" in output_path:
            aspect_ratio = "16:9"
            
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                output_mime_type="image/png"
            )
        )
        
        # Save image
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        for generated_image in result.generated_images:
            generated_image.image.save(output_path)
            print(f"Successfully saved generated image to {output_path}")
            return output_path
            
    except Exception as e:
        print(f"Image generation failed for {output_path}: {e}")
        print("Falling back to Pillow-generated visual placeholder...")
        return create_pillow_placeholder(prompt, output_path)

def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def extract_section(text, start_marker, end_marker=None):
    try:
        parts = text.split(start_marker)
        if len(parts) < 2:
            return ""
        content = parts[1]
        if end_marker:
            content = content.split(end_marker)[0]
        return content.strip()
    except Exception:
        return ""

def send_to_telegram_with_retry(message_text, document_path, image_paths):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram config credentials missing. Skipping Telegram posting.")
        return
        
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    url_doc = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Telegram posting attempt {attempt} of {max_retries}...")
            
            # 1. Send the Summary HTML message
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message_text,
                'parse_mode': 'HTML'
            }
            try:
                res_msg = requests.post(url_msg, json=payload)
                res_msg.raise_for_status()
                print("Telegram summary message sent successfully.")
            except Exception as msg_err:
                print(f"Failed to send HTML message: {msg_err}. Retrying as plain text...")
                plain_text = message_text
                for tag in ['<b>', '</b>', '<i>', '</i>', '<code>', '</code>', '<pre>', '</pre>']:
                    plain_text = plain_text.replace(tag, '')
                payload_plain = {
                    'chat_id': TELEGRAM_CHAT_ID,
                    'text': plain_text
                }
                res_msg = requests.post(url_msg, json=payload_plain)
                res_msg.raise_for_status()
                print("Telegram summary message sent successfully as plain text.")
            
            # 2. Send the Marketing Package Document (.md file)
            if os.path.exists(document_path):
                with open(document_path, 'rb') as doc_file:
                    payload_doc = {'chat_id': TELEGRAM_CHAT_ID}
                    files_doc = {'document': doc_file}
                    res_doc = requests.post(url_doc, data=payload_doc, files=files_doc)
                    res_doc.raise_for_status()
                print("Telegram document attachment sent successfully.")
                
            # 3. Send all successfully generated images
            for img_path in image_paths:
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as img_file:
                        payload_img = {'chat_id': TELEGRAM_CHAT_ID}
                        files_img = {'photo': img_file}
                        res_img = requests.post(url_photo, data=payload_img, files=files_img)
                        res_img.raise_for_status()
                    print(f"Telegram image {img_path} sent successfully.")
            
            print("Telegram execution finished successfully!")
            return True # Success
            
        except Exception as e:
            print(f"Telegram attempt {attempt} failed: {e}")
            if attempt == max_retries:
                # Log error locally on final failure
                os.makedirs("outputs", exist_ok=True)
                with open("outputs/telegram_errors.log", "a", encoding="utf-8") as err_log:
                    err_log.write(f"[{datetime.datetime.now().isoformat()}] Telegram post failed after 3 attempts. Error: {e}\n")
                print("Logged error to outputs/telegram_errors.log")
                return False

def run_marketing_pipeline():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    print(f"--- Starting Daily Marketing Package Engine for {today_str} ---")
    
    # Step 1: Load Knowledge
    print("Loading Knowledge Base...")
    kb = load_knowledge_base()
    
    calendar_festivals = load_file("calendar/festivals.md")
    calendar_campaigns = load_file("calendar/campaigns.md")
    history_posts = load_file("history/previous-posts.md")
    sources = load_file("sources.md")
    instagram_skill = load_file("RoshinisInstagramSkill.md")
    brand_style_guide = load_file("brand-kit/style-guide.md")
    
    # Determine today's day of the week and strategy
    today_obj = datetime.date.today()
    day_name = today_obj.strftime("%A")  # e.g., "Monday"
    
    day_strategy_mapping = {
        "Monday": "Health Tip",
        "Tuesday": "Recipe",
        "Wednesday": "Ingredient Spotlight",
        "Thursday": "Customer Story",
        "Friday": "Educational Carousel",
        "Saturday": "Lifestyle / Reel",
        "Sunday": "Offer / Product Highlight"
    }
    today_strategy = day_strategy_mapping.get(day_name, "Lifestyle / Reel")
    print(f"Today is {day_name}. Content Strategy: {today_strategy}")

    # Step 2: Daily Research & Trend Discovery
    print("Running Research Agent (Daily Research & Trend Discovery)...")
    research_prompt = f"""
    You are the Research Agent. Based on the following sources, calendar, and previously posted content, discover today's information and trends.
    
    Sources: {sources}
    Calendar: {calendar_campaigns}
    Festivals: {calendar_festivals}
    History Ledger: {history_posts}
    
    Your task:
    1. Industry & Nutrition Research: Extract latest nutrition research, healthy recipes, millet news, seasonal fruits/vegetables, health awareness days.
    2. Social Media Trend Discovery: Discover trending reels, healthy recipes, trending audio, viral photography styles, carousel formats, and relatable memes.
    3. Trend Validation: Verify the trend fits Roshini's Home Products' brand voice (warm, family-friendly, positive, educational).
       STRICTLY reject trends referencing politics, controversial topics, celebrity gossip, or unprofessional memes.
    4. Wholesome Meme & Viral Concepts: If a suitable trend/meme exists, describe one (e.g. parent & child moment, gym nutrition, POV style before/after breakfast).
    
    Output a clear trend brief for the team. Include sections:
    - Today's nutrition topic
    - Trending recipe
    - Trending reel/audio
    - Trending meme (if applicable and validated, otherwise write "None validated")
    - Festival or seasonal event
    - Competitor insights
    - Recommended content angle
    """
    research_brief = call_gemini(research_prompt)
    with open("today-research.md", "w", encoding="utf-8") as f:
        f.write(research_brief)
    print("Research brief saved as 'today-research.md'.")
    
    # Step 3: Generate Daily Marketing Package (Optimized into 1 single API call to save daily quota limits)
    print("Generating Daily Marketing Package...")
    
    generation_prompt = f"""
    STRICT OUTPUT RULE: Do not output any thinking block, inner monologue, planning, or reasoning text. You must output ONLY the final structured marketing package. Start your response directly with the header "--- START SELECTION ---".
    
    You are the Content and Image Planner for Roshini's Home Products. Your task is to act as the 'roshinis-instagram' marketing skill.
    
    Here is the 'roshinis-instagram' skill specification:
    {instagram_skill}
    
    Visual Style Guide & Brand Kit:
    {brand_style_guide}
    
    STRICT IMAGE PROMPT RULE: All AI Image Prompts (in Section 3 and the JSON block) must adhere strictly to the "Visual Brand Aesthetic" (Section 1) and "Visual Asset Descriptions" (Section 5) in the Visual Style Guide. Use soft natural daylight, textured warm wood/linen backdrops, clay bowl/linen garnishes, and correct premium product packaging descriptions for Roshini's products (e.g. stand-up pouch, warm green and gold colors, minimal layout).
    
    Today's Date: {today_str} ({day_name})
    Today's Content Strategy Focus: {today_strategy}
    
    Research Brief:
    {research_brief}
    
    Customer Personas:
    {kb.get("knowledge-base/customer-personas.md", "")}
    
    Active Campaigns / Offers:
    {calendar_campaigns}
    
    Health claims guidelines (Ensure FSSAI compliance, no medical cure/treatment claims, Nutrimix is never called sprouted):
    {kb.get("knowledge-base/health-claims.md", "")}
    
    Instructions:
    1. Select an appropriate product from the catalog matching today's focus and calendar.
    2. Act as the 'roshinis-instagram' skill to generate a complete Instagram campaign for the product.
    3. Conform to the output format, image rules, and caption rules of the skill.
    4. Provide the output in three logical parts (Part 1, Part 2, Part 3) and a separate Image Prompts JSON section, starting each section with the EXACT headers specified below.
    
    --- START SELECTION ---
    Provide metadata:
    1. Featured Product (from product catalog)
    2. Customer Persona
    3. Content Strategy (today is {day_name} -> {today_strategy})
    4. Active Campaign / Promo Code
    
    --- START CAMPAIGN PART 1 ---
    Provide Sections 1 to 6 of the skill's output format:
    ## 1. Objective
    ## 2. Creative Concept
    ## 3. AI Image Prompt (highly detailed, photorealistic, 8k, commercial food photography style, wood tabletop, natural lighting, correct packaging & branding)
    ## 4. Image Specs
    ## 5. Headline
    ## 6. Supporting Text
    
    --- START CAMPAIGN PART 2 ---
    Provide Sections 7 to 9 of the skill's output format:
    ## 7. Caption (Must follow Caption Rules and FSSAI compliance rules: no cures, supports/helps phrasing, allergen alerts)
    ## 8. Hashtags (5 brand, 10 niche, 10 discovery)
    ## 9. Instagram Story (1080x1920 layout, text, CTA, interactive sticker suggestion)
    
    --- START CAMPAIGN PART 3 ---
    Provide Sections 10 to 12 of the skill's output format:
    ## 10. Reel (Scene-by-scene storyboard/script grid with Timing, Visual/Camera, VO/Audio, On-Screen Text)
    ## 11. Carousel (5 slides detail)
    ## 12. Posting Strategy (Recommend best day, best time in IST, caption length, boost recommendation, target audience)
    
    --- START IMAGE PROMPTS ---
    Provide highly descriptive prompts for an AI art generator (Imagen) to produce assets. Ensure it matches the style guide (e.g. natural lighting, warm wooden backgrounds, premium composition). Format the output inside this section strictly as a valid JSON matching this schema:
    {{
      "instagram_post_image": "prompt text for the main post visual (Section 3)",
      "instagram_carousel_1": "prompt text for carousel slide 1",
      "instagram_carousel_2": "prompt text for carousel slide 2",
      "instagram_carousel_3": "prompt text for carousel slide 3",
      "instagram_carousel_4": "prompt text for carousel slide 4",
      "instagram_carousel_5": "prompt text for carousel slide 5",
      "blog_featured_image": "prompt text for a 16:9 lifestyle/educational background",
      "product_hero_image": "prompt text for premium packaging mockup sitting on kitchen table",
      "lifestyle_image": "prompt text for a lifestyle shot showing human interaction with the product",
      "recipe_image": "prompt text for a plated close-up of a recipe utilizing the product"
    }}
    """
    
    full_package = call_gemini(generation_prompt)
    
    # Parse sections
    selection_info = extract_section(full_package, "--- START SELECTION ---", "--- START CAMPAIGN PART 1 ---")
    campaign_part_1 = extract_section(full_package, "--- START CAMPAIGN PART 1 ---", "--- START CAMPAIGN PART 2 ---")
    campaign_part_2 = extract_section(full_package, "--- START CAMPAIGN PART 2 ---", "--- START CAMPAIGN PART 3 ---")
    campaign_part_3 = extract_section(full_package, "--- START CAMPAIGN PART 3 ---", "--- START IMAGE PROMPTS ---")
    image_prompts_section = extract_section(full_package, "--- START IMAGE PROMPTS ---")
    
    # Fallback notifications for empty or failed generation steps
    if not selection_info.strip():
        selection_info = "Product: Roshini's Nutrimix\nTheme: Nutrition & Family Wellness"
    if not campaign_part_1.strip():
        campaign_part_1 = f"⚠️ <i>Campaign Part 1 generation failed due to API limits. Detail: {escape_html(full_package[:250])}</i>"
    if not campaign_part_2.strip():
        campaign_part_2 = f"⚠️ <i>Campaign Part 2 generation failed due to API limits. Detail: {escape_html(full_package[:250])}</i>"
    if not campaign_part_3.strip():
        campaign_part_3 = f"⚠️ <i>Campaign Part 3 generation failed due to API limits. Detail: {escape_html(full_package[:250])}</i>"
    
    # Step 4: Generate Images
    print("Generating Image Prompts and Visual Assets...")
    img_paths = []
    try:
        cleaned_json = image_prompts_section.strip().replace("```json", "").replace("```", "").strip()
        image_prompts = json.loads(cleaned_json)
        
        img_mapping = {
            "instagram_post_image": f"outputs/images/{today_str}_post.png",
            "instagram_carousel_1": f"outputs/images/{today_str}_carousel_1.png",
            "instagram_carousel_2": f"outputs/images/{today_str}_carousel_2.png",
            "instagram_carousel_3": f"outputs/images/{today_str}_carousel_3.png",
            "instagram_carousel_4": f"outputs/images/{today_str}_carousel_4.png",
            "instagram_carousel_5": f"outputs/images/{today_str}_carousel_5.png",
            "blog_featured_image": f"outputs/images/{today_str}_blog.png",
            "product_hero_image": f"outputs/images/{today_str}_product_hero.png",
            "lifestyle_image": f"outputs/images/{today_str}_lifestyle.png",
            "recipe_image": f"outputs/images/{today_str}_recipe.png",
        }
        
        for key, output_path in img_mapping.items():
            prompt_text = image_prompts.get(key, "Organic multigrain millet mix with nuts, natural lighting")
            res_path = generate_image_asset(prompt_text, output_path)
            if res_path:
                img_paths.append(res_path)
                
    except Exception as e:
        print(f"Error parsing/generating JSON image prompts: {e}. Generating single fallback image.")
        res_fallback = generate_image_asset("Healthy traditional Indian breakfast, warm morning light, top down shot", f"outputs/images/{today_str}_fallback.png")
        if res_fallback:
            img_paths.append(res_fallback)
            
    # Step 5: Quality Check / Update Previous Posts History Ledger
    try:
        with open("history/previous-posts.md", "a", encoding="utf-8") as hist_file:
            hist_file.write(f"\n- {today_str}: Daily campaign featuring {selection_info.splitlines()[0] if selection_info.splitlines() else 'Nutrimix'}")
        print("History ledger 'previous-posts.md' updated.")
    except Exception as e:
        print(f"Failed to update history ledger: {e}")
        
    # Step 6: Export Package
    print("Saving YYYY-MM-DD-marketing-package.md...")
    output_doc_path = f"outputs/{today_str}-marketing-package.md"
    os.makedirs("outputs", exist_ok=True)
    
    image_links_list = []
    for i, path in enumerate(img_paths):
        abs_path_str = os.path.abspath(path).replace('\\', '/')
        basename = os.path.basename(path)
        image_links_list.append(f"- Image asset {i+1}: [{basename}](file:///{abs_path_str})")
    image_links = "\n".join(image_links_list)
    
    final_markdown_report = f"""# Daily Marketing Package: {today_str}
    
## Step 1 – Metadata & Summary
{selection_info}
    
---
    
## Step 2 – Campaign Copy (RoshinisInstagramSkill)
### Part 1: Creative & Objectives (Sections 1-6)
{campaign_part_1}

### Part 2: Captions, Hashtags & Stories (Sections 7-9)
{campaign_part_2}

### Part 3: Reels, Carousels & Strategy (Sections 10-12)
{campaign_part_3}
    
---
    
## Step 3 – Generated Visual Assets
{image_links}
"""
    
    with open(output_doc_path, "w", encoding="utf-8") as f:
        f.write(final_markdown_report)
    print(f"Final marketing package saved to {output_doc_path}")
    
    # Step 7: Send to Telegram
    lines = [line.strip() for line in selection_info.splitlines() if line.strip()]
    feat_product = "Roshini's Nutrimix"
    for line in lines:
        if "Featured Product" in line or "Product:" in line:
            feat_product = line.split(":", 1)[1].strip() if ":" in line else line
            break
            
    # Format and escape sections for direct HTML display
    feat_product_esc = escape_html(feat_product)
    feat_strategy_esc = escape_html(today_strategy)
    part_1_escaped = escape_html(campaign_part_1)
    part_2_escaped = escape_html(campaign_part_2)
    part_3_escaped = escape_html(campaign_part_3)
    
    # Helper to slice to Telegram's 4096 character limit
    def safe_slice(text):
        if len(text) > 4000:
            return text[:3900] + "\n\n<i>[Truncated due to Telegram limits]</i>"
        return text

    # Message 1: Overview & Part 1
    telegram_text_1 = safe_slice(f"""📅 <b>Daily Campaign Overview & Creative ({today_str})</b>

✅ <b>Featured Product:</b> {feat_product_esc}
✅ <b>Content Strategy:</b> {feat_strategy_esc}

━━━━━━━━━━━━━━━━━━━━━━━━━━

{part_1_escaped}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📷 <b>Generated Images Attached ({len(img_paths)} total)</b>
""")

    # Message 2: Part 2 (Caption, Hashtags & Story)
    telegram_text_2 = safe_slice(f"""📝 <b>Daily Campaign Caption & Story ({today_str})</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━

{part_2_escaped}
""")

    # Message 3: Part 3 (Reels, Carousels & Strategy)
    telegram_text_3 = safe_slice(f"""🎬 <b>Daily Campaign Reels, Carousels & Strategy ({today_str})</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━

{part_3_escaped}
""")
    
    print("Dispatching assets to Telegram...")
    # Send Part 1 + Image attachments + Marketing Package Document
    send_to_telegram_with_retry(telegram_text_1, output_doc_path, img_paths)
    
    # Send Part 2 (no attachments)
    send_to_telegram_with_retry(telegram_text_2, "", [])
    
    # Send Part 3 (no attachments)
    send_to_telegram_with_retry(telegram_text_3, "", [])
    
    print("Daily Marketing Engine run completed!")

if __name__ == "__main__":
    run_marketing_pipeline()
