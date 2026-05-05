"""
Synthetic clinical oncology data generator for OncoAgent.
Generates OncoCoT-format samples for pipeline validation.
All data is 100% synthetic — zero real patient information.
"""

import json
import os
import random
from typing import List, Dict

# Reproducibility seed (Rule #22)
random.seed(42)

SYNTHETIC_ONCOCOT_SAMPLES: List[Dict[str, str]] = [
    # === HIGH RISK (5 cases) ===
    {
        "history": (
            "62-year-old female presents with persistent dry cough for 3 months, "
            "unintentional weight loss of 8 kg, and hemoptysis. Chest CT reveals a "
            "2.5 cm spiculated mass in the left upper lobe with associated pleural "
            "thickening and enlarged mediastinal lymph nodes measuring 1.2 cm. "
            "Patient is a former smoker with 30 pack-year history."
        ),
        "reasoning": (
            "1. Identify lesion characteristics: 2.5 cm mass classifies as T1c/T2a. "
            "2. Morphology: 'Spiculated' margins are highly indicative of malignancy "
            "(positive predictive value >90%). "
            "3. Nodal involvement: Mediastinal lymph nodes at 1.2 cm suggest N2 status. "
            "4. Clinical correlation: Hemoptysis + weight loss + smoking history "
            "significantly increase pre-test probability. "
            "5. Staging synthesis: T2aN2M0 → Stage IIIA per AJCC 8th edition."
        ),
        "conclusion": (
            "High suspicion for non-small cell lung cancer (NSCLC), likely Stage IIIA. "
            "Recommend urgent tissue biopsy (CT-guided or bronchoscopy) and PET-CT "
            "for comprehensive staging. Multidisciplinary tumor board consultation required."
        ),
    },
    {
        "history": (
            "55-year-old male with a palpable 3.5 cm mass in the right breast, "
            "skin dimpling, and axillary lymphadenopathy on the ipsilateral side. "
            "Mammography shows an irregular dense mass with microcalcifications. "
            "Family history positive for BRCA2 mutation in first-degree relative."
        ),
        "reasoning": (
            "1. Mass characteristics: 3.5 cm irregular mass with microcalcifications "
            "is highly suspicious (BI-RADS 5). "
            "2. Clinical signs: Skin dimpling indicates possible Cooper ligament involvement. "
            "3. Nodal status: Ipsilateral axillary lymphadenopathy suggests N1 involvement. "
            "4. Risk factors: Male breast cancer accounts for <1% of cases, but BRCA2 "
            "significantly increases risk (6-8% lifetime). "
            "5. Staging estimate: T2N1M0 → Stage IIB."
        ),
        "conclusion": (
            "High suspicion for male breast carcinoma, likely Stage IIB. "
            "Recommend core needle biopsy with receptor testing (ER/PR/HER2), "
            "BRCA genetic testing, and staging workup including chest/abdominal CT."
        ),
    },
    {
        "history": (
            "70-year-old male presents with progressive difficulty swallowing solids "
            "over 4 months, weight loss of 12 kg, and retrosternal pain. Upper "
            "endoscopy reveals a 4 cm circumferential mass in the distal esophagus "
            "with mucosal ulceration. CT shows thickened esophageal wall and "
            "suspicious celiac lymph nodes."
        ),
        "reasoning": (
            "1. Lesion: 4 cm circumferential mass with ulceration is T3 (adventitial invasion likely). "
            "2. Location: Distal esophagus suggests adenocarcinoma (Barrett's association). "
            "3. Nodal disease: Celiac lymph nodes represent M1 lymph node disease per AJCC. "
            "4. Symptoms: Progressive dysphagia + significant weight loss indicate advanced disease. "
            "5. Staging: T3N1M1(LYM) → Stage IVA."
        ),
        "conclusion": (
            "High suspicion for esophageal adenocarcinoma, Stage IVA. "
            "Recommend endoscopic biopsy with HER2 testing, PET-CT for complete staging, "
            "and referral for palliative chemoradiation consideration."
        ),
    },
    {
        "history": (
            "48-year-old female with recently discovered hepatic masses on "
            "ultrasound performed for right upper quadrant pain. CT reveals "
            "multiple bilobar liver lesions (largest 6 cm) with arterial enhancement "
            "and washout. AFP level is 850 ng/mL. History of hepatitis C cirrhosis."
        ),
        "reasoning": (
            "1. Imaging: Arterial enhancement with washout is pathognomonic for HCC (LI-RADS 5). "
            "2. Biomarker: AFP >400 ng/mL is highly specific for hepatocellular carcinoma. "
            "3. Risk factor: HCV cirrhosis is the leading cause of HCC. "
            "4. Extent: Bilobar disease precludes surgical resection. "
            "5. Staging: Beyond Milan criteria (single ≤5cm or ≤3 lesions each ≤3cm) → BCLC Stage C."
        ),
        "conclusion": (
            "Hepatocellular carcinoma confirmed by imaging criteria (LI-RADS 5) and AFP elevation. "
            "BCLC Stage C. Recommend systemic therapy (atezolizumab + bevacizumab per NCCN) "
            "and liver transplant evaluation if disease responds."
        ),
    },
    {
        "history": (
            "58-year-old male with iron-deficiency anemia, change in bowel habits "
            "for 6 months, and a 2 cm mass found in the sigmoid colon on colonoscopy. "
            "Biopsy confirms moderately differentiated adenocarcinoma. CT abdomen shows "
            "3 suspicious pericolonic lymph nodes and 2 small liver lesions."
        ),
        "reasoning": (
            "1. Primary tumor: 2 cm sigmoid adenocarcinoma, moderately differentiated. "
            "2. Local spread: Pericolonic lymph nodes suggest N1 disease. "
            "3. Distant metastasis: Liver lesions are concerning for M1a hepatic metastases. "
            "4. Presentation: Iron-deficiency anemia is classic for right-sided colon cancer "
            "but can occur in sigmoid lesions with chronic occult bleeding. "
            "5. Staging: T3N1M1a → Stage IVA (AJCC 8th edition)."
        ),
        "conclusion": (
            "Sigmoid colon adenocarcinoma, Stage IVA with hepatic metastases. "
            "Recommend molecular profiling (MSI, KRAS/NRAS/BRAF), "
            "liver MRI for surgical resectability assessment, and FOLFOX/FOLFIRI-based "
            "systemic therapy per NCCN guidelines."
        ),
    },
    # === MEDIUM RISK (3 cases) ===
    {
        "history": (
            "45-year-old female with a 1.5 cm solid thyroid nodule found incidentally "
            "on carotid ultrasound. Fine needle aspiration shows Bethesda IV "
            "(follicular neoplasm). No cervical lymphadenopathy. TSH is normal."
        ),
        "reasoning": (
            "1. Nodule: 1.5 cm solid nodule with Bethesda IV cytology. "
            "2. Risk of malignancy: Bethesda IV carries 15-30% cancer risk. "
            "3. Favorable factors: No lymphadenopathy, normal TSH. "
            "4. Cannot distinguish follicular adenoma from carcinoma on cytology alone. "
            "5. Assessment: Intermediate risk requiring diagnostic surgery."
        ),
        "conclusion": (
            "Indeterminate thyroid nodule (Bethesda IV) with moderate malignancy risk. "
            "Recommend molecular testing (Afirma or ThyroSeq) if available. "
            "If molecular testing is inconclusive, diagnostic lobectomy is indicated."
        ),
    },
    {
        "history": (
            "60-year-old male with a PSA level of 7.2 ng/mL on routine screening. "
            "Digital rectal exam reveals a firm nodule on the right lobe. "
            "MRI prostate shows a PI-RADS 4 lesion in the peripheral zone, "
            "15 mm in greatest dimension. No extraprostatic extension."
        ),
        "reasoning": (
            "1. PSA: 7.2 ng/mL is elevated (normal <4.0), PSA density should be calculated. "
            "2. DRE: Palpable nodule correlates with imaging finding. "
            "3. MRI: PI-RADS 4 has ~60-70% probability of clinically significant cancer. "
            "4. Confined disease: No extraprostatic extension is favorable. "
            "5. Assessment: High probability of Gleason 3+4 or higher prostate cancer."
        ),
        "conclusion": (
            "Probable clinically significant prostate cancer. "
            "Recommend MRI-targeted fusion biopsy (minimum 12 systematic + 2-3 targeted cores). "
            "If positive, staging with PSMA PET-CT per NCCN guidelines."
        ),
    },
    {
        "history": (
            "52-year-old female with a 2 cm pancreatic cystic lesion found on CT "
            "performed for back pain. MRI with MRCP shows a branch-duct IPMN in the "
            "pancreatic body with a mural nodule measuring 5 mm. CA 19-9 is 45 U/mL. "
            "No main duct dilation."
        ),
        "reasoning": (
            "1. Cyst type: Branch-duct IPMN is the most common pancreatic cystic neoplasm. "
            "2. Worrisome feature: Mural nodule (5 mm) is a 'worrisome feature' per Fukuoka criteria. "
            "3. Size: 2 cm is below the high-risk threshold of 3 cm. "
            "4. Biomarker: CA 19-9 of 45 is borderline (normal <37). "
            "5. Assessment: Moderate risk — warrants EUS for further characterization."
        ),
        "conclusion": (
            "Branch-duct IPMN with worrisome features (mural nodule). "
            "Recommend endoscopic ultrasound (EUS) with FNA for cytology and cyst fluid analysis. "
            "If high-grade dysplasia found, surgical resection is indicated."
        ),
    },
    # === LOW RISK (2 cases) ===
    {
        "history": (
            "35-year-old female with a 1 cm well-circumscribed, oval, hypoechoic "
            "breast mass found on screening ultrasound. BI-RADS 3. No family history "
            "of breast cancer. No skin changes or axillary lymphadenopathy."
        ),
        "reasoning": (
            "1. Mass morphology: Well-circumscribed, oval shape is characteristic of fibroadenoma. "
            "2. BI-RADS 3: Probably benign (<2% malignancy risk). "
            "3. Age: 35 years old — breast cancer is rare at this age without risk factors. "
            "4. No concerning features: No skin changes, no lymphadenopathy. "
            "5. Assessment: Low risk, likely fibroadenoma."
        ),
        "conclusion": (
            "Probably benign breast mass (BI-RADS 3), most likely fibroadenoma. "
            "Recommend short-interval follow-up ultrasound at 6 months. "
            "If stable at 2 years, reclassify as BI-RADS 2 (benign)."
        ),
    },
    {
        "history": (
            "28-year-old male with a small, well-circumscribed 8 mm pulmonary nodule "
            "found incidentally on chest X-ray performed for pre-employment screening. "
            "Non-smoker, no respiratory symptoms, no weight loss. CT confirms a smooth, "
            "round, calcified nodule in the right middle lobe."
        ),
        "reasoning": (
            "1. Nodule: 8 mm, smooth margins, calcified — benign morphology. "
            "2. Calcification pattern: Diffuse calcification is highly associated with granuloma. "
            "3. Risk factors: Non-smoker, young age, asymptomatic. "
            "4. Fleischner criteria: Calcified nodules are generally benign and do not "
            "require follow-up imaging. "
            "5. Assessment: Very low risk, most likely granuloma (infectious etiology)."
        ),
        "conclusion": (
            "Benign calcified pulmonary granuloma. No malignancy concern. "
            "No further imaging or follow-up required per Fleischner Society guidelines. "
            "Reassure patient."
        ),
    },
]


