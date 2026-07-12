# Public API Usage Guide

This guide documents the public blog APIs available in the backend.

Base URL examples:

- Production: `https://roshini-backend.onrender.com`
- Production API root: `https://roshini-backend.onrender.com/api`

The public content system uses both `vlogs` and `blogs` in endpoint names. In practice, these routes power the public **blog** experience.

## Live Backend Verification

Verified against the deployed backend on **July 12, 2026**:

- `GET /health` returned `200` with `{"status":"healthy"}`
- `GET /api/vlogs` returned `200` with published blog data
- `GET /api/vlogs/featured` returned `200` with an empty `vlogs` array at the time of testing
- `GET /api/vlog-categories` returned `200` with active categories

I did **not** execute public write endpoints like submit/import/like against production during verification, to avoid creating or mutating live content.

## Overview

Public APIs available today:

- Read published blog content
- Search and filter blog content
- Fetch categories
- Like a blog post
- Submit a blog for review
- Import one or many blog posts from external tools

## Content Model

A blog record can include:

- `title`
- `slug`
- `content`
- `excerpt`
- `image`
- `vCategory`
- `vTags`
- `seoTitle`
- `seoDescription`
- `seoKeywords`
- `canonicalUrl`
- `ogImage`
- `featured`
- `status`
- `isPublished`
- `publishDate`
- `likesCount`
- `viewCount`

## Read APIs

### 1. List published blogs

`GET /api/vlogs`

Query parameters:

- `page` - defaults to `1`
- `limit` - defaults to `10`
- `category` - category slug
- `tag` - tag slug
- `search` - text search across title/content
- `sort` - supports `latest`, `popular`, `featured`

Example:

```bash
curl "http://localhost:8000/api/vlogs?page=1&limit=9&search=millets&sort=latest"
```

Typical response shape:

```json
{
  "vlogs": [
    {
      "_id": "68723f1e12ab34cd56ef7890",
      "title": "Healthy Millet Breakfast Ideas",
      "slug": "healthy-millet-breakfast-ideas",
      "excerpt": "Quick breakfast ideas using millet and other natural ingredients.",
      "isPublished": true,
      "status": "Published",
      "publishDate": "2026-07-12T06:20:00.000Z",
      "likesCount": 4,
      "viewCount": 92,
      "featured": false,
      "vCategory": {
        "_id": "68723f1e12ab34cd56ef7001",
        "cName": "Recipes",
        "slug": "recipes"
      },
      "vTags": [
        {
          "_id": "68723f1e12ab34cd56ef7002",
          "name": "Millets",
          "slug": "millets"
        }
      ]
    }
  ],
  "totalCount": 1,
  "totalPages": 1,
  "currentPage": 1
}
```

### 2. Get featured blogs

`GET /api/vlogs/featured`

Returns up to 5 featured, published blog posts.

```bash
curl "http://localhost:8000/api/vlogs/featured"
```

### 3. Get latest blogs

`GET /api/vlogs/latest`

Returns up to 5 latest published blog posts.

```bash
curl "http://localhost:8000/api/vlogs/latest"
```

### 4. Get popular blogs

`GET /api/vlogs/popular`

Returns up to 5 published blog posts sorted by `viewCount`.

```bash
curl "http://localhost:8000/api/vlogs/popular"
```

### 5. Search blogs

`GET /api/vlogs/search`

Query parameters:

- `query` - required search term
- `page` - defaults to `1`
- `limit` - defaults to `10`

```bash
curl "http://localhost:8000/api/vlogs/search?query=organic&page=1&limit=10"
```

### 6. Get blogs by category

`GET /api/vlogs/category/:categorySlug`

Query parameters:

- `page`
- `limit`

```bash
curl "http://localhost:8000/api/vlogs/category/recipes?page=1&limit=6"
```

### 7. Get a single blog by slug

`GET /api/vlogs/:slug`

This endpoint also increments the blog's `viewCount`.

```bash
curl "http://localhost:8000/api/vlogs/healthy-millet-breakfast-ideas"
```

