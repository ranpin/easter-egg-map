import re, json

with open('data/seed-eggs-v3.json', 'r') as f:
    content = f.read()

# Fix: remove extra ] [ boundaries from append operations
# Pattern: ]\n,\n[ or ],\n[
content = re.sub(r'\]\s*,\s*\n\s*\[', ',', content)

with open('data/seed-eggs-v3.json', 'w') as f:
    f.write(content)

data = json.loads(content)
print(f'OK: {len(data)} items')

cats = {}
for d in data:
    cats[d['category']] = cats.get(d['category'], 0) + 1
print('Categories:', cats)

tags = {}
for d in data:
    tags[d['regionTag']] = tags.get(d['regionTag'], 0) + 1
print('Tags:', tags)

countries = {}
for d in data:
    countries[d['country']] = countries.get(d['country'], 0) + 1
print('Countries:', countries)
