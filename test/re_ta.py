"""
MIMIC-III Table Retrieval System
Query tables using sentence embeddings with CLI interface
"""

import json
import argparse
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
from rich.console import Console
from rich.table import Table as RichTable
from rich.panel import Panel
from rich import print as rprint

# ========================================
# SAMPLE QUERIES JSON DATA
# ========================================

SAMPLE_QUERIES = {
    "queries": [
        # ADMISSIONS queries
        {
            "id": "q001",
            "query": "When was the patient admitted to the hospital?",
            "expected_tables": ["admissions"],
            "category": "admission_info"
        },
        {
            "id": "q002",
            "query": "What time did the patient get discharged?",
            "expected_tables": ["admissions"],
            "category": "discharge_info"
        },
        {
            "id": "q003",
            "query": "Did the patient die during hospitalization?",
            "expected_tables": ["admissions"],
            "category": "mortality"
        },
        {
            "id": "q004",
            "query": "What was the primary diagnosis at admission?",
            "expected_tables": ["admissions"],
            "category": "diagnosis"
        },
        {
            "id": "q005",
            "query": "Emergency or elective admission?",
            "expected_tables": ["admissions"],
            "category": "admission_type"
        },
        {
            "id": "q006",
            "query": "Patient insurance and demographics",
            "expected_tables": ["admissions"],
            "category": "demographics"
        },
        
        # PATIENTS queries
        {
            "id": "q007",
            "query": "How old is the patient?",
            "expected_tables": ["patients"],
            "category": "demographics"
        },
        {
            "id": "q008",
            "query": "Patient gender and date of birth",
            "expected_tables": ["patients"],
            "category": "demographics"
        },
        {
            "id": "q009",
            "query": "Is the patient deceased?",
            "expected_tables": ["patients"],
            "category": "mortality"
        },
        
        # DIAGNOSES queries
        {
            "id": "q010",
            "query": "What diseases does patient A have?",
            "expected_tables": ["diagnoses_icd", "d_icd_diagnoses"],
            "category": "diagnosis"
        },
        {
            "id": "q011",
            "query": "All diagnosis codes for this admission",
            "expected_tables": ["diagnoses_icd"],
            "category": "diagnosis"
        },
        {
            "id": "q012",
            "query": "What does ICD9 code 41401 mean?",
            "expected_tables": ["d_icd_diagnoses"],
            "category": "code_lookup"
        },
        {
            "id": "q013",
            "query": "Primary and secondary diagnoses",
            "expected_tables": ["diagnoses_icd"],
            "category": "diagnosis"
        },
        
        # ICUSTAYS queries
        {
            "id": "q014",
            "query": "When did patient enter ICU?",
            "expected_tables": ["icustays"],
            "category": "icu_admission"
        },
        {
            "id": "q015",
            "query": "How long was the patient in intensive care?",
            "expected_tables": ["icustays"],
            "category": "icu_los"
        },
        {
            "id": "q016",
            "query": "Which ICU unit was the patient in?",
            "expected_tables": ["icustays"],
            "category": "icu_location"
        },
        {
            "id": "q017",
            "query": "ICU length of stay in days",
            "expected_tables": ["icustays"],
            "category": "icu_los"
        },
        
        # LABEVENTS queries
        {
            "id": "q018",
            "query": "Patient lab test results",
            "expected_tables": ["labevents", "d_labitems"],
            "category": "lab_results"
        },
        {
            "id": "q019",
            "query": "Blood test values for patient B",
            "expected_tables": ["labevents"],
            "category": "lab_results"
        },
        {
            "id": "q020",
            "query": "Hemoglobin and creatinine levels",
            "expected_tables": ["labevents"],
            "category": "lab_results"
        },
        {
            "id": "q021",
            "query": "Abnormal lab values flagged",
            "expected_tables": ["labevents"],
            "category": "lab_results"
        },
        {
            "id": "q022",
            "query": "What lab tests are available?",
            "expected_tables": ["d_labitems"],
            "category": "item_lookup"
        },
        {
            "id": "q023",
            "query": "Lab events summary for patient",
            "expected_tables": ["labevents", "d_labitems"],
            "category": "lab_results"
        },
        
        # PRESCRIPTIONS queries
        {
            "id": "q024",
            "query": "What medications was patient prescribed?",
            "expected_tables": ["prescriptions"],
            "category": "medications"
        },
        {
            "id": "q025",
            "query": "Drug list after ICU admission",
            "expected_tables": ["prescriptions", "icustays"],
            "category": "medications"
        },
        {
            "id": "q026",
            "query": "Medication dosage and route",
            "expected_tables": ["prescriptions"],
            "category": "medications"
        },
        {
            "id": "q027",
            "query": "When did antibiotic treatment start?",
            "expected_tables": ["prescriptions"],
            "category": "medications"
        },
        
        # CHARTEVENTS queries
        {
            "id": "q028",
            "query": "Patient heart rate over time",
            "expected_tables": ["chartevents", "d_items"],
            "category": "vital_signs"
        },
        {
            "id": "q029",
            "query": "Blood pressure readings",
            "expected_tables": ["chartevents"],
            "category": "vital_signs"
        },
        {
            "id": "q030",
            "query": "Temperature and SpO2 values",
            "expected_tables": ["chartevents"],
            "category": "vital_signs"
        },
        {
            "id": "q031",
            "query": "Vital signs in the last 24 hours",
            "expected_tables": ["chartevents"],
            "category": "vital_signs"
        },
        
        # PROCEDURES queries
        {
            "id": "q032",
            "query": "What procedures were performed on patient?",
            "expected_tables": ["procedures_icd", "d_icd_procedures"],
            "category": "procedures"
        },
        {
            "id": "q033",
            "query": "Surgical procedures during admission",
            "expected_tables": ["procedures_icd"],
            "category": "procedures"
        },
        {
            "id": "q034",
            "query": "What does procedure code 9604 mean?",
            "expected_tables": ["d_icd_procedures"],
            "category": "code_lookup"
        },
        {
            "id": "q035",
            "query": "ICU procedures like dialysis or intubation",
            "expected_tables": ["procedureevents_mv"],
            "category": "icu_procedures"
        },
        
        # MICROBIOLOGY queries
        {
            "id": "q036",
            "query": "Culture results for patient",
            "expected_tables": ["microbiologyevents"],
            "category": "microbiology"
        },
        {
            "id": "q037",
            "query": "What bacteria grew in blood culture?",
            "expected_tables": ["microbiologyevents"],
            "category": "microbiology"
        },
        {
            "id": "q038",
            "query": "Antibiotic sensitivity testing results",
            "expected_tables": ["microbiologyevents"],
            "category": "microbiology"
        },
        {
            "id": "q039",
            "query": "Is the organism resistant to antibiotics?",
            "expected_tables": ["microbiologyevents"],
            "category": "microbiology"
        },
        
        # INPUT/OUTPUT queries
        {
            "id": "q040",
            "query": "Fluids administered to patient",
            "expected_tables": ["inputevents_cv", "inputevents_mv"],
            "category": "fluid_intake"
        },
        {
            "id": "q041",
            "query": "IV medications given in ICU",
            "expected_tables": ["inputevents_mv"],
            "category": "fluid_intake"
        },
        {
            "id": "q042",
            "query": "Urine output measurements",
            "expected_tables": ["outputevents"],
            "category": "fluid_output"
        },
        {
            "id": "q043",
            "query": "Fluid balance for patient",
            "expected_tables": ["inputevents_mv", "outputevents"],
            "category": "fluid_balance"
        },
        
        # NOTEEVENTS queries
        {
            "id": "q044",
            "query": "Doctor notes for patient C",
            "expected_tables": ["noteevents"],
            "category": "clinical_notes"
        },
        {
            "id": "q045",
            "query": "Discharge summary",
            "expected_tables": ["noteevents"],
            "category": "clinical_notes"
        },
        {
            "id": "q046",
            "query": "Nursing notes from ICU",
            "expected_tables": ["noteevents"],
            "category": "clinical_notes"
        },
        {
            "id": "q047",
            "query": "Radiology reports",
            "expected_tables": ["noteevents"],
            "category": "clinical_notes"
        },
        
        # TRANSFERS queries
        {
            "id": "q048",
            "query": "Where is the patient located now?",
            "expected_tables": ["transfers"],
            "category": "location"
        },
        {
            "id": "q049",
            "query": "Patient transfer history",
            "expected_tables": ["transfers"],
            "category": "location"
        },
        {
            "id": "q050",
            "query": "When was patient moved to ICU?",
            "expected_tables": ["transfers", "icustays"],
            "category": "location"
        },
        
        # SERVICES queries
        {
            "id": "q051",
            "query": "Which services were consulted?",
            "expected_tables": ["services"],
            "category": "services"
        },
        {
            "id": "q052",
            "query": "Transfer from cardiology to surgery",
            "expected_tables": ["services"],
            "category": "services"
        },
        
        # CPT/DRG queries
        {
            "id": "q053",
            "query": "Billing codes for procedures",
            "expected_tables": ["cptevents", "d_cpt"],
            "category": "billing"
        },
        {
            "id": "q054",
            "query": "DRG codes and severity scores",
            "expected_tables": ["drgcodes"],
            "category": "billing"
        },
        
        # CAREGIVERS queries
        {
            "id": "q055",
            "query": "Who provided care to the patient?",
            "expected_tables": ["caregivers"],
            "category": "staff"
        },
        
        # CALLOUT queries
        {
            "id": "q056",
            "query": "Discharge planning and transfer requests",
            "expected_tables": ["callout"],
            "category": "discharge_planning"
        },
        
        # Complex multi-table queries
        {
            "id": "q057",
            "query": "Complete patient summary: admission, diagnosis, procedures, medications",
            "expected_tables": ["admissions", "diagnoses_icd", "procedures_icd", "prescriptions"],
            "category": "comprehensive"
        },
        {
            "id": "q058",
            "query": "ICU patient monitoring: vital signs, labs, fluids",
            "expected_tables": ["chartevents", "labevents", "inputevents_mv", "outputevents"],
            "category": "comprehensive"
        },
        {
            "id": "q059",
            "query": "Patient outcome: length of stay, mortality, complications",
            "expected_tables": ["admissions", "icustays", "patients"],
            "category": "comprehensive"
        },
        {
            "id": "q060",
            "query": "Infection workup: labs, cultures, antibiotics",
            "expected_tables": ["labevents", "microbiologyevents", "prescriptions"],
            "category": "comprehensive"
        }
    ]
}

