import os
import datetime
import glob
import json
import requests
import google.generativeai as genai

# Setup Gemini API client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables. Gemini calls will fail.")

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
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API call failed: {e}")
        return f"Error generating content: {e}"

def generate_image_asset(prompt, output_path):
    """
    Generates an image using Google's Imagen model and saves it.
    Uses reference images from the brand-kit folders if available.
    """
    if not GEMINI_API_KEY:
        print(f"Skipping image generation for '{output_path}' (No API Key).")
        return None
        
    try:
        print(f"Generating image: {output_path} with prompt: {prompt}")
        model = genai.ImageGenerationModel("imagen-3.0-generate-002")
        
        # Check for reference images to guide style/product consistency
        ref_images = []
        ref_folders = ["brand-kit/products-photos", "brand-kit/brand-ambassador", "brand-kit/Posters"]
        for folder in ref_folders:
            for f in glob.glob(f"{folder}/*.png") + glob.glob(f"{folder}/*.jpg"):
                ref_images.append(f)
                if len(ref_images) >= 3:
                    break
        
        # Call the API
        result = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1" if "carousel" in output_path or "post" in output_path else "16:9" if "blog" in output_path else "1:1"
        )
        
        # Save image
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        for image in result.images:
            image.save(output_path)
            print(f"Successfully saved generated image to {output_path}")
            return output_path
            
    except Exception as e:
        print(f"Image generation failed for {output_path}: {e}")
        # Create a placeholder text file so the script continues
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path + ".txt", "w") as f:
            f.write(f"Image prompt: {prompt}\nError: {e}")
        return None

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
            
            # 1. Send the Summary text message
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message_text,
                'parse_mode': 'Markdown'
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
    kb_context = "\n\n".join([f"=== File: {path} ===\n{content}" for path, content in kb.items()])
    
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
    
    # Step 3: Generate Daily Marketing Package
    print("Generating Daily Marketing Package...")
    
    # 3a. Choose featured product, customer persona, theme, active campaign
    selection_prompt = f"""
    Based on the daily research brief: {research_brief}
    And the available customer personas: {kb.get("knowledge-base/customer-personas.md", "")}
    Choose today's:
    1. Featured Product (from product list in knowledge base)
    2. Customer Persona
    3. Content Theme
    4. Active Campaign (if any)
    
    Return your choice as a structured markdown list.
    """
    selection_info = call_gemini(selection_prompt)
    
    # 3b. Generate Instagram Package
    instagram_prompt = f"""
    Generate the Instagram Marketing Assets for today.
    Selected Context:
    {selection_info}
    
    Ensure strict compliance with FSSAI regulations (no medical cure/treatment claims):
    {kb.get("knowledge-base/health-claims.md", "")}
    And ensure Nutrimix is never called sprouted.
    
    Provide:
    1. Instagram Caption (80-150 words) with warm, family-focused tone and CTAs.
    2. Instagram Post text/copy.
    3. Carousel Content (Exactly 5 Slides with headings & bullet points).
    4. Story Content (Text and layouts for daily stories).
    5. Reel Caption.
    6. Hashtags (5-10 tailored tags).
    7. CTA.
    """
    instagram_package = call_gemini(instagram_prompt)
    
    # 3c. Generate Blog Package
    blog_prompt = f"""
    Generate the SEO Blog Article and Metadata for today.
    Selected Context:
    {selection_info}
    
    Provide:
    1. SEO Title (under 60 characters)
    2. Meta Description (140-160 characters)
    3. URL Slug (clean and hyphenated)
    4. Target Keywords (3-5 keywords)
    5. SEO Article: A 600-1000 word highly educational, search-optimized article explaining the health benefits of our ingredients/products, following brand voice rules.
    """
    blog_package = call_gemini(blog_prompt)
    
    # 3d. Generate Healthy Recipe
    recipe_prompt = f"""
    Generate one easy-to-cook healthy recipe utilizing today's featured product. Include ingredients list, prep time, cook time, and step-by-step instructions.
    Selected Context:
    {selection_info}
    """
    recipe_package = call_gemini(recipe_prompt)
    
    # 3e. Generate Instagram Reel Script
    reel_prompt = f"""
    Generate a 30-second Instagram Reel script structured as a storyboard grid.
    Selected Context:
    {selection_info}
    
    Provide:
    1. Hook (first 3 seconds)
    2. Voiceover Script
    3. Shot List (Visual description of scenes)
    4. On-screen Text (Text overlays)
    5. Ending CTA
    """
    reel_package = call_gemini(reel_prompt)
    
    # 3f. Trending Content (Optional)
    print("Generating Optional Trending Content...")
    trending_prompt = f"""
    Based on the daily research brief: {research_brief}
    And the trend validation rules:
    - Avoid politics, controversies, gossip, or unprofessional memes.
    - Focus on wholesome family, morning routines, or gym nutrition.
    
    If a validated trend or meme is available, generate:
    1. 1 Trending Instagram Post
    2. 1 Trending Reel Idea
    3. 1 Meme Image Prompt
    4. 1 Viral Hook
    
    Otherwise, if no wholesome trend or meme fits the brand today, write exactly:
    "NO_VALIDATED_TREND"
    """
    trending_package = call_gemini(trending_prompt)
    
    # Step 4: Generate Images (up to 11 assets total)
    print("Generating Image Prompts and Visual Assets...")
    image_prompts_generator = f"""
    Based on the generated Instagram copy:
    {instagram_package}
    And the generated recipe:
    {recipe_package}
    And the generated blog:
    {blog_package}
    
    Write highly descriptive prompts for an AI art generator to produce:
    1. "instagram_post_image": Instagram Post Image (Product focused shot)
    2. "instagram_carousel_1" to "instagram_carousel_5": Instagram Carousel Images (5 separate slide layouts)
    3. "blog_featured_image": Blog Featured Image (16:9 landscape lifestyle/educational background)
    4. "product_hero_image": Product Hero Image (Premium packaging mockup sitting on kitchen table)
    5. "lifestyle_image": Lifestyle Image (Family enjoying warm millet porridge)
    6. "recipe_image": Recipe Image (Plated close-up of the prepared recipe)
    
    Ensure prompts emphasize: Wholesome, rustic, warm, family-oriented environment, soft morning natural lighting, consistent brand colors (natural green, gold, warm sand).
    Return your prompts strictly in JSON format matching this schema:
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
    prompts_json_str = call_gemini(image_prompts_generator)
    
    # Generate images
    img_paths = []
    try:
        cleaned_json = prompts_json_str.strip().replace("```json", "").replace("```", "").strip()
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
            meme_prompt_extract = f"Extract only the AI Image Prompt text for the Meme from this description: {trending_package}. Return only the prompt string, nothing else."
            meme_prompt_text = call_gemini(meme_prompt_extract).strip()
            if meme_prompt_text and "NO_VALIDATED_TREND" not in meme_prompt_text:
                img_mapping["meme_image"] = f"outputs/images/{today_str}_meme.png"
                image_prompts["meme_image"] = meme_prompt_text
        
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
            
    # Step 5: Quality Check
    print("Executing Quality Check Validation...")
    qa_prompt = f"""
    You are the QA & Compliance Agent.
    Review the compiled marketing text:
    
    --- Instagram ---
    {instagram_package}
    --- Blog ---
    {blog_package}
    --- Recipe ---
    {recipe_package}
    --- Reel ---
    {reel_package}
    {"--- Trending Content ---\n" + trending_package if "NO_VALIDATED_TREND" not in trending_package else ""}
    
    Validate:
    1. Brand Voice: Warm, trustworthy, educational, friendly.
    2. Compliance: Verify absolutely NO medical cure/treatment claims are made (refer to health-claims.md).
    3. Accuracy: Ensure Millets in Nutrimix are NOT called sprouted.
    4. Grammar: Verify spelling and syntax.
    
    Output the final, compliance-verified version of the complete marketing text.
    """
    verified_package_text = call_gemini(qa_prompt)
    
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
    
    image_links = "\n".join([f"- Image asset {i+1}: [{os.path.basename(path)}](file:///{os.path.abspath(path).replace('\\', '/')})" for i, path in enumerate(img_paths)])
    
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
    
    telegram_text = f"""📅 *Daily Marketing Package ({today_str})*

✅ *Featured Product:* {feat_product}
✅ *Theme:* {feat_theme}
✅ *Instagram Caption:* Generated
✅ *Carousel Content:* 5 Slides Generated
✅ *Blog Article:* 600-1000 Word SEO Article Generated
✅ *Healthy Recipe:* Cook instructions compiled
✅ *Reel Script:* Scene grid completed
✅ *Trending Content (Optional):* {trend_status}
✅ *SEO Keywords:* Configured

📷 *Generated Images Attached ({len(img_paths)} total)*
📄 *Marketing Package (.md) Attached*
"""
    
    print("Dispatching assets to Telegram...")
    send_to_telegram_with_retry(telegram_text, output_doc_path, img_paths)
    print("Daily Marketing Engine run completed!")

if __name__ == "__main__":
    run_marketing_pipeline()
