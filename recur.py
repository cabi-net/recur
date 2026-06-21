#!/usr/bin/env python3
"""
recur - a place for thoughts to arrive and return
"""

import json
import random
import re
from pathlib import Path
from datetime import datetime

ENTRIES_FILE = Path.home() / ".recur" / "entries.json"
STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "you", "your", "it", "its",
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "as",
    "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "do", "does", "did", "will", "would", "could", "should", "can",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "this",
    "that", "these", "those", "what", "which", "who", "when", "where",
    "just", "about", "into", "through", "during", "before", "after",
    "above", "below", "between", "under", "again", "there", "here",
    "all", "each", "some", "any", "both", "more", "most", "other",
    "such", "only", "same", "than", "too", "very", "now", "how", "why"
}

def load_entries():
    if not ENTRIES_FILE.exists():
        ENTRIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        return []
    return json.loads(ENTRIES_FILE.read_text())

def save_entries(entries):
    ENTRIES_FILE.write_text(json.dumps(entries, indent=2))

def extract_words(text):
    words = re.findall(r'[a-z]+', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]

def find_recurrence(new_text, entries):
    """find a past entry that shares a word with this one"""
    if not entries:
        return None, None

    new_words = extract_words(new_text)
    if not new_words:
        return None, None

    random.shuffle(new_words)

    for word in new_words:
        matching = []
        for i, entry in enumerate(entries):
            if word in extract_words(entry["text"]):
                matching.append((i, entry))
        if matching:
            idx, found = random.choice(matching)
            return word, (idx, found)

    return None, None

def format_time(iso_string):
    dt = datetime.fromisoformat(iso_string)
    return dt.strftime("%b %d, %Y")

def prompt(text=""):
    print(f"\033[90m>\033[0m ", end="")
    if text:
        print(f"\033[90m{text}\033[0m")
        return None
    return input()

def main():
    entries = load_entries()

    print()
    prompt("recur")
    print()
    prompt("let your thoughts arrive.")
    prompt("press enter twice when done.")
    print()

    # gather entry
    lines = []
    while True:
        line = prompt()
        if line is None:
            line = ""
        line = line.rstrip()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)

    new_text = "\n".join(lines).strip()
    if not new_text:
        prompt("nothing arrived. that's okay too.")
        return

    # look for recurrence
    word, match = find_recurrence(new_text, entries)

    if match:
        idx, old_entry = match
        print()
        prompt(f'"{word}" recurred...')
        prompt()
        prompt(f"from {format_time(old_entry['when'])}:")
        prompt()
        for line in old_entry["text"].split("\n"):
            prompt(f"  {line}")
        prompt()
        prompt("would you like to rewrite this? [y/N]")

        response = prompt()
        if response.lower() == "y":
            prompt()
            prompt("rewrite it. enter twice when done.")
            prompt()

            update_lines = []
            while True:
                line = prompt()
                if line is None:
                    line = ""
                line = line.rstrip()
                if line == "" and update_lines and update_lines[-1] == "":
                    break
                update_lines.append(line)

            updated_text = "\n".join(update_lines).strip()
            if updated_text:
                entries[idx]["text"] = updated_text
                entries[idx]["updated"] = datetime.now().isoformat()
                prompt()
                prompt("rewritten.")

    # save new entry
    entries.append({
        "text": new_text,
        "when": datetime.now().isoformat()
    })
    save_entries(entries)

    print()
    prompt("saved.")
    prompt()

if __name__ == "__main__":
    main()
