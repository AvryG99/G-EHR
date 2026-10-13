# RAG-Optimized Descriptions for MIMIC-III Database

TABLE_DESCRIPTIONS = {
    "admissions": "Hospital admissions. When was patient admitted? When discharged? What admission type? Emergency or elective admission? Patient demographics: insurance, language, religion, marital status, ethnicity. Admission location and discharge location. Did patient die in hospital? What was primary diagnosis at admission? Emergency department times.",
    
    "patients": "Patient demographics. Patient age, date of birth. Patient gender male or female. Patient death date. Did patient die? Patient survival status. Basic patient information.",
    
    "icustays": "ICU stays intensive care unit. When did patient enter ICU? When did patient leave ICU? How long in ICU? Length of ICU stay. Which ICU unit? First ICU unit, last ICU unit. ICU admission and discharge times.",
    
    "diagnoses_icd": "Patient diagnoses diagnosis codes ICD9 codes. What disease does patient have? What conditions diagnosed? All diagnoses for admission. Primary and secondary diagnoses. Diagnosis code lookup.",
    
    "d_icd_diagnoses": "ICD9 diagnosis code dictionary definitions. What does diagnosis code mean? Diagnosis code description. Short title and long title for ICD9 codes. Decode diagnosis codes.",
    
    "procedures_icd": "Procedures performed on patient. ICD9 procedure codes. What procedures did patient have? What operations? Surgical procedures. Medical procedures during admission.",
    
    "d_icd_procedures": "ICD9 procedure code dictionary definitions. What does procedure code mean? Procedure code description. Short title and long title for procedure codes. Decode procedure codes.",
    
    "prescriptions": "Medications prescribed to patient. What drugs prescribed? What medications ordered? Prescription start date and end date. Drug names generic and brand. Drug dosage and route. Oral IV medications.",
    
    "labevents": "Laboratory test results lab tests. Blood tests chemistry panels. Lab values. What were patient lab results? Hemoglobin glucose creatinine sodium potassium. Abnormal lab values flagged results. Lab test times.",
    
    "d_labitems": "Lab test dictionary definitions. What lab test names. Lab item descriptions. Lab test categories. Blood urine tests. LOINC codes for lab tests.",
    
    "chartevents": "Vital signs bedside measurements. Heart rate blood pressure temperature respiratory rate. Oxygen saturation SpO2. Ventilator settings. Nursing assessments. Patient vital signs over time. Hourly measurements.",
    
    "inputevents_cv": "Fluids and medications given to patient CareVue system. IV fluids administered. Medication infusions. What fluids did patient receive? Fluid intake. Medication administration times and amounts.",
    
    "inputevents_mv": "Fluids and medications given to patient MetaVision system. IV fluids administered. Medication infusions. What fluids did patient receive? Fluid intake. Medication administration times and amounts.",
    
    "outputevents": "Patient outputs urine output. Drain output. How much urine? Fluid output measurements. Output volumes over time.",
    
    "microbiologyevents": "Microbiology results cultures. Bacteria organisms cultured. Antibiotic sensitivity testing. What organisms grew? Antibiotic resistance. Culture results. Specimen types blood urine sputum. Susceptibility testing.",
    
    "procedureevents_mv": "Procedures performed in ICU MetaVision. Dialysis intubation procedures. Invasive procedures. What procedures in ICU? Procedure start and end times.",
    
    "noteevents": "Clinical notes doctor notes nurse notes. Discharge summaries. Radiology reports. Progress notes. Clinical documentation. Free text notes. What did doctor write? Nursing notes. Physician notes.",
    
    "d_items": "Item dictionary for measurements. Chart events input events item definitions. What does item ID mean? Measurement names labels. Vital sign names medication names.",
    
    "cptevents": "CPT billing codes procedures. Procedure billing. What procedures billed? CPT codes for procedures performed.",
    
    "d_cpt": "CPT code dictionary definitions. What does CPT code mean? CPT code descriptions. Billing code lookup.",
    
    "drgcodes": "DRG diagnosis related group codes. Hospital billing codes. Severity scores mortality risk. DRG descriptions.",
    
    "caregivers": "Hospital staff doctors nurses. Who provided care? Caregiver roles. Staff identifiers.",
    
    "services": "Hospital services consulted. Cardiology surgery services. Which services consulted? Service transfers. What specialty services involved?",
    
    "transfers": "Patient location changes ward transfers. Patient movement in hospital. Which unit? Transfer between units. When transferred? ICU transfers. Ward changes.",
    
    "callout": "Discharge planning transfer requests. Callout for patient discharge. Transfer acceptance rejection. Discharge coordination.",
    
    "datetimeevents": "Events with datetime values. Procedure times event times. Time-based measurements."
}

