"""
Seed script to generate 10,000+ products in the database.
Run: python seed_data.py
"""
import random
import re
from datetime import datetime, timedelta
from app import app, db
from models import Category, Product, User, Coupon

# ─── Category Definitions ───────────────────────────────────────────────────
CATEGORIES = [
    {"name": "Electronics",        "slug": "electronics",      "icon": "📱", "id_offset": 1},
    {"name": "Smartphones",        "slug": "smartphones",      "icon": "📱", "parent": "electronics"},
    {"name": "Laptops",            "slug": "laptops",          "icon": "💻", "parent": "electronics"},
    {"name": "Televisions",        "slug": "televisions",      "icon": "📺", "parent": "electronics"},
    {"name": "Cameras",            "slug": "cameras",          "icon": "📷", "parent": "electronics"},
    {"name": "Audio",              "slug": "audio",            "icon": "🎧", "parent": "electronics"},
    {"name": "Fashion",            "slug": "fashion",          "icon": "👗", "id_offset": 2},
    {"name": "Men's Clothing",     "slug": "mens-clothing",    "icon": "👕", "parent": "fashion"},
    {"name": "Women's Clothing",   "slug": "womens-clothing",  "icon": "👗", "parent": "fashion"},
    {"name": "Kids' Clothing",     "slug": "kids-clothing",    "icon": "🧒", "parent": "fashion"},
    {"name": "Footwear",           "slug": "footwear",         "icon": "👟", "parent": "fashion"},
    {"name": "Watches",            "slug": "watches",          "icon": "⌚", "parent": "fashion"},
    {"name": "Home & Kitchen",     "slug": "home-kitchen",     "icon": "🏠", "id_offset": 3},
    {"name": "Furniture",          "slug": "furniture",        "icon": "🛋️", "parent": "home-kitchen"},
    {"name": "Kitchen Appliances", "slug": "kitchen-appliances","icon": "🍳", "parent": "home-kitchen"},
    {"name": "Bedding",            "slug": "bedding",          "icon": "🛏️", "parent": "home-kitchen"},
    {"name": "Books",              "slug": "books",            "icon": "📚", "id_offset": 4},
    {"name": "Sports & Fitness",   "slug": "sports-fitness",   "icon": "🏋️", "id_offset": 5},
    {"name": "Beauty & Personal Care","slug":"beauty-care",    "icon": "💄", "id_offset": 6},
    {"name": "Toys & Games",       "slug": "toys-games",       "icon": "🎮", "id_offset": 7},
    {"name": "Groceries",          "slug": "groceries",        "icon": "🛒", "id_offset": 8},
    {"name": "Automotive",         "slug": "automotive",       "icon": "🚗", "id_offset": 9},
]

