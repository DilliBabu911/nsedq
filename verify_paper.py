import re
path = r"d:\Desktop Backup 1\Dilli\Publications\ESWA_NSEDQ\NSEDQ_ESWA_Final.md"
with open(path, encoding="utf-8") as f:
    text = f.read()

words = len(text.split())
placeholders = len(re.findall(r'\[RESULT\]', text))
old_nums = len(re.findall(r'0\.916|0\.881|97\.3%|72\.6%', text))
real_nums = len(re.findall(r'77\.1%|0\.8482|0\.8472|0\.8497|0\.8540|0\.444|0\.464|0\.699', text))

print(f"Word count:              {words:,}")
print(f"[RESULT] placeholders:   {placeholders}")
print(f"Old designed numbers:    {old_nums}")
print(f"Real result numbers:     {real_nums}")

# Check key real values are present
checks = {
    "2 CRL iterations":     "2 iterations" in text,
    "77.1% reduction":      "77.1%" in text,
    "CTS 0.8482":           "0.8482" in text,
    "DQTS 0.9996 (IBM HR)": "0.9996" in text,
    "KS rate 0.444":        "0.444" in text,
    "PCR 100% patient":     "100%" in text,
    "B5 DQTS 0.248":        "0.248" in text,
    "48 proof certs":       "48" in text,
}
print("\nKey result checks:")
for k, v in checks.items():
    print(f"  {'[OK]' if v else '[MISSING]'} {k}")
