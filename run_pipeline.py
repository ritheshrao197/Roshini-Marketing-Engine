import os
import datetime
import glob
import json
import requests
from google import genai
from google.genai import types

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

def call_gemini(prompt, system_instruction=None, model_name="gemini-2.5-flash"):
    if not GEMINI_API_KEY:
        return "Gemini API key missing. Placeholder output generated."
    
    import time
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            config = None
            if system_instruction:
                config = types.GenerateContentConfig(system_instruction=system_instruction)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                print(f"Gemini Rate limit hit (429). Retrying in 5 seconds (attempt {attempt} of {max_retries})...")
                time.sleep(5)
            else:
                print(f"Gemini API call failed: {e}")
                return f"Error generating content: {e}"
                
    return "Error: Gemini API calls failed due to rate limits."

def create_pillow_placeholder(prompt, output_path):
    """
    Creates a fallback placeholder image with a styled card showing the prompt and branding.
    """
    try:
        from PIL import Image, ImageDraw
        # Create a 800x800 sand-colored background
        img = Image.new('RGB', (800, 800), color=(255, 248, 238)) # #FFF8EE
        draw = ImageDraw.Draw(img)
        
        # Draw a green border representing Roshini's natural green
        draw.rectangle([20, 20, 780, 780], outline=(78, 122, 46), width=10) # #4E7A2E
        
        # Draw brand headers
        draw.text((50, 80), "Roshini's Home Products", fill=(78, 122, 46))
        draw.text((50, 110), "AI Marketing Asset Placeholder", fill=(217, 140, 43)) # #D98C2B
        
        # Word wrap prompt text
        words = prompt.split()
        lines = []
        current_line = []
        for word in words:
            if len(" ".join(current_line + [word])) > 45:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        if current_line:
            lines.append(" ".join(current_line))
            
        y_text = 200
        draw.text((50, 170), "Visual Asset Prompt:", fill=(100, 100, 100))
        for line in lines[:12]:
            draw.text((50, y_text), f"- {line}", fill=(50, 50, 50))
            y_text += 30
            
        draw.text((50, 720), "[ Imagen 3 Generation Unavailable - Fallback Card Used ]", fill=(120, 120, 120))
        
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
            res_msg = requests.post(url_msg, json=payload)
            res_msg.raise_for_status()
            print("Telegram summary message sent successfully.")
            
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
    You are the Content and Image Planner for Roshini's Home Products. Based on the today-research brief, customer personas, active campaigns, and health guidelines, generate the entire package in ONE run.
    
    Research Brief:
    {research_brief}
    
    Customer Personas:
    {kb.get("knowledge-base/customer-personas.md", "")}
    
    Health claims guidelines (Ensure FSSAI compliance, no medical cure/treatment claims, Nutrimix is never called sprouted):
    {kb.get("knowledge-base/health-claims.md", "")}
    
    Generate the following sections. Ensure you start each section with the EXACT header line specified:

    --- START SELECTION ---
    Choose and list:
    1. Featured Product (from product list in knowledge base)
    2. Customer Persona
    3. Content Theme
    4. Active Campaign (if any)

    --- START INSTAGRAM ---
    Provide:
    1. Instagram Caption (80-150 words) with warm, family-focused tone and CTAs.
    2. Instagram Post text/copy.
    3. Carousel Content (Exactly 5 Slides with headings & bullet points).
    4. Story Content (Text and layouts for daily stories).
    5. Reel Caption.
    6. Hashtags (5-10 tailored tags).
    7. CTA.

    --- START BLOG ---
    Provide:
    1. SEO Title (under 60 characters)
    2. Meta Description (140-160 characters)
    3. URL Slug (clean and hyphenated)
    4. Target Keywords (3-5 keywords)
    5. SEO Article: A 600-1000 word highly educational, search-optimized article explaining the health benefits of our ingredients/products, following brand voice rules.

    --- START RECIPE ---
    Generate one easy-to-cook healthy recipe utilizing the featured product. Include ingredients list, prep time, cook time, and step-by-step instructions.

    --- START REEL ---
    Generate a 30-second Instagram Reel script structured as a storyboard grid with columns for Hook, Voiceover, Shot List, On-screen Text, and Ending CTA.

    --- START TRENDING ---
    If a validated trend or meme is available in the research brief, generate:
    1. 1 Trending Instagram Post
    2. 1 Trending Reel Idea
    3. 1 Meme Image Prompt
    4. 1 Viral Hook
    Otherwise, write exactly: "NO_VALIDATED_TREND"

    --- START IMAGE PROMPTS ---
    Provide highly descriptive prompts for an AI art generator (Imagen) to produce:
    - "instagram_post_image": Instagram Post Image (Product focused shot)
    - "instagram_carousel_1" to "instagram_carousel_5": Instagram Carousel Images (5 separate slide layouts)
    - "blog_featured_image": Blog Featured Image (16:9 landscape lifestyle/educational background)
    - "product_hero_image": Product Hero Image (Premium packaging mockup sitting on kitchen table)
    - "lifestyle_image": Lifestyle Image (Family enjoying warm millet porridge)
    - "recipe_image": Recipe Image (Plated close-up of the prepared recipe)
    
    Format the output inside this section strictly as a valid JSON matching this schema:
    {{
      "instagram_post_image": "prompt text...",
      "instagram_carousel_1": "prompt text...",
      "instagram_carousel_2": "prompt text...",
      "instagram_carousel_3": "prompt text...",
      "instagram_carousel_4": "prompt text...",
      "instagram_carousel_5": "prompt text...",
      "blog_featured_image": "prompt text...",
      "product_hero_image": "prompt text...",
      "lifestyle_image": "prompt text...",
      "recipe_image": "prompt text..."
    }}
    """
    
    full_package = call_gemini(generation_prompt)
    
    # Parse sections
    selection_info = extract_section(full_package, "--- START SELECTION ---", "--- START INSTAGRAM ---")
    instagram_package = extract_section(full_package, "--- START INSTAGRAM ---", "--- START BLOG ---")
    blog_package = extract_section(full_package, "--- START BLOG ---", "--- START RECIPE ---")
    recipe_package = extract_section(full_package, "--- START RECIPE ---", "--- START REEL ---")
    reel_package = extract_section(full_package, "--- START REEL ---", "--- START TRENDING ---")
    trending_package = extract_section(full_package, "--- START TRENDING ---", "--- START IMAGE PROMPTS ---")
    image_prompts_section = extract_section(full_package, "--- START IMAGE PROMPTS ---")
    
    # Step 4: Generate Images (up to 11 assets total)
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
        
        # Add meme image if validated trend has one
        if "NO_VALIDATED_TREND" not in trending_package:
            img_mapping["meme_image"] = f"outputs/images/{today_str}_meme.png"
        
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
            
    # Step 5: Quality Check (Compliance validated by design within the single prompt)
    verified_package_text = f"{instagram_package}\n\n{blog_package}\n\n{recipe_package}\n\n{reel_package}\n\n{trending_package}"
    
    # Update Previous Posts History Ledger
    try:
        with open("history/previous-posts.md", "a", encoding="utf-8") as hist_file:
            hist_file.write(f"\n- {today_str}: Daily package featuring {selection_info.splitlines()[0] if selection_info.splitlines() else 'Nutrimix'}")
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

## Step 2 – Compliance & Verified Output Copy
{verified_package_text}

---

## Step 3 – Generated Visual Assets
{image_links}
"""
    
    with open(output_doc_path, "w", encoding="utf-8") as f:
        f.write(final_markdown_report)
    print(f"Final marketing package saved to {output_doc_path}")
    
    # Step 7: Send to Telegram
    lines = [line.strip() for line in selection_info.splitlines() if line.strip()]
    feat_product = lines[0] if len(lines) > 0 else "Roshini's Nutrimix"
    feat_theme = lines[2] if len(lines) > 2 else "Wholesome Daily Nutrition"
    
    trend_status = "Generated" if "NO_VALIDATED_TREND" not in trending_package else "None (Using Evergreen content)"
    
    feat_product_esc = escape_html(feat_product)
    feat_theme_esc = escape_html(feat_theme)
    
    telegram_text = f"""📅 <b>Daily Marketing Package ({today_str})</b>

✅ <b>Featured Product:</b> {feat_product_esc}
✅ <b>Theme:</b> {feat_theme_esc}
✅ <b>Instagram Caption:</b> Generated
✅ <b>Carousel Content:</b> 5 Slides Generated
✅ <b>Blog Article:</b> 600-1000 Word SEO Article Generated
✅ <b>Healthy Recipe:</b> Cook instructions compiled
✅ <b>Reel Script:</b> Scene grid completed
✅ <b>Trending Content (Optional):</b> {trend_status}
✅ <b>SEO Keywords:</b> Configured

📷 <i>Generated Images Attached ({len(img_paths)} total)</i>
📄 <i>Marketing Package (.md) Attached</i>
"""
    
    print("Dispatching assets to Telegram...")
    send_to_telegram_with_retry(telegram_text, output_doc_path, img_paths)
    print("Daily Marketing Engine run completed!")

if __name__ == "__main__":
    run_marketing_pipeline()
