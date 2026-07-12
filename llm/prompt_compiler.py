import os

def compile_image_prompt(spec: dict, resolved_assets: dict) -> str:
    """
    Converts a structured JSON scene specification into a highly descriptive
    250-600 word advertising image prompt.
    """
    if not isinstance(spec, dict):
        return str(spec)
        
    creative = spec.get("creative_direction", {})
    img_spec = spec.get("image_specification", {})
    if not img_spec:
        # Fallback in case of flat dictionary structure
        img_spec = spec
        
    subject = img_spec.get("subject", "Roshini's product packaging")
    camera = img_spec.get("camera", "50mm lens, f/2.8 aperture, Canon EOS R5, HDR")
    lighting = img_spec.get("lighting", "warm golden morning sunlight coming from the side")
    background = img_spec.get("background", "softly blurred cozy kitchen setting with warm earthy beige tones")
    composition = img_spec.get("composition", "front-facing, centered, occupying 45% of the frame")
    
    ingredients_list = img_spec.get("ingredients", [])
    if not ingredients_list:
        ingredients_list = resolved_assets.get("ingredients", [])
    ingredients_str = ", ".join(ingredients_list) if ingredients_list else ""
    
    props_list = img_spec.get("props", [])
    props_str = ", ".join(props_list) if props_list else ""
    
    branding = img_spec.get("branding", "official Roshini Home Products logo mark")
    quality = img_spec.get("quality", "8K resolution, ultra-realistic textures, magazine-quality photography")
    output_style = img_spec.get("output_style", "photorealistic commercial food photography, professional food styling")
    
    # Resolve file references for the prompt conceptually
    package_file = resolved_assets.get("package")
    package_ref = f"exact pouch asset '{os.path.basename(package_file)}'" if package_file else "premium stand-up pouch packaging"
    logo_ref = f"official brand logo white version '{os.path.basename(resolved_assets.get('logo_white', 'Logo.png'))}'"
    
    # Structure the prompt (approx. 250-600 words)
    long_prompt = (
        f"{output_style}. "
        f"This is a premium commercial advertisement. "
        f"The primary subject is: {subject}. Specifically, render the {package_ref} with high-fidelity detail, "
        f"preserving the exact layout, colors, and graphics. "
        f"Branding Integration: The {logo_ref} must be clearly visible, crisp, and never modified or redesigned. "
        f"Ensure the brand green (#4E7A2E) and gold (#D98C2B) accents are faithfully preserved in the product colors and theme. "
        f"Composition: The product pouch is {composition}. It sits on a handcrafted teak wooden tabletop with rich natural grain. "
    )
    
    if ingredients_str:
        long_prompt += (
            f"Artfully arranged around the base of the product pouch are premium, raw, organic ingredients: {ingredients_str}. "
            f"These ingredients must look fresh, natural, and styled by a professional food stylist. "
        )
    if props_str:
        long_prompt += (
            f"Props included in the scene: {props_str}. "
            f"Arrange them naturally to tell a story of {creative.get('story', 'wholesome family wellness')} and evoke a feeling of {creative.get('emotion', 'healthy premium living')}."
        )
        
    long_prompt += (
        f"Lighting: The scene is illuminated by {lighting}. This creates soft, natural shadows and beautiful specular highlights. "
        f"Camera parameters: Shot with a {camera}. Use a shallow depth of field, rendering a {background}. "
        f"Overall aesthetic: {quality}. Leave negative space in the upper third of the composition for marketing copy overlays. "
        f"Strictly avoid any CGI look, plastic-looking food, or watermarks. Make the textures look organic, realistic, and premium."
    )
    
    return long_prompt

def get_standard_negative_prompt() -> str:
    """
    Returns the standard negative prompt to filter out low-quality outputs.
    """
    return (
        "No fake logos, no extra packages, no duplicate products, no blurry objects, "
        "no plastic-looking food, no CGI look, no unrealistic colors, no watermarks, "
        "no extra text, no cropped products, no deformed packaging, no wrong ingredients, "
        "no low quality, no hands unless specified, no AI artifacts, no misspelled labels."
    )
