# Combine translated HTML with original styles/JS

with open('upload.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('upload_translated.html', 'a', encoding='utf-8') as target:
    target.writelines(lines[299:])

print("File combined successfully!")
