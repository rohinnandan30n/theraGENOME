"""RNA-seq data processing with DESeq2-style normalization and differential expression analysis."""

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional, Any
from uuid import UUID
import logging
from scipy import stats
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class RNASeqProcessor:
    """RNA-seq count matrix processor with DESeq2-style normalization."""

    def __init__(self):
        """Initialize RNA-seq processor."""
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def load_count_matrix(file_path: str) -> pd.DataFrame:
        """
        Load count matrix from CSV or H5AD format.

        Args:
            file_path: Path to count matrix file (.csv or .h5ad)

        Returns:
            DataFrame with genes as rows, samples as columns
        """
        file_path = Path(file_path)

        if file_path.suffix == ".csv":
            # Load CSV format
            df = pd.read_csv(file_path, index_col=0)
            logger.info(f"Loaded CSV count matrix: {df.shape[0]} genes × {df.shape[1]} samples")
            return df

        elif file_path.suffix == ".h5ad":
            try:
                import anndata
                adata = anndata.read_h5ad(file_path)
                df = pd.DataFrame(
                    data=adata.X.toarray() if hasattr(adata.X, "toarray") else adata.X,
                    index=adata.var_names,
                    columns=adata.obs_names,
                )
                logger.info(f"Loaded H5AD count matrix: {df.shape[0]} genes × {df.shape[1]} samples")
                return df
            except ImportError:
                raise ImportError("anndata required for H5AD support: pip install anndata")
        else:
            raise ValueError(f"Unsupported format: {file_path.suffix}")

    @staticmethod
    def median_of_ratios_normalization(
        counts: pd.DataFrame,
        min_count: int = 10,
        min_samples: int = 2
    ) -> pd.DataFrame:
        """
        DESeq2-style median-of-ratios normalization.

        Method:
        1. Filter genes with sufficient counts (min_count in min_samples)
        2. Calculate size factors (geometric means)
        3. Normalize each sample by its size factor

        Args:
            counts: Count matrix (genes × samples)
            min_count: Minimum count threshold for filtering
            min_samples: Minimum samples with count > min_count

        Returns:
            Normalized count matrix
        """
        logger.info("Starting median-of-ratios normalization...")

        # Filter genes with low counts
        mask = (counts > min_count).sum(axis=1) >= min_samples
        counts_filtered = counts[mask].copy()
        logger.info(f"Filtered from {counts.shape[0]} to {counts_filtered.shape[0]} genes")

        # Calculate geometric means per gene
        # Use log-space to avoid overflow: geom_mean = exp(mean(log(X)))
        log_counts = np.log(counts_filtered + 1)  # +1 to avoid log(0)
        geom_means = np.exp(log_counts.mean(axis=1))

        # Calculate size factors: median(counts / geom_mean) per sample
        size_factors = []
        for sample in counts_filtered.columns:
            ratios = counts_filtered[sample] / geom_means
            ratios = ratios[ratios > 0]  # Remove zeros
            size_factor = np.median(ratios)
            size_factors.append(size_factor)

        # Normalize: counts / size_factor
        normalized = counts.copy()
        for i, sample in enumerate(normalized.columns):
            normalized[sample] = normalized[sample] / size_factors[i]

        logger.info(f"Size factors: mean={np.mean(size_factors):.2f}, "
                   f"range=[{np.min(size_factors):.2f}, {np.max(size_factors):.2f}]")

        return normalized

    @staticmethod
    def differential_expression_analysis(
        normalized_counts: pd.DataFrame,
        case_samples: List[str],
        control_samples: List[str],
        pseudocount: float = 1.0
    ) -> pd.DataFrame:
        """
        Perform differential expression analysis (case vs. control).

        Uses log2-fold-change and two-sample t-test p-values.

        Args:
            normalized_counts: Normalized count matrix
            case_samples: Sample IDs for case group
            control_samples: Sample IDs for control group
            pseudocount: Added to avoid log(0)

        Returns:
            DataFrame with DE results
        """
        logger.info(f"Differential expression: {len(case_samples)} case vs {len(control_samples)} control")

        # Extract group means
        case_data = normalized_counts[case_samples]
        control_data = normalized_counts[control_samples]

        case_mean = case_data.mean(axis=1)
        control_mean = control_data.mean(axis=1)
        base_mean = (case_mean + control_mean) / 2

        # Calculate log2 fold-change
        log2fc = np.log2((case_mean + pseudocount) / (control_mean + pseudocount))

        # Perform t-tests
        p_values = []
        for gene in normalized_counts.index:
            t_stat, p_val = stats.ttest_ind(case_data.loc[gene], control_data.loc[gene])
            p_values.append(p_val)

        p_values = np.array(p_values)

        # Benjamini-Hochberg FDR correction
        padj = RNASeqProcessor._benjamini_hochberg_correction(p_values)

        # Create results DataFrame
        results = pd.DataFrame({
            'log2_fold_change': log2fc,
            'p_value': p_values,
            'padj': padj,
            'base_mean': base_mean,
            'case_mean': case_mean,
            'control_mean': control_mean,
        })

        results.index.name = 'gene_id'

        logger.info(f"Significant genes (padj < 0.05): {(padj < 0.05).sum()}")
        logger.info(f"Upregulated (log2FC > 1): {(log2fc > 1).sum()}")
        logger.info(f"Downregulated (log2FC < -1): {(log2fc < -1).sum()}")

        return results

    @staticmethod
    def _benjamini_hochberg_correction(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray:
        """
        Benjamini-Hochberg FDR correction.

        Args:
            p_values: Array of p-values
            alpha: FDR threshold

        Returns:
            Adjusted p-values
        """
        n = len(p_values)
        p_sorted_indices = np.argsort(p_values)
        p_sorted = p_values[p_sorted_indices]

        # BH correction: adjusted_p = p * (n / rank)
        ranks = np.arange(1, n + 1)
        adjusted_sorted = np.minimum.accumulate(p_sorted * n / ranks[::-1])[::-1]

        # Unsort back to original order
        adjusted = np.empty_like(adjusted_sorted)
        adjusted[p_sorted_indices] = adjusted_sorted

        # Clip to [0, 1]
        adjusted = np.clip(adjusted, 0, 1)

        return adjusted

    @staticmethod
    def classify_significance(log2fc: float, padj: float, padj_threshold: float = 0.05, lfc_threshold: float = 1.0) -> str:
        """Classify gene significance."""
        if padj > padj_threshold:
            return "stable"
        elif log2fc > lfc_threshold:
            return "up"
        elif log2fc < -lfc_threshold:
            return "down"
        return "stable"

    @staticmethod
    def classify_expression_level(base_mean: float) -> str:
        """Classify expression level based on mean normalized count."""
        if base_mean < 1:
            return "absent"
        elif base_mean < 10:
            return "low"
        elif base_mean < 100:
            return "medium"
        else:
            return "high"

    @staticmethod
    def calculate_effect_size(log2fc: float) -> float:
        """Calculate effect size (absolute log2FC)."""
        return abs(log2fc)

    @staticmethod
    def enrich_with_annotations(
        de_results: pd.DataFrame,
        gene_annotations: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Enrich DE results with gene annotations.

        Args:
            de_results: DE results DataFrame
            gene_annotations: Optional dictionary of gene annotations

        Returns:
            Enriched DataFrame
        """
        de_results['significance_flag'] = de_results.apply(
            lambda row: RNASeqProcessor.classify_significance(
                row['log2_fold_change'],
                row['padj']
            ),
            axis=1
        )

        de_results['effect_size'] = de_results['log2_fold_change'].apply(
            RNASeqProcessor.calculate_effect_size
        )

        de_results['expression_level'] = de_results['base_mean'].apply(
            RNASeqProcessor.classify_expression_level
        )

        # Add placeholder annotations
        de_results['transcript_biotype'] = 'protein_coding'  # Would come from ENSEMBL
        de_results['gene_name'] = de_results.index  # Placeholder
        de_results['go_annotations'] = None
        de_results['pathway_associations'] = None
        de_results['clinical_relevance'] = None

        return de_results

    @staticmethod
    def process_rna_seq(
        file_path: str,
        case_samples: List[str],
        control_samples: List[str],
        min_count: int = 10
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Complete RNA-seq processing pipeline.

        Args:
            file_path: Path to count matrix
            case_samples: Case group sample IDs
            control_samples: Control group sample IDs
            min_count: Minimum count threshold

        Returns:
            (DE results DataFrame, processing metadata)
        """
        logger.info("Starting RNA-seq processing pipeline...")

        # Load counts
        counts = RNASeqProcessor.load_count_matrix(file_path)

        # Normalize
        normalized = RNASeqProcessor.median_of_ratios_normalization(counts, min_count=min_count)

        # DE analysis
        de_results = RNASeqProcessor.differential_expression_analysis(
            normalized,
            case_samples,
            control_samples
        )

        # Enrich annotations
        de_results = RNASeqProcessor.enrich_with_annotations(de_results)

        # Metadata
        metadata = {
            'total_genes_input': counts.shape[0],
            'total_genes_analyzed': normalized.shape[0],
            'total_samples': counts.shape[1],
            'case_samples': case_samples,
            'control_samples': control_samples,
            'normalization_method': 'deseq2_median_of_ratios',
            'significant_genes': (de_results['padj'] < 0.05).sum(),
            'upregulated_genes': (de_results['log2_fold_change'] > 1).sum(),
            'downregulated_genes': (de_results['log2_fold_change'] < -1).sum(),
        }

        logger.info(f"RNA-seq processing complete: {metadata['significant_genes']} significant genes")
        return de_results, metadata
