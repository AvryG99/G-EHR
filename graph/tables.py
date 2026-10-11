# schema/tables.py

tables = {
    "admissions": {
        "description": "Hospital admissions. When was patient admitted? When discharged? What admission type? Emergency or elective admission? Patient demographics: insurance, language, religion, marital status, ethnicity. Admission location and discharge location. Did patient die in hospital? What was primary diagnosis at admission? Emergency department times.",
        "primary_key": "hadm_id",
        "attributes": {
            "row_id": {"datatype": "int32", "description": "Hospital admission ID, admission identifier, admission number, hospital stay ID, which admission"},
            "subject_id": {"datatype": "int32", "description": "Patient ID, patient identifier, patient number, which patient, patient reference"},
            "hadm_id": {"datatype": "int32", "description": "Hospital admission ID, admission identifier, which admission"},
            "admittime": {"datatype": "int64", "description": "Admission time, when admitted, admission date, hospital admission time, when patient entered hospital"},
            "dischtime": {"datatype": "int64", "description": "Discharge time, when discharged, discharge date, when patient left hospital, hospital discharge time"},
            "admission_type": {"datatype": "str", "description": "Admission type: emergency elective urgent newborn, type of admission, admission category, emergency vs elective"},
            "admission_location": {"datatype": "str", "description": "Admission location, where patient came from, admission source, transferred from where, patient origin"},
            "discharge_location": {"datatype": "str", "description": "Discharge location, where patient went, discharge destination, transferred to where, discharge to home or facility"},
            "insurance": {"datatype": "str", "description": "Patient’s insurance type"},
            "language": {"datatype": "str", "description": "Language spoken by the patient"},
            "marital_status": {"datatype": "str", "description": "Marital status of the patient"},
            "ethnicity": {"datatype": "str", "description": "Ethnicity of the patient"},
            "age": {"datatype": "number", "description": "Age of patient"}
        }
    },
    "chartevents": {
        "description": "Vital signs bedside measurements. Heart rate blood pressure temperature respiratory rate. Oxygen saturation SpO2. Ventilator settings. Nursing assessments. Patient vital signs over time. Hourly measurements.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Row identifier (internal use)"},
            "subject_id": {"datatype": "BIGINT", "description": "Reference to patient ID"},
            "hadm_id": {"datatype": "BIGINT", "description": "Reference to hospital admission ID"},
            "icustay_id": {"datatype": "DOUBLE PRECISION", "description": "Reference to ICU stay ID"},
            "itemid": {"datatype": "BIGINT", "description": "Identifier for measurement/item"},
            "charttime": {"datatype": "TEXT", "description": "Time of charted observation"},
            "valuenum": {"datatype": "DOUBLE PRECISION", "description": "Numeric value of observation (if applicable)"},
            "valueuom": {"datatype": "TEXT", "description": "Unit of measurement"}
        }
    },
    "d_icd_diagnoses": {
        "description": "ICD9 diagnosis code dictionary definitions. What does diagnosis code mean? Diagnosis code description. Short title and long title for ICD9 codes. Decode diagnosis codes.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Row identifier (internal use)"},
            "icd9_code": {"datatype": "TEXT", "description": "ICD-9 diagnosis code"},
            "short_title": {"datatype": "TEXT", "description": "Short description of the diagnosis"},
            "long_title": {"datatype": "TEXT", "description": "Full description of the diagnosis"}
        }
    },
    "d_icd_procedures": {
        "description": "ICD9 procedure code dictionary definitions. What does procedure code mean? Procedure code description. Short title and long title for procedure codes. Decode procedure codes.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Row identifier (internal use)"},
            "icd9_code": {"datatype": "BIGINT", "description": "ICD-9 procedure code"},
            "short_title": {"datatype": "TEXT", "description": "Short description of the procedure"},
            "long_title": {"datatype": "TEXT", "description": "Full description of the procedure"}
        }
    },
    "d_items": {
        "description": "Item dictionary for measurements. Chart events input events item definitions. What does item ID mean? Measurement names labels. Vital sign names medication names.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Row identifier (internal use)"},
            "itemid": {"datatype": "BIGINT", "description": "Unique identifier for item/measurement"},
            "label": {"datatype": "TEXT", "description": "Label or name of the item"},
            "linksto": {"datatype": "TEXT", "description": "Table this item links to (e.g., CHARTEVENTS, LABEVENTS)"}
        }
    },
    "d_labitems": {
        "description": "Lab test dictionary definitions. What lab test names. Lab item descriptions. Lab test categories. Blood urine tests. LOINC codes for lab tests.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Row identifier (internal use)"},
            "itemid": {"datatype": "BIGINT", "description": "Unique identifier for lab item"},
            "label": {"datatype": "TEXT", "description": "Name of the lab item"}
        }
    },
    "diagnoses_icd": {
        "description": "Patient diagnoses diagnosis codes ICD9 codes. What disease does patient have? What conditions diagnosed? All diagnoses for admission. Primary and secondary diagnoses. Diagnosis code lookup.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "icd9_code": {"datatype": "TEXT", "description": "ICD-9 diagnosis code"},
            "charttime": {"datatype": "TEXT", "description": "Time of charted event"}
        }
    },
    "icustays": {
        "description": "ICU stays intensive care unit. When did patient enter ICU? When did patient leave ICU? How long in ICU? Length of ICU stay. Which ICU unit? First ICU unit, last ICU unit. ICU admission and discharge times.",
        "primary_key": "icustay_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "icustay_id": {"datatype": "BIGINT", "description": "Unique ICU stay identifier"},
            "first_careunit": {"datatype": "TEXT", "description": "First ICU care unit of the stay"},
            "last_careunit": {"datatype": "TEXT", "description": "Last ICU care unit of the stay"},
            "first_wardid": {"datatype": "BIGINT", "description": "Identifier for the first ward"},
            "last_wardid": {"datatype": "BIGINT", "description": "Identifier for the last ward"},
            "intime": {"datatype": "TEXT", "description": "ICU admission time"},
            "outtime": {"datatype": "TEXT", "description": "ICU discharge time"},
        }
    },
    "inputevents_cv": {
        "description": "Fluids and medications given to patient CareVue system. IV fluids administered. Medication infusions. What fluids did patient receive? Fluid intake. Medication administration times and amounts.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "icustay_id": {"datatype": "BIGINT", "description": "Unique ICU stay identifier"},
            "charttime": {"datatype": "TEXT", "description": "Time of charted event"},
            "itemid": {"datatype": "BIGINT", "description": "Identifier for the administered item"},
            "amount": {"datatype": "DOUBLE PRECISION", "description": "Amount of fluid/medication administered"}
        }
    },
    "labevents": {
        "description": "Laboratory test results lab tests. Blood tests chemistry panels. Lab values. What were patient lab results? Hemoglobin glucose creatinine sodium potassium. Abnormal lab values flagged results. Lab test times.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "DOUBLE PRECISION", "description": "Hospital admission ID, links to admissions"},
            "itemid": {"datatype": "BIGINT", "description": "Identifier for lab test item"},
            "charttime": {"datatype": "TEXT", "description": "Time when the lab test was charted"},
            "valuenum": {"datatype": "DOUBLE PRECISION", "description": "Numeric value of the lab test result"},
            "valueuom": {"datatype": "TEXT", "description": "Unit of measurement for the test result"},
        }
    },
    "microbiologyevents": {
        "description": "Microbiology results cultures. Bacteria organisms cultured. Antibiotic sensitivity testing. What organisms grew? Antibiotic resistance. Culture results. Specimen types blood urine sputum. Susceptibility testing.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "charttime": {"datatype": "TEXT", "description": "Time when the microbiology event was charted"},
            "spec_type_desc": {"datatype": "TEXT", "description": "Description of the specimen type"},
            "org_name": {"datatype": "TEXT", "description": "Name of the cultured organism"}
        }
    },
    "outputevents": {
        "description": "Patient outputs urine output. Drain output. How much urine? Fluid output measurements. Output volumes over time.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "icustay_id": {"datatype": "DOUBLE PRECISION", "description": "Unique ICU stay identifier"},
            "charttime": {"datatype": "TEXT", "description": "Time when the output event was charted"},
            "itemid": {"datatype": "BIGINT", "description": "Identifier for the output item"},
            "value": {"datatype": "DOUBLE PRECISION", "description": "Numeric value of the output measurement"}
        }
    },
    "patients": {
        "description": "Patient demographics. Patient age, date of birth. Patient gender male or female. Patient death date. Did patient die? Patient survival status. Basic patient information.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier"},
            "gender": {"datatype": "TEXT", "description": "Patient gender"},
            "dob": {"datatype": "TEXT", "description": "Date of birth"},
            "dod": {"datatype": "TEXT", "description": "Date of death"}
        }
    },
    "prescriptions": {
        "description": "Medications prescribed to patient. What drugs prescribed? What medications ordered? Prescription start date and end date. Drug names generic and brand. Drug dosage and route. Oral IV medications.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "startdate": {"datatype": "TEXT", "description": "Start date of the prescription"},
            "enddate": {"datatype": "TEXT", "description": "End date of the prescription"},
            "drug": {"datatype": "TEXT", "description": "Drug identifier or name"},
            "dose_val_rx": {"datatype": "TEXT", "description": "Prescribed dose value"},
            "dose_unit_rx": {"datatype": "TEXT", "description": "Unit of the prescribed dose"},
            "route": {"datatype": "TEXT", "description": "Route of administration (e.g., oral, IV)"}
        }
    },
    "procedures_icd": {
        "description": "Procedures performed on patient. ICD9 procedure codes. What procedures did patient have? What operations? Surgical procedures. Medical procedures during admission.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "icd9_code": {"datatype": "BIGINT", "description": "ICD-9 procedure code"},
            "charttime": {"datatype": "TEXT", "description": "Time of charted observation"}
        }
    },
    "transfers": {
        "description": "Patient location changes ward transfers. Patient movement in hospital. Which unit? Transfer between units. When transferred? ICU transfers. Ward changes.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "icustay_id": {"datatype": "DOUBLE PRECISION", "description": "Unique ICU stay identifier"},
            "eventtype": {"datatype": "TEXT", "description": "Type of transfer event"},
            "intime": {"datatype": "TEXT", "description": "Transfer start time"},
            "outtime": {"datatype": "TEXT", "description": "Transfer end time"},
            "wardid": {"datatype": "INT", "description": "Identify the ward"}
        }   
    },
    "cost": {
        "description": "The cost attribute denotes the monetary cost/price incurred when accessing or joining a table, used to estimate the financial expense of query execution.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "eventtype": {"datatype": "TEXT", "description": "Type of transfer event"},
            "event_id": {"datatype": "BIGINT", "description": "Type of transfer event"},
            "charttime": {"datatype": "TEXT", "description": "Time of charted observation"},
            "cost": {"datatype": "TEXT", "description": "buffer"}
        }
    }
}