# ─── Product Templates ───────────────────────────────────────────────────────
PRODUCT_TEMPLATES = {
    "smartphones": {
        "brands": ["Samsung", "Apple", "OnePlus", "Xiaomi", "Realme", "Oppo", "Vivo", "Motorola", "Nokia", "Google"],
        "models": ["Galaxy {}", "iPhone {}", "Nord {}", "Redmi {}", "Narzo {}", "Reno {}", "V{}", "Moto G{}", "G{}", "Pixel {}"],
        "suffixes": ["Pro", "Plus", "Max", "Ultra", "Lite", "5G", "Pro Max", "Neo", "SE", "Mini"],
        "specs": ["6.7 inch", "6.4 inch", "6.1 inch", "6.8 inch", "5.4 inch"],
        "ram": ["4GB", "6GB", "8GB", "12GB", "16GB"],
        "storage": ["64GB", "128GB", "256GB", "512GB", "1TB"],
        "price_range": (8000, 150000),
        "discount_range": (5, 45),
        "image_seeds": [15, 25, 35, 45, 55, 65],
    },
    "laptops": {
        "brands": ["Dell", "HP", "Lenovo", "Apple", "Asus", "Acer", "MSI", "Microsoft", "Razer", "LG"],
        "models": ["Inspiron {}", "Pavilion {}", "IdeaPad {}", "MacBook {}", "VivoBook {}", "Aspire {}", "Bravo {}", "Surface {}", "Blade {}", "Gram {}"],
        "suffixes": ["Pro", "Plus", "Air", "Ultra", "Gaming", "Touch", "Slim", "Max"],
        "specs": ["14 inch", "15.6 inch", "13.3 inch", "16 inch", "17.3 inch"],
        "ram": ["8GB", "16GB", "32GB", "64GB"],
        "storage": ["256GB SSD", "512GB SSD", "1TB SSD", "2TB SSD"],
        "price_range": (25000, 200000),
        "discount_range": (5, 35),
        "image_seeds": [20, 30, 40, 50, 60],
    },
    "televisions": {
        "brands": ["Samsung", "LG", "Sony", "Mi", "OnePlus", "Vu", "Philips", "TCL", "Hisense", "Panasonic"],
        "models": ["Crystal 4K {}", "NanoCell {}", "Bravia {}", "Smart TV {}", "U Series {}", "Premium {}", "Ambilight {}", "QLED {}", "A Series {}", "TH-{}"],
        "suffixes": ["4K", "OLED", "QLED", "LED", "AMOLED", "8K", "UHD"],
        "specs": ["32 inch", "40 inch", "43 inch", "50 inch", "55 inch", "65 inch", "75 inch"],
        "price_range": (12000, 250000),
        "discount_range": (10, 50),
        "image_seeds": [10, 20, 30, 40],
    },
    "cameras": {
        "brands": ["Canon", "Nikon", "Sony", "Fujifilm", "Panasonic", "Olympus", "Leica", "GoPro"],
        "models": ["EOS {}", "D{}", "Alpha {}", "X-T{}", "Lumix {}", "OM-{}", "Q{}", "HERO {}"],
        "suffixes": ["DSLR", "Mirrorless", "Point & Shoot", "Action Cam", "4K", "Pro"],
        "price_range": (5000, 300000),
        "discount_range": (5, 30),
        "image_seeds": [25, 35, 45],
    },
    "audio": {
        "brands": ["Sony", "Bose", "JBL", "Sennheiser", "Apple", "Samsung", "Boat", "Noise", "OnePlus", "Jabra"],
        "models": ["WH-{}", "QuietComfort {}", "Charge {}", "HD{}", "AirPods {}", "Galaxy Buds {}", "Airdopes {}", "Air {}", "Buds {}", "Elite {}"],
        "suffixes": ["Pro", "Plus", "Max", "Wireless", "NC", "TWS"],
        "price_range": (500, 80000),
        "discount_range": (10, 60),
        "image_seeds": [11, 22, 33, 44],
    },
    "mens-clothing": {
        "brands": ["Levi's", "Raymond", "Arrow", "Van Heusen", "Peter England", "Zara", "H&M", "US Polo", "Jack & Jones", "Flying Machine"],
        "types": ["T-Shirt", "Formal Shirt", "Casual Shirt", "Jeans", "Trousers", "Polo", "Kurta", "Blazer", "Jacket", "Shorts"],
        "colors": ["Black", "White", "Blue", "Navy", "Grey", "Red", "Green", "Maroon", "Olive", "Beige"],
        "price_range": (299, 8000),
        "discount_range": (20, 70),
        "image_seeds": [64, 74, 84, 94],
    },
    "womens-clothing": {
        "brands": ["Zara", "H&M", "Mango", "Forever 21", "W", "Biba", "Libas", "Anouk", "Global Desi", "FabIndia"],
        "types": ["Saree", "Kurti", "Dress", "Top", "Lehenga", "Salwar Suit", "Palazzo", "Jumpsuit", "Blouse", "Skirt"],
        "colors": ["Pink", "Red", "Blue", "Yellow", "Green", "Purple", "Orange", "White", "Black", "Teal"],
        "price_range": (399, 15000),
        "discount_range": (20, 70),
        "image_seeds": [65, 75, 85, 95],
    },
    "kids-clothing": {
        "brands": ["H&M Kids", "Zara Kids", "FirstCry", "LilPicks", "Mom & Me", "Hopscotch", "Gini & Jony", "Mothercare"],
        "types": ["T-Shirt", "Frock", "Romper", "Jumpsuit", "Jeans", "Shorts", "Pajama Set", "School Uniform"],
        "age_groups": ["0-6M", "6-12M", "1-2Y", "2-3Y", "3-4Y", "4-5Y", "5-6Y", "6-7Y", "7-8Y", "8-9Y", "9-10Y"],
        "price_range": (199, 2500),
        "discount_range": (20, 60),
        "image_seeds": [60, 70, 80, 90],
    },
    "footwear": {
        "brands": ["Nike", "Adidas", "Puma", "Reebok", "Bata", "Red Tape", "Woodland", "Sparx", "Liberty", "Skechers"],
        "types": ["Sneakers", "Running Shoes", "Formal Shoes", "Sandals", "Flip Flops", "Loafers", "Boots", "Sports Shoes"],
        "sizes": ["6", "7", "8", "9", "10", "11"],
        "price_range": (499, 20000),
        "discount_range": (10, 60),
        "image_seeds": [21, 31, 41, 51],
    },
    "watches": {
        "brands": ["Titan", "Fastrack", "Casio", "Fossil", "Seiko", "Timex", "Citizen", "Orient", "Michael Kors", "Daniel Wellington"],
        "types": ["Analog", "Digital", "Smart Watch", "Chronograph", "Automatic", "Solar"],
        "materials": ["Stainless Steel", "Leather Strap", "Silicon Band", "NATO Strap", "Mesh"],
        "price_range": (799, 50000),
        "discount_range": (10, 50),
        "image_seeds": [11, 22, 33],
    },
    "furniture": {
        "brands": ["IKEA", "Pepperfry", "Urban Ladder", "Godrej Interio", "Durian", "Nilkamal", "HomeTown"],
        "types": ["Sofa", "Bed", "Dining Table", "Wardrobe", "Study Table", "Bookshelf", "TV Unit", "Coffee Table", "Recliner"],
        "materials": ["Wooden", "Metal", "Fabric", "Leather", "MDF", "Engineered Wood"],
        "price_range": (2000, 150000),
        "discount_range": (10, 50),
        "image_seeds": [42, 52, 62, 72],
    },
    "kitchen-appliances": {
        "brands": ["Philips", "Bajaj", "Prestige", "Havells", "Bosch", "LG", "Samsung", "IFB", "Whirlpool", "Pigeon"],
        "types": ["Mixer Grinder", "Microwave", "Air Fryer", "Refrigerator", "Washing Machine", "Induction Cooktop", "Electric Kettle", "Toaster", "Coffee Maker", "Dishwasher"],
        "price_range": (500, 80000),
        "discount_range": (10, 50),
        "image_seeds": [44, 54, 64, 74],
    },
    "bedding": {
        "brands": ["Spaces", "Raymond Home", "Trident", "Story@Home", "Bombay Dyeing", "D'Decor", "Portico"],
        "types": ["Bed Sheet", "Comforter", "Pillow", "Duvet", "Mattress", "Mattress Protector", "Pillow Cover", "Blanket"],
        "sizes": ["Single", "Double", "Queen", "King"],
        "price_range": (299, 30000),
        "discount_range": (20, 70),
        "image_seeds": [46, 56, 66, 76],
    },
    "books": {
        "genres": ["Fiction", "Self Help", "Biography", "Science", "Technology", "History", "Business", "Children", "Philosophy", "Mystery"],
        "publishers": ["Penguin", "Harper Collins", "Rupa Publications", "Westland", "Bloomsbury", "Oxford Press", "Scholastic"],
        "titles": [
            "The Art of {}", "Journey to {}", "Understanding {}", "The Power of {}",
            "Complete Guide to {}", "Learning {} Fast", "Master {}", "The {} Handbook",
            "Introduction to {}", "Advanced {}", "The {} Revolution", "Secrets of {}"
        ],
        "subjects": [
            "Programming", "Leadership", "Success", "Python", "Data Science", "History",
            "Philosophy", "Marketing", "Finance", "Psychology", "Design", "AI",
            "Machine Learning", "Business", "Meditation", "Cooking", "Travel"
        ],
        "price_range": (99, 2500),
        "discount_range": (20, 60),
        "image_seeds": [10, 20, 30, 40, 50],
    },
    "sports-fitness": {
        "brands": ["Nike", "Adidas", "Reebok", "Decathlon", "Yonex", "Cosco", "SG", "NIVIA"],
        "types": ["Cricket Bat", "Football", "Yoga Mat", "Dumbbell", "Resistance Band", "Cycle", "Treadmill", "Badminton Racket", "Tennis Racket", "Gym Gloves"],
        "price_range": (199, 80000),
        "discount_range": (10, 50),
        "image_seeds": [16, 26, 36, 46],
    },
    "beauty-care": {
        "brands": ["Lakme", "Maybelline", "L'Oreal", "Nykaa", "Mamaearth", "WOW", "Biotique", "Himalaya", "Dove", "Nivea"],
        "types": ["Face Wash", "Moisturizer", "Sunscreen", "Lipstick", "Foundation", "Mascara", "Shampoo", "Conditioner", "Serum", "Face Mask"],
        "price_range": (99, 5000),
        "discount_range": (15, 65),
        "image_seeds": [18, 28, 38, 48],
    },
    "toys-games": {
        "brands": ["Lego", "Hot Wheels", "Barbie", "Fisher Price", "Funskool", "Hasbro", "Mattel", "Nerf"],
        "types": ["Building Blocks", "Action Figure", "Board Game", "Doll", "Remote Control Car", "Puzzle", "Educational Toy", "Play Dough"],
        "age_groups": ["0-2Y", "2-4Y", "4-6Y", "6-8Y", "8-10Y", "10-12Y", "12+Y"],
        "price_range": (199, 15000),
        "discount_range": (15, 60),
        "image_seeds": [19, 29, 39, 49],
    },
    "groceries": {
        "brands": ["Tata", "Aashirvaad", "Fortune", "Patanjali", "Nestle", "Maggi", "Britannia", "Amul", "Mother Dairy", "Haldiram's"],
        "types": ["Rice", "Dal", "Oil", "Flour", "Sugar", "Biscuits", "Noodles", "Milk", "Butter", "Cheese", "Spices", "Tea", "Coffee"],
        "sizes": ["250g", "500g", "1kg", "2kg", "5kg"],
        "price_range": (29, 2000),
        "discount_range": (5, 30),
        "image_seeds": [50, 60, 70, 80],
    },
    "automotive": {
        "brands": ["Bosch", "Minda", "Wago", "Amaron", "Exide", "3M", "Michelin", "MRF", "Osram"],
        "types": ["Car Battery", "Tyre", "Brake Pads", "Engine Oil", "Wiper Blade", "Car Cover", "Seat Cover", "Car Perfume", "Dash Cam", "Jump Starter"],
        "price_range": (199, 50000),
        "discount_range": (10, 40),
        "image_seeds": [17, 27, 37],
    },
}

