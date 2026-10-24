import pandas as pd

for fname in ["ibm_hr.csv", "ibm_hr1.csv"]:
    try:
        df = pd.read_csv(f"d:\\Desktop Backup 1\\Dilli\\Publications\\ESWA_NSEDQ\\data\\{fname}")
        print(f"\n{fname}: {df.shape[0]} rows x {df.shape[1]} cols")
        print(f"  Columns: {list(df.columns[:6])}")
        # Real IBM HR has exactly 1470 rows and 35 cols
        is_real = df.shape == (1470, 35) or (df.shape[0] == 1470 and "Attrition" in df.columns)
        print(f"  Real IBM HR dataset: {'YES' if is_real else 'NO (synthetic replica)'}")
        if "Age" in df.columns:
            print(f"  Age range: {df['Age'].min()} – {df['Age'].max()}, mean={df['Age'].mean():.1f}")
        if "Attrition" in df.columns:
            print(f"  Attrition Yes%: {(df['Attrition']=='Yes').mean()*100:.1f}%")
    except Exception as e:
        print(f"{fname}: ERROR — {e}")
