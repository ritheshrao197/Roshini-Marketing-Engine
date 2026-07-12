import os

PRODUCT_ASSETS = {
    "chia-seeds": {
        "package": "brand-kit/products-photos/Roshinis_Chia_Seeds_Transparent_Pouch.png",
        "colors": ["#4E7A2E", "#D98C2B"],
        "ingredients": ["organic chia seeds"]
    },
    "flax-seeds": {
        "package": "brand-kit/products-photos/Roshinis_Flax_Seeds_Transparent_Pouch.png",
        "colors": ["#4E7A2E", "#D98C2B"],
        "ingredients": ["organic brown flax seeds"]
    },
    "pumpkin-seeds": {
        "package": "brand-kit/products-photos/Roshinis_Pumpkin_Seeds_Transparent_Pouch.png",
        "colors": ["#4E7A2E", "#D98C2B"],
        "ingredients": ["organic raw pumpkin seeds"]
    },
    "sunflower-seeds": {
        "package": "brand-kit/products-photos/Roshinis_Sunflower_Seeds_Transparent_Pouch.png",
        "colors": ["#4E7A2E", "#D98C2B"],
        "ingredients": ["organic raw sunflower seeds"]
    },
    "sathvik7": {
        "package": None,
        "colors": ["#4E7A2E", "#D98C2B"],
        "ingredients": ["pumpkin seeds", "sunflower seeds", "chia seeds", "flax seeds", "watermelon seeds", "white sesame seeds", "roasted almonds"]
    },
    "nutrimix": {
        "package": None, # Fallback to logo / text layout
        "colors": ["#4E7A2E", "#D98C2B"],
        "ingredients": ["sprouted ragi", "sprouted jowar", "sprouted green gram", "roasted almonds", "cashews", "cardamom"]
    }
}

def resolve_product_assets(product_name: str) -> dict:
    """
    Normalizes a product name/slug and returns resolved brand assets
    such as packaging filepaths, color schemes, and ingredients.
    """
    if not product_name:
        product_name = "nutrimix"
        
    normalized = product_name.lower().strip().replace(" ", "").replace("-", "").replace("'", "")
    
    matched_key = None
    for key in PRODUCT_ASSETS.keys():
        key_norm = key.replace("-", "").replace("_", "")
        if key_norm in normalized or normalized in key_norm:
            matched_key = key
            break
            
    if matched_key:
        assets = PRODUCT_ASSETS[matched_key].copy()
    else:
        # Default fallback asset spec
        assets = {
            "package": None,
            "colors": ["#4E7A2E", "#D98C2B"],
            "ingredients": []
        }
        
    # Inject standard global branding components
    assets["logo_white"] = "brand-kit/Logo white version.png"
    assets["logo_color"] = "brand-kit/Logo.png"
    assets["logo_mark_white"] = "brand-kit/Logo mark white.png"
    assets["logo_mark_color"] = "brand-kit/logo mark.png"
    assets["style_guide"] = "brand-kit/style-guide.md"
    assets["color_guidelines"] = "brand-kit/color-guidelines.md"
    
    return assets
