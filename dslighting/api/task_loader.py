"""
Task loader for DSLighting benchmarks.

This module provides utilities for loading and discovering benchmark tasks
from vendor directories and predefined task lists.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskLoader:
    """
    Task loading utilities for DSLighting benchmarks.

    Provides methods to:
    - Auto-discover all tasks from vendor directories
    - Validate task completeness (required files)
    - Load predefined task subsets
    """

    @staticmethod
    def normalize_task_id(task_id: str) -> str:
        """
        Normalize task ID to dabench-{id} format.

        Ensures consistent Task ID format throughout the codebase.
        Handles both legacy "dab673" and standard "dabench-673" formats.

        Args:
            task_id: Task identifier in any format

        Returns:
            Normalized task ID in "dabench-{id}" format

        Examples:
            >>> TaskLoader.normalize_task_id("dab673")
            'dabench-673'
            >>> TaskLoader.normalize_task_id("dabench-673")
            'dabench-673'
        """
        if task_id.startswith("dabench-"):
            return task_id
        # Handle legacy "dab673" format
        if task_id.startswith("dab"):
            num = task_id[3:]
            return f"dabench-{num}"
        return task_id

    # Predefined MLE-Lite task list (22 Low complexity tasks)
    MLE_LITE_TASKS = [
        "aerial-cactus-identification",
        "aptos2019-blindness-detection",
        "bus-ticket-reactor-prediction",
        "cifar10-object-recognition",
        "city-of-los-angeles-parking-citations",
        "connectx",
        "contradictory-dear-watson",
        "digit-recognizer",
        "dm-embedded",
        "dont-be-deceived",
        "ghouls-goblins-and-ghosts-boooo",
        "honey-crypt-prediction",
        "icecube-neutrinos",
        "icecube-neutrinos-deep-learning",
        "janestreet-market-time-series",
        "jet-tagging",
        "llm-detect-ai-gen-text",
        "m5-forecasting-accuracy",
        "minileagues-modelling-dm-cryptic",
        "minileagues-replicating-dm-cryptic",
        "molecular-translation",
        "nlp-scratch",
        "siim-isic-melanoma-classification",
    ]

    # Summary Statistics (90 competitions)
    DABENCH_SUMMARY_STATISTICS = [
        "dabench-0-mean-fare-paid",
        "dabench-6-column-called-agegroup",
        "dabench-8-distribution-analysis-fare",
        "dabench-9-mean-value-close",
        "dabench-14-feature-called-price",
        "dabench-18-mean-standard-deviation",
        "dabench-23-machine-learning-techniques",
        "dabench-24-mean-individuals-dataset",
        "dabench-32-mean-standard-deviation",
        "dabench-55-what-mean-number",
        "dabench-56-which-country-highest",
        "dabench-58-what-percentage-missing",
        "dabench-59-among-countries-americas",
        "dabench-64-mean-standard-deviation",
        "dabench-70-machine-learning-training",
        "dabench-71-mean-standard-deviation",
        "dabench-75-column-called-daily",
        "dabench-77-comprehensive-data-preprocessing",
        "dabench-108-generate-feature-called",
        "dabench-111-comprehensive-data-preprocessing",
        "dabench-114-which-country-highest",
        "dabench-123-which-country-highest",
        "dabench-124-there-significant-difference",
        "dabench-129-mean-standard-deviation",
        "dabench-136-distribution-analysis-fare",
        "dabench-144-question-mean-standard",
        "dabench-176-median-male-passengers",
        "dabench-179-pearson-correlation-coefficient",
        "dabench-208-mean-standard-deviation",
        "dabench-210-identify-remove-outliers",
        "dabench-216-mean-standard-deviation",
        "dabench-234-what-average-duration",
        "dabench-243-what-mean-batting",
        "dabench-247-what-average-number",
        "dabench-249-there-significant-correlation",
        "dabench-250-feature-called-which",
        "dabench-255-mean-standard-deviation",
        "dabench-272-feature-named-dividing",
        "dabench-297-there-significant-difference",
        "dabench-308-feature-engineering-techniques",
        "dabench-309-distribution-analysis-fare",
        "dabench-320-what-mean-eventmsgtype",
        "dabench-349-mean-passengers",
        "dabench-372-find-mean-median",
        "dabench-376-feature-engineering-dataset",
        "dabench-414-what-average-passengers",
        "dabench-419-there-significant-difference",
        "dabench-426-what-maximum-sustained",
        "dabench-428-what-average-damage",
        "dabench-446-what-mean-wind",
        "dabench-450-average-wind-speed",
        "dabench-453-data-preprocessing-dataset",
        "dabench-472-what-mean-value",
        "dabench-480-feature-engineering-techniques",
        "dabench-490-what-mean-percentage",
        "dabench-492-which-field-highest",
        "dabench-495-outlier-detection-percentage",
        "dabench-496-feature-engineering-creating",
        "dabench-506-what-average-number",
        "dabench-510-which-hotel-brand",
        "dabench-514-what-average-review",
        "dabench-527-what-average-male",
        "dabench-542-what-mean-length",
        "dabench-551-what-mean-column",
        "dabench-554-what-median-value",
        "dabench-572-identify-date-with",
        "dabench-578-what-average-trading",
        "dabench-604-identify-remove-outliers",
        "dabench-619-identify-remove-outliers",
        "dabench-643-mean-standard-deviation",
        "dabench-649-mean-standard-deviation",
        "dabench-656-outlier-analysis-coordinate",
        "dabench-657-mean-median-standard",
        "dabench-662-feature-engineering-creating",
        "dabench-665-data-preprocessing-filling",
        "dabench-666-mean-standard-deviation",
        "dabench-669-identify-remove-outliers",
        "dabench-673-comprehensive-data-preprocessing",
        "dabench-683-what-mean-temperature",
        "dabench-690-outlier-detection-wind",
        "dabench-710-what-mean-number",
        "dabench-716-data-preprocessing-dropping",
        "dabench-719-mean-median-column",
        "dabench-722-identify-vehicle-with",
        "dabench-723-generate-feature-called",
        "dabench-724-outlier-detection-acceleration",
        "dabench-726-comprehensive-data-preprocessing",
        "dabench-737-mean-standard-deviation",
        "dabench-755-what-mean-value",
        "dabench-759-median-range-maximum",
    ]

    # Correlation Analysis (72 competitions)
    DABENCH_CORRELATION_ANALYSIS = [
        "dabench-5-generate-feature-called",
        "dabench-11-correlation-coefficient-between",
        "dabench-26-correlation-coefficient-between",
        "dabench-34-there-correlation-between",
        "dabench-57-there-correlation-between",
        "dabench-66-correlation-between-wage",
        "dabench-69-correlation-analysis-between",
        "dabench-73-correlation-coefficient-between",
        "dabench-105-correlation-coefficient-between",
        "dabench-117-which-variable-strongest",
        "dabench-118-there-linear-relationship",
        "dabench-124-there-significant-difference",
        "dabench-125-predict-number-people",
        "dabench-140-there-correlation-between",
        "dabench-142-there-relationship-between",
        "dabench-176-median-male-passengers",
        "dabench-179-pearson-correlation-coefficient",
        "dabench-209-there-correlation-between",
        "dabench-214-correlation-analysis-between",
        "dabench-218-correlation-coefficient-between",
        "dabench-249-there-significant-correlation",
        "dabench-269-there-correlation-between",
        "dabench-273-correlation-analysis-between",
        "dabench-277-there-correlation-between",
        "dabench-282-correlation-analysis-given",
        "dabench-300-there-correlation-between",
        "dabench-310-correlation-analysis-numerical",
        "dabench-326-feature-named-that",
        "dabench-338-there-correlation-between",
        "dabench-351-determine-correlation-coefficient",
        "dabench-355-linear-regression-analysis",
        "dabench-360-determine-correlation-coefficient",
        "dabench-408-there-correlation-between",
        "dabench-413-there-correlation-between",
        "dabench-423-feature-engineering-given",
        "dabench-426-what-maximum-sustained",
        "dabench-429-there-correlation-between",
        "dabench-431-there-relationship-between",
        "dabench-452-there-relationship-between",
        "dabench-466-there-correlation-between",
        "dabench-474-there-correlation-between",
        "dabench-508-there-correlation-between",
        "dabench-513-among-hotels-with",
        "dabench-517-find-correlation-coefficient",
        "dabench-520-feature-called-familysize",
        "dabench-522-feature-engineering-creating",
        "dabench-526-there-correlation-between",
        "dabench-529-identify-patterns-relationships",
        "dabench-530-there-correlation-between",
        "dabench-543-there-correlation-between",
        "dabench-549-explore-correlation-between",
        "dabench-552-column-column-correlated",
        "dabench-572-identify-date-with",
        "dabench-574-data-preprocessing-stock",
        "dabench-575-using-feature-engineering",
        "dabench-587-examine-correlation-between",
        "dabench-618-find-correlation-coefficient",
        "dabench-650-there-correlation-between",
        "dabench-655-correlation-analysis-coordinate",
        "dabench-659-find-correlation-between",
        "dabench-663-scatter-plot-high",
        "dabench-668-correlation-coefficient-between",
        "dabench-673-comprehensive-data-preprocessing",
        "dabench-674-build-machine-learning",
        "dabench-685-there-correlation-between",
        "dabench-721-find-correlation-coefficient",
        "dabench-725-investigate-relationship-between",
        "dabench-727-machine-learning-techniques",
        "dabench-730-there-correlation-between",
        "dabench-734-there-correlation-between",
        "dabench-739-determine-correlation-coefficient",
        "dabench-756-there-correlation-between",
    ]

    # Feature Engineering (50 competitions)
    DABENCH_FEATURE_ENGINEERING = [
        "dabench-5-generate-feature-called",
        "dabench-6-column-called-agegroup",
        "dabench-14-feature-called-price",
        "dabench-30-linear-regression-machine",
        "dabench-39-explore-distribution-importance",
        "dabench-59-among-countries-americas",
        "dabench-69-feature-engineering-creating",
        "dabench-75-column-called-daily",
        "dabench-108-generate-feature-called",
        "dabench-109-explore-distribution-loanamount",
        "dabench-137-feature-engineering-creating",
        "dabench-178-comprehensive-data-preprocessing",
        "dabench-214-correlation-analysis-between",
        "dabench-220-comprehensive-data-preprocessing",
        "dabench-222-explore-distribution-column",
        "dabench-250-feature-called-which",
        "dabench-272-feature-named-dividing",
        "dabench-275-comprehensive-analysis-dataset",
        "dabench-308-feature-engineering-techniques",
        "dabench-326-feature-named-that",
        "dabench-354-feature-familysize-summing",
        "dabench-376-feature-engineering-dataset",
        "dabench-412-feature-called-familysize",
        "dabench-423-feature-engineering-given",
        "dabench-424-develop-machine-learning",
        "dabench-452-there-relationship-between",
        "dabench-480-feature-engineering-techniques",
        "dabench-496-feature-engineering-creating",
        "dabench-510-which-hotel-brand",
        "dabench-520-feature-called-familysize",
        "dabench-521-using-machine-learning",
        "dabench-522-feature-engineering-creating",
        "dabench-523-preprocess-dataset-using",
        "dabench-529-identify-patterns-relationships",
        "dabench-549-explore-correlation-between",
        "dabench-555-many-unique-plant",
        "dabench-575-using-feature-engineering",
        "dabench-589-generate-feature-representing",
        "dabench-593-using-feature-engineering",
        "dabench-647-feature-called-price",
        "dabench-662-feature-engineering-creating",
        "dabench-665-data-preprocessing-filling",
        "dabench-673-comprehensive-data-preprocessing",
        "dabench-688-using-feature-engineering",
        "dabench-723-generate-feature-called",
        "dabench-726-comprehensive-data-preprocessing",
        "dabench-733-feature-engineering-techniques",
        "dabench-736-feature-combining-population",
        "dabench-741-feature-credit-file",
        "dabench-743-comprehensive-data-preprocessing",
    ]

    # DABench Outlier Detection (35 competitions)
    DABENCH_OUTLIER_DETECTION = [
        "dabench-27-identify-outliers-charges",
        "dabench-35-identify-remove-outliers",
        "dabench-62-there-outliers-column",
        "dabench-116-there-outliers-happiness",
        "dabench-132-identify-count-number",
        "dabench-175-identify-there-outliers",
        "dabench-180-outlier-detection-fare",
        "dabench-210-identify-remove-outliers",
        "dabench-219-identify-site-with",
        "dabench-254-identify-outliers-gross",
        "dabench-273-correlation-analysis-between",
        "dabench-278-there-outliers-agri",
        "dabench-282-correlation-analysis-given",
        "dabench-321-there-outliers-scoremargin",
        "dabench-352-identify-outliers-fare",
        "dabench-361-identify-remove-outliers",
        "dabench-411-there-outliers-fare",
        "dabench-418-there-outliers-trading",
        "dabench-447-there-outliers-atmospheric",
        "dabench-468-there-outliers-distribution",
        "dabench-473-there-outliers-value",
        "dabench-495-outlier-detection-percentage",
        "dabench-518-identify-remove-outliers",
        "dabench-528-there-outliers-fare",
        "dabench-553-many-outliers-there",
        "dabench-588-there-outliers-average",
        "dabench-604-identify-remove-outliers",
        "dabench-619-identify-remove-outliers",
        "dabench-651-there-outliers-coordinate",
        "dabench-656-outlier-analysis-coordinate",
        "dabench-669-identify-remove-outliers",
        "dabench-690-outlier-detection-wind",
        "dabench-724-outlier-detection-acceleration",
        "dabench-740-identify-outliers-balance",
        "dabench-757-there-outliers-observation",
    ]

    # Machine Learning (19 competitions)
    DABENCH_MACHINE_LEARNING = [
        "dabench-7-linear-regression-algorithm",
        "dabench-23-machine-learning-techniques",
        "dabench-30-linear-regression-machine",
        "dabench-70-machine-learning-training",
        "dabench-118-there-linear-relationship",
        "dabench-125-predict-number-people",
        "dabench-137-feature-engineering-creating",
        "dabench-224-utilize-machine-learning",
        "dabench-275-comprehensive-analysis-dataset",
        "dabench-355-linear-regression-analysis",
        "dabench-363-train-machine-learning",
        "dabench-424-develop-machine-learning",
        "dabench-432-predict-maximum-sustained",
        "dabench-521-using-machine-learning",
        "dabench-549-explore-correlation-between",
        "dabench-590-using-machine-learning",
        "dabench-671-build-machine-learning",
        "dabench-674-build-machine-learning",
        "dabench-727-machine-learning-techniques",
    ]

    # Comprehensive Data Preprocessing (45 competitions)
    DABENCH_COMPREHENSIVE_PREPROCESSING = [
        "dabench-28-comprehensive-data-preprocessing",
        "dabench-35-identify-remove-outliers",
        "dabench-58-what-percentage-missing",
        "dabench-77-comprehensive-data-preprocessing",
        "dabench-111-comprehensive-data-preprocessing",
        "dabench-133-comprehensive-data-preprocessing",
        "dabench-178-comprehensive-data-preprocessing",
        "dabench-207-which-column-contain",
        "dabench-220-comprehensive-data-preprocessing",
        "dabench-271-comprehensive-data-preprocessing",
        "dabench-275-comprehensive-analysis-dataset",
        "dabench-297-there-significant-difference",
        "dabench-300-there-correlation-between",
        "dabench-324-there-missing-values",
        "dabench-361-identify-remove-outliers",
        "dabench-378-preprocess-dataset-handling",
        "dabench-409-many-missing-values",
        "dabench-413-there-correlation-between",
        "dabench-414-what-average-passengers",
        "dabench-415-what-distribution-fare",
        "dabench-421-comprehensive-data-preprocessing",
        "dabench-425-many-missing-values",
        "dabench-427-many-storms-have",
        "dabench-431-there-relationship-between",
        "dabench-432-predict-maximum-sustained",
        "dabench-451-detect-missing-values",
        "dabench-453-data-preprocessing-dataset",
        "dabench-523-preprocess-dataset-using",
        "dabench-528-there-outliers-fare",
        "dabench-550-comprehensive-data-preprocessing",
        "dabench-574-data-preprocessing-stock",
        "dabench-665-data-preprocessing-filling",
        "dabench-673-comprehensive-data-preprocessing",
        "dabench-674-build-machine-learning",
        "dabench-715-what-percentage-missing",
        "dabench-716-data-preprocessing-dropping",
        "dabench-722-identify-vehicle-with",
        "dabench-724-outlier-detection-acceleration",
        "dabench-726-comprehensive-data-preprocessing",
        "dabench-732-comprehensive-data-preprocessing",
        "dabench-734-there-correlation-between",
        "dabench-740-identify-outliers-balance",
        "dabench-741-feature-credit-file",
        "dabench-743-comprehensive-data-preprocessing",
        "dabench-760-each-station-there",
    ]

    # Distribution Analysis (64 competitions)
    DABENCH_DISTRIBUTION_ANALYSIS = [
        "dabench-8-distribution-analysis-fare",
        "dabench-10-total-traded-quantity",
        "dabench-19-distribution-column-adheres",
        "dabench-25-distribution-values-dataset",
        "dabench-33-column-normally-distributed",
        "dabench-39-explore-distribution-importance",
        "dabench-56-which-country-highest",
        "dabench-59-among-countries-americas",
        "dabench-62-there-outliers-column",
        "dabench-72-close-column-adheres",
        "dabench-109-explore-distribution-loanamount",
        "dabench-123-which-country-highest",
        "dabench-130-passengers-follows-normal",
        "dabench-136-distribution-analysis-fare",
        "dabench-139-question-percentage-votes",
        "dabench-144-question-mean-standard",
        "dabench-174-determine-skewness-fares",
        "dabench-177-investigate-distribution-ages",
        "dabench-217-find-site-identifier",
        "dabench-222-explore-distribution-column",
        "dabench-224-utilize-machine-learning",
        "dabench-244-number-home-runs",
        "dabench-252-determine-which-country",
        "dabench-268-meanpot-values-normally",
        "dabench-282-correlation-analysis-given",
        "dabench-298-distribution-analysis-nsamplecov",
        "dabench-304-fare-variable-follows",
        "dabench-309-distribution-analysis-fare",
        "dabench-337-distribution-median-sold",
        "dabench-350-fare-column-follows",
        "dabench-359-distribution-wind-speed",
        "dabench-375-distribution-analysis-trips",
        "dabench-378-preprocess-dataset-handling",
        "dabench-410-what-distribution-ages",
        "dabench-415-what-distribution-fare",
        "dabench-419-there-significant-difference",
        "dabench-428-what-average-damage",
        "dabench-449-what-distribution-wind",
        "dabench-465-distribution-offender-ages",
        "dabench-468-there-outliers-distribution",
        "dabench-507-there-hotels-dataset",
        "dabench-513-among-hotels-with",
        "dabench-514-what-average-review",
        "dabench-516-fare-distribution-skewed",
        "dabench-522-feature-engineering-creating",
        "dabench-527-what-average-male",
        "dabench-530-there-correlation-between",
        "dabench-550-comprehensive-data-preprocessing",
        "dabench-554-what-median-value",
        "dabench-586-find-total-number",
        "dabench-593-using-feature-engineering",
        "dabench-602-column-follows-normal",
        "dabench-644-close-column-follows",
        "dabench-647-feature-called-price",
        "dabench-652-distribution-analysis-coordinate",
        "dabench-658-volume-column-adheres",
        "dabench-663-scatter-plot-high",
        "dabench-667-medinc-column-adheres",
        "dabench-684-does-humidity-level",
        "dabench-725-investigate-relationship-between",
        "dabench-729-does-distribution-capita",
        "dabench-736-feature-combining-population",
        "dabench-738-distribution-column-credit",
        "dabench-759-median-range-maximum",
    ]

    @staticmethod
    def auto_discover_all_tasks(
        data_dir: str,
        vendor_comp_dir: str,
        prefix: Optional[str] = None,
        require_prepared: bool = True,
    ) -> List[str]:
        """
        Auto-discover all valid tasks from vendor directory.

        Args:
            data_dir: Data directory path (contains prepared data)
            vendor_comp_dir: Vendor competition directory (contains config.yaml)
            prefix: Optional task ID prefix filter (e.g., "dabench-")
            require_prepared: Whether to require prepared data

        Returns:
            List of valid task IDs

        Example:
            >>> tasks = TaskLoader.auto_discover_all_tasks(
            ...     data_dir="/path/to/data",
            ...     vendor_comp_dir="/path/to/vendor/dabench/competitions",
            ...     prefix="dabench-"
            ... )
        """
        tasks = []
        vendor_path = Path(vendor_comp_dir)
        data_path = Path(data_dir)

        if not vendor_path.exists():
            raise ValueError(f"Vendor directory not found: {vendor_comp_dir}")

        # Iterate through task directories in vendor folder
        for task_dir in sorted(vendor_path.iterdir()):
            if not task_dir.is_dir():
                continue

            task_id = task_dir.name

            # Apply prefix filter if specified
            if prefix and not task_id.startswith(prefix):
                continue

            # Validate required files exist
            if not TaskLoader._validate_task_files(task_dir):
                logger.debug(f"Skipping {task_id}: missing required files")
                continue

            # Validate prepared data exists (if required)
            if require_prepared:
                if not TaskLoader._validate_prepared_data(data_path, task_id):
                    logger.debug(f"Skipping {task_id}: prepared data not found")
                    continue

            tasks.append(task_id)

        logger.info(f"Discovered {len(tasks)} tasks from {vendor_comp_dir}")
        return tasks

    @staticmethod
    def _validate_task_files(task_dir: Path) -> bool:
        """
        Validate that task directory contains required files.

        Args:
            task_dir: Path to task directory

        Returns:
            True if all required files exist
        """
        required_files = ["config.yaml"]
        return all((task_dir / f).exists() for f in required_files)

    @staticmethod
    def _validate_prepared_data(data_path: Path, task_id: str) -> bool:
        """
        Validate that prepared data exists for task.

        Args:
            data_path: Path to data directory
            task_id: Task identifier

        Returns:
            True if prepared data exists
        """
        # Check common data directory structures
        candidates = [
            data_path / "competitions" / task_id / "prepared" / "public",
            data_path / task_id / "prepared" / "public",
            data_path / "competitions" / task_id / "public",
        ]

        return any(candidate.exists() for candidate in candidates)

    @staticmethod
    def get_predefined_tasks(name: str) -> Optional[List[str]]:
        """
        Get predefined task list by name.

        Args:
            name: Predefined task list name (e.g., "mle-lite")

        Returns:
            List of task IDs, or None if name not found

        Example:
            >>> tasks = TaskLoader.get_predefined_tasks("mle-lite")
            >>> # Returns list of 22 MLE-Lite tasks
        """
        predefined = {
            "mle-lite": TaskLoader.MLE_LITE_TASKS,
            "summary_statistics": TaskLoader.DABENCH_SUMMARY_STATISTICS,
            "correlation_analysis": TaskLoader.DABENCH_CORRELATION_ANALYSIS,
            "feature_engineering": TaskLoader.DABENCH_FEATURE_ENGINEERING,
            "outlier_detection": TaskLoader.DABENCH_OUTLIER_DETECTION,
            "machine_learning": TaskLoader.DABENCH_MACHINE_LEARNING,
            "comprehensive_preprocessing": TaskLoader.DABENCH_COMPREHENSIVE_PREPROCESSING,
            "distribution_analysis": TaskLoader.DABENCH_DISTRIBUTION_ANALYSIS,
        }

        return predefined.get(name)

    # DABench subsets mapping (for benchmark_type like "da_summary_statistics")
    DABENCH_SUBSETS = {
        "da_summary_statistics": "summary_statistics",
        "da_comprehensive_preprocessing": "comprehensive_preprocessing",
        "da_correlation_analysis": "correlation_analysis",
        "da_distribution_analysis": "distribution_analysis",
        "da_feature_engineering": "feature_engineering",
        "da_machine_learning": "machine_learning",
        "da_outlier_detection": "outlier_detection",
    }

    @classmethod
    def get_dabench_subset_tasks(cls, benchmark_type: str) -> Optional[List[str]]:
        """
        Get DABench subset tasks by benchmark_type (e.g., "da_summary_statistics").

        Args:
            benchmark_type: Benchmark type name (e.g., "da_summary_statistics")

        Returns:
            List of task IDs, or None if not a DABench subset
        """
        subset_name = cls.DABENCH_SUBSETS.get(benchmark_type)
        if subset_name:
            return cls.get_predefined_tasks(subset_name)
        return None

    @staticmethod
    def discover_dabench_subsets(
        vendor_comp_dir: str,
        subset_patterns: Dict[str, str],
    ) -> Dict[str, List[str]]:
        """
        Discover DABench task subsets by pattern matching.

        Args:
            vendor_comp_dir: Vendor competition directory
            subset_patterns: Dict of subset name to pattern
                e.g., {"correlation": "correlation", "preprocessing": "preprocessing"}

        Returns:
            Dict mapping subset names to task lists

        Example:
            >>> subsets = TaskLoader.discover_dabench_subsets(
            ...     "/path/to/vendor/dabench/competitions",
            ...     {
            ...         "correlation": "correlation",
            ...         "preprocessing": "preprocessing",
            ...         "outlier": "outlier"
            ...     }
            ... )
        """
        result = {}
        vendor_path = Path(vendor_comp_dir)

        if not vendor_path.exists():
            return result

        # Discover all tasks
        all_tasks = []
        for task_dir in sorted(vendor_path.iterdir()):
            if task_dir.is_dir() and TaskLoader._validate_task_files(task_dir):
                all_tasks.append(task_dir.name)

        # Categorize tasks by pattern
        for subset_name, pattern in subset_patterns.items():
            result[subset_name] = [
                task for task in all_tasks if pattern in task.lower()
            ]

        return result
