from abc import ABCMeta, abstractmethod
from typing import List, Tuple

import pandas as pd

from ludwig.api import LudwigModel
from ludwig.api_annotations import DeveloperAPI
from ludwig.constants import BINARY, CATEGORY, TYPE
from ludwig.explain.explanation import Explanation
from ludwig.explain.util import prepare_data


@DeveloperAPI
class Explainer(metaclass=ABCMeta):
    def __init__(
        self,
        model: LudwigModel,
        inputs_df: pd.DataFrame,
        sample_df: pd.DataFrame,
        target: str,
        use_global: bool = False,
    ):
        """Constructor for the explainer.

        # Inputs

        :param model: (LudwigModel) The LudwigModel to explain.
        :param inputs_df: (pd.DataFrame) The input data to explain.
        :param sample_df: (pd.DataFrame) A sample of the ground truth data.
        :param target: (str) The name of the target to explain.
        :param use_global: (bool) Return global explanation aggregated over all rows if True (default: False).
        """
        self.model = model
        self.inputs_df = inputs_df
        self.sample_df = sample_df
        self.target = target
        self.use_global = use_global
        self.inputs_df, self.sample_df, self.feature_cols, self.target_feature_name = prepare_data(
            model, inputs_df, sample_df, target
        )

        if self.use_global:
            self.explanations = [Explanation(self.target_feature_name)]
        else:
            self.explanations = [Explanation(self.target_feature_name) for _ in self.inputs_df.index]

        # Lookup from column name to output feature
        config = self.model.config
        self.output_feature_map = {feature["column"]: feature for feature in config["output_features"]}

    @property
    def is_binary_target(self) -> bool:
        """Whether the target is binary."""
        return self.output_feature_map[self.target_feature_name][TYPE] == BINARY

    @property
    def is_category_target(self) -> bool:
        """Whether the target is categorical."""
        return self.output_feature_map[self.target_feature_name][TYPE] == CATEGORY

    @property
    def vocab_size(self) -> int:
        """The vocab size of the target feature.

        For regression (number) this is 1, for binary it is 2, and for category it is the vocab size.
        """
        if self.is_category_target:
            return self.model.training_set_metadata[self.target_feature_name]["vocab_size"]
        elif self.is_binary_target:
            return 2
        return 1

    @abstractmethod
    def explain(self) -> Tuple[List[Explanation], List[float]]:
        """Explain the model's predictions.

        # Return

        :return: (Tuple[List[Explanation], List[float]]) `(explanations, expected_values)`
            `explanations`: (List[Explanation]) A list of explanations, one for each row in the input data. Each
            explanation contains the feature attributions for each label in the target feature's vocab.

            `expected_values`: (List[float]) of length [output feature cardinality] Expected value for each label in
            the target feature's vocab.
        """