COLUMN_DESCRIPTIONS = {
    "admissions": {
        "hadm_id": "Hospital admission ID, admission identifier, admission number, hospital stay ID, which admission",
        "subject_id": "Patient ID, patient identifier, patient number, which patient, patient reference",
        "admittime": "Admission time, when admitted, admission date, hospital admission time, when patient entered hospital",
        "dischtime": "Discharge time, when discharged, discharge date, when patient left hospital, hospital discharge time",
        "deathtime": "Death time, when patient died, time of death, death during admission",
        "admission_type": "Admission type: emergency elective urgent newborn, type of admission, admission category, emergency vs elective",
        "admission_location": "Admission location, where patient came from, admission source, transferred from where, patient origin",
        "discharge_location": "Discharge location, where patient went, discharge destination, transferred to where, discharge to home or facility",
        "insurance": "Insurance type, insurance provider, payer, Medicare Medicaid private insurance, insurance coverage",
        "language": "Patient language, what language does patient speak, language spoken",
        "religion": "Patient religion, religious affiliation",
        "marital_status": "Marital status, married single divorced widowed, marriage status",
        "ethnicity": "Patient ethnicity, race, ethnic background",
        "diagnosis": "Primary diagnosis, admission diagnosis, chief diagnosis, what disease, main condition",
        "hospital_expire_flag": "Hospital death flag, did patient die in hospital, mortality during admission, patient died yes or no"
    },
    
    "patients": {
        "subject_id": "Patient ID, patient identifier, patient number, unique patient, which patient",
        "gender": "Patient gender, male or female, sex, patient sex",
        "dob": "Date of birth, birth date, when born, patient birthday, DOB",
        "dod": "Date of death, death date, when died, patient death date, DOD",
        "expire_flag": "Death indicator, did patient die, patient expired, mortality flag, patient deceased"
    },
    
    "icustays": {
        "icustay_id": "ICU stay ID, ICU identifier, intensive care stay ID, which ICU stay",
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "intime": "ICU admission time, ICU in time, when entered ICU, ICU start time",
        "outtime": "ICU discharge time, ICU out time, when left ICU, ICU end time",
        "los": "Length of stay, how long in ICU, ICU duration, days in ICU, ICU length",
        "first_careunit": "First ICU unit, initial ICU, which ICU first, starting ICU unit",
        "last_careunit": "Last ICU unit, final ICU, which ICU last, ending ICU unit"
    },
    
    "diagnoses_icd": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "icd9_code": "ICD9 diagnosis code, diagnosis code, disease code, condition code",
        "seq_num": "Diagnosis sequence number, primary secondary diagnosis, diagnosis order, diagnosis rank"
    },
    
    "d_icd_diagnoses": {
        "icd9_code": "ICD9 diagnosis code, diagnosis code, disease code",
        "short_title": "Short diagnosis description, brief diagnosis name, diagnosis abbreviation",
        "long_title": "Full diagnosis description, complete diagnosis name, detailed diagnosis"
    },
    
    "procedures_icd": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "icd9_code": "ICD9 procedure code, procedure code, operation code, surgery code",
        "seq_num": "Procedure sequence number, procedure order, primary procedure"
    },
    
    "d_icd_procedures": {
        "icd9_code": "ICD9 procedure code, procedure code, operation code",
        "short_title": "Short procedure description, brief procedure name",
        "long_title": "Full procedure description, complete procedure name, detailed procedure"
    },
    
    "prescriptions": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "icustay_id": "ICU stay ID, ICU identifier",
        "startdate": "Prescription start date, when started, medication start, drug start date",
        "enddate": "Prescription end date, when stopped, medication end, drug stop date",
        "drug": "Drug name, medication name, drug identifier, what medication",
        "drug_name_poe": "Drug name provider order entry, medication name ordered",
        "drug_name_generic": "Generic drug name, generic medication name",
        "dose_val_rx": "Dose value, dosage amount, how much drug, medication dose",
        "dose_unit_rx": "Dose unit, dosage unit, mg mL units",
        "route": "Administration route, how given, oral IV IM, medication route, route of administration"
    },
    
    "labevents": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "itemid": "Lab item ID, lab test identifier, which lab test",
        "charttime": "Lab test time, when tested, lab collection time, test date time",
        "value": "Lab result value, lab value, test result text",
        "valuenum": "Lab numeric value, lab number result, test value number",
        "valueuom": "Lab unit of measurement, lab unit, test unit, measurement unit",
        "flag": "Abnormal flag, abnormal lab value, high low normal, flagged result"
    },
    
    "d_labitems": {
        "itemid": "Lab item ID, lab test identifier, which lab test",
        "label": "Lab test name, lab item name, test description",
        "fluid": "Specimen type, blood urine fluid, sample type, what specimen",
        "category": "Lab category, test category, chemistry hematology",
        "loinc_code": "LOINC code, lab standard code"
    },
    
    "chartevents": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "icustay_id": "ICU stay ID, ICU identifier",
        "itemid": "Item ID, measurement identifier, vital sign ID, which measurement",
        "charttime": "Chart time, measurement time, when recorded, vital sign time",
        "value": "Measurement value, vital sign value, recorded value text",
        "valuenum": "Numeric measurement value, vital sign number, value number",
        "valueuom": "Unit of measurement, measurement unit, vital sign unit",
        "cgid": "Caregiver ID, who recorded, staff who charted"
    },
    
    "inputevents_cv": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "icustay_id": "ICU stay ID, ICU identifier",
        "itemid": "Input item ID, fluid medication identifier, what given",
        "charttime": "Administration time, when given, infusion time",
        "amount": "Amount given, volume administered, how much fluid medication",
        "amountuom": "Amount unit, volume unit, mL L units",
        "rate": "Administration rate, infusion rate, flow rate",
        "rateuom": "Rate unit, infusion unit, mL per hour"
    },
    
    "inputevents_mv": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "icustay_id": "ICU stay ID, ICU identifier",
        "itemid": "Input item ID, fluid medication identifier, what given",
        "starttime": "Start time, infusion start, when started",
        "endtime": "End time, infusion end, when stopped",
        "amount": "Amount given, volume administered, how much fluid medication",
        "amountuom": "Amount unit, volume unit, mL L units",
        "rate": "Administration rate, infusion rate, flow rate",
        "rateuom": "Rate unit, infusion unit, mL per hour",
        "ordercategoryname": "Order category, medication type, fluid type"
    },
    
    "outputevents": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "icustay_id": "ICU stay ID, ICU identifier",
        "itemid": "Output item ID, output type identifier, urine drain output",
        "charttime": "Output time, when measured, measurement time",
        "value": "Output value, output amount, how much output volume",
        "valueuom": "Output unit, volume unit, mL units"
    },
    
    "microbiologyevents": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "chartdate": "Culture date, specimen date, when cultured",
        "charttime": "Culture time, specimen time",
        "spec_type_desc": "Specimen type, sample type, blood urine sputum culture",
        "org_name": "Organism name, bacteria name, what grew, microorganism cultured",
        "ab_name": "Antibiotic name, which antibiotic tested, drug tested",
        "interpretation": "Susceptibility result, sensitive resistant intermediate, S R I, antibiotic sensitivity"
    },
    
    "procedureevents_mv": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "icustay_id": "ICU stay ID, ICU identifier",
        "itemid": "Procedure item ID, procedure identifier, which procedure",
        "starttime": "Procedure start time, when started",
        "endtime": "Procedure end time, when finished",
        "ordercategoryname": "Procedure category, procedure type, dialysis intubation"
    },
    
    "noteevents": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "chartdate": "Note date, when written, documentation date",
        "charttime": "Note time, when documented",
        "category": "Note category, note type, discharge summary nursing radiology",
        "description": "Note description, note subtype",
        "text": "Note text, clinical note content, free text, what did doctor write, note documentation"
    },
    
    "d_items": {
        "itemid": "Item ID, measurement identifier, event item ID",
        "label": "Item name, measurement name, item label",
        "abbreviation": "Item abbreviation, short name",
        "category": "Item category, measurement category",
        "unitname": "Unit name, measurement unit",
        "linksto": "Links to table, which table uses this item, chartevents labevents"
    },
    
    "services": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "transfertime": "Service transfer time, when changed service, service change time",
        "prev_service": "Previous service, prior service, service transferred from",
        "curr_service": "Current service, new service, service transferred to, which service now"
    },
    
    "transfers": {
        "subject_id": "Patient ID, patient identifier, which patient",
        "hadm_id": "Hospital admission ID, admission identifier, which admission",
        "icustay_id": "ICU stay ID, ICU identifier",
        "intime": "Transfer in time, when arrived, location start time",
        "outtime": "Transfer out time, when left, location end time",
        "prev_careunit": "Previous unit, prior location, unit transferred from, where was patient",
        "curr_careunit": "Current unit, new location, unit transferred to, where is patient now",
        "eventtype": "Transfer event type, admit discharge transfer"
    }
}