# How many products per category slug
PRODUCT_COUNTS = {
    "smartphones": 1500,
    "laptops": 800,
    "televisions": 500,
    "cameras": 300,
    "audio": 600,
    "mens-clothing": 1000,
    "womens-clothing": 1000,
    "kids-clothing": 500,
    "footwear": 600,
    "watches": 400,
    "furniture": 400,
    "kitchen-appliances": 500,
    "bedding": 300,
    "books": 800,
    "sports-fitness": 400,
    "beauty-care": 500,
    "toys-games": 300,
    "groceries": 400,
    "automotive": 200,
}


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text.strip('-')


def random_image_url(seed, width=400, height=400):
    category_images = {
        "smartphones": f"https://picsum.photos/seed/phone{seed}/400/400",
        "laptops": f"https://picsum.photos/seed/laptop{seed}/400/400",
        "televisions": f"https://picsum.photos/seed/tv{seed}/400/400",
        "cameras": f"https://picsum.photos/seed/cam{seed}/400/400",
        "audio": f"https://picsum.photos/seed/audio{seed}/400/400",
        "mens-clothing": f"https://picsum.photos/seed/mens{seed}/400/400",
        "womens-clothing": f"https://picsum.photos/seed/womens{seed}/400/400",
        "kids-clothing": f"https://picsum.photos/seed/kids{seed}/400/400",
        "footwear": f"https://picsum.photos/seed/shoes{seed}/400/400",
        "watches": f"https://picsum.photos/seed/watch{seed}/400/400",
        "furniture": f"https://picsum.photos/seed/furn{seed}/400/400",
        "kitchen-appliances": f"https://picsum.photos/seed/kitchen{seed}/400/400",
        "bedding": f"https://picsum.photos/seed/bed{seed}/400/400",
        "books": f"https://picsum.photos/seed/book{seed}/400/400",
        "sports-fitness": f"https://picsum.photos/seed/sport{seed}/400/400",
        "beauty-care": f"https://picsum.photos/seed/beauty{seed}/400/400",
        "toys-games": f"https://picsum.photos/seed/toy{seed}/400/400",
        "groceries": f"https://picsum.photos/seed/grocery{seed}/400/400",
        "automotive": f"https://picsum.photos/seed/car{seed}/400/400",
    }
    return f"https://picsum.photos/seed/product{seed}/400/400"


