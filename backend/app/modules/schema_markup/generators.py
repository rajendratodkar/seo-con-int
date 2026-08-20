"""JSON-LD schema generators.

Each generator takes page data and returns a dict ready for json.dumps().
Generators follow schema.org specifications.
"""
from datetime import datetime, timezone


def generate_article(
    title: str,
    url: str,
    description: str | None = None,
    author_name: str | None = None,
    publisher_name: str | None = None,
    image_url: str | None = None,
    date_published: str | None = None,
    date_modified: str | None = None,
    site_name: str | None = None,
) -> dict:
    """Generate Article schema."""
    now = datetime.now(timezone.utc).isoformat()
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "url": url,
    }
    if description:
        schema["description"] = description
    if author_name:
        schema["author"] = {"@type": "Person", "name": author_name}
    if publisher_name:
        schema["publisher"] = {
            "@type": "Organization",
            "name": publisher_name,
        }
    if image_url:
        schema["image"] = image_url
    schema["datePublished"] = date_published or now
    schema["dateModified"] = date_modified or now
    if site_name:
        schema["mainEntityOfPage"] = {"@type": "WebPage", "@id": url}
    return schema


def generate_faq(items: list[dict], page_url: str | None = None) -> dict:
    """Generate FAQPage schema.

    items: list of {"question": str, "answer": str}
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [],
    }
    for item in items:
        schema["mainEntity"].append({
            "@type": "Question",
            "name": item["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item["answer"],
            },
        })
    return schema


def generate_howto(
    title: str,
    steps: list[dict],
    description: str | None = None,
    image_url: str | None = None,
    total_time: str | None = None,
) -> dict:
    """Generate HowTo schema.

    steps: list of {"name": str, "text": str, "image": str (optional)}
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": title,
    }
    if description:
        schema["description"] = description
    if image_url:
        schema["image"] = image_url
    if total_time:
        schema["totalTime"] = total_time  # ISO 8601 duration: PT1H30M

    schema["step"] = []
    for i, step in enumerate(steps, 1):
        s = {
            "@type": "HowToStep",
            "position": i,
            "name": step["name"],
            "text": step["text"],
        }
        if step.get("image"):
            s["image"] = step["image"]
        schema["step"].append(s)
    return schema


def generate_product(
    name: str,
    description: str | None = None,
    image_url: str | None = None,
    brand: str | None = None,
    sku: str | None = None,
    price: float | None = None,
    currency: str = "USD",
    availability: str = "https://schema.org/InStock",
    url: str | None = None,
) -> dict:
    """Generate Product schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
    }
    if description:
        schema["description"] = description
    if image_url:
        schema["image"] = image_url
    if brand:
        schema["brand"] = {"@type": "Brand", "name": brand}
    if sku:
        schema["sku"] = sku
    if price is not None:
        schema["offers"] = {
            "@type": "Offer",
            "price": price,
            "priceCurrency": currency,
            "availability": availability,
        }
    if url:
        schema["url"] = url
    return schema


def generate_breadcrumblist(items: list[dict]) -> dict:
    """Generate BreadcrumbList schema.

    items: list of {"name": str, "url": str}
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [],
    }
    for i, item in enumerate(items, 1):
        schema["itemListElement"].append({
            "@type": "ListItem",
            "position": i,
            "name": item["name"],
            "item": item["url"],
        })
    return schema


def generate_organization(
    name: str,
    url: str | None = None,
    logo_url: str | None = None,
    description: str | None = None,
    same_as: list[str] | None = None,
) -> dict:
    """Generate Organization schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": name,
    }
    if url:
        schema["url"] = url
    if logo_url:
        schema["logo"] = logo_url
    if description:
        schema["description"] = description
    if same_as:
        schema["sameAs"] = same_as
    return schema


# Registry of available generators
GENERATORS = {
    "Article": generate_article,
    "FAQPage": generate_faq,
    "HowTo": generate_howto,
    "Product": generate_product,
    "BreadcrumbList": generate_breadcrumblist,
    "Organization": generate_organization,
}
