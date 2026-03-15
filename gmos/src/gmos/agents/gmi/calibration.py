"""
Calibration Layer for Phase 4

Makes confidence, uncertainty, and abstention thresholds
explicit and measurable.

This addresses the Phase 3 insight that SafeHold was overactive
(67% rate) and hurt accuracy - we need to calibrate when to abstain.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict
import math


@dataclass
class ConfidenceBucket:
    """A bucket for calibration analysis."""
    bucket_id: int
    confidence_range: Tuple[float, float]  # (min, max)
    predictions: List[float] = field(default_factory=list)
    outcomes: List[bool] = field(default_factory=list)
    
    @property
    def count(self) -> int:
        return len(self.outcomes)
    
    @property
    def accuracy(self) -> float:
        if not self.outcomes:
            return 0.0
        return sum(self.outcomes) / len(self.outcomes)
    
    @property
    def average_confidence(self) -> float:
        if not self.predictions:
            return 0.0
        return sum(self.predictions) / len(self.predictions)
    
    @property
    def calibration_error(self) -> float:
        """Absolute difference between confidence and accuracy."""
        return abs(self.average_confidence - self.accuracy)


class CalibrationAnalyzer:
    """
    Analyzes calibration of confidence estimates.
    
    Tracks predictions vs outcomes to measure whether
    confidence levels correlate with actual accuracy.
    """
    
    def __init__(self, n_buckets: int = 10):
        """
        Initialize calibration analyzer.
        
        Args:
            n_buckets: Number of confidence buckets for analysis
        """
        self.n_buckets = n_buckets
        self.buckets: List[ConfidenceBucket] = [
            ConfidenceBucket(
                bucket_id=i,
                confidence_range=(i / n_buckets, (i + 1) / n_buckets)
            )
            for i in range(n_buckets)
        ]
        
        # Overall stats
        self.total_predictions = 0
        self.total_correct = 0
        
    def record_prediction(
        self,
        confidence: float,
        outcome: bool,
    ):
        """
        Record a prediction and its outcome for calibration analysis.
        
        Args:
            confidence: Predicted confidence (0-1)
            outcome: Whether the prediction was correct
        """
        # Find the right bucket
        bucket_idx = min(
            int(confidence * self.n_buckets),
            self.n_buckets - 1
        )
        bucket_idx = max(0, bucket_idx)
        
        self.buckets[bucket_idx].predictions.append(confidence)
        self.buckets[bucket_idx].outcomes.append(outcome)
        
        self.total_predictions += 1
        if outcome:
            self.total_correct += 1
    
    def get_overall_accuracy(self) -> float:
        """Get overall accuracy across all predictions."""
        if self.total_predictions == 0:
            return 0.0
        return self.total_correct / self.total_predictions
    
    def get_reliability_curve(self) -> List[Tuple[float, float]]:
        """
        Get reliability curve: confidence vs accuracy per bucket.
        
        Returns:
            List of (average_confidence, accuracy) tuples
        """
        curve = []
        for bucket in self.buckets:
            if bucket.count > 0:
                curve.append((bucket.average_confidence, bucket.accuracy))
        return curve
    
    def get_calibration_error(self) -> float:
        """
        Get Expected Calibration Error (ECE).
        
        ECE = sum(bucket_weight * |bucket_accuracy - bucket_confidence|)
        
        Returns:
            ECE value (0-1, lower is better)
        """
        if self.total_predictions == 0:
            return 0.0
        
        ece = 0.0
        for bucket in self.buckets:
            if bucket.count > 0:
                weight = bucket.count / self.total_predictions
                ece += weight * bucket.calibration_error
        
        return ece
    
    def get_confidence_histogram(self) -> Dict[int, int]:
        """Get histogram of confidence values."""
        histogram = defaultdict(int)
        for bucket in self.buckets:
            histogram[bucket.bucket_id] = bucket.count
        return dict(histogram)
    
    def is_well_calibrated(self, threshold: float = 0.1) -> bool:
        """
        Check if the system is well calibrated.
        
        Args:
            threshold: Maximum acceptable ECE
            
        Returns:
            True if ECE is below threshold
        """
        return self.get_calibration_error() < threshold
    
    def get_optimal_threshold(
        self,
        target_accuracy: float = 0.8,
    ) -> float:
        """
        Find the confidence threshold that achieves target accuracy.
        
        This is key for SafeHold calibration: what confidence
        threshold gives us acceptable accuracy?
        
        Args:
            target_accuracy: Desired accuracy level
            
        Returns:
            Confidence threshold to use
        """
        # Build cumulative accuracy curve
        curve = self.get_reliability_curve()
        if not curve:
            return 0.5
        
        # Find threshold that achieves target
        # Go from high to low confidence
        for conf, acc in reversed(curve):
            if acc >= target_accuracy:
                return conf
        
        # If none meets target, return lowest
        return min(conf for conf, _ in curve)
    
    def analyze(self) -> Dict[str, Any]:
        """Get complete calibration analysis."""
        return {
            "total_predictions": self.total_predictions,
            "overall_accuracy": self.get_overall_accuracy(),
            "ece": self.get_calibration_error(),
            "is_well_calibrated": self.is_well_calibrated(),
            "reliability_curve": self.get_reliability_curve(),
            "confidence_histogram": self.get_confidence_histogram(),
            "bucket_details": [
                {
                    "bucket_id": b.bucket_id,
                    "range": b.confidence_range,
                    "count": b.count,
                    "accuracy": b.accuracy,
                    "avg_confidence": b.average_confidence,
                    "calibration_error": b.calibration_error,
                }
                for b in self.buckets if b.count > 0
            ],
        }


@dataclass
class AbstentionConfig:
    """Configuration for abstention (SafeHold) thresholds."""
    # Thresholds for different behaviors
    proceed_threshold: float = 0.8    # Proceed if confidence > this
    evidence_threshold: float = 0.5   # Request evidence if confidence > this
    abstain_threshold: float = 0.3    # Abstain if confidence < this
    
    # Calibrated thresholds (set after analysis)
    calibrated_proceed_threshold: Optional[float] = None
    calibrated_evidence_threshold: Optional[float] = None
    calibrated_abstain_threshold: Optional[float] = None
    
    def get_action(
        self,
        confidence: float,
    ) -> str:
        """
        Get recommended action based on confidence.
        
        Args:
            confidence: Current confidence estimate
            
        Returns:
            "proceed", "request_evidence", or "abstain"
        """
        # Use calibrated thresholds if available
        proceed = self.calibrated_proceed_threshold or self.proceed_threshold
        evidence = self.calibrated_evidence_threshold or self.evidence_threshold
        abstain = self.calibrated_abstain_threshold or self.abstain_threshold
        
        if confidence >= proceed:
            return "proceed"
        elif confidence >= evidence:
            return "request_evidence"
        else:
            return "abstain"


class CalibrationRunner:
    """
    Runs calibration experiments to find optimal thresholds.
    
    This helps answer: what SafeHold threshold gives the best
    accuracy vs abstention tradeoff?
    """
    
    def __init__(self):
        self.analyzer = CalibrationAnalyzer()
        self.abstention_results: List[Tuple[float, float, float]] = []  # (threshold, accuracy, abstention_rate)
    
    def run_threshold_sweep(
        self,
        confidence_values: List[float],
        outcomes: List[bool],
        thresholds: List[float],
    ) -> List[Dict[str, float]]:
        """
        Sweep through different thresholds to find optimal.
        
        For each threshold, computes what accuracy would be if we
        only proceed when confidence >= threshold.
        
        Args:
            confidence_values: List of confidence estimates
            outcomes: List of correctness (True = correct)
            thresholds: Thresholds to sweep
            
        Returns:
            List of {threshold, accuracy, abstention_rate, f1}
        """
        results = []
        
        for threshold in thresholds:
            # Filter to predictions above threshold
            above = [(c, o) for c, o in zip(confidence_values, outcomes) if c >= threshold]
            
            if not above:
                results.append({
                    "threshold": threshold,
                    "accuracy": 0.0,
                    "abstention_rate": 1.0,
                    "f1": 0.0,
                })
                continue
            
            correct = sum(1 for _, o in above if o)
            accuracy = correct / len(above)
            abstention_rate = 1.0 - len(above) / len(confidence_values)
            
            # F1-like score: balance accuracy and coverage
            # Higher weight on accuracy since we want correct when we act
            f1 = 2 * accuracy * (1 - abstention_rate) / (accuracy + (1 - abstention_rate) + 1e-6)
            
            results.append({
                "threshold": threshold,
                "accuracy": accuracy,
                "abstention_rate": abstention_rate,
                "f1": f1,
            })
            
            # Record for analyzer
            for conf, outcome in above:
                self.analyzer.record_prediction(conf, outcome)
        
        return results
    
    def find_optimal_threshold(
        self,
        results: List[Dict[str, float]],
        target_abstention: float = 0.2,
    ) -> float:
        """
        Find threshold that best meets target abstention rate.
        
        Args:
            results: Results from threshold sweep
            target_abstention: Desired abstention rate
            
        Returns:
            Optimal threshold
        """
        if not results:
            return 0.5
        
        # Find threshold closest to target abstention
        best = results[0]
        best_diff = abs(best["abstention_rate"] - target_abstention)
        
        for r in results:
            diff = abs(r["abstention_rate"] - target_abstention)
            if diff < best_diff:
                best = r
                best_diff = diff
        
        return best["threshold"]
    
    def get_calibrated_config(
        self,
        confidence_values: List[float],
        outcomes: List[bool],
    ) -> AbstentionConfig:
        """
        Get calibrated abstention configuration.
        
        Args:
            confidence_values: List of confidence estimates
            outcomes: List of correctness
            
        Returns:
            Configured AbstentionConfig with calibrated thresholds
        """
        # Run threshold sweep
        thresholds = [i * 0.1 for i in range(11)]
        results = self.run_threshold_sweep(
            confidence_values, outcomes, thresholds
        )
        
        # Analyze calibration
        analysis = self.analyzer.analyze()
        
        # Find optimal thresholds
        # Target: ~20% abstention, maximize accuracy
        optimal = self.find_optimal_threshold(results, target_abstention=0.2)
        
        # Get accuracy at each threshold level
        proceed_threshold = self.analyzer.get_optimal_threshold(target_accuracy=0.8)
        
        # Create calibrated config
        config = AbstentionConfig()
        config.calibrated_proceed_threshold = proceed_threshold
        config.calibrated_evidence_threshold = proceed_threshold - 0.2
        config.calibrated_abstain_threshold = optimal
        
        return config


def create_calibration_analyzer() -> CalibrationAnalyzer:
    """Factory function to create calibration analyzer."""
    return CalibrationAnalyzer()


def create_abstention_config() -> AbstentionConfig:
    """Factory function to create default abstention config."""
    return AbstentionConfig()
