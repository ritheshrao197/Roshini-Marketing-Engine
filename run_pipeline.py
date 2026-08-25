#!/usr/bin/env python3
"""
Daily Instagram Content Pipeline Runner

Orchestrates the daily Instagram content workflow:
Research → Generate post → Generate image → Export → Notify → History
"""

import sys
import io
import json
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
from agent.instagram_generator import generate_daily_instagram_post
from llm.image_generator import generate_image
from agent.exporter import export_package
from agent.telegram import notify
from agent.history import update_history
from utils.files import ensure_directory
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger(__name__)


def run(config: Config, force: bool = False):
    """
    Execute the daily Instagram content pipeline.

    Args:
        config: Configuration object.
        force: Force regeneration even if content exists for today.

    Flow:
    0. Check if today's post already exists
    1. Research → season/festival/product-rotation context
    2. Generate → topic, English + Kannada captions, hashtags, image prompt
    3. Image → render the actual Instagram image from the prompt
    4. Export → outputs/YYYY-MM-DD.md and .json
    5. Notify → send the image + captions via Telegram
    6. History → append today's post metadata
    """
    try:
        logger.info("=" * 60)
        logger.info("🚀 STARTING DAILY INSTAGRAM PIPELINE")
        if force:
            logger.info("   ⚠️ FORCE MODE: Regenerating content")
        logger.info("=" * 60)

        import datetime
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        output_dir = Config.get('OUTPUT_DIR', 'outputs')
        json_package_path = f"{output_dir}/{date_str}.json"
        md_package_path = f"{output_dir}/{date_str}.md"
        image_path = f"{output_dir}/images/{date_str}.png"

        # Step 0: Reuse today's post if it already exists (unless forced)
        if os.path.exists(json_package_path) and not force:
            logger.info(f"📦 Today's post already exists: {json_package_path}. Skipping generation.")
            with open(json_package_path, 'r', encoding='utf-8') as f:
                post = json.load(f)

            existing_image = post.get('imagePath')
            existing_image = existing_image if existing_image and os.path.exists(existing_image) else None

            logger.info("📱 Sending Telegram notification...")
            notify(post, existing_image, md_package_path)
            logger.info("   ✅ Notification sent")

            logger.info("=" * 60)
            logger.info("🎉 PIPELINE COMPLETED (USED EXISTING CONTENT)!")
            logger.info("=" * 60)
            return True

        logger.info("🆕 No existing post found or force mode. Generating new content...")

        # Step 1: Research
        logger.info("📊 Step 1: Researching...")
        research_data = research()
        logger.info(f"   ✅ Research complete: {len(research_data.get('trendingTopics', []))} trending topics found")

        # Step 2: Generate Instagram post content
        logger.info("✍️ Step 2: Generating Instagram post content...")
        post = generate_daily_instagram_post(research_data)
        logger.info(f"   ✅ Content generated: [{post.get('contentType')}] {post.get('topic')}")

        # Step 3: Generate the actual image
        logger.info("🎨 Step 3: Generating image...")
        ensure_directory(f"{output_dir}/images")
        generated_image_path = generate_image(post['imagePrompt'], image_path)
        if generated_image_path:
            logger.info(f"   ✅ Image generated: {generated_image_path}")
        else:
            logger.warning("   ⚠️ Image generation failed; continuing without an image.")

        # Step 4: Export Files
        logger.info("💾 Step 4: Exporting package (.md, .json)...")
        export_path = export_package(post, generated_image_path)
        logger.info(f"   ✅ Package exported to {export_path}")

        # Step 5: Telegram Notification
        logger.info("📱 Step 5: Sending Telegram notification...")
        notify(post, generated_image_path, export_path)
        logger.info("   ✅ Notification sent")

        # Step 6: History Ledger Update
        logger.info("📚 Step 6: Updating history ledger JSON...")
        update_history(post)
        logger.info("   ✅ History updated")

        logger.info("=" * 60)
        logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        summary = (
            f"\n\n📊 Summary:\n"
            f"   - Content type: {post.get('contentType')}\n"
            f"   - Topic: {post.get('topic')}\n"
            f"   - Image: {generated_image_path or 'Not generated'}\n"
            f"   - Package: {export_path}\n"
        )
        logger.info(summary)

        return True

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\n❌ Pipeline failed: {e}")
        print("Check logs for details.\n")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Roshini Instagram content pipeline.")
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
    args = parser.parse_args()

    # Load environment
    config = Config.load_env()

    # Run pipeline
    success = run(config, force=args.force)
    sys.exit(0 if success else 1)
