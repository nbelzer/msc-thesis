unavailable_content = []
with open('./out/content-unavailable.txt', 'r') as f:
    unavailable_content = [resource.split("\n")[0] for resource in f.readlines()]

print(f"Scanning for {len(unavailable_content)} unavailable items.")

with open('./out/page-map.csv', 'r') as content_map:
    with open('./out/page-map-clean.csv', 'w') as cleaned_map:
        for line in content_map:
            parsed = line.split("\n")[0].split(';')
            if len(parsed) != 3:
                continue
            origin = parsed[0]
            links = parsed[1].split(' ')
            resources = parsed[2].split(' ')

            if origin in unavailable_content:
                # Simply skip this resource
                continue

            cleaned_links = [ l for l in links if l not in unavailable_content ]
            cleaned_resources = [ r for r in resources if r not in unavailable_content ]
            cleaned_map.write(f"{origin};{' '.join(cleaned_links)};{' '.join(cleaned_resources)}\n")
