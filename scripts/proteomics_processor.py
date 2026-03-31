"""Proteomics data processing from MaxQuant output."""

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ProteomicsProcessor:
    """MaxQuant proteomics data processor."""

    # MaxQuant column name patterns
    LFQ_PATTERN = "LFQ intensity"
    PEPTIDE_COUNT_PATTERN = "Peptides"
    UNIQUE_PEPTIDE_PATTERN = "Unique peptides"
    RAZOR_PEPTIDE_PATTERN = "Razor peptides"
    SEQUENCE_COVERAGE_PATTERN = "Sequence coverage [%]"
    MW_PATTERN = "Molecular weight"
    PROTEIN_ID_PATTERN = "Protein IDs"
    GENE_NAME_PATTERN = "Gene names"

    def __init__(self):
        """Initialize proteomics processor."""
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def load_maxquant_output(file_path: str) -> pd.DataFrame:
        """
        Load MaxQuant proteinGroups.txt output.

        Args:
            file_path: Path to proteinGroups.txt or similar TSV

        Returns:
            DataFrame with protein quantification data
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Load TSV file
        df = pd.read_csv(file_path, sep="\t", low_memory=False)
        logger.info(f"Loaded MaxQuant output: {df.shape[0]} proteins × {df.shape[1]} columns")

        return df

    @staticmethod
    def extract_lfq_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Extract LFQ intensity columns from MaxQuant output.

        Args:
            df: MaxQuant dataframe

        Returns:
            (LFQ matrix, sample names)
        """
        # Find LFQ columns
        lfq_cols = [col for col in df.columns if ProteomicsProcessor.LFQ_PATTERN in col]

        if not lfq_cols:
            raise ValueError("No LFQ intensity columns found in MaxQuant output")

        lfq_data = df[lfq_cols].copy()

        # Extract sample names (remove "LFQ intensity " prefix)
        sample_names = [col.replace(f"{ProteomicsProcessor.LFQ_PATTERN} ", "") for col in lfq_cols]

        logger.info(f"Extracted {len(sample_names)} samples with LFQ quantification")

        return lfq_data, sample_names

    @staticmethod
    def log2_normalize_lfq(
        lfq_data: pd.DataFrame,
        pseudocount: float = 1.0
    ) -> pd.DataFrame:
        """
        Log2 normalize LFQ intensities.

        Converts raw LFQ values to log2 scale:
        log2_intensity = log2(LFQ_intensity + pseudocount)

        Args:
            lfq_data: Raw LFQ intensity matrix
            pseudocount: Pseudocount to avoid log(0)

        Returns:
            Log2-normalized LFQ matrix
        """
        logger.info("Performing log2 normalization of LFQ intensities...")

        # Replace NaN with 0
        lfq_data = lfq_data.fillna(0)

        # Log2 transform
        log2_data = np.log2(lfq_data + pseudocount)

        # Replace -inf (from log2(pseudocount) when original=0) with 0
        log2_data = log2_data.replace(-np.inf, 0)

        logger.info(f"Log2 normalization complete: "
                   f"mean={log2_data.values[log2_data > 0].mean():.2f}, "
                   f"std={log2_data.values[log2_data > 0].std():.2f}")

        return log2_data

    @staticmethod
    def calculate_fold_change(
        log2_data: pd.DataFrame,
        case_samples: Optional[List[str]] = None,
        control_samples: Optional[List[str]] = None
    ) -> Optional[pd.Series]:
        """
        Calculate case/control fold change if groups provided.

        Args:
            log2_data: Log2-normalized LFQ data
            case_samples: Case sample names
            control_samples: Control sample names

        Returns:
            Fold change series or None if groups not provided
        """
        if case_samples is None or control_samples is None:
            return None

        case_mean = log2_data[[s for s in case_samples if s in log2_data.columns]].mean(axis=1)
        control_mean = log2_data[[s for s in control_samples if s in log2_data.columns]].mean(axis=1)

        fold_change = case_mean - control_mean  # Log2 FC = log2(case) - log2(control)

        logger.info(f"Calculated fold changes: "
                   f"median={fold_change.median():.2f}, "
                   f"range=[{fold_change.min():.2f}, {fold_change.max():.2f}]")

        return fold_change

    @staticmethod
    def extract_protein_metadata(df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract protein metadata from MaxQuant output.

        Args:
            df: MaxQuant dataframe

        Returns:
            DataFrame with protein metadata
        """
        metadata = pd.DataFrame()

        # Protein identifiers
        if ProteomicsProcessor.PROTEIN_ID_PATTERN in df.columns:
            metadata['protein_id'] = df[ProteomicsProcessor.PROTEIN_ID_PATTERN]
        else:
            metadata['protein_id'] = df.index

        # Gene names
        if ProteomicsProcessor.GENE_NAME_PATTERN in df.columns:
            metadata['gene_name'] = df[ProteomicsProcessor.GENE_NAME_PATTERN]
        else:
            metadata['gene_name'] = None

        # Peptide counts
        peptide_cols = [col for col in df.columns if ProteomicsProcessor.PEPTIDE_COUNT_PATTERN in col and "Unique" not in col]
        if peptide_cols:
            metadata['peptide_count'] = df[peptide_cols[0]].astype(int)

        unique_pep_cols = [col for col in df.columns if ProteomicsProcessor.UNIQUE_PEPTIDE_PATTERN in col]
        if unique_pep_cols:
            metadata['unique_peptides'] = df[unique_pep_cols[0]].astype(int)

        razor_pep_cols = [col for col in df.columns if ProteomicsProcessor.RAZOR_PEPTIDE_PATTERN in col]
        if razor_pep_cols:
            metadata['razor_peptides'] = df[razor_pep_cols[0]].astype(int)

        # Sequence coverage
        coverage_cols = [col for col in df.columns if ProteomicsProcessor.SEQUENCE_COVERAGE_PATTERN in col]
        if coverage_cols:
            metadata['sequence_coverage'] = pd.to_numeric(df[coverage_cols[0]], errors='coerce')

        # Molecular weight
        mw_cols = [col for col in df.columns if ProteomicsProcessor.MW_PATTERN in col]
        if mw_cols:
            metadata['molecular_weight'] = pd.to_numeric(df[mw_cols[0]], errors='coerce')

        return metadata

    @staticmethod
    def classify_protein_class(gene_name: Optional[str]) -> str:
        """
        Simple protein classification based on gene name.

        In production, use DrugBank/UniProt annotations.

        Args:
            gene_name: Gene name/symbol

        Returns:
            Protein class
        """
        if not isinstance(gene_name, str):
            return "unknown"

        # Simple heuristic-based classification
        gene_lower = gene_name.lower()

        if any(x in gene_lower for x in ["cyp", "udp", "cat", "gst"]):
            return "enzyme"
        elif any(x in gene_lower for x in ["egfr", "her2", "vegfr", "igfr"]):
            return "receptor"
        elif any(x in gene_lower for x in ["slc", "abcb", "abcc"]):
            return "transporter"
        elif any(x in gene_lower for x in ["col", "hsp"]):
            return "structural"

        return "unknown"

    @staticmethod
    def filter_detectable_proteins(
        metadata: pd.DataFrame,
        lfq_data: pd.DataFrame,
        min_lfq: float = 0.0,
        min_peptides: int = 1
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Filter for detectable/quantifiable proteins.

        Args:
            metadata: Protein metadata
            lfq_data: LFQ intensity matrix
            min_lfq: Minimum LFQ intensity (0 allows zeros)
            min_peptides: Minimum unique peptides

        Returns:
            (Filtered metadata, filtered LFQ data)
        """
        initial_count = len(metadata)

        # Filter: at least one sample with detectable signal
        detected_mask = (lfq_data > min_lfq).any(axis=1)

        # Filter: minimum peptides (if available)
        if 'unique_peptides' in metadata.columns:
            peptide_mask = metadata['unique_peptides'] >= min_peptides
            mask = detected_mask & peptide_mask
        else:
            mask = detected_mask

        filtered_metadata = metadata[mask].copy()
        filtered_lfq = lfq_data[mask].copy()

        logger.info(f"Filtered proteins: {initial_count} → {len(filtered_metadata)} "
                   f"({100*len(filtered_metadata)/initial_count:.1f}% retained)")

        return filtered_metadata, filtered_lfq

    @staticmethod
    def process_proteomics(
        file_path: str,
        case_samples: Optional[List[str]] = None,
        control_samples: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Complete proteomics processing pipeline.

        Args:
            file_path: Path to MaxQuant proteinGroups.txt
            case_samples: Optional case group sample names
            control_samples: Optional control group sample names

        Returns:
            (Protein quantification results, metadata)
        """
        logger.info("Starting proteomics processing pipeline...")

        # Load MaxQuant output
        df = ProteomicsProcessor.load_maxquant_output(file_path)

        # Extract LFQ columns
        lfq_data, sample_names = ProteomicsProcessor.extract_lfq_columns(df)

        # Normalize
        log2_data = ProteomicsProcessor.log2_normalize_lfq(lfq_data)

        # Calculate fold change if groups provided
        fold_change = None
        if case_samples and control_samples:
            fold_change = ProteomicsProcessor.calculate_fold_change(log2_data, case_samples, control_samples)

        # Extract metadata
        metadata = ProteomicsProcessor.extract_protein_metadata(df)
        metadata['protein_class'] = metadata['gene_name'].apply(ProteomicsProcessor.classify_protein_class)

        # Filter detectable proteins
        metadata, log2_data = ProteomicsProcessor.filter_detectable_proteins(metadata, log2_data)

        # Combine results
        results = metadata.copy()
        results['lfq_intensity'] = lfq_data.iloc[:, 0] if len(lfq_data.columns) > 0 else 0  # First sample LFQ
        results['log2_intensity'] = log2_data.iloc[:, 0] if len(log2_data.columns) > 0 else 0
        if fold_change is not None:
            results['fold_change'] = fold_change

        # Processing metadata
        proc_metadata = {
            'total_proteins_detected': len(df),
            'total_proteins_quantified': len(metadata),
            'total_samples': len(sample_names),
            'sample_names': sample_names,
            'normalization_method': 'log2_lfq',
            'case_samples': case_samples,
            'control_samples': control_samples,
            'drug_target_proteins': 0,  # Would query DrugBank
            'enzyme_proteins': (metadata['protein_class'] == 'enzyme').sum(),
            'receptor_proteins': (metadata['protein_class'] == 'receptor').sum(),
        }

        logger.info(f"Proteomics processing complete: {len(metadata)} proteins quantified")
        return results, proc_metadata