Typical response shape:

```json
{
  "vlog": {
    "_id": "68723f1e12ab34cd56ef7890",
    "title": "Healthy Millet Breakfast Ideas",
    "slug": "healthy-millet-breakfast-ideas",
    "content": "<h1>Healthy Millet Breakfast Ideas</h1><p>...</p>",
    "excerpt": "Quick breakfast ideas using millet and other natural ingredients.",
    "seoTitle": "Healthy Millet Breakfast Ideas | Roshini's Home Products",
    "seoDescription": "Quick breakfast ideas using millet and other natural ingredients.",
    "likesCount": 4,
    "viewCount": 93
  }
}
```

### 8. Get related blogs

`GET /api/vlogs/:id/related`

Returns up to 4 related posts using category or tag overlap.

```bash
curl "http://localhost:8000/api/vlogs/68723f1e12ab34cd56ef7890/related"
```

### 9. Get public blog categories

`GET /api/vlog-categories`

```bash
curl "http://localhost:8000/api/vlog-categories"
```

## Interaction API

### Like a blog

`POST /api/vlogs/:id/like`

```bash
curl -X POST "http://localhost:8000/api/vlogs/68723f1e12ab34cd56ef7890/like"
```

Typical response:

```json
{
  "success": "Vlog liked successfully",
  "likesCount": 5
}
```

## Public Submission APIs

These endpoints create blog entries in **draft/review** state for admin review. Public submissions are not published immediately.

### 1. Submit a blog

`POST /api/blogs/submit`

Alias:

- `POST /api/vlogs/submit`

Supported input:

- `title` - required
- `content` - required
- `category` - required
- `excerpt` - optional
- `tags` - optional array or comma-separated string
- `seoTitle` - optional
- `seoDescription` - optional
- `imageUrl` - optional remote image URL
- `thumbnail` - optional uploaded file via multipart form data

JSON example:

```bash
curl -X POST "http://localhost:8000/api/blogs/submit" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"7 Healthy Millet Snacks\",\"content\":\"<p>Millet snacks are easy to prepare.</p>\",\"category\":\"Health Tips\",\"tags\":[\"Millets\",\"Healthy Snacks\"],\"excerpt\":\"Easy and healthy millet snack ideas for busy families.\"}"
```

Multipart example with thumbnail:

```bash
curl -X POST "http://localhost:8000/api/blogs/submit" \
  -F "title=Summer Millet Recipes" \
  -F "category=Recipes" \
  -F "content=<p>Fresh millet recipes for summer meals.</p>" \
  -F "tags=[\"Recipes\",\"Summer\"]" \
  -F "thumbnail=@cover.jpg"
```

Typical success response:

```json
{
  "success": "Blog submitted successfully. It will be reviewed, edited, and published by an administrator.",
  "blog": {
    "_id": "68723f1e12ab34cd56ef7999",
    "title": "7 Healthy Millet Snacks",
    "slug": "7-healthy-millet-snacks",
    "excerpt": "Easy and healthy millet snack ideas for busy families.",
    "status": "Draft",
    "isPublished": false,
    "publishDate": null,
    "createdBy": null
  }
}
```

Validation notes:

- If `excerpt` is omitted, the API generates one from the content.
- If `category` does not exist, it can be created automatically.
- If `tags` do not exist, they can be created automatically.
- If the title slug already exists, the API appends `-1`, `-2`, and so on.

## Public Import APIs

These endpoints are useful for CMS migrations, AI tooling, or external publishing pipelines.

### 1. Import a single blog

`POST /api/blogs/import`

Alias:

- `POST /api/vlogs/import`

Supported input:

- `title` - required
- `content` - required
- `excerpt` - optional
- `format` - optional, use `markdown` to convert markdown to HTML
- `category` - optional, falls back to `General` if omitted
- `tags` - optional
- `seoTitle` - optional
- `seoDescription` - optional
- `seoKeywords` - optional array or parsable string
- `canonicalUrl` - optional
- `ogImage` - optional
- `imageUrl` - optional

