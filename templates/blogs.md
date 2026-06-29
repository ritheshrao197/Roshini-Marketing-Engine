# SEO Blog Article & Metadata Template

Use this blueprint to generate structured, SEO-optimized blog posts that rank on Google Search and funnel organic traffic to product landing pages.

---

## 1. Metadata Block
Every blog must begin with this structured SEO block:

- **Primary Target Keyword:** (From `knowledge-base/customer-personas.md` or SEO targets)
- **Secondary Keywords:** (3-5 relevant queries)
- **Proposed URL Slug:** Clean, lowercase, hyphen-separated. E.g. `/why-sprouted-millets-are-superfoods`
- **SEO Title:** (Under 60 characters, containing primary keyword at the beginning)
- **Meta Description:** (140-160 characters, high click-through rate hook, ends with a CTA)
- **Featured Image Alt Text:** Descriptive, keyword-rich description of featured image.

---

## 2. Blog Structure & Layout Guidelines

- **H1 Header (Main Title):** Warm, engaging, containing primary keyword.
- **Introduction (100-150 words):** Hook the reader immediately by speaking to their pain points (tiredness, parenting stress). Introduce the traditional solution early.
- **H2 Header: The Problem State:** Explain the downsides of modern dietary habits (refined sugar, chemical preservatives).
- **H2 Header: The Nutritional Science:** Detail how traditional ingredients or sprouting solve the problem (incorporate phytic acid info, mineral bioavailability, sprouted benefits). Use bullet points and bold key text.
- **H3 Header: Spotlights:** Focus on specific ingredients (Ragi, almonds, walnuts).
- **H2 Header: Standard Recipe / Preparation:** Share a fast, easy recipe utilizing Nutrimix.
- **H2 Header: Frequently Asked Questions:** Answer 2-3 common queries in simple terms (refer to `knowledge-base/faq.md`).
- **Conclusion & Product Funnel CTA (100 words):** Pivot back to Roshini's Homemade Nutrimix. Emphasize purity, fresh-to-order preparation, and small home-batch care. Add a direct purchase link.

---

## 3. FAQ Schema JSON-LD Template
Every blog post must end with a valid FAQ Page schema block for Google search result rich snippets:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "FAQ QUESTION 1 TEXT",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "FAQ ANSWER 1 TEXT"
      }
    },
    {
      "@type": "Question",
      "name": "FAQ QUESTION 2 TEXT",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "FAQ ANSWER 2 TEXT"
      }
    }
  ]
}
</script>
```

---

## 4. Internal & External Linking Guidelines
- **Internal Links:** Always insert at least 2 links to other internal assets:
  - Link to the **Nutrimix Product Page** using anchor text like "fresh sprouted nutrimix" or "homemade ragi malt".
  - Link to a **Recipe Page** using anchors like "easy millet smoothie recipe" or "kids sprouted ragi laddu".
- **External Links:** Provide 1-2 outbound links to authority health/government resources (such as `www.nin.res.in`, `fssai.gov.in`, or healthline articles) to validate scientific claims.
