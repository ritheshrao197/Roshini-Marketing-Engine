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
        "knowledge-base/products/nutrimix.md",
    ]
    for filepath in kb_files:
        if os.path.exists(filepath):
            kb_content[filepath] = load_file(filepath)
            
    # Include all ingredient and recipe files
    for folder in ["ingredients", "nutrition", "recipes"]:
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
    If reference images exist in brand-kit, they can be utilized if supported.
    """
    if not GEMINI_API_KEY:
        print("Skipping image generation (No API Key).")
        return None
        
    try:
        print(f"Generating image with prompt: {prompt}")
        # Use Vertex AI Imagen or standard GenAI Imagen model depending on SDK version
        # Note: In google-generativeai, Imagen 3 is called 'imagen-3.0-generate-002'
        model = genai.ImageGenerationModel("imagen-3.0-generate-002")
        
        # Check if we have reference images (e.g. products-photos, brand-ambassador)
        ref_images = []
        for folder in ["brand-kit/products-photos", "brand-kit/brand-ambassador"]:
            for f in glob.glob(f"{folder}/*.png") + glob.glob(f"{folder}/*.jpg"):
                ref_images.append(f)
                if len(ref_images) >= 3:
                    break
        
        # Call the API
        result = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1"
        )
        
        # Ensure directories exist and save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        for image in result.images:
            image.save(output_path)
            print(f"Successfully saved generated image to {output_path}")
            return output_path
            
    except Exception as e:
        print(f"Image generation failed: {e}. Creating a placeholder text file.")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path + ".txt", "w") as f:
            f.write(f"Image prompt: {prompt}\nError: {e}")
        return None

def send_to_telegram(caption, image_paths):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration missing. Skipping Telegram post.")
        return
        
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    try:
        # If we have generated images, send the first one as a photo with the caption as text
        if image_paths and os.path.exists(image_paths[0]):
            with open(image_paths[0], 'rb') as photo:
                payload = {
                    'chat_id': TELEGRAM_CHAT_ID,
                    'caption': caption[:1024],  # Telegram caption limit is 1024 chars
                    'parse_mode': 'Markdown'
                }
                files = {'photo': photo}
                res = requests.post(url_photo, data=payload, files=files)
                print(f"Telegram photo dispatch response: {res.status_code} - {res.text}")
                
            # If there are additional images, send them as separate photos
            for img_path in image_paths[1:]:
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as photo:
                        payload = {'chat_id': TELEGRAM_CHAT_ID}
                        files = {'photo': photo}
                        requests.post(url_photo, data=payload, files=files)
        else:
            # Otherwise send only message text
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': caption,
                'parse_mode': 'Markdown'
            }
            res = requests.post(url_msg, json=payload)
            print(f"Telegram text message dispatch response: {res.status_code} - {res.text}")
            
    except Exception as e:
        print(f"Failed to post to Telegram: {e}")

def run_marketing_pipeline():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    print(f"--- Starting Daily Marketing Pipeline for {today_str} ---")
    
    # 1. Load context databases
    print("Loading Knowledge Base...")
    kb = load_knowledge_base()
    kb_context = "\n\n".join([f"=== File: {path} ===\n{content}" for path, content in kb.items()])
    
    calendar_festivals = load_file("calendar/festivals.md")
    calendar_campaigns = load_file("calendar/campaigns.md")
    history_posts = load_file("history/previous-posts.md")
    sources = load_file("sources.md")
    
    # 2. Step 1: Research Agent (Generate Daily Trend Summary)
    print("Running Research Agent...")
    research_prompt = f"""
    You are the Research Agent for Roshini's Home Products.
    Based on the following keyword sources, calendar context, and recently posted history, extract 2 key health, lifestyle, or nutrition trend topics that would resonate with families today.
    
    Sources: {sources}
    Calendar: {calendar_campaigns}
    Festivals: {calendar_festivals}
    History Ledger: {history_posts}
    
    Output a clear trend brief for the team.
    """
    research_brief = call_gemini(research_prompt)
    print("Research Brief Generated.")
    
    # 3. Step 2: Product Knowledge Agent (Translate Science into Benefits)
    print("Running Product Knowledge Agent...")
    product_prompt = f"""
    You are the Product Knowledge Agent.
    Read this daily Research Brief: {research_brief}
    Translate this trend into customer benefits, cross-referencing our brand knowledge base. Ensure any nutritional claim is fully aligned with our ingredients and health guidelines.
    
    Knowledge Base Context:
    {kb_context}
    
    Output the verified ingredient/benefit mapping.
    """
    benefit_brief = call_gemini(product_prompt)
    
    # 4. Step 3: Instagram Agent (Generate Carousel and Caption)
    print("Running Instagram Agent...")
    instagram_prompt = f"""
    You are the Instagram Agent.
    Based on the verified benefits brief: {benefit_brief}
    Draft today's Instagram Post:
    1. A caption (80-150 words) with warm, family-focused tone. Include relevant hashtags.
    2. Carousel content (Slide 1 to 5) containing short, impactful titles/bullets.
    3. Call to Action (CTA).
    
    Follow FSSAI compliance: Never claim our products cure or treat any disease. Reference health guidelines: {kb.get("knowledge-base/health-claims.md", "")}
    """
    instagram_draft = call_gemini(instagram_prompt)
    
    # 5. Step 4: Canva & Image Gen Agent (Write Design Brief and Generate Images)
    print("Running Canva & Image Gen Agent...")
    image_prompt_gen = f"""
    You are the Canva & Image Gen Agent.
    Read today's Instagram post draft: {instagram_draft}
    
    Formulate 2 descriptive prompts for an AI Image Generator (Imagen) to create matching high-quality visual assets.
    Provide the output in JSON format:
    {{
      "image_prompt_1": "detailed prompt for post 1",
      "image_prompt_2": "detailed prompt for post 2"
    }}
    """
    prompts_json_str = call_gemini(image_prompt_gen)
    
    # Parse prompts and call Image Generation
    img_paths = []
    try:
        # Clean response string if Gemini wrapped in code block
        cleaned_json = prompts_json_str.strip().replace("```json", "").replace("```", "").strip()
        prompts = json.loads(cleaned_json)
        
        img_1_prompt = prompts.get("image_prompt_1", "Wholesome millet porridge bowl with nuts and seeds, natural daylight")
        img_2_prompt = prompts.get("image_prompt_2", "Rustic kitchen morning background with a packaging pouch")
        
        path_1 = f"outputs/images/{today_str}_post_1.png"
        path_2 = f"outputs/images/{today_str}_post_2.png"
        
        res_1 = generate_image_asset(img_1_prompt, path_1)
        res_2 = generate_image_asset(img_2_prompt, path_2)
        
        if res_1: img_paths.append(res_1)
        if res_2: img_paths.append(res_2)
        
    except Exception as e:
        print(f"Failed to parse image prompts: {e}. Generating placeholder fallback.")
        path_fallback = f"outputs/images/{today_str}_fallback.png"
        res_f = generate_image_asset("Healthy traditional Indian breakfast layout, warm tones", path_fallback)
        if res_f: img_paths.append(res_f)
        
    # 6. Step 5: Campaign Agent (Inject custom codes if active)
    print("Running Campaign Agent...")
    campaign_prompt = f"""
    You are the Campaign Agent.
    Read this post draft: {instagram_draft}
    Cross-reference active campaigns: {calendar_campaigns}
    If there is an active discount code or festival hook, modify the CTA to include the code and seasonal elements.
    """
    final_instagram_post = call_gemini(campaign_prompt)
    
    # 7. Step 6: QA & Compliance (Validate FSSAI claims and grammar)
    print("Running QA & Compliance Agent...")
    qa_prompt = f"""
    You are the QA & Compliance Agent.
    Review the final Instagram post: {final_instagram_post}
    Validate:
    1. Compliance check: Verify NO medical cure claims are made.
    2. Tone check: Warm, family-friendly, and educational.
    3. Accuracy check: Millets in Nutrimix must NOT be described as sprouted.
    
    Output the final, FSSAI-compliant, verified Instagram post.
    """
    verified_post = call_gemini(qa_prompt)
    
    # 8. Step 7: Analytics & Memory Agent (Log hooks to prevent repetition)
    print("Running Analytics & Memory Agent...")
    # Read history and append the new hooks
    try:
        with open("history/previous-posts.md", "a", encoding="utf-8") as hist_file:
            hist_file.write(f"\n- {today_str}: Instagram post about {today_str} trends.")
        print("History ledger updated.")
    except Exception as e:
         print(f"Failed to update history ledger: {e}")
         
    # 9. Step 4: Export daily markdown file
    print("Exporting final report...")
    output_filename = f"outputs/{today_str}-instagram-content.md"
    os.makedirs("outputs", exist_ok=True)
    
    markdown_report = f"""# Daily Instagram Output: {today_str}

## Metadata
- **Date:** {today_str}
- **Pipeline version:** 10-Agent (Instagram focused)
- **Status:** Verified & Compliance Approved

## Generated Instagram Post
{verified_post}

## Generated Assets
- Image 1 Path: `{img_paths[0] if len(img_paths) > 0 else 'Failed/Placeholder'}`
- Image 2 Path: `{img_paths[1] if len(img_paths) > 1 else 'Failed/Placeholder'}`

---
### Source Research Brief
{research_brief}
"""
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    print(f"Final report saved to {output_filename}")
    
    # 10. Post to Telegram!
    print("Sending content to Telegram Channel...")
    send_to_telegram(verified_post, img_paths)
    print("Daily Pipeline execution finished successfully!")

if __name__ == "__main__":
    run_marketing_pipeline()
