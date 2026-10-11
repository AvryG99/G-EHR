import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

class EnhancedMIMICRetriever:
    """
    Enhanced RAG module with Re-ranking, Query Expansion, and Score Boosting
    for retrieving relevant MIMIC-III columns based on medical queries
    """
    
    def __init__(self, json_file_path: str):
        """
        Initialize retriever
        
        Args:
            json_file_path: Path to JSON file containing column metadata
        """
        # Load column data from JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            self.columns_data = json.load(f)
        
        # Initialize sentence transformer model
        print("Loading all-mpnet-base-v2 model...")
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        
        # Prepare embeddings
        self.column_names = []
        self.column_texts = []
        self.column_metadata = []
        
        # Keywords mapping for boosting
        self.keyword_boost_map = self._init_keyword_boost_map()
        
        self._prepare_column_embeddings()
        
    def _init_keyword_boost_map(self) -> Dict[str, List[str]]:
        """
        Initialize mapping between keywords and related columns
        Used for score boosting based on keyword matching
        
        Returns:
            Dictionary mapping keywords -> column names
        """
        return {
            # Patient identification
            'patient': ['subject_id', 'hadm_id', 'icustay_id'],
            'admission': ['subject_id', 'hadm_id', 'admittime', 'dischtime', 'admission_type', 'admission_location'],
            
            # Medications
            'medication': ['drug', 'drug_name_poe', 'drug_name_generic', 'dose_val_rx', 'dose_unit_rx', 'route', 'startdate', 'enddate'],
            'drug': ['drug', 'drug_name_poe', 'drug_name_generic', 'formulary_drug_cd', 'gsn', 'ndc'],
            'prescription': ['drug', 'dose_val_rx', 'dose_unit_rx', 'route', 'startdate', 'enddate'],
            'antibiotic': ['drug', 'ab_name', 'interpretation', 'org_name'],
            'dose': ['dose_val_rx', 'dose_unit_rx', 'amount', 'amountuom'],
            
            # Lab tests
            'lab': ['itemid', 'value', 'valuenum', 'valueuom', 'flag', 'charttime'],
            'test': ['itemid', 'value', 'valuenum', 'flag', 'label'],
            'blood': ['itemid', 'value', 'valuenum', 'fluid', 'spec_type_desc'],
            'laboratory': ['itemid', 'value', 'valuenum', 'valueuom', 'flag', 'loinc_code'],
            'result': ['value', 'valuenum', 'valueuom', 'flag'],
            
            # Diagnoses
            'diagnosis': ['icd9_code', 'seq_num', 'short_title', 'long_title'],
            'disease': ['icd9_code', 'short_title', 'long_title', 'diagnosis'],
            'condition': ['icd9_code', 'short_title', 'long_title'],
            'icd': ['icd9_code', 'seq_num', 'short_title', 'long_title'],
            
            # Procedures
            'procedure': ['icd9_code', 'seq_num', 'short_title', 'long_title', 'procedureevents_mv'],
            'surgery': ['icd9_code', 'seq_num', 'short_title', 'long_title'],
            'operation': ['icd9_code', 'seq_num', 'starttime', 'endtime'],
            
            # Vital signs
            'vital': ['itemid', 'value', 'valuenum', 'valueuom', 'charttime'],
            'vitals': ['itemid', 'value', 'valuenum', 'valueuom', 'charttime'],
            'temperature': ['itemid', 'value', 'valuenum', 'charttime'],
            'blood pressure': ['itemid', 'value', 'valuenum', 'charttime'],
            'heart rate': ['itemid', 'value', 'valuenum', 'charttime'],
            'respiratory': ['itemid', 'value', 'valuenum', 'charttime'],
            
            # Time-related
            'time': ['charttime', 'admittime', 'dischtime', 'starttime', 'endtime', 'intime', 'outtime'],
            'date': ['charttime', 'admittime', 'dischtime', 'chartdate', 'startdate', 'enddate'],
            'duration': ['starttime', 'endtime', 'startdate', 'enddate', 'los'],
            'period': ['starttime', 'endtime', 'admittime', 'dischtime'],
            'when': ['charttime', 'admittime', 'dischtime', 'starttime', 'endtime'],
            
            # Admission/Discharge
            'admit': ['admittime', 'admission_type', 'admission_location', 'hadm_id'],
            'discharge': ['dischtime', 'discharge_location', 'hadm_id'],
            'hospital stay': ['admittime', 'dischtime', 'hadm_id', 'los'],
            'length of stay': ['los', 'admittime', 'dischtime'],
            
            # ICU
            'icu': ['icustay_id', 'intime', 'outtime', 'first_careunit', 'last_careunit', 'los'],
            'intensive care': ['icustay_id', 'intime', 'outtime', 'first_careunit', 'last_careunit'],
            'critical care': ['icustay_id', 'first_careunit', 'last_careunit'],
            
            # Microbiology
            'culture': ['spec_type_desc', 'org_name', 'ab_name', 'interpretation', 'chartdate'],
            'microbiology': ['spec_type_desc', 'org_name', 'ab_name', 'interpretation'],
            'organism': ['org_name', 'spec_type_desc', 'interpretation'],
            'infection': ['org_name', 'spec_type_desc', 'ab_name', 'interpretation'],
            'susceptibility': ['ab_name', 'interpretation', 'org_name'],
            'sensitivity': ['ab_name', 'interpretation', 'org_name'],
            'resistant': ['interpretation', 'ab_name', 'org_name'],
            
            # Input/Output
            'infusion': ['itemid', 'amount', 'amountuom', 'rate', 'rateuom', 'starttime', 'endtime'],
            'input': ['itemid', 'amount', 'amountuom', 'rate', 'rateuom'],
            'output': ['itemid', 'value', 'valueuom', 'charttime'],
            'fluid': ['amount', 'amountuom', 'rate', 'rateuom', 'fluid'],
            'iv': ['itemid', 'amount', 'rate', 'starttime', 'endtime'],
            'intravenous': ['itemid', 'amount', 'rate', 'starttime', 'endtime'],
            
            # Demographics
            'age': ['dob', 'admittime'],
            'gender': ['gender'],
            'sex': ['gender'],
            'demographic': ['gender', 'dob', 'ethnicity', 'marital_status'],
            'ethnicity': ['ethnicity'],
            'race': ['ethnicity'],
            
            # Mortality
            'death': ['deathtime', 'dod', 'hospital_expire_flag', 'expire_flag'],
            'mortality': ['hospital_expire_flag', 'expire_flag', 'deathtime', 'dod'],
            'died': ['deathtime', 'dod', 'hospital_expire_flag', 'expire_flag'],
            'survival': ['expire_flag', 'hospital_expire_flag', 'dod'],
            
            # Notes/Documentation
            'note': ['text', 'description', 'chartdate', 'category'],
            'documentation': ['text', 'description', 'cgid'],
            'report': ['text', 'description', 'chartdate'],
            
            # Transfers
            'transfer': ['prev_careunit', 'curr_careunit', 'eventtype', 'intime', 'outtime'],
            'location': ['prev_careunit', 'curr_careunit', 'admission_location', 'discharge_location'],
            'unit': ['first_careunit', 'last_careunit', 'prev_careunit', 'curr_careunit'],
        }
    
    def _prepare_column_embeddings(self):
        """Create embeddings for all columns in database"""
        print("Creating embeddings for columns...")
        
        for col_name, col_info in self.columns_data.items():
            self.column_names.append(col_name)
            self.column_metadata.append(col_info)
            
            # Create full text description for each column
            text = f"{col_name}. "
            text += f"Description: {col_info.get('description', 'No description available')}. "
            
            # Add data_type if available
            if 'data_type' in col_info:
                text += f"Data type: {col_info['data_type']}. "
            
            # Add tables if available
            if 'tables' in col_info and col_info['tables']:
                text += f"Found in tables: {', '.join(col_info['tables'])}"
            
            self.column_texts.append(text)
        
        # Create embeddings for all columns
        self.column_embeddings = self.model.encode(
            self.column_texts, 
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        print(f"Created embeddings for {len(self.column_names)} columns")
    
    def _apply_keyword_boosting(self, query: str, similarities: np.ndarray, boost_weight: float = 0.2) -> np.ndarray:
        """
        Apply keyword boosting based on query
        
        Args:
            query: Query string
            similarities: Array of similarity scores
            boost_weight: Boost weight (0-1)
            
        Returns:
            Array of boosted similarity scores
        """
        query_lower = query.lower()
        boost_scores = np.zeros_like(similarities)
        
        # Find keywords in query
        matched_keywords = []
        for keyword in self.keyword_boost_map.keys():
            if keyword in query_lower:
                matched_keywords.append(keyword)
        
        # Boost related columns
        if matched_keywords:
            for keyword in matched_keywords:
                relevant_columns = self.keyword_boost_map[keyword]
                for col in relevant_columns:
                    if col in self.column_names:
                        idx = self.column_names.index(col)
                        boost_scores[idx] += boost_weight / len(matched_keywords)
        
        # Normalize boost scores
        if boost_scores.max() > 0:
            boost_scores = boost_scores / boost_scores.max() * boost_weight
        
        # Combine: (1 - boost_weight) * similarity + boost
        final_scores = similarities * (1 - boost_weight) + boost_scores
        
        return final_scores
    
    def _rerank_by_table_coherence(self, candidates: List[Dict], top_k: int) -> List[Dict]:
        """
        Re-rank results based on table coherence
        Prioritize columns from same tables for efficient querying
        
        Args:
            candidates: List of candidate columns
            top_k: Number of final results
            
        Returns:
            Re-ranked list
        """
        if len(candidates) <= 1:
            return candidates
        
        # Count table occurrences
        table_counts = defaultdict(int)
        for cand in candidates:
            for table in cand['tables']:
                table_counts[table] += 1
        
        max_table_count = max(table_counts.values()) if table_counts else 1
        
        # Calculate coherence score for each candidate
        for cand in candidates:
            if cand['tables']:
                # Coherence = average occurrence of tables
                coherence_score = sum(table_counts[t] for t in cand['tables']) / len(cand['tables'])
                coherence_normalized = coherence_score / max_table_count
            else:
                coherence_normalized = 0
            
            # Combine similarity and coherence (75% similarity, 25% coherence)
            cand['final_score'] = cand['similarity_score'] * 0.75 + coherence_normalized * 0.25
            cand['coherence_score'] = coherence_normalized
        
        # Sort by final_score
        candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return candidates[:top_k]
    
    def _generate_query_expansions(self, query: str) -> List[str]:
        """
        Automatically generate query expansions
        
        Args:
            query: Original query
            
        Returns:
            List of expanded queries
        """
        expansions = []
        query_lower = query.lower()
        
        # Medical synonyms and related terms
        expansion_map = {
            'medication': ['drug', 'prescription', 'treatment', 'therapy'],
            'drug': ['medication', 'prescription', 'pharmaceutical'],
            'test': ['lab', 'examination', 'investigation', 'analysis'],
            'lab': ['laboratory', 'test', 'blood work'],
            'diagnosis': ['disease', 'condition', 'disorder', 'illness'],
            'procedure': ['surgery', 'operation', 'intervention', 'treatment'],
            'vital': ['vitals', 'vital signs', 'measurements', 'monitoring'],
            'culture': ['microbiology', 'organism', 'infection', 'bacteria'],
            'time': ['date', 'when', 'period', 'duration'],
            'patient': ['subject', 'individual', 'case'],
            'admission': ['admit', 'hospitalization', 'hospital stay'],
            'discharge': ['release', 'hospital exit', 'leaving hospital'],
            'icu': ['intensive care', 'critical care', 'intensive care unit'],
            'antibiotic': ['antimicrobial', 'antibacterial', 'anti-infective'],
        }
        
        # Generate expansions
        for key_word, synonyms in expansion_map.items():
            if key_word in query_lower:
                for synonym in synonyms[:2]:  # Take first 2 synonyms
                    expanded = query_lower.replace(key_word, synonym)
                    if expanded != query_lower:
                        expansions.append(expanded)
        
        return expansions[:3]  # Limit to 3 expansions
    
    def retrieve_columns(
        self, 
        query: str, 
        top_k: int = 10,
        similarity_threshold: float = 0.3,
        use_reranking: bool = True,
        use_boosting: bool = True,
        boost_weight: float = 0.2
    ) -> List[Dict]:
        """
        Retrieve relevant columns with advanced techniques
        
        Args:
            query: Medical query
            top_k: Maximum number of columns to retrieve
            similarity_threshold: Minimum similarity threshold
            use_reranking: Use re-ranking or not
            use_boosting: Use keyword boosting or not
            boost_weight: Boost weight (0-1)
            
        Returns:
            List of dictionaries containing column info and similarity scores
        """
        # Create embedding for query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, self.column_embeddings)[0]
        
        # Apply keyword boosting
        if use_boosting:
            similarities = self._apply_keyword_boosting(query, similarities, boost_weight)
        
        # Get top candidates (2x for re-ranking)
        initial_k = top_k * 2 if use_reranking else top_k
        top_indices = np.argsort(similarities)[::-1][:initial_k]
        
        # Create initial results
        candidates = []
        for idx in top_indices:
            score = similarities[idx]
            
            if score >= similarity_threshold:
                candidates.append({
                    'column_name': self.column_names[idx],
                    'similarity_score': float(score),
                    'description': self.column_metadata[idx].get('description', 'N/A')[:200],
                    'data_type': self.column_metadata[idx].get('data_type', 'N/A'),
                    'tables': self.column_metadata[idx].get('tables', [])
                })
        
        # Re-ranking based on table coherence
        if use_reranking:
            candidates = self._rerank_by_table_coherence(candidates, top_k)
        else:
            candidates = candidates[:top_k]
        
        return candidates
    
    def retrieve_with_query_expansion(
        self,
        query: str,
        expansion_queries: List[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Retrieve with query expansion - expand query into multiple variants
        
        Args:
            query: Original query
            expansion_queries: Expansion queries (auto-generated if None)
            top_k: Number of results
            
        Returns:
            List of retrieved columns
        """
        # Auto-generate expansions if not provided
        if expansion_queries is None:
            expansion_queries = self._generate_query_expansions(query)
        
        all_queries = [query] + expansion_queries
        
        # Retrieve for each query
        all_results = defaultdict(lambda: {'score': 0, 'count': 0, 'info': None})
        
        for q in all_queries:
            results = self.retrieve_columns(q, top_k=top_k * 2, use_reranking=True, use_boosting=True)
            for r in results:
                col_name = r['column_name']
                all_results[col_name]['score'] += r['similarity_score']
                all_results[col_name]['count'] += 1
                if all_results[col_name]['info'] is None:
                    all_results[col_name]['info'] = r
        
        # Calculate average score
        final_results = []
        for col_name, data in all_results.items():
            avg_score = data['score'] / len(all_queries)
            info = data['info']
            info['similarity_score'] = avg_score
            info['query_coverage'] = data['count'] / len(all_queries)
            final_results.append(info)
        
        # Sort and return top_k
        final_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return final_results[:top_k]
    
    def format_results(self, results: List[Dict]) -> str:
        """
        Format results in readable form
        
        Args:
            results: List of retrieved columns
            
        Returns:
            Formatted string
        """
        if not results:
            return "No relevant columns found for the query."
        
        output = f"\n{'='*80}\n"
        output += f"Found {len(results)} relevant columns:\n"
        output += f"{'='*80}\n\n"
        
        for i, result in enumerate(results, 1):
            output += f"{i}. Column: {result['column_name']}\n"
            output += f"   Similarity Score: {result['similarity_score']:.3f}\n"
            if 'coherence_score' in result:
                output += f"   Table Coherence: {result['coherence_score']:.3f}\n"
            if 'final_score' in result:
                output += f"   Final Score: {result['final_score']:.3f}\n"
            output += f"   Data Type: {result['data_type']}\n"
            output += f"   Found in Tables: {', '.join(result['tables'])}\n"
            desc = result['description'][:150]
            output += f"   Description: {desc}...\n"
            output += f"   {'-'*76}\n\n"
        
        return output
    
    def get_query_summary(self, query: str, top_k: int = 10) -> Dict:
        """
        Get comprehensive summary for query
        
        Args:
            query: Medical query
            top_k: Number of columns to retrieve
            
        Returns:
            Dictionary with query analysis
        """
        results = self.retrieve_columns(query, top_k=top_k, use_reranking=True, use_boosting=True)
        
        # Collect all tables
        all_tables = set()
        for r in results:
            all_tables.update(r['tables'])
        
        return {
            'query': query,
            'relevant_columns': results,
            'column_names': [r['column_name'] for r in results],
            'tables_needed': list(all_tables),
            'num_columns': len(results),
            'num_tables': len(all_tables)
        }


# Example usage
if __name__ == "__main__":
    print("Enhanced MIMIC-III Column Retrieval RAG Module")
    print("=" * 80)
    print("\n🚀 Advanced Features:")
    print("\n1. RE-RANKING")
    print("   - Prioritize columns from same tables")
    print("   - Improve query efficiency")
    print("   - results = retriever.retrieve_columns(query, use_reranking=True)")
    
    print("\n2. QUERY EXPANSION")
    print("   - Auto-expand query into variants")
    print("   - Combine results from multiple queries")
    print("   - results = retriever.retrieve_with_query_expansion(query)")
    
    print("\n3. KEYWORD BOOSTING")
    print("   - Boost relevant columns based on keywords")
    print("   - Improve precision for medical terms")
    print("   - results = retriever.retrieve_columns(query, use_boosting=True)")
    
    print("\n" + "="*80)
    print("\nExample Queries:")
    example_queries = [
        "What medications did patient A take during hospitalization?",
        "List all blood tests for the patient",
        "What was the primary diagnosis at admission?",
        "Which procedures were performed in the ICU?",
        "How long was the patient's hospital stay?",
        "What were the patient's vital signs?",
        "Did the patient have positive microbiology cultures?",
        "What IV medications were administered?"
    ]
    
    for i, q in enumerate(example_queries, 1):
        print(f"{i}. {q}")
    
    print("\n" + "="*80)
    print("\nUsage:")
    # Initialize retriever
    retriever = EnhancedMIMICRetriever('./graph/unique_columns.json')

    # Basic retrieval with all features
    results = retriever.retrieve_columns(
        "What medications did the patient A take?",
        use_reranking=True,
        use_boosting=True,
        boost_weight=0.2
    )

    # Query expansion (most powerful)
    results = retriever.retrieve_with_query_expansion(
        "What antibiotics were used for the patient?"
    )

    # Get comprehensive summary
    summary = retriever.get_query_summary("Patient vital signs during ICU stay")
    print(f"Columns: {summary['column_names']}")
    print(f"Tables: {summary['tables_needed']}")

    # Format and display
    print(retriever.format_results(results))