# Table descriptions for embedding
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


# ========================================
# RETRIEVAL SYSTEM
# ========================================

class TableRetriever:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize retriever with specified model
        
        Args:
            model_name: 'all-MiniLM-L6-v2' or 'all-mpnet-base-v2'
        """
        self.console = Console()
        self.model_name = model_name
        
        self.console.print(f"[cyan]Loading model: {model_name}...[/cyan]")
        self.model = SentenceTransformer(f'sentence-transformers/{model_name}')
        
        # Precompute table embeddings
        self.table_names = list(TABLE_DESCRIPTIONS.keys())
        self.table_descriptions = [TABLE_DESCRIPTIONS[name] for name in self.table_names]
        
        self.console.print("[cyan]Encoding table descriptions...[/cyan]")
        self.table_embeddings = self.model.encode(
            self.table_descriptions,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        self.console.print("[green]✓ Model loaded and ready![/green]\n")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Retrieve top-k most relevant tables for a query
        
        Args:
            query: User query string
            top_k: Number of top results to return
            
        Returns:
            List of (table_name, similarity_score) tuples
        """
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.table_embeddings)[0]
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Return results
        results = [(self.table_names[idx], float(similarities[idx])) for idx in top_indices]
        return results
    
    def display_results(self, query: str, results: List[Tuple[str, float]], expected: List[str] = None):
        """
        Display retrieval results in a nice format
        """
        # Query panel
        self.console.print(Panel(
            f"[bold cyan]{query}[/bold cyan]",
            title="Query",
            border_style="cyan"
        ))
        
        # Results table
        table = RichTable(title="Top Retrieved Tables", show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="dim", width=6)
        table.add_column("Table Name", style="cyan", width=25)
        table.add_column("Similarity", justify="right", width=12)
        table.add_column("Match", justify="center", width=8)
        
        for rank, (table_name, score) in enumerate(results, 1):
            # Check if it's expected
            is_match = ""
            if expected and table_name in expected:
                is_match = "✓"
                style = "green"
            else:
                style = "white"
            
            table.add_row(
                str(rank),
                f"[{style}]{table_name}[/{style}]",
                f"[{style}]{score:.4f}[/{style}]",
                f"[green]{is_match}[/green]" if is_match else ""
            )
        
        self.console.print(table)
        
        # Expected tables
        if expected:
            self.console.print(f"\n[yellow]Expected tables: {', '.join(expected)}[/yellow]")
        
        self.console.print("\n" + "="*80 + "\n")


