#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""Fill the database with demo content for the public site: company info
(logo, cover, gallery), categories, products with photos, slider and banners.

Photos are downloaded from Wikimedia Commons (freely licensed) and stored
through media_access.save_upload, exactly like uploads from the console.
Safe to re-run: rows that already exist (same slug / title) are skipped.

    backend/venv/bin/python -m backend.src.seed_demo
    backend/venv/bin/python -m backend.src.seed_demo --refresh-photos   # re-apply the curated photos
"""

import io
import json
import logging
import subprocess
import sys
import time
import urllib.parse

from datetime import datetime

from PIL import Image, ImageDraw
from werkzeug.datastructures import FileStorage

from backend.src.crm.web import app
from backend.src.model import Banner, Category, Product, SliderItem
from backend.src.model import (banner_access, category_access, company_access, company_image_access,
                               media_access, product_access, slider_access)

log = logging.getLogger(__name__)

USERNAME = 'admin'
# Wikimedia's policy wants a descriptive UA; generic ones get HTTP 429.
USER_AGENT = 'AluFactoryDemoSeed/1.0 (local demo data script; https://www.mediawiki.org/wiki/API:Etiquette)'
COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
THUMB_WIDTH = 1600

# Hand-picked, freely licensed photos on Wikimedia Commons ("Quality images").
PHOTO = {
    'sparks': 'File:Starý most Bratislava odstranovanie.jpg',
    'facade_lvm_1': 'File:Münster, LVM-Versicherung -- 2017 -- 6848.jpg',
    'facade_lvm_2': 'File:Münster, LVM -- 2017 -- 6351-7.jpg',
    'facade_lvm_3': 'File:Münster, LVM -- 2017 -- 9343-7.jpg',
    'office_lvm': 'File:Münster, LVM, Bürogebäude -- 2013 -- 5149-51.jpg',
    'post_tower': 'File:Bonn, Post-Tower -- 2017 -- 2128 (bw).jpg',
    'honeycomb': 'File:Sunlight on the curved honeycomb glass façade of the hotel Andaz mixed with interior lighting at sunset in Singapore.jpg',
    'toronto': 'File:Glass facades in downtown Toronto.jpg',
    'london': 'File:Ayuntamiento y Shard, Londres, Inglaterra, 2014-08-11, DD 076.JPG',
    'stamford': 'File:Swissôtel The Stamford reflecting in the water.jpg',
    'polyhedral': 'File:Lighted polyhedral building Louis Vuitton in Singapore.jpg',
    'den_haag': 'File:Den Haag Paleis van Justitie 2025-06-16.jpg',
    'frost_windows': 'File:Windows of the Frost Building (Toronto, Canada).jpg',
    'westlotto_1': 'File:Münster, Westdeutsche Lotterie -- 2018 -- 0417.jpg',
    'westlotto_2': 'File:Münster, WestLotto -- 2013 -- 3296.jpg',
    'melrose': 'File:Melrose Building -- Houston.jpg',
    'air_ducts': 'File:Air duct pipes at Viborg Katedralskole.jpg',
    'colour_pipes': 'File:Warm und kalt IMGP7847.jpg',
    'red_pipes': 'File:Haltern am See, Silbersee III, Rohre -- 2021 -- 4533.jpg',
    'rusty_pipes': 'File:Haltern am See, Silbersee III, Rohre -- 2025 -- 8549.jpg',
    'perforated': 'File:Kopenhagen (DK), Nyhavn -- 2017 -- 1711.jpg',
    'cladding': 'File:Fassadenverkleidung einer Turnhalle.jpg',
    'glass_hall': 'File:Christchurch Town Hall of the Performing Arts, New Zealand.jpg',
    'steam_engine': 'File:Gmunden Gisela Dampfmaschine von 1870-2695.jpg',
    'blast_furnace': 'File:Duisburg, Landschaftspark Duisburg-Nord, Hochofen 2 -- 2016 -- 1115.jpg',
    'dosing': 'File:Dülmen, Privatrösterei Schröer, Kaffeebehälter -- 2018 -- 0529.jpg',
    'clockwork': 'File:Dülmen, Heilig-Kreuz-Kirche, Uhrwerk -- 2019 -- 3056.jpg',
    'tool_hall': 'File:Haltern am See, Sythen, Werkzeughalle der Quarzwerke -- 2015 -- 4984.jpg',
    'welder_rebar': 'File:Payvandlash jarayoni.jpg',
    'welder_team': 'File:Welding Work in Isla Margarita.jpg',
    'welder_site': 'File:Rekonstrukce Nábřeží Kapitána Jaroše, svářeč.jpg',
    'logistics': 'File:Rhenus, Frankfurt am Main (P1032698).jpg',
    'glass_pavilion': 'File:Münster, Freiherr-vom-Stein-Haus -- 2021 -- 9042-6.jpg',
    'wall_detail': 'File:Cape Town (ZA), Waterfront, Clock Tower, Detail -- 2024 -- 2911.jpg',
    'etched_bar': 'File:Aluminium bar surface etched.jpg',
    'heatsinks': 'File:Black anodised aluminium heatsinks 6.5–35 mm width.jpg',
}

# Photos per product slug.
PRODUCT_PHOTOS = {
    'af-70-thermal-window': ['frost_windows', 'office_lvm'],
    'af-45-cold-window': ['westlotto_1', 'facade_lvm_3'],
    'af-75-entrance-door': ['glass_hall', 'westlotto_2'],
    'af-50-interior-door': ['glass_pavilion'],
    'af-fx-curtain-wall': ['facade_lvm_1', 'toronto', 'post_tower'],
    'af-ux-unitized-facade': ['honeycomb', 'london'],
    'af-160-lift-slide': ['westlotto_2', 'glass_pavilion'],
    'af-sl-slim-slide': ['facade_lvm_2'],
    't-slot-profile-4040': ['tool_hall', 'etched_bar'],
    'heatsink-profile-hs-120': ['heatsinks'],
    'glass-balustrade-gb-10': ['melrose'],
    'picket-railing-pr-40': ['den_haag'],
    'acp-4-mm-pvdf': ['cladding', 'wall_detail'],
    'acp-mirror-series': ['polyhedral', 'honeycomb'],
    'aluminium-sheet-1050-h14': ['etched_bar', 'cladding'],
    'checker-plate-5-bar': ['perforated'],
    'round-tube-6063': ['air_ducts', 'red_pipes'],
    'rectangular-tube-6040': ['rusty_pipes', 'colour_pipes'],
    'door-handle-set-dh-1': ['wall_detail'],
    'epdm-gasket-kit': ['dosing'],
}

CATEGORIES = [
    ('Window Systems', 'window-systems', 'Thermally broken and cold aluminium window profiles for residential and commercial buildings.'),
    ('Door Systems', 'door-systems', 'Entrance, interior and hinged aluminium door systems.'),
    ('Facade Systems', 'facade-systems', 'Stick and unitized curtain wall facades for modern architecture.'),
    ('Sliding Systems', 'sliding-systems', 'Lift-and-slide and parallel sliding systems for large openings.'),
    ('Industrial Profiles', 'industrial-profiles', 'Structural and T-slot aluminium profiles for machines and automation.'),
    ('Railings & Balustrades', 'railings', 'Aluminium and glass railings for balconies, stairs and terraces.'),
    ('Composite Panels', 'composite-panels', 'Aluminium composite panels (ACP) for cladding and signage.'),
    ('Sheets & Coils', 'sheets-coils', 'Rolled aluminium sheets, plates and coils in various alloys.'),
    ('Pipes & Tubes', 'pipes-tubes', 'Round, square and rectangular aluminium tubes.'),
    ('Accessories', 'accessories', 'Hardware, seals, handles and fixings for aluminium systems.'),
]

# Two products per category: (name, short description, description); photos in PRODUCT_PHOTOS.
PRODUCTS = {
    'window-systems': [
        ('AF-70 Thermal Window', 'Energy-efficient 70 mm window system with thermal break.',
         'A three-chamber 70 mm window system with polyamide thermal break.\n\n'
         'Uw from 1.3 W/m²K, glazing 24–50 mm, EPDM gaskets.\nSuitable for turn-tilt, casement and fixed windows.'),
        ('AF-45 Cold Window', 'Economical system for balconies and internal partitions.',
         'Non-insulated 45 mm system for balconies, shop fronts and internal partitions.\n\n'
         'Glazing 4–24 mm, fast assembly, wide choice of RAL colours.'),
    ],
    'door-systems': [
        ('AF-75 Entrance Door', 'Insulated heavy-duty entrance door for public buildings.',
         'A 75 mm insulated door system designed for high-traffic entrances.\n\n'
         'Leaf weight up to 180 kg, concealed hinges, panic hardware ready.'),
        ('AF-50 Interior Door', 'Slim aluminium door for offices and interiors.',
         'Minimalist 50 mm frame for office doors and glass partitions.\n\nSingle or double leaf, glazing up to 32 mm.'),
    ],
    'facade-systems': [
        ('AF-FX Curtain Wall', 'Stick curtain wall with 50 mm visible width.',
         'Mullion-transom facade system with 50 mm sight lines.\n\n'
         'Structural glazing option, spans up to 6 m, tested for wind and water tightness.'),
        ('AF-UX Unitized Facade', 'Prefabricated facade units for high-rise buildings.',
         'Factory-assembled facade modules for fast installation on high-rise projects.\n\n'
         'Units up to 1.8 × 4.2 m, pressure-equalised joints.'),
    ],
    'sliding-systems': [
        ('AF-160 Lift & Slide', 'Large sliding doors up to 400 kg per sash.',
         'Lift-and-slide system for panoramic openings.\n\nSash weight up to 400 kg, threshold 20 mm, thermal break.'),
        ('AF-SL Slim Slide', 'Minimal 20 mm interlock for maximum glass.',
         'Ultra-slim sliding system with 20 mm central interlock.\n\nMulti-track configurations, concealed frame option.'),
    ],
    'industrial-profiles': [
        ('T-Slot Profile 40×40', 'Modular profile for frames, guards and workstations.',
         '40×40 mm T-slot profile, slot 8, anodised finish.\n\nCut to length, compatible with standard fasteners.'),
        ('Heatsink Profile HS-120', 'Extruded heatsink for LED and power electronics.',
         '120 mm wide heatsink profile with 18 fins.\n\nAlloy 6063-T5, natural or black anodised.'),
    ],
    'railings': [
        ('Glass Balustrade GB-10', 'Frameless glass railing with base shoe profile.',
         'Base-shoe balustrade for 12–21.5 mm laminated glass.\n\nFloor or side mounting, stainless or aluminium cap rail.'),
        ('Picket Railing PR-40', 'Classic railing for balconies and stairs.',
         'Powder-coated aluminium picket railing, maintenance free.\n\nModular posts every 1.2 m, any RAL colour.'),
    ],
    'composite-panels': [
        ('ACP 4 mm PVDF', 'Aluminium composite panel with PVDF coating.',
         '4 mm panel with 0.5 mm aluminium skins and PE or FR core.\n\nPVDF coating, 20-year colour warranty.'),
        ('ACP Mirror Series', 'High-gloss mirror finish panels for interiors and signage.',
         'Mirror-finish composite panels in silver, gold and bronze.\n\nEasy to route, fold and bend.'),
    ],
    'sheets-coils': [
        ('Aluminium Sheet 1050 H14', 'General-purpose sheet with excellent formability.',
         'Alloy 1050 H14, thickness 0.5–6 mm, sizes 1000×2000 and 1250×2500 mm.'),
        ('Checker Plate 5 Bar', 'Anti-slip tread plate for floors and vehicles.',
         'Five-bar pattern tread plate, alloy 3105, thickness 1.5–5 mm.'),
    ],
    'pipes-tubes': [
        ('Round Tube 6063', 'Seamless extruded round tubes.',
         'Outer diameter 10–200 mm, wall 1–10 mm, alloy 6063-T6.'),
        ('Rectangular Tube 60×40', 'Structural rectangular hollow section.',
         '60×40 mm, wall 2–4 mm, lengths up to 6 m.'),
    ],
    'accessories': [
        ('Door Handle Set DH-1', 'Ergonomic handle set for aluminium doors.',
         'Aluminium lever handles with rosettes, fits standard profile cylinders.'),
        ('EPDM Gasket Kit', 'Weather seals for windows, doors and facades.',
         'Glazing and frame gaskets in EPDM, UV and ozone resistant, sold per 100 m.'),
    ],
}

SLIDES = [
    ('Aluminium solutions built to last', 'Profiles, facades and custom products — from design to delivery.', '/products', 'sparks'),
    ('Facades that define skylines', 'Curtain wall systems engineered for modern architecture.', '/products?category=facade-systems', 'facade_lvm_3'),
    ('Windows and doors for every climate', 'Thermally broken systems with outstanding energy efficiency.', '/products?category=window-systems', 'office_lvm'),
    ('Precision extrusion', 'Industrial profiles made to your drawings and tolerances.', '/products?category=industrial-profiles', 'welder_site'),
    ('Talk to our engineers', 'We help you choose the right system for your project.', '/contact', 'stamford'),
]

# (title, subtitle, product slug or None, link url, photo key)
BANNERS = [
    ('New: AF-FX Curtain Wall', 'Slim 50 mm sight lines for maximum daylight.', 'af-fx-curtain-wall', None, 'facade_lvm_1'),
    ('Lift & Slide up to 400 kg', 'Panoramic openings without compromise.', 'af-160-lift-slide', None, 'westlotto_2'),
    ('Custom colours in any RAL', 'Powder coating and anodising in our own shop.', None, '/about', 'colour_pipes'),
    ('Request a project quote', 'Send us your drawings — we reply within 24 hours.', None, '/contact', 'toronto'),
]

GALLERY = [('welder_team', 'Our team at work'), ('welder_site', 'On-site welding'), ('welder_rebar', 'Reinforcement works'),
           ('tool_hall', 'Tool hall'), ('dosing', 'Dosing equipment'), ('clockwork', 'Precision mechanics'),
           ('steam_engine', 'Machine maintenance'), ('logistics', 'Logistics centre'), ('air_ducts', 'Ventilation systems'),
           ('heatsinks', 'Anodised profiles')]
COVER_PHOTO = 'blast_furnace'

COMPANY = {
    'company_name': 'Alu Factory',
    'email': 'info@alu-factory.example',
    'phone': '+993 12 34 56 78',
    'address': 'Industrial zone, Ashgabat, Turkmenistan',
    'latitude': 37.9601,
    'longitude': 58.3261,
    'description': 'Alu Factory produces aluminium profiles and building systems: windows, doors, facades, '
                   'railings and industrial extrusions.\n\n'
                   'Our plant covers the full cycle — extrusion, powder coating, anodising, machining and assembly. '
                   'Every batch passes quality control in our own laboratory before it leaves the factory.\n\n'
                   'We work with architects, contractors and manufacturers, offering engineering support from the '
                   'first sketch to delivery on site.',
}


def _http_get(url, timeout=60):
    # curl: Python 3.9's urllib keeps failing with IncompleteRead on the
    # Commons API's chunked responses.
    return subprocess.run(['curl', '-sfL', '--retry', '4', '--retry-all-errors', '-m', str(timeout),
                           '-A', USER_AGENT, url],
                          check=True, capture_output=True).stdout


_media_by_key = {}


def photo_url(title):
    """1600px thumbnail URL of a Commons file."""
    params = {'action': 'query', 'format': 'json', 'titles': title,
              'prop': 'imageinfo', 'iiprop': 'url', 'iiurlwidth': THUMB_WIDTH}
    data = json.loads(_http_get(COMMONS_API + '?' + urllib.parse.urlencode(params)))
    page = next(iter(data['query']['pages'].values()))
    info = page['imageinfo'][0]
    return info.get('thumburl') or info['url']


def save_media(content, filename, alt_text):
    storage = FileStorage(stream=io.BytesIO(content), filename=filename)
    media = media_access.save_upload(storage, app.config['MEDIA_UPLOAD_FOLDER'], alt_text, USERNAME)
    if media is None:
        raise ValueError('not an image: %s' % filename)
    return media


def photo(key, alt_text):
    """Media row for PHOTO[key]; each photo is downloaded once per run."""
    if key not in _media_by_key:
        _media_by_key[key] = save_media(_http_get(photo_url(PHOTO[key])), '%s.jpg' % key, alt_text)
        time.sleep(1)  # be polite to Wikimedia
    return _media_by_key[key]


def _drop_unused(media_ids):
    for media_id in media_ids:
        if media_id is not None:
            media_access.delete_if_unused(media_id, app.config['MEDIA_UPLOAD_FOLDER'], USERNAME)


def make_logo():
    """Brand mark (same design as BrandLogo.vue) as a 512×512 PNG."""
    size = 512
    gradient = Image.new('RGB', (size, size))
    stops = [(0.0, (0x43, 0x61, 0xee)), (0.55, (0x3a, 0x86, 0xff)), (1.0, (0x4c, 0xc9, 0xf0))]
    pixels = gradient.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
                if t <= t1:
                    k = (t - t0) / (t1 - t0)
                    pixels[x, y] = tuple(round(a + (b - a) * k) for a, b in zip(c0, c1))
                    break
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=140, fill=255)
    logo = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    logo.paste(gradient, (0, 0), mask)

    draw = ImageDraw.Draw(logo)
    s = size / 40
    width = round(3.2 * s)
    draw.line([(11 * s, 29 * s), (20 * s, 10 * s), (29 * s, 29 * s)], fill='white', width=width, joint='curve')
    for x, y in ((11 * s, 29 * s), (29 * s, 29 * s), (20 * s, 10 * s)):
        draw.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill='white')
    draw.line([(15 * s, 22.5 * s), (25 * s, 22.5 * s)], fill=(255, 255, 255, 180), width=width)
    for x in (15 * s, 25 * s):
        draw.ellipse((x - width / 2, 22.5 * s - width / 2, x + width / 2, 22.5 * s + width / 2), fill=(255, 255, 255, 180))

    buffer = io.BytesIO()
    logo.save(buffer, 'PNG')
    return buffer.getvalue()


def seed_company():
    company = company_access.get()
    fields = dict(COMPANY)
    if company is None or company.logo_media_id is None:
        fields['logo_media_id'] = save_media(make_logo(), 'logo.png', 'Alu Factory logo').id
    if company is None or company.cover_media_id is None:
        fields['cover_media_id'] = photo(COVER_PHOTO, 'Alu Factory plant').id
    if company is None:
        company_access.add(fields, USERNAME)
    else:
        company_access.edit(company, fields, USERNAME)
    print('company: %s' % fields['company_name'])

    if not company_image_access.list_all():
        for i, (key, caption) in enumerate(GALLERY):
            company_image_access.add({'media_id': photo(key, caption).id, 'caption': caption,
                                      'sort_order': i, 'is_active': True}, USERNAME)
        print('gallery: %s images' % len(GALLERY))


def seed_catalog():
    for sort, (name, slug, description) in enumerate(CATEGORIES):
        category = Category.query.filter(Category.slug == slug).first()
        if category is None:
            category_access.add(name, slug, description, True, sort, USERNAME)
            category = Category.query.filter(Category.slug == slug).first()

        items = [p for p in PRODUCTS[slug] if not product_access.slug_exists(_slug(p[0]))]
        if not items:
            continue
        for i, (p_name, short, desc) in enumerate(items):
            own = [photo(key, p_name) for key in PRODUCT_PHOTOS[_slug(p_name)]]
            product_access.add({'category_id': category.id,
                                'name': p_name,
                                'slug': _slug(p_name),
                                'short_description': short,
                                'description': desc,
                                'is_active': True,
                                'is_featured': i == 0 and sort < 4,
                                'sort_order': i},
                               [(m.id, j == 0) for j, m in enumerate(own)],
                               USERNAME)
        print('category %-24s +%s products' % (name, len(items)))


def _slug(name):
    from backend.src.crm.view.validation import slugify
    return slugify(name, 220)


def seed_slider():
    for sort, (title, subtitle, link, key) in enumerate(SLIDES):
        if SliderItem.query.filter(SliderItem.title == title).first():
            continue
        slider_access.add({'media_id': photo(key, title).id, 'title': title, 'subtitle': subtitle, 'link_url': link,
                           'sort_order': sort, 'is_active': True, 'starts_at': None, 'ends_at': None}, USERNAME)
        print('slide: %s' % title)


def seed_banners():
    for sort, (title, subtitle, product_slug, link, key) in enumerate(BANNERS):
        if Banner.query.filter(Banner.title == title).first():
            continue
        product = Product.query.filter(Product.slug == product_slug).first() if product_slug else None
        banner_access.add({'media_id': photo(key, title).id, 'product_id': product.id if product else None,
                           'title': title, 'subtitle': subtitle, 'link_url': link,
                           'sort_order': sort, 'is_active': True, 'starts_at': None, 'ends_at': None}, USERNAME)
        print('banner: %s' % title)


def refresh_photos():
    """Point existing demo rows at the curated photos and delete the media
    they used before (when nothing else references it)."""
    old = []
    company = company_access.get()
    if company is not None:
        old.append(company.cover_media_id)
        company_access.edit(company, {'cover_media_id': photo(COVER_PHOTO, 'Alu Factory plant').id}, USERNAME)

    gallery = company_image_access.list_all()
    for image, (key, caption) in zip(gallery, GALLERY):
        old.append(image.media_id)
        company_image_access.edit(image, {'media_id': photo(key, caption).id, 'caption': caption}, USERNAME)

    for slug, keys in PRODUCT_PHOTOS.items():
        product = Product.query.filter(Product.slug == slug).first()
        if product is None:
            continue
        images = [(photo(key, product.name).id, i == 0) for i, key in enumerate(keys)]
        fields = {'category_id': product.category_id, 'name': product.name, 'slug': product.slug,
                  'short_description': product.short_description, 'description': product.description,
                  'is_active': product.is_active, 'is_featured': product.is_featured, 'sort_order': product.sort_order}
        ok, detached = product_access.edit(product, product.version, fields, images, USERNAME)
        old.extend(detached)

    for title, _subtitle, _link, key in SLIDES:
        item = SliderItem.query.filter(SliderItem.title == title).first()
        if item is not None:
            old.append(item.media_id)
            slider_access.edit(item, {'media_id': photo(key, title).id}, USERNAME)

    for title, _subtitle, _slug, _link, key in BANNERS:
        banner = Banner.query.filter(Banner.title == title).first()
        if banner is not None:
            old.append(banner.media_id)
            banner_access.edit(banner, {'media_id': photo(key, title).id}, USERNAME)

    _drop_unused(set(old))
    print('refreshed photos, %s downloaded' % len(_media_by_key))


def main():
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    started = datetime.now()
    with app.app_context():
        if '--refresh-photos' in sys.argv:
            refresh_photos()
        seed_company()
        seed_catalog()
        seed_slider()
        seed_banners()
    print('done in %ss' % (datetime.now() - started).seconds)


if __name__ == '__main__':
    main()
