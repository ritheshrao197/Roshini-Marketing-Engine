#!/usr/bin/env python3
"""
Daily Marketing Pipeline Runner

Orchestrates the complete marketing content generation workflow:
Research → Plan → Generate → Validate → Upload → Export → Notify → History
"""

import sys
import io
from pathlib import Path
import argparse
import os

# Force UTF-8 console encoding on Windows
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to the Python path and set it as the current directory
base_dir = Path(__file__).parent
sys.path.insert(0, str(base_dir))
os.chdir(str(base_dir))

# Import agents
from agent.research import research
from agent.planner import plan
from agent.content_generator import generate_content
from agent.seo_generator import generate_seo
from agent.image_prompt_generator import generate_image_prompts
from agent.duplicate_checker import check_duplicates
from agent.validator import validate
from agent.uploader import upload
from agent.exporter import export_package
from agent.telegram import notify
from agent.history import update_history
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger(__name__)


def run(config: Config):
    """
    Execute the complete marketing pipeline.
    
    Flow:
    1. Research → Load sources, RSS, APIs, collect today's insights
    2. Plan → Choose product, theme, persona, website topics
    3. Generate → Create Instagram posts, blogs, health tips, recipes
    4. SEO → Generate SEO metadata (title, slug, meta, keywords)
    5. Image Prompts → Generate prompts for Instagram, blog, recipe, hero
    6. Duplicate Check → Search existing blogs, avoid duplicates
    7. Validate → Grammar, SEO, medical claims, brand, category
    8. Upload → POST to backend with retries, save locally if fails
    9. Export → Generate YYYY-MM-DD.md package
    10. Notify → Send summary via Telegram with draft IDs
    11. History → Append date, product, topics, keywords, draft IDs
    """
    try:
        logger.info("="*60)
        logger.info("🚀 STARTING DAILY MARKETING PIPELINE")
        logger.info("="*60)
        
        # Step 1: Research
        logger.info("📊 Step 1: Researching...")
        research_data = research()
        logger.info(f"   ✅ Research complete: {len(research_data.get('topics', []))} topics found")
        
        # Step 2: Plan
        logger.info("📝 Step 2: Planning content...")
        plan_data = plan(research_data)
        logger.info(f"   ✅ Plan complete: {plan_data.get('product')} - {plan_data.get('theme')}")
        
        # Step 3: Generate Content
        logger.info("✍️ Step 3: Generating content...")
        content = generate_content(plan_data)
        logger.info(f"   ✅ Content generated: {len(content.get('blogs', []))} blogs, {len(content.get('recipes', []))} recipes")
        
        # Step 4: SEO
        logger.info("🔍 Step 4: Generating SEO metadata...")
        seo_data = generate_seo(content)
        logger.info(f"   ✅ SEO complete for {len(seo_data.get('pages', []))} pages")
        
        # Step 5: Image Prompts
        logger.info("🎨 Step 5: Generating image prompts...")
        image_prompts = generate_image_prompts(content, seo_data)
        logger.info(f"   ✅ {len(image_prompts)} image prompts generated")
        
        # Step 6: Duplicate Check
        logger.info("🔎 Step 6: Checking for duplicates...")
        content = check_duplicates(content, seo_data)
        logger.info(f"   ✅ Duplicate check complete")
        
        # Step 7: Validate
        logger.info("✅ Step 7: Validating content...")
        validation_results = validate(content, seo_data)
        logger.info(f"   ✅ Validation complete: {validation_results.get('passed', 0)} checks passed")
        
        # Step 8: Upload
        logger.info("📤 Step 8: Uploading to backend...")
        upload_results = upload(content, seo_data)
        draft_ids = upload_results.get('draft_ids', [])
        logger.info(f"   ✅ Upload complete: {len(draft_ids)} drafts uploaded")
        
        # Step 9: Export
        logger.info("💾 Step 9: Exporting package...")
        export_path = export_package(content, seo_data, upload_results)
        logger.info(f"   ✅ Package exported to {export_path}")
        
        # Step 10: Notify
        logger.info("📱 Step 10: Sending Telegram notification...")
        notify(content, seo_data, upload_results, export_path)
        logger.info(f"   ✅ Notification sent")
        
        # Step 11: History
        logger.info("📚 Step 11: Updating history...")
        update_history(content, seo_data, upload_results)
        logger.info(f"   ✅ History updated")
        
        logger.info("="*60)
        logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        summary = (
            f"\n\n📊 Summary:\n"
            f"   - Blogs generated: {len(content.get('blogs', []))}\n"
            f"   - Drafts uploaded: {len(draft_ids)}\n"
            f"   - Package: {export_path}\n"
            f"   - Draft IDs: {', '.join(draft_ids) if draft_ids else 'None'}\n"
        )
        logger.info(summary)
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\n❌ Pipeline failed: {e}")
        print("Check logs for details.\n")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Roshini Marketing Engine pipeline.")
    parser.add_argument(
        "--mode",
        type=str,
        default="daily",
        choices=["daily", "test"],
        help="The mode to run the pipeline in ('daily' or 'test')."
    )
    args = parser.parse_args()
    
    # Load environment
    config = Config.load_env()
    
    # Run pipeline
    success = run(config) # The 'mode' argument can be passed into run() if needed in the future
    sys.exit(0 if success else 1)