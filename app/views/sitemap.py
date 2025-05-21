from flask import Blueprint, Response
from datetime import datetime

sitemap_bp = Blueprint('sitemap', __name__)

@sitemap_bp.route('/robots.txt')
def robots_txt():
    content = """User-agent: *
Disallow: /static/
Disallow: /uploads/
Disallow: /admin/
Allow: /

Sitemap: https://www.ttcoach.ch/sitemap.xml
"""
    return Response(content, mimetype='text/plain')





@sitemap_bp.route('/sitemap.xml')
def sitemap():
    base_url = "https://www.ttcoach.ch"
    lastmod = datetime.now().date().isoformat()

    # Liste statique ou à compléter dynamiquement
    routes = [
        {'loc': f"{base_url}/", 'priority': '1.0'},
        {'loc': f"{base_url}/recherche", 'priority': '0.8'},
        {'loc': f"{base_url}/messagerie/discussion", 'priority': '0.5'},
    ]

    xml_routes = [
        f"""<url>
  <loc>{r['loc']}</loc>
  <lastmod>{lastmod}</lastmod>
  <changefreq>weekly</changefreq>
  <priority>{r['priority']}</priority>
</url>""" for r in routes
    ]

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(xml_routes)}
</urlset>"""

    return Response(sitemap_xml, mimetype='application/xml')