# ========================================
# EVALUATION
# ========================================

def evaluate_retrieval(retriever: TableRetriever, queries: List[Dict], top_k: int = 5):
    """
    Evaluate retrieval performance on query set
    """
    console = Console()
    
    total_queries = len(queries)
    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    mrr_sum = 0
    
    console.print(f"\n[bold cyan]Evaluating on {total_queries} queries...[/bold cyan]\n")
    
    for query_data in queries:
        query = query_data['query']
        expected = query_data.get('expected_tables', [])
        
        if not expected:
            continue
        
        # Retrieve
        results = retriever.retrieve(query, top_k=top_k)
        retrieved_tables = [table_name for table_name, _ in results]
        
        # Calculate metrics
        found_at = None
        for idx, table in enumerate(retrieved_tables):
            if table in expected:
                if found_at is None:
                    found_at = idx + 1
                
                if idx == 0:
                    hits_at_1 += 1
                if idx < 3:
                    hits_at_3 += 1
                if idx < 5:
                    hits_at_5 += 1
        
        # MRR (Mean Reciprocal Rank)
        if found_at:
            mrr_sum += 1.0 / found_at
    
    # Calculate final metrics
    precision_at_1 = hits_at_1 / total_queries
    precision_at_3 = hits_at_3 / total_queries
    precision_at_5 = hits_at_5 / total_queries
    mrr = mrr_sum / total_queries
    
    # Display results
    metrics_table = RichTable(title="Evaluation Metrics", show_header=True, header_style="bold green")
    metrics_table.add_column("Metric", style="cyan", width=20)
    metrics_table.add_column("Value", justify="right", width=15)
    
    metrics_table.add_row("Precision@1", f"{precision_at_1:.4f}")
    metrics_table.add_row("Precision@3", f"{precision_at_3:.4f}")
    metrics_table.add_row("Precision@5", f"{precision_at_5:.4f}")
    metrics_table.add_row("MRR", f"{mrr:.4f}")
    
    console.print(metrics_table)
    console.print()


