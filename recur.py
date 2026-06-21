#!/usr/bin/env python3
"""
recur
"""

import json
import random
import re
import sys
import time
from pathlib import Path
from datetime import datetime

# ensure unicode symbols render on legacy windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    "such", "like", "only", "same", "than", "too", "very", "now", "how", "why"
}

def load_entries():
    if not ENTRIES_FILE.exists():
        ENTRIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        return []
    # utf-8-sig tolerates a byte-order mark if one slipped into the file
    return json.loads(ENTRIES_FILE.read_text(encoding="utf-8-sig"))

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

GREETINGS = {"hi", "hello", "hey"}

# shown the first time a new user simply says hello.
# {name} is scramble-glitched into place when output is a terminal.
HELLO_LOG = """hi! i'm {name} — i made this.

recur is for logging any thought or idea, stowing it away from view, and noticing when it
comes back in another way. write something, and one day it might find you again.
"""

NAME = "sila"
GLITCH_CHARS = "!@#$%&*?/\\|<>=+~^0123456789"
GLITCH_DELAY = 0.11  # seconds per frame
GLITCH_NOISE_FRAMES = 8  # pure-scramble frames before the name resolves

GREY, RESET = "\033[90m", "\033[0m"

def glitch_name(prefix, name, suffix):
    """print one line, scrambling `name` then resolving it left-to-right in place.

    uses only \\r (carriage return) so it stays reliable across terminals.
    """
    def draw(name_render):
        sys.stdout.write(f"\r{GREY}>{RESET} {GREY}{prefix}{name_render}{suffix}{RESET}")
        sys.stdout.flush()

    # pure noise, then resolve one real character at a time
    frames = ["".join(random.choice(GLITCH_CHARS) for _ in name)
              for _ in range(GLITCH_NOISE_FRAMES)]
    for i in range(len(name) + 1):
        frames.append(name[:i] + "".join(random.choice(GLITCH_CHARS) for _ in name[i:]))

    for frame in frames:
        draw(frame)
        time.sleep(GLITCH_DELAY)
    draw(name)
    sys.stdout.write("\n")
    sys.stdout.flush()

def greeting_only(text):
    """true if the entry is nothing but a greeting (one word: hi/hello/hey)"""
    words = re.findall(r'[a-z]+', text.lower())
    return len(words) == 1 and words[0] in GREETINGS

def has_greeting(text):
    """true if the entry contains a greeting word anywhere"""
    return any(w in GREETINGS for w in re.findall(r'[a-z]+', text.lower()))

def show_hello():
    print()
    animate = sys.stdout.isatty()
    for line in HELLO_LOG.split("\n"):
        if "{name}" in line:
            if animate:
                prefix, suffix = line.split("{name}")
                glitch_name(prefix, NAME, suffix)
            else:
                # non-terminal (piped / redirected): print plainly, no animation
                prompt(line.format(name=NAME))
        else:
            prompt(line)
    print()

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
    prompt("write something... press enter twice when done.")
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

    # drop a leading byte-order mark, whether it arrives as ﻿ or
    # as the mojibake "ï»¿" produced when utf-8 bom bytes hit a non-utf-8 stdin
    new_text = "\n".join(lines).strip()
    for bom in ("﻿", "ï»¿"):
        if new_text.startswith(bom):
            new_text = new_text[len(bom):]
    if not new_text:
        prompt("nothing arrived. that's okay too.")
        return

    # easter egg: greet first-time users who say hello
    first_time = not entries
    if first_time and has_greeting(new_text):
        show_hello()
        # a bare greeting is consumed by the hello; anything more gets saved
        if greeting_only(new_text):
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
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        # keep the window open when launched by double-click
        try:
            input("\033[90m(press enter to close)\033[0m ")
        except (KeyboardInterrupt, EOFError):
            pass
