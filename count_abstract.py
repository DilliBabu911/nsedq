import re
path = r"d:\Desktop Backup 1\Dilli\Publications\ESWA_NSEDQ\NSEDQ_ESWA_Final.md"
with open(path, encoding="utf-8") as f:
    text = f.read()
abs_match = re.search(r"## Abstract\s*\n+(.*?)\n\n\*\*Keywords", text, re.DOTALL)
abs_text = abs_match.group(1).strip() if abs_match else ""
# Clean markdown formatting before counting
abs_clean = re.sub(r"\*+", "", abs_text)
abs_clean = re.sub(r"\[.*?\]", "", abs_clean)
abs_clean = re.sub(r"\s+", " ", abs_clean).strip()
words = abs_clean.split()
print(f"Abstract word count (clean): {len(words)}")
print(f"\nFull abstract text:\n{abs_clean[:500]}...")