def generate_product_name(slug, index):
    t = PRODUCT_TEMPLATES.get(slug, {})
    brands = t.get("brands", ["Brand"])
    brand = random.choice(brands)

    if slug in ["mens-clothing", "womens-clothing", "kids-clothing"]:
        types = t.get("types", ["Item"])
        colors = t.get("colors", [""])
        ptype = random.choice(types)
        color = random.choice(colors)
        name = f"{brand} {color} {ptype}"
    elif slug == "footwear":
        types = t.get("types", ["Shoes"])
        ptype = random.choice(types)
        name = f"{brand} {ptype} {index}"
    elif slug == "watches":
        types = t.get("types", ["Watch"])
        ptype = random.choice(types)
        name = f"{brand} {ptype} {index}"
    elif slug == "furniture":
        types = t.get("types", ["Furniture"])
        materials = t.get("materials", [""])
        mat = random.choice(materials)
        ptype = random.choice(types)
        name = f"{mat} {ptype} - {brand} #{index}"
    elif slug == "kitchen-appliances":
        types = t.get("types", ["Appliance"])
        ptype = random.choice(types)
        name = f"{brand} {ptype} {index}W"
    elif slug == "bedding":
        types = t.get("types", ["Bedding"])
        sizes = t.get("sizes", [""])
        ptype = random.choice(types)
        size = random.choice(sizes)
        name = f"{brand} {size} {ptype}"
    elif slug == "books":
        titles = t.get("titles", ["Book {}"])
        subjects = t.get("subjects", ["Knowledge"])
        publishers = t.get("publishers", ["Publisher"])
        title = random.choice(titles).format(random.choice(subjects))
        publisher = random.choice(publishers)
        name = f"{title} - {publisher}"
    elif slug == "sports-fitness":
        types = t.get("types", ["Sports Item"])
        ptype = random.choice(types)
        name = f"{brand} {ptype} Pro {index}"
    elif slug == "beauty-care":
        types = t.get("types", ["Beauty Product"])
        ptype = random.choice(types)
        name = f"{brand} {ptype} {index}ml"
    elif slug == "toys-games":
        types = t.get("types", ["Toy"])
        age_groups = t.get("age_groups", ["3+"])
        ptype = random.choice(types)
        age = random.choice(age_groups)
        name = f"{brand} {ptype} ({age})"
    elif slug == "groceries":
        types = t.get("types", ["Product"])
        sizes = t.get("sizes", [""])
        ptype = random.choice(types)
        size = random.choice(sizes)
        name = f"{brand} {ptype} {size}"
    elif slug == "automotive":
        types = t.get("types", ["Auto Part"])
        ptype = random.choice(types)
        name = f"{brand} {ptype} {index}"
    elif slug == "cameras":
        models = t.get("models", ["Camera {}"])
        suffixes = t.get("suffixes", [""])
        model = random.choice(models).format(random.randint(100, 9999))
        suffix = random.choice(suffixes)
        name = f"{brand} {model} {suffix}"
    elif slug == "audio":
        models = t.get("models", ["Audio {}"])
        suffixes = t.get("suffixes", [""])
        model = random.choice(models).format(random.randint(100, 9999))
        suffix = random.choice(suffixes)
        name = f"{brand} {model} {suffix}"
    elif slug in ["smartphones", "laptops", "televisions"]:
        models = t.get("models", ["Model {}"])
        suffixes = t.get("suffixes", [""])
        model = random.choice(models).format(random.randint(10, 99))
        suffix = random.choice(suffixes)
        name = f"{brand} {model} {suffix}"
    else:
        name = f"{brand} Product {index}"

    return name, brand