# ========================================
# CLI INTERFACE
# ========================================

def main():
    parser = argparse.ArgumentParser(
        description="MIMIC-III Table Retrieval System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use MiniLM model (faster)
  python retrieval.py --model mini-lm --query "When was patient admitted?"
  
  # Use MPNet model (better quality)
  python retrieval.py --model mpnet --query "Lab test results"
  
  # Run evaluation on sample queries
  python retrieval.py --model mini-lm --evaluate
  
  # Interactive mode
  python retrieval.py --model mpnet --interactive
  
  # Save sample queries to file
  python retrieval.py --save-queries queries.json
        """
    )
    
    parser.add_argument(
        '--model',
        type=str,
        choices=['mini-lm', 'mpnet'],
        default='mini-lm',
        help='Embedding model to use (default: mini-lm)'
    )
    
    parser.add_argument(
        '--query',
        type=str,
        help='Single query to run'
    )
    
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of top results to return (default: 5)'
    )
    
    parser.add_argument(
        '--evaluate',
        action='store_true',
        help='Run evaluation on sample queries'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Start interactive query mode'
    )
    
    parser.add_argument(
        '--save-queries',
        type=str,
        help='Save sample queries to JSON file'
    )
    
    parser.add_argument(
        '--load-queries',
        type=str,
        help='Load queries from JSON file'
    )
    
    args = parser.parse_args()
    
    console = Console()
    
    # Save sample queries
    if args.save_queries:
        with open(args.save_queries, 'w', encoding='utf-8') as f:
            json.dump(SAMPLE_QUERIES, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✓ Saved {len(SAMPLE_QUERIES['queries'])} queries to {args.save_queries}[/green]")
        return
    
    # Map model names
    model_map = {
        'mini-lm': 'all-MiniLM-L6-v2',
        'mpnet': 'all-mpnet-base-v2'
    }
    model_name = model_map[args.model]
    
    # Initialize retriever
    retriever = TableRetriever(model_name=model_name)
    
    # Load queries
    queries = SAMPLE_QUERIES['queries']
    if args.load_queries:
        with open(args.load_queries, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            queries = loaded.get('queries', loaded)
    
    # Single query mode
    if args.query:
        results = retriever.retrieve(args.query, top_k=args.top_k)
        retriever.display_results(args.query, results)
        return
    
    # Evaluation mode
    if args.evaluate:
        evaluate_retrieval(retriever, queries, top_k=args.top_k)
        
        # Show some examples
        console.print("[bold]Sample Retrievals:[/bold]\n")
        for i in range(min(5, len(queries))):
            query_data = queries[i]
            results = retriever.retrieve(query_data['query'], top_k=3)
            retriever.display_results(
                query_data['query'],
                results,
                expected=query_data.get('expected_tables')
            )
        return
    
    # Interactive mode
    if args.interactive:
        console.print("[bold cyan]Interactive Query Mode[/bold cyan]")
        console.print("Type your query or 'quit' to exit\n")
        
        while True:
            try:
                query = console.input("[bold green]Query:[/bold green] ")
                
                if query.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                if not query.strip():
                    continue
                
                results = retriever.retrieve(query, top_k=args.top_k)
                retriever.display_results(query, results)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()