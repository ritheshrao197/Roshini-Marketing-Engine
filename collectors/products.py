"""
Product Collector - Gathers product-related data and competitor info.
"""

import os
from typing import Dict, Any, List

from utils.logger import get_logger

logger = get_logger(__name__)


class ProductCollector:
    """Collects product information from the knowledge base."""

    def collect(self) -> List[Dict[str, Any]]:
        """Collect product data from knowledge-base/products."""
        logger.info("Collecting product data...")
        products = []
        products_dir = "knowledge-base/products"
        if os.path.exists(products_dir):
            for filename in os.listdir(products_dir):
                if filename.endswith('.md'):
                    filepath = os.path.join(products_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        products.append({
                            "name": filename.replace('.md', ''),
                            "content": f.read(),
                            "source": filepath
                        })
        logger.info(f"Collected {len(products)} products")
        return products