def generate_description(name, category_name):
    descriptions = [
        f"Premium quality {name} designed for modern lifestyle. Features cutting-edge technology and superior build quality.",
        f"Experience the best with {name}. Crafted with precision and care to deliver outstanding performance.",
        f"Upgrade your {category_name.lower()} experience with {name}. Top-rated by thousands of happy customers.",
        f"The {name} offers exceptional value for money. Trusted brand with excellent after-sales service.",
        f"Introducing {name} — your perfect companion for everyday use. Stylish design meets functionality.",
    ]
    return random.choice(descriptions)


def generate_specifications(slug, brand):
    specs_map = {
        "smartphones": f"Display: 6.5\" FHD+\nProcessor: Octa-core\nRAM: {random.choice(['4','6','8','12'])}GB\nStorage: {random.choice(['64','128','256'])}GB\nCamera: {random.choice(['48','64','108','200'])}MP\nBattery: {random.choice(['4000','4500','5000','5500'])}mAh",
        "laptops": f"Display: {random.choice(['14','15.6','13.3'])}\" FHD\nProcessor: {random.choice(['Intel i5','Intel i7','AMD Ryzen 5','AMD Ryzen 7','Apple M2'])}\nRAM: {random.choice(['8','16','32'])}GB\nStorage: {random.choice(['256','512','1TB'])} SSD\nOS: {random.choice(['Windows 11','macOS','Ubuntu'])}",
        "televisions": f"Screen Size: {random.choice(['43','50','55','65'])} inches\nResolution: {random.choice(['4K UHD','Full HD','8K'])}\nHDR: {random.choice(['HDR10','Dolby Vision','HDR10+'])}\nRefresh Rate: {random.choice(['60Hz','120Hz','144Hz'])}",
    }
    return specs_map.get(slug, f"Brand: {brand}\nWarranty: 1 Year\nCountry of Origin: India")


