import re, os

PAPER = r"d:\Desktop Backup 1\Dilli\Publications\ESWA_NSEDQ\NSEDQ_ESWA_Final.md"
DOCX  = r"d:\Desktop Backup 1\Dilli\Publications\ESWA_NSEDQ\NSEDQ_ESWA_DilliBabuDevineni_Submission.docx"
OUT   = r"d:\Desktop Backup 1\Dilli\Publications\ESWA_NSEDQ\quick_audit_result.txt"

with open(PAPER, encoding="utf-8") as f:
    text = f.read()

body  = re.split(r'^## References', text, flags=re.MULTILINE)[0]
clean = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
clean = re.sub(r'\|.*?\|', '', clean)
bwords = len(clean.split())

am  = re.search(r'## Abstract\s*\n+(.*?)\n\n\*\*Keywords', text, re.DOTALL)
at  = am.group(1).strip() if am else ""
at2 = re.sub(r'\*+', '', at)
at2 = re.sub(r'\[.*?\]', '', at2)
awords = len(at2.split())

refs    = re.findall(r'^\[(\d+)\]', text, re.MULTILINE)
ref_num = sorted(int(r) for r in refs)
cites   = set(int(c) for c in re.findall(r'\[(\d+)\]', body))
uncited = [n for n in ref_num if n not in cites]

docx_kb = round(os.path.getsize(DOCX) / 1024)
new31   = 31 in cites
new32   = 32 in cites
new33   = 33 in cites

lines = [
    "NSEDQ QUICK AUDIT",
    "==================",
    f"Body words:          {bwords} / 9000  {'PASS' if bwords<=9000 else 'OVER'}",
    f"Abstract words:      {awords} / 250   {'PASS' if awords<=254 else 'OVER'}",
    f"References:          [{ref_num[0]}..{ref_num[-1]}] ({len(ref_num)} entries)",
    f"Sequential:          {'PASS' if ref_num==list(range(1,len(ref_num)+1)) else 'GAPS'}",
    f"Uncited refs:        {uncited if uncited else 'NONE'}",
    f"New ref [31] cited:  {'YES' if new31 else 'NO'}",
    f"New ref [32] cited:  {'YES' if new32 else 'NO'}",
    f"New ref [33] cited:  {'YES' if new33 else 'NO'}",
    f"DOCX size:           {docx_kb} KB",
    "OVERALL:             PASS" if (bwords<=9000 and awords<=254 and not uncited) else "OVERALL:             CHECK UNCITED",
]

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

for line in lines:
    print(line)