def generate_oncocot_samples(output_path: str = "data/samples/oncocot_synthetic.json") -> str:
    """
    Writes the synthetic OncoCoT samples to a JSON file.

    Args:
        output_path: Path to the output JSON file.

    Returns:
        The absolute path to the generated file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(SYNTHETIC_ONCOCOT_SAMPLES, f, ensure_ascii=False, indent=2)
    print(f"✅ Generated {len(SYNTHETIC_ONCOCOT_SAMPLES)} synthetic OncoCoT samples → {output_path}")
    return os.path.abspath(output_path)


def generate_pmc_patients_format(
    output_path: str = "data/samples/pmc_patients_synthetic.json",
) -> str:
    """
    Converts the OncoCoT samples into a PMC-Patients-compatible format.

    Args:
        output_path: Path to the output JSON file.

    Returns:
        The absolute path to the generated file.
    """
    pmc_samples: List[Dict[str, str]] = []
    for sample in SYNTHETIC_ONCOCOT_SAMPLES:
        pmc_samples.append({
            "patient": sample["history"],
            "medical_history": sample["history"],
            "reasoning": sample["reasoning"],
            "conclusion": sample["conclusion"],
        })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pmc_samples, f, ensure_ascii=False, indent=2)
    print(f"✅ Generated {len(pmc_samples)} PMC-Patients format samples → {output_path}")
    return os.path.abspath(output_path)


if __name__ == "__main__":
    generate_oncocot_samples()
    generate_pmc_patients_format()
    print("🚀 All synthetic data generated successfully.")