def seed_categories():
    print("Seeding categories...")
    cat_map = {}
    for cat_data in CATEGORIES:
        existing = Category.query.filter_by(slug=cat_data["slug"]).first()
        if existing:
            cat_map[cat_data["slug"]] = existing
            continue
        cat = Category(
            name=cat_data["name"],
            slug=cat_data["slug"],
            icon=cat_data.get("icon", "🛍️"),
            description=f"Shop the best {cat_data['name']} products",
        )
        db.session.add(cat)
        cat_map[cat_data["slug"]] = cat

    db.session.flush()

    # Set parent relationships
    for cat_data in CATEGORIES:
        if "parent" in cat_data:
            child = cat_map.get(cat_data["slug"])
            parent = cat_map.get(cat_data["parent"])
            if child and parent:
                child.parent_id = parent.id

    db.session.commit()
    print(f"  ✅ {len(cat_map)} categories seeded.")
    return cat_map


def seed_products(cat_map):
    print("Seeding products (this may take a minute)...")
    total = 0
    existing_slugs = set(p.slug for p in Product.query.with_entities(Product.slug).all())

    for slug, count in PRODUCT_COUNTS.items():
        cat = cat_map.get(slug)
        if not cat:
            # try parent slug
            for c in CATEGORIES:
                if c["slug"] == slug:
                    parent_slug = c.get("parent")
                    if parent_slug:
                        cat = cat_map.get(parent_slug)
            if not cat:
                print(f"  ⚠️  Category '{slug}' not found, skipping.")
                continue

        t = PRODUCT_TEMPLATES.get(slug, {})
        price_min, price_max = t.get("price_range", (100, 5000))
        disc_min, disc_max = t.get("discount_range", (5, 40))
        image_seeds = t.get("image_seeds", [random.randint(1, 100)])
        batch = []

        for i in range(count):
            name, brand = generate_product_name(slug, i + 1)
            base_slug = slugify(name)
            unique_slug = base_slug
            counter = 1
            while unique_slug in existing_slugs:
                unique_slug = f"{base_slug}-{counter}-{slug[:4]}"
                counter += 1
            existing_slugs.add(unique_slug)

            price = round(random.uniform(price_min, price_max), 2)
            discount = random.randint(disc_min, disc_max)
            seed_val = random.choice(image_seeds) + i

            product = Product(
                name=name,
                slug=unique_slug,
                description=generate_description(name, cat.name),
                brand=brand,
                category_id=cat.id,
                original_price=price,
                discount_percent=discount,
                stock=random.randint(0, 500),
                rating=round(random.uniform(3.0, 5.0), 1),
                rating_count=random.randint(10, 50000),
                image_url=f"https://picsum.photos/seed/{slug}{seed_val}/400/400",
                image_url2=f"https://picsum.photos/seed/{slug}{seed_val+1}/400/400",
                image_url3=f"https://picsum.photos/seed/{slug}{seed_val+2}/400/400",
                is_featured=(random.random() < 0.05),
                tags=f"{cat.name}, {brand}, {slug}",
                specifications=generate_specifications(slug, brand),
            )
            batch.append(product)

            if len(batch) >= 500:
                db.session.bulk_save_objects(batch)
                db.session.commit()
                total += len(batch)
                print(f"  → {slug}: {total} products inserted...")
                batch = []

        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            total += len(batch)

        print(f"  ✅ {slug}: done ({count} products)")

    print(f"\n🎉 Total products seeded: {total}")
    return total


