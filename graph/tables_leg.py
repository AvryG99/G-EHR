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
            "deathtime": {"datatype": "int64", "description": "Death time, when patient died, time of death, death during admission"},
            "admission_type": {"datatype": "str", "description": "Admission type: emergency elective urgent newborn, type of admission, admission category, emergency vs elective"},
            "admission_location": {"datatype": "str", "description": "Admission location, where patient came from, admission source, transferred from where, patient origin"},
            "discharge_location": {"datatype": "str", "description": "Discharge location, where patient went, discharge destination, transferred to where, discharge to home or facility"},
            "insurance": {"datatype": "str", "description": "Patient’s insurance type"},
            "language": {"datatype": "str", "description": "Language spoken by the patient"},
            "religion": {"datatype": "str", "description": "Religion of the patient"},
            "marital_status": {"datatype": "str", "description": "Marital status of the patient"},
            "ethnicity": {"datatype": "str", "description": "Ethnicity of the patient"},
            "edregtime": {"datatype": "int64", "description": "Emergency department registration time"},
            "edouttime": {"datatype": "int64", "description": "Emergency department out time"},
            "diagnosis": {"datatype": "str", "description": "Primary diagnosis at admission"},
            "hospital_expire_flag": {"datatype": "BIGINT", "description": "Flag indicating if patient died in hospital"},
            "has_chartevents_data": {"datatype": "BIGINT", "description": "Flag indicating if chart events data available"}
        }
    },
    "callout": {
        "description": "Discharge planning transfer requests. Callout for patient discharge. Transfer acceptance rejection. Discharge coordination.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "int32", "description": "Row identifier (internal use)"},
            "subject_id": {"datatype": "int32", "description": "Reference to patient ID"},
            "hadm_id": {"datatype": "int32", "description": "Reference to hospital admission ID"},
            "submit_wardid": {"datatype": "int32", "description": "Ward ID where callout was submitted"},
            "submit_careunit": {"datatype": "str", "description": "Care unit where callout was submitted"},
            "curr_wardid": {"datatype": "int32", "description": "Current ward ID"},
            "curr_careunit": {"datatype": "str", "description": "Current care unit"},
            "callout_wardid": {"datatype": "int32", "description": "Destination ward ID for callout"},
            "callout_service": {"datatype": "str", "description": "Service associated with callout"},
            "request_tele": {"datatype": "int8", "description": "Flag for telemetry request"},
            "request_resp": {"datatype": "int8", "description": "Flag for respiratory request"},
            "request_cdiff": {"datatype": "int8", "description": "Flag for C. diff isolation request"},
            "request_mrsa": {"datatype": "int8", "description": "Flag for MRSA isolation request"},
            "request_vre": {"datatype": "int8", "description": "Flag for VRE isolation request"},
            "callout_status": {"datatype": "str", "description": "Status of callout"},
            "callout_outcome": {"datatype": "str", "description": "Outcome of callout"},
            "discharge_wardid": {"datatype": "int32", "description": "Ward ID for patient discharge"},
            "acknowledge_status": {"datatype": "str", "description": "Acknowledgement status"},
            "createtime": {"datatype": "int64", "description": "Time when callout was created"},
            "updatetime": {"datatype": "int64", "description": "Last update time of callout"},
            "acknowledgetime": {"datatype": "int64", "description": "Time when callout was acknowledged"},
            "outcometime": {"datatype": "int64", "description": "Time when callout outcome recorded"},
            "firstreservationtime": {"datatype": "int64", "description": "First reservation time"},
            "currentreservationtime": {"datatype": "int64", "description": "Current reservation time"}
        }
    },
    "caregivers": {
        "description": "Hospital staff doctors nurses. Who provided care? Caregiver roles. Staff identifiers.",
        "primary_key": "cgid",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Row identifier (internal use)"},
            "cgid": {"datatype": "BIGINT", "description": "Unique caregiver ID"},
            "label": {"datatype": "TEXT", "description": "Short label or identifier for caregiver"},
            "description": {"datatype": "TEXT", "description": "Description of caregiver role or type"}
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
            "storetime": {"datatype": "TEXT", "description": "Time data was stored"},
            "cgid": {"datatype": "BIGINT", "description": "Caregiver ID who entered the data"},
            "value": {"datatype": "TEXT", "description": "Raw value of the observation"},
            "valuenum": {"datatype": "DOUBLE PRECISION", "description": "Numeric value of observation (if applicable)"},
            "valueuom": {"datatype": "TEXT", "description": "Unit of measurement"},
            "warning": {"datatype": "DOUBLE PRECISION", "description": "Warning flag for observation"},
            "error": {"datatype": "DOUBLE PRECISION", "description": "Error flag for observation"},
            "resultstatus": {"datatype": "TEXT", "description": "Status of the result (e.g. final, amended)"},
            "stopped": {"datatype": "TEXT", "description": "Indicator if measurement was stopped"}
        }
    },
    "cptevents": {
        "description": "CPT billing codes procedures. Procedure billing. What procedures billed? CPT codes for procedures performed.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "costcenter": {"datatype": "TEXT", "description": "Hospital cost center associated with the event"},
            "chartdate": {"datatype": "TEXT", "description": "Date of CPT event"},
            "cpt_cd": {"datatype": "BIGINT", "description": "CPT (Current Procedural Terminology) code"},
            "cpt_number": {"datatype": "BIGINT", "description": "CPT numeric code"},
            "cpt_suffix": {"datatype": "DOUBLE PRECISION", "description": "CPT suffix (if any)"},
            "ticket_id_seq": {"datatype": "DOUBLE PRECISION", "description": "Ticket ID sequence for grouping"},
            "sectionheader": {"datatype": "TEXT", "description": "CPT section header"},
            "subsectionheader": {"datatype": "TEXT", "description": "CPT subsection header"},
            "description": {"datatype": "TEXT", "description": "Description of CPT code/event"}
        }
    },
    "d_cpt": {
        "description": "CPT code dictionary definitions. What does CPT code mean? CPT code descriptions. Billing code lookup.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Row identifier (internal use)"},
            "category": {"datatype": "BIGINT", "description": "Category code for CPT"},
            "sectionrange": {"datatype": "TEXT", "description": "Range of section codes"},
            "sectionheader": {"datatype": "TEXT", "description": "Section header description"},
            "subsectionrange": {"datatype": "TEXT", "description": "Range of subsection codes"},
            "subsectionheader": {"datatype": "TEXT", "description": "Subsection header description"},
            "codesuffix": {"datatype": "TEXT", "description": "Suffix used for CPT codes"},
            "mincodeinsubsection": {"datatype": "BIGINT", "description": "Minimum CPT code in subsection"},
            "maxcodeinsubsection": {"datatype": "BIGINT", "description": "Maximum CPT code in subsection"}
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
            "abbreviation": {"datatype": "TEXT", "description": "Abbreviation of the item"},
            "dbsource": {"datatype": "TEXT", "description": "Source database of the item"},
            "linksto": {"datatype": "TEXT", "description": "Table this item links to (e.g., CHARTEVENTS, LABEVENTS)"},
            "category": {"datatype": "TEXT", "description": "Category of the item"},
            "unitname": {"datatype": "TEXT", "description": "Measurement unit (if applicable)"},
            "param_type": {"datatype": "TEXT", "description": "Parameter type (e.g., numeric, text)"},
            "conceptid": {"datatype": "DOUBLE PRECISION", "description": "Concept identifier for mapping"}
        }
    },
    "d_labitems": {
        "description": "Lab test dictionary definitions. What lab test names. Lab item descriptions. Lab test categories. Blood urine tests. LOINC codes for lab tests.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Row identifier (internal use)"},
            "itemid": {"datatype": "BIGINT", "description": "Unique identifier for lab item"},
            "label": {"datatype": "TEXT", "description": "Name of the lab item"},
            "fluid": {"datatype": "TEXT", "description": "Type of fluid the lab item is performed on"},
            "category": {"datatype": "TEXT", "description": "Category of the lab item"},
            "loinc_code": {"datatype": "TEXT", "description": "LOINC code mapping (if available)"}
        }
    },
    "datetimeevents": {
        "description": "Events with datetime values. Procedure times event times. Time-based measurements.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Row identifier (internal use)"},
            "subject_id": {"datatype": "BIGINT", "description": "Reference to patient ID"},
            "hadm_id": {"datatype": "BIGINT", "description": "Reference to hospital admission ID"},
            "icustay_id": {"datatype": "DOUBLE PRECISION", "description": "Reference to ICU stay ID"},
            "itemid": {"datatype": "BIGINT", "description": "Identifier for measurement/item"},
            "charttime": {"datatype": "TEXT", "description": "Time of observation"},
            "storetime": {"datatype": "TEXT", "description": "Time data was stored"},
            "cgid": {"datatype": "BIGINT", "description": "Caregiver ID who entered the data"},
            "value": {"datatype": "TEXT", "description": "Raw value of the observation"},
            "valueuom": {"datatype": "TEXT", "description": "Unit of measurement"},
            "warning": {"datatype": "DOUBLE PRECISION", "description": "Warning flag"},
            "error": {"datatype": "DOUBLE PRECISION", "description": "Error flag"},
            "resultstatus": {"datatype": "DOUBLE PRECISION", "description": "Status of the result (numeric flag)"},
            "stopped": {"datatype": "TEXT", "description": "Indicator if observation was stopped"}
        }
    },
    "diagnoses_icd": {
        "description": "Patient diagnoses diagnosis codes ICD9 codes. What disease does patient have? What conditions diagnosed? All diagnoses for admission. Primary and secondary diagnoses. Diagnosis code lookup.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "seq_num": {"datatype": "BIGINT", "description": "Sequence number for diagnosis"},
            "icd9_code": {"datatype": "TEXT", "description": "ICD-9 diagnosis code"}
        }
    },
    "drgcodes": {
        "description": "DRG diagnosis related group codes. Hospital billing codes. Severity scores mortality risk. DRG descriptions.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Row identifier (internal use)"},
            "subject_id": {"datatype": "BIGINT", "description": "Reference to patient ID"},
            "hadm_id": {"datatype": "BIGINT", "description": "Reference to hospital admission ID"},
            "drg_type": {"datatype": "TEXT", "description": "Type of DRG code (e.g., HCFA, APR)"},
            "drg_code": {"datatype": "BIGINT", "description": "Diagnosis Related Group code"},
            "description": {"datatype": "TEXT", "description": "Description of the DRG code"},
            "drg_severity": {"datatype": "DOUBLE PRECISION", "description": "Severity score associated with DRG"},
            "drg_mortality": {"datatype": "DOUBLE PRECISION", "description": "Mortality risk score associated with DRG"}
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
            "dbsource": {"datatype": "TEXT", "description": "Source database"},
            "first_careunit": {"datatype": "TEXT", "description": "First ICU care unit of the stay"},
            "last_careunit": {"datatype": "TEXT", "description": "Last ICU care unit of the stay"},
            "first_wardid": {"datatype": "BIGINT", "description": "Identifier for the first ward"},
            "last_wardid": {"datatype": "BIGINT", "description": "Identifier for the last ward"},
            "intime": {"datatype": "TEXT", "description": "ICU admission time"},
            "outtime": {"datatype": "TEXT", "description": "ICU discharge time"},
            "los": {"datatype": "DOUBLE PRECISION", "description": "Length of stay in the ICU (days)"}
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
            "amount": {"datatype": "DOUBLE PRECISION", "description": "Amount of fluid/medication administered"},
            "amountuom": {"datatype": "TEXT", "description": "Unit of measurement for amount"},
            "rate": {"datatype": "DOUBLE PRECISION", "description": "Rate of administration"},
            "rateuom": {"datatype": "TEXT", "description": "Unit of measurement for rate"},
            "storetime": {"datatype": "TEXT", "description": "Time data was stored in system"},
            "cgid": {"datatype": "DOUBLE PRECISION", "description": "Identifier for caregiver who input data"},
            "orderid": {"datatype": "BIGINT", "description": "Order ID associated with this input event"},
            "linkorderid": {"datatype": "BIGINT", "description": "Linked order ID if applicable"},
            "stopped": {"datatype": "TEXT", "description": "Reason or indicator if the input was stopped"},
            "newbottle": {"datatype": "DOUBLE PRECISION", "description": "Indicator if a new bottle was started"},
            "originalamount": {"datatype": "DOUBLE PRECISION", "description": "Original amount prescribed"},
            "originalamountuom": {"datatype": "TEXT", "description": "Original unit of measurement for amount"},
            "originalroute": {"datatype": "TEXT", "description": "Original administration route"},
            "originalrate": {"datatype": "DOUBLE PRECISION", "description": "Original prescribed rate"},
            "originalrateuom": {"datatype": "TEXT", "description": "Original unit of measurement for rate"},
            "originalsite": {"datatype": "TEXT", "description": "Original site of administration"}
        }
    },
    "inputevents_mv": {
        "description": "Fluids and medications given to patient MetaVision system. IV fluids administered. Medication infusions. What fluids did patient receive? Fluid intake. Medication administration times and amounts.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "icustay_id": {"datatype": "BIGINT", "description": "Unique ICU stay identifier"},
            "starttime": {"datatype": "TEXT", "description": "Start time of input event"},
            "endtime": {"datatype": "TEXT", "description": "End time of input event"},
            "itemid": {"datatype": "BIGINT", "description": "Identifier for the administered item"},
            "amount": {"datatype": "DOUBLE PRECISION", "description": "Amount of fluid/medication administered"},
            "amountuom": {"datatype": "TEXT", "description": "Unit of measurement for amount"},
            "rate": {"datatype": "DOUBLE PRECISION", "description": "Rate of administration"},
            "rateuom": {"datatype": "TEXT", "description": "Unit of measurement for rate"},
            "storetime": {"datatype": "TEXT", "description": "Time data was stored in system"},
            "cgid": {"datatype": "BIGINT", "description": "Identifier for caregiver who input data"},
            "orderid": {"datatype": "BIGINT", "description": "Order ID associated with this input event"},
            "linkorderid": {"datatype": "BIGINT", "description": "Linked order ID if applicable"},
            "ordercategoryname": {"datatype": "TEXT", "description": "Category of the order"},
            "secondaryordercategoryname": {"datatype": "TEXT", "description": "Secondary category of the order"},
            "ordercomponenttypedescription": {"datatype": "TEXT", "description": "Description of the order component type"},
            "ordercategorydescription": {"datatype": "TEXT", "description": "Description of the order category"},
            "patientweight": {"datatype": "DOUBLE PRECISION", "description": "Patient weight at time of order"},
            "totalamount": {"datatype": "DOUBLE PRECISION", "description": "Total amount administered"},
            "totalamountuom": {"datatype": "TEXT", "description": "Unit of measurement for total amount"},
            "isopenbag": {"datatype": "BIGINT", "description": "Indicator if medication is from an open bag"},
            "continueinnextdept": {"datatype": "BIGINT", "description": "Indicator if the input continues in next department"},
            "cancelreason": {"datatype": "BIGINT", "description": "Reason code for cancellation"},
            "statusdescription": {"datatype": "TEXT", "description": "Description of order status"},
            "comments_editedby": {"datatype": "TEXT", "description": "User who last edited comments"},
            "comments_canceledby": {"datatype": "TEXT", "description": "User who canceled the order"},
            "comments_date": {"datatype": "TEXT", "description": "Date when comments were recorded"},
            "originalamount": {"datatype": "DOUBLE PRECISION", "description": "Original prescribed amount"},
            "originalrate": {"datatype": "DOUBLE PRECISION", "description": "Original prescribed rate"}
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
            "value": {"datatype": "TEXT", "description": "Raw text result of the lab test"},
            "valuenum": {"datatype": "DOUBLE PRECISION", "description": "Numeric value of the lab test result"},
            "valueuom": {"datatype": "TEXT", "description": "Unit of measurement for the test result"},
            "flag": {"datatype": "TEXT", "description": "Indicator if the lab value is abnormal or flagged"}
        }
    },
    "microbiologyevents": {
        "description": "Microbiology results cultures. Bacteria organisms cultured. Antibiotic sensitivity testing. What organisms grew? Antibiotic resistance. Culture results. Specimen types blood urine sputum. Susceptibility testing.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "chartdate": {"datatype": "TEXT", "description": "Date when the microbiology event was charted"},
            "charttime": {"datatype": "TEXT", "description": "Time when the microbiology event was charted"},
            "spec_itemid": {"datatype": "BIGINT", "description": "Identifier for specimen type"},
            "spec_type_desc": {"datatype": "TEXT", "description": "Description of the specimen type"},
            "org_itemid": {"datatype": "DOUBLE PRECISION", "description": "Identifier for the cultured organism"},
            "org_name": {"datatype": "TEXT", "description": "Name of the cultured organism"},
            "isolate_num": {"datatype": "DOUBLE PRECISION", "description": "Isolate number for the culture"},
            "ab_itemid": {"datatype": "DOUBLE PRECISION", "description": "Identifier for antibiotic tested"},
            "ab_name": {"datatype": "TEXT", "description": "Name of antibiotic tested"},
            "dilution_text": {"datatype": "TEXT", "description": "Text representation of dilution"},
            "dilution_comparison": {"datatype": "TEXT", "description": "Comparison operator for dilution (e.g., <=, =)"},
            "dilution_value": {"datatype": "DOUBLE PRECISION", "description": "Numeric value of dilution"},
            "interpretation": {"datatype": "TEXT", "description": "Interpretation of susceptibility (e.g., S, I, R)"}
        }
    },
    "noteevents": {
        "description": "Clinical notes doctor notes nurse notes. Discharge summaries. Radiology reports. Progress notes. Clinical documentation. Free text notes. What did doctor write? Nursing notes. Physician notes.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "TEXT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "TEXT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "TEXT", "description": "Hospital admission ID, links to admissions"},
            "chartdate": {"datatype": "TEXT", "description": "Date when the note was created"},
            "charttime": {"datatype": "TEXT", "description": "Time when the note was created"},
            "storetime": {"datatype": "TEXT", "description": "Time when the note was stored"},
            "category": {"datatype": "TEXT", "description": "Category of the clinical note (e.g., Nursing, Radiology)"},
            "description": {"datatype": "TEXT", "description": "Description or subtype of the note"},
            "cgid": {"datatype": "TEXT", "description": "Identifier for the caregiver who created the note"},
            "iserror": {"datatype": "TEXT", "description": "Indicator if the note contains an error"},
            "text": {"datatype": "TEXT", "description": "Full content of the clinical note"}
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
            "value": {"datatype": "DOUBLE PRECISION", "description": "Numeric value of the output measurement"},
            "valueuom": {"datatype": "TEXT", "description": "Unit of measurement for the output value"},
            "storetime": {"datatype": "TEXT", "description": "Time the event was stored in the system"},
            "cgid": {"datatype": "BIGINT", "description": "Identifier for caregiver who input data"},
            "stopped": {"datatype": "DOUBLE PRECISION", "description": "Indicator if the output event was stopped"},
            "newbottle": {"datatype": "DOUBLE PRECISION", "description": "Indicator if a new bottle was used"},
            "iserror": {"datatype": "DOUBLE PRECISION", "description": "Indicator if there was an error in measurement"}
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
            "dod": {"datatype": "TEXT", "description": "Date of death"},
            "dod_hosp": {"datatype": "TEXT", "description": "Date of death recorded in hospital"},
            "dod_ssn": {"datatype": "TEXT", "description": "Date of death from social security"},
            "expire_flag": {"datatype": "BIGINT", "description": "Indicator if the patient expired during hospital stay"}
        }
    },
    "prescriptions": {
        "description": "Medications prescribed to patient. What drugs prescribed? What medications ordered? Prescription start date and end date. Drug names generic and brand. Drug dosage and route. Oral IV medications.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "icustay_id": {"datatype": "DOUBLE PRECISION", "description": "Unique ICU stay identifier"},
            "startdate": {"datatype": "TEXT", "description": "Start date of the prescription"},
            "enddate": {"datatype": "TEXT", "description": "End date of the prescription"},
            "drug_type": {"datatype": "TEXT", "description": "Type of drug (e.g., IV, oral)"},
            "drug": {"datatype": "TEXT", "description": "Drug identifier or name"},
            "drug_name_poe": {"datatype": "TEXT", "description": "Provider order entry drug name"},
            "drug_name_generic": {"datatype": "TEXT", "description": "Generic drug name"},
            "formulary_drug_cd": {"datatype": "TEXT", "description": "Formulary drug code"},
            "gsn": {"datatype": "DOUBLE PRECISION", "description": "Generic sequence number"},
            "ndc": {"datatype": "DOUBLE PRECISION", "description": "National drug code"},
            "prod_strength": {"datatype": "TEXT", "description": "Product strength"},
            "dose_val_rx": {"datatype": "TEXT", "description": "Prescribed dose value"},
            "dose_unit_rx": {"datatype": "TEXT", "description": "Unit of the prescribed dose"},
            "form_val_disp": {"datatype": "TEXT", "description": "Dispensed form value"},
            "form_unit_disp": {"datatype": "TEXT", "description": "Unit of the dispensed form"},
            "route": {"datatype": "TEXT", "description": "Route of administration (e.g., oral, IV)"}
        }
    },
    "procedureevents_mv": {
        "description": "Procedures performed in ICU MetaVision. Dialysis intubation procedures. Invasive procedures. What procedures in ICU? Procedure start and end times.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "icustay_id": {"datatype": "BIGINT", "description": "Unique ICU stay identifier"},
            "starttime": {"datatype": "TEXT", "description": "Start time of the procedure event"},
            "endtime": {"datatype": "TEXT", "description": "End time of the procedure event"},
            "itemid": {"datatype": "BIGINT", "description": "Identifier for the procedure item"},
            "value": {"datatype": "BIGINT", "description": "Numeric value associated with the procedure"},
            "valueuom": {"datatype": "TEXT", "description": "Unit of measurement for the value"},
            "location": {"datatype": "TEXT", "description": "Location where the procedure was performed"},
            "locationcategory": {"datatype": "TEXT", "description": "Category of the location"},
            "storetime": {"datatype": "TEXT", "description": "Time the procedure event was stored in the system"},
            "cgid": {"datatype": "BIGINT", "description": "Identifier for caregiver who input the procedure data"},
            "orderid": {"datatype": "BIGINT", "description": "Order ID associated with this procedure event"},
            "linkorderid": {"datatype": "BIGINT", "description": "Linked order ID if applicable"},
            "ordercategoryname": {"datatype": "TEXT", "description": "Category of the order"},
            "secondaryordercategoryname": {"datatype": "DOUBLE PRECISION", "description": "Secondary category of the order"},
            "ordercategorydescription": {"datatype": "TEXT", "description": "Description of the order category"},
            "isopenbag": {"datatype": "BIGINT", "description": "Indicator if medication is from an open bag"},
            "continueinnextdept": {"datatype": "BIGINT", "description": "Indicator if the procedure continues in next department"},
            "cancelreason": {"datatype": "BIGINT", "description": "Reason code for cancellation"},
            "statusdescription": {"datatype": "TEXT", "description": "Description of order status"},
            "comments_editedby": {"datatype": "TEXT", "description": "User who last edited comments"},
            "comments_canceledby": {"datatype": "TEXT", "description": "User who canceled the order"},
            "comments_date": {"datatype": "TEXT", "description": "Date when comments were recorded"}
        }
    },
    "procedures_icd": {
        "description": "Procedures performed on patient. ICD9 procedure codes. What procedures did patient have? What operations? Surgical procedures. Medical procedures during admission.",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "seq_num": {"datatype": "BIGINT", "description": "Sequence number for procedure"},
            "icd9_code": {"datatype": "BIGINT", "description": "ICD-9 procedure code"}
        }
    },
    "services": {
        "description": "Hospital services consulted. Cardiology surgery services. Which services consulted? Service transfers. What specialty services involved?",
        "primary_key": "row_id",
        "attributes": {
            "row_id": {"datatype": "BIGINT", "description": "Internal row identifier"},
            "subject_id": {"datatype": "BIGINT", "description": "Unique patient identifier, links to patients"},
            "hadm_id": {"datatype": "BIGINT", "description": "Hospital admission ID, links to admissions"},
            "transfertime": {"datatype": "TEXT", "description": "Time of service transfer"},
            "prev_service": {"datatype": "TEXT", "description": "Previous care service"},
            "curr_service": {"datatype": "TEXT", "description": "Current care service after transfer"}
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
            "dbsource": {"datatype": "TEXT", "description": "Source database"},
            "eventtype": {"datatype": "TEXT", "description": "Type of transfer event"},
            "prev_careunit": {"datatype": "TEXT", "description": "Previous ICU care unit"},
            "curr_careunit": {"datatype": "TEXT", "description": "Current ICU care unit after transfer"},
            "prev_wardid": {"datatype": "DOUBLE PRECISION", "description": "Previous ward identifier"},
            "curr_wardid": {"datatype": "DOUBLE PRECISION", "description": "Current ward identifier after transfer"},
            "intime": {"datatype": "TEXT", "description": "Transfer start time"},
            "outtime": {"datatype": "TEXT", "description": "Transfer end time"},
            "los": {"datatype": "DOUBLE PRECISION", "description": "Length of stay in the unit (days)"}
        }
    }
}
