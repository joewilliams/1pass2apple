import csv
import json
import sys
import os
import re
import shutil
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: python3 mangle.py /path/to/data.1pif output_basename")
    print("Example: python3 mangle.py ./data.1pif shared")
    sys.exit(1)

filename = sys.argv[1]
basename = sys.argv[2]

export_dir = Path(filename).parent
attachments_src = export_dir / "attachments"

csv_path = Path(f"{basename}.csv")
attachments_out = Path(f"attachments_extracted.{basename}")
attachments_out.mkdir(exist_ok=True)

w = csv.writer(open(csv_path, "w", newline="", encoding="utf-8"))
w.writerow(['Title', 'URL', 'Username', 'Password', 'Notes', 'OTPAuth'])

with open(filename, 'r', encoding='utf-8', errors='replace') as file:
    for line in file:
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        title = data.get('title', 'Untitled')
        uuid = data.get('uuid', '')

        if data.get('typeName') == 'system.folder.Regular':
            print(f"[{title}] skipping folder", file=sys.stderr)
            continue
        if data.get('trashed'):
            print(f"[{title}] skipping trash entry", file=sys.stderr)
            continue

        secure = data.get('secureContents', {})
        username = password = otpauth = note = url = ''

        # URL
        if 'URLs' in secure and secure['URLs']:
            url = secure['URLs'][0].get('url', '')

        # Password
        if 'password' in secure:
            password = secure['password']

        # Notes on regular items
        if 'notesPlain' in secure and secure['notesPlain']:
            note = secure['notesPlain']

        # Fields
        if 'fields' in secure:
            for field in secure['fields']:
                name = field.get('name', '').lower()
                value = field.get('value', '')
                designation = field.get('designation', '').lower()

                if name == 'password' or designation == 'password':
                    password = value
                elif name == 'username' or designation == 'username':
                    username = value
                elif name == 'title':
                    title = value

        # Sections (OTP + Secure Notes)
        if 'sections' in secure:
            for section in secure['sections']:
                if 'fields' in section and section['fields']:
                    first = section['fields'][0]
                    t = first.get('t', '').lower()
                    v = first.get('v', '')
                    if t == 'one-time password':
                        otpauth = v
                    if data.get('typeName') == 'securenotes.SecureNote' and not note:
                        note = v

        # Fallback
        if not note:
            parts = []
            if 'name' in secure:
                parts.append(f"name: {secure['name']}")
            if 'number' in secure:
                parts.append(f"number: {secure['number']}")
            note = ", ".join(parts)

        # Attachments
        attachment_names = []
        if attachments_src.exists() and uuid:
            item_att_dir = attachments_src / uuid
            if item_att_dir.is_dir():
                safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)[:80] or uuid
                dest_dir = attachments_out / safe_title
                dest_dir.mkdir(exist_ok=True)

                for f in item_att_dir.iterdir():
                    if f.is_file():
                        dest = dest_dir / f.name
                        shutil.copy2(f, dest)
                        attachment_names.append(f.name)

        if attachment_names:
            note = (note + f"\n\nAttachments (in attachments_extracted.{basename}): " + ", ".join(attachment_names)).strip()

        w.writerow([title, url, username, password, note, otpauth])

print(f"CSV written to: {csv_path.resolve()}", file=sys.stderr)
print(f"Attachments extracted to: {attachments_out.resolve()}", file=sys.stderr)