# Embedding Model Recommendations
EMBEDDING_MODEL_RECOMMENDATIONS = """
Recommended Embedding Models for handling table/column name variations:

1. **sentence-transformers/all-mpnet-base-v2** (Recommended)
   - Best semantic understanding
   - Handles: "Lab Events" → "labevents", "ICU stay" → "icustays"
   - Good for medical domain

2. **sentence-transformers/all-MiniLM-L6-v2**
   - Faster, good performance
   - Handles case and space variations well
   - Lightweight option

3. **OpenAI text-embedding-3-small** or **text-embedding-3-large**
   - Excellent semantic matching
   - Handles: "patient diagnosis" → "diagnoses_icd"
   - Commercial option

4. **sentence-transformers/multi-qa-mpnet-base-dot-v1**
   - Optimized for question-answer matching
   - Good for doctor queries

Tips for better RAG matching:
- Use lowercase normalization before embedding
- Include both table names and common variations in descriptions
- Add medical synonyms (e.g., "lab tests" and "laboratory tests")
- Consider BM25 hybrid search for exact matches
"""

# Generate metadata only from the canonical original schema.
if __name__ == "__main__":
    import json
    from pathlib import Path
    from graph.tables import unique_columns

    Path(__file__).with_name("unique_columns.json").write_text(
        json.dumps(unique_columns(), indent=2, ensure_ascii=False) + "\n"
    )