JSON example:

```bash
curl -X POST "http://localhost:8000/api/blogs/import" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Healthy Millets for Growing Kids\",\"content\":\"# Healthy Millets\\n\\nMillets are rich in **proteins** and minerals.\",\"format\":\"markdown\",\"category\":\"Health Tips\",\"tags\":[\"Millets\",\"Protein\"],\"seoTitle\":\"Healthy Millets for Growing Kids\",\"seoDescription\":\"A quick guide to millet nutrition for children.\",\"seoKeywords\":[\"millet\",\"kids nutrition\",\"healthy food\"]}"
```

Typical success response:

```json
{
  "success": "Blog imported successfully as Draft",
  "blog": {
    "_id": "68723f1e12ab34cd56ef8001",
    "title": "Healthy Millets for Growing Kids",
    "slug": "healthy-millets-for-growing-kids",
    "status": "Draft",
    "isPublished": false
  }
}
```

### 2. Import multiple blogs in bulk

`POST /api/blogs/import/bulk`

Alias:

- `POST /api/vlogs/import/bulk`

Request body can be either:

- an object with `blogs: []`
- a raw array of blog objects

Example:

```bash
curl -X POST "http://localhost:8000/api/blogs/import/bulk" \
  -H "Content-Type: application/json" \
  -d "{\"blogs\":[{\"title\":\"Bulk Blog 1\",\"content\":\"<p>Bulk HTML blog 1</p>\",\"category\":\"Recipes\",\"tags\":[\"Recipes\",\"Healthy Meals\"]},{\"title\":\"Bulk Blog 2\",\"content\":\"## Sugar Free Millet Laddu\",\"format\":\"markdown\",\"category\":\"Recipes\",\"tags\":[\"Millets\",\"Organic\"]}]}"
```

Typical success response:

```json
{
  "success": "2 blogs imported successfully, 0 failed",
  "importedCount": 2,
  "failedCount": 0,
  "importedBlogs": [
    {
      "title": "Bulk Blog 1",
      "slug": "bulk-blog-1"
    },
    {
      "title": "Bulk Blog 2",
      "slug": "bulk-blog-2"
    }
  ],
  "errors": []
}
```

## Example Content Payloads

### HTML content sample

```json
{
  "title": "5 Quick Millet Breakfasts",
  "content": "<h1>5 Quick Millet Breakfasts</h1><p>These breakfast ideas are easy to make and naturally wholesome.</p><ul><li>Millet porridge</li><li>Vegetable millet upma</li></ul>",
  "category": "Recipes",
  "tags": ["Millets", "Breakfast"],
  "excerpt": "Five easy breakfast ideas using millet.",
  "seoTitle": "5 Quick Millet Breakfasts",
  "seoDescription": "Simple millet breakfast ideas for everyday cooking."
}
```

### Markdown content sample

```json
{
  "title": "Why Millets Are Good for Families",
  "content": "# Why Millets Are Good for Families\n\nMillets are rich in **fiber**, minerals, and plant-based nutrition.\n\n## Benefits\n\n- Easy to include in meals\n- Works well in snacks and breakfast\n- Useful for varied family diets",
  "format": "markdown",
  "category": "Health Tips",
  "tags": ["Nutrition", "Millets", "Family Health"]
}
```

## Error Responses

Common validation and error patterns:

```json
{
  "error": "Title, category, and content are required fields."
}
```

```json
{
  "error": "Title and content are required."
}
```

```json
{
  "error": "Vlog not found"
}
```

```json
{
  "error": "Category not found"
}
```

## Notes for Integrators

- Public submit/import endpoints create draft content by default.
- Single blog fetch uses the blog `slug`, while like/related routes use the blog database `id`.
- Search works in two ways:
  - `GET /api/vlogs?search=...`
  - `GET /api/vlogs/search?query=...`
- Naming uses `vlog` internally, but the user-facing feature is a blog system.
- The repository currently exposes REST routes directly and does not include a generated Swagger/OpenAPI document.
