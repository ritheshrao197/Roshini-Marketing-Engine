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
from agent.content_loader import check_existing_content
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger(__name__)


def run(config: Config, force: bool = False, upload_only: bool = False):
    """
    Execute the complete marketing pipeline.
    
    Args:
        config: Configuration object.
        force: Force regeneration even if content exists.
        upload_only: Skip generation, just upload existing content.
    
    Flow:
    0. Check if content already exists for today
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
        if force:
            logger.info("   ⚠️ FORCE MODE: Regenerating content")
        if upload_only:
            logger.info("   📤 UPLOAD ONLY MODE: Skipping generation")
        logger.info("="*60)
        
        # Step 0: Check for existing content (unless force mode)
        logger.info("🔍 Step 0: Checking for existing content today...")
        import datetime
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        output_dir = config.get('OUTPUT_DIR', 'outputs')
        json_package_path = f"{output_dir}/{date_str}.json"
        md_package_path = f"{output_dir}/{date_str}.md"
        
        exists = False
        content = None
        seo_data = None
        package_path = None
        
        if os.path.exists(json_package_path) and not force:
            try:
                with open(json_package_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                # Re-generate/validate SEO mapping for compatibility
                seo_data = generate_seo(content)
                package_path = md_package_path
                exists = True
                logger.info(f"📦 JSON content package already exists for today: {json_package_path}")
            except Exception as e:
                logger.warning(f"Failed to load existing JSON package: {e}. Falling back to parsing MD.")
                
        if not exists and not force:
            # Fallback check
            exists, content, seo_data, package_path = check_existing_content()
        
        if exists and not force:
            logger.info(f"📦 Content already exists for today! Skipping generation.")
            logger.info(f"   Found: {len(content.get('blogs', []))} articles/blogs")
            
            # Just upload and notify
            upload_results = {"uploaded": [], "failed": [], "draft_ids": []}
            
            # Step 8: Upload existing content
            logger.info("📤 Re-uploading to backend...")
            upload_results = upload(content, seo_data)
            draft_ids = upload_results.get('draft_ids', [])
            logger.info(f"   ✅ Upload complete: {len(draft_ids)} drafts uploaded")
            
            # Step 10: Notify with existing content
            logger.info("📱 Sending Telegram notification...")
            notify(content, seo_data, upload_results, package_path)
            logger.info(f"   ✅ Notification sent")
            
            # Step 11: Update history
            logger.info("📚 Updating history...")
            update_history(content, seo_data, upload_results)
            logger.info(f"   ✅ History updated")
            
            logger.info("="*60)
            logger.info("🎉 PIPELINE COMPLETED (USED EXISTING CONTENT)!")
            logger.info("="*60)
            summary = (
                f"\n\n📊 Summary (Existing Content):\n"
                f"   - Articles: {len(content.get('blogs', []))}\n"
                f"   - Drafts uploaded: {len(draft_ids)}\n"
                f"   - Package: {package_path}\n"
                f"   - Draft IDs: {', '.join(draft_ids) if draft_ids else 'None'}\n"
            )
            logger.info(summary)
            
            return True
        
        if upload_only and not exists:
            logger.error("❌ Upload-only mode but no existing content found!")
            return False
        
        if upload_only and exists:
            logger.info(f"📤 Upload-only mode: Uploading {len(content.get('blogs', []))} articles...")
            upload_results = upload(content, seo_data)
            draft_ids = upload_results.get('draft_ids', [])
            
            logger.info("📱 Sending Telegram notification...")
            notify(content, seo_data, upload_results, package_path)
            
            logger.info("📚 Updating history...")
            update_history(content, seo_data, upload_results)
            
            logger.info("="*60)
            logger.info("🎉 UPLOAD ONLY COMPLETED!")
            logger.info("="*60)
            return True
        
        logger.info("🆕 No existing content found or force mode. Generating new content...")
        
        # Step 1: Research
        logger.info("📊 Step 1: Researching...")
        research_data = research()
        logger.info(f"   ✅ Research complete: {len(research_data.get('trendingTopics', []))} trending topics found")
        
        # Step 2: Plan
        logger.info("📝 Step 2: Planning content...")
        plan_data = plan(research_data)
        logger.info(f"   ✅ Plan complete: {plan_data.get('product')} - {plan_data.get('theme')}")
        
        # Step 3: Duplicate Check (runs on plan_data before generating full articles)
        logger.info("🔎 Step 3: Checking for duplicates in planned articles...")
        plan_data = check_duplicates(plan_data)
        logger.info(f"   ✅ Duplicate check complete and plan updated")
        
        # Step 4: Generate Content
        logger.info("✍️ Step 4: Generating content campaign...")
        content = generate_content(plan_data)
        logger.info(f"   ✅ Content generated: {len(content.get('blogs', []))} articles")
        
        # Step 5: SEO Validation and Correction (Generates missing values in-place)
        logger.info("🔍 Step 5: Validating and correcting SEO metadata...")
        seo_data = generate_seo(content)
        logger.info(f"   ✅ SEO checks and corrections complete")
        
        # Step 6: Image Prompts compatibility helper
        logger.info("🎨 Step 6: Compiling image prompts...")
        image_prompts = generate_image_prompts(content, seo_data)
        content['image_prompts'] = image_prompts
        logger.info(f"   ✅ {len(image_prompts)} image prompts registered")
        
        # Step 7: Validate Content Quality (Grammar, Brand, Medical claims)
        logger.info("✅ Step 7: Validating content quality...")
        validation_results = validate(content, seo_data)
        logger.info(f"   ✅ Validation complete: {validation_results.get('passed', 0)} checks passed")
        
        # Step 8: Upload Articles
        logger.info("📤 Step 8: Uploading to backend individually...")
        upload_results = upload(content, seo_data)
        draft_ids = upload_results.get('draft_ids', [])
        logger.info(f"   ✅ Upload complete: {len(draft_ids)} drafts uploaded")
        
        # Step 9: Export Files
        logger.info("💾 Step 9: Exporting packages (.md, .json, -api.json)...")
        export_path = export_package(content, seo_data, upload_results)
        logger.info(f"   ✅ Package exported to {export_path}")
        
        # Step 10: Telegram Notification
        logger.info("📱 Step 10: Sending Telegram notification...")
        notify(content, seo_data, upload_results, export_path)
        logger.info(f"   ✅ Notification sent")
        
        # Step 11: History Ledger Update
        logger.info("📚 Step 11: Updating history ledger JSON...")
        update_history(content, seo_data, upload_results)
        logger.info(f"   ✅ History updated")
        
        logger.info("="*60)
        logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        summary = (
            f"\n\n📊 Summary:\n"
            f"   - Articles generated: {len(content.get('blogs', []))}\n"
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if content exists for today."
    )
    parser.add_argument(
        "--upload-only",
        action="store_true",
        help="Skip generation, just upload existing content."
    )
    args = parser.parse_args()
    
    # Load environment
    config = Config.load_env()
    
    # Run pipeline
    success = run(config, force=args.force, upload_only=args.upload_only)
    sys.exit(0 if success else 1)