def seed_coupons():
    print("Seeding coupons...")
    coupons = [
        {"code": "SAVE10", "discount_percent": 10, "max_discount": 200, "min_order": 500},
        {"code": "SAVE20", "discount_percent": 20, "max_discount": 400, "min_order": 1000},
        {"code": "SAVE30", "discount_percent": 30, "max_discount": 600, "min_order": 2000},
        {"code": "FLAT100", "discount_flat": 100, "min_order": 500},
        {"code": "FLAT500", "discount_flat": 500, "min_order": 2000},
        {"code": "FLAT1000", "discount_flat": 1000, "min_order": 5000},
        {"code": "NEWUSER", "discount_percent": 15, "max_discount": 300, "min_order": 0},
        {"code": "SHOPKART50", "discount_percent": 50, "max_discount": 1000, "min_order": 3000},
    ]
    for c in coupons:
        existing = Coupon.query.filter_by(code=c["code"]).first()
        if not existing:
            coupon = Coupon(
                code=c["code"],
                discount_percent=c.get("discount_percent", 0),
                discount_flat=c.get("discount_flat", 0),
                max_discount=c.get("max_discount", 500),
                min_order=c.get("min_order", 0),
                uses_left=1000,
                expires_at=datetime.utcnow() + timedelta(days=365),
            )
            db.session.add(coupon)
    db.session.commit()
    print("  ✅ Coupons seeded.")


def seed_admin_user():
    print("Seeding admin user...")
    existing = User.query.filter_by(email="admin@shopkart.com").first()
    if not existing:
        admin = User(name="Admin", email="admin@shopkart.com", is_admin=True)
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("  ✅ Admin user created: admin@shopkart.com / admin123")
    else:
        print("  ℹ️  Admin user already exists.")


if __name__ == "__main__":
    with app.app_context():
        print("🚀 ShopKart Database Seeder")
        print("=" * 40)
        db.create_all()
        seed_admin_user()
        cat_map = seed_categories()
        seed_products(cat_map)
        seed_coupons()
        print("\n✅ Seeding complete! Run `python app.py` to start the server.")
