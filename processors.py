import logging
import os
import typing as T
from pathlib import Path

import pandas as pd
from transformers.data.processors.utils import DataProcessor
from transformers.data.processors.utils import InputExample

logger = logging.getLogger("webdetectclf")

LABELS = [str(i) for i in range(1, 10)]


class MultiPhaseTrainProcessor(DataProcessor):
    def get_number_of_train_phases(self, data_dir: str) -> int:
        train_prefixed_files = list(
            filter(
                lambda s: s.startswith("train") and s.endswith(".tsv"),
                sorted([p.name for p in Path(data_dir).iterdir()]),
            )
        )
        if len(train_prefixed_files) == 1 and train_prefixed_files[0] == "train.tsv":
            return 0
        for i, basename in enumerate(train_prefixed_files, start=1):
            if f"train{i}.tsv" != basename:
                raise Exception(
                    "Did not find files sequentially named 'train1.tsv', 'train2.tsv'."
                )
        return len(train_prefixed_files)


class FrameProcessor(MultiPhaseTrainProcessor):
    def get_train_examples(self, data_dir, phase=0):
        """See base class."""

        if phase:
            file_path = f"train{phase}.tsv"
        else:
            file_path = "train.tsv"
        return self._create_examples(
            self._read_csv(os.path.join(data_dir, file_path)), "train"
        )

    def get_dev_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_csv(os.path.join(data_dir, "dev.tsv")), "dev"
        )

    def get_test_examples(self, data_dir):
        """See base class."""
        return self._create_examples(
            self._read_csv(os.path.join(data_dir, "test.tsv")), "test"
        )

    def get_labels(self):
        """See base class."""
        return LABELS

    @staticmethod
    def _read_csv(file_path: str) -> pd.DataFrame:
        _ = (
            "Unnamed: 0",
            "ImageID",
            "Month",
            "ID",
            "news_title",
            "Q1 Relevant",
            "Q2 Focus",
            "original_index",
            "Q3 Theme1",
            "Q3 Theme2",
            "V1image",
            "V2ethnicity",
            "V3relevance",
            "V4relevance",
            "Q4 Image1",
            "Q4 Image2",
            "WebDetectEntities",
        )

        with open(file_path) as f:
            df = pd.read_csv(f, dtype=object, sep="\t", index_col=False)
        return df

    def _create_examples(self, df, set_type) -> T.List[InputExample]:
        """Creates examples for the training and dev sets."""

        examples = []
        for _, row in df.iterrows():
            row = row.fillna("")
            guid = "%s-image_id_%s-id_%s" % (set_type, row["ImageID"], row["ID"])
            text_a = row["news_title"]
            label = row["Q3 Theme1"]
            examples.append(InputExample(guid=guid, text_a=text_a, label=label))
        return examples


class WebDetectProcessor(FrameProcessor):
    def _create_examples(self, df, set_type) -> T.List[InputExample]:
        """Creates examples for the training and dev sets."""

        examples = []
        for _, row in df.iterrows():
            row = row.fillna("")
            guid = "%s-image_id_%s-id_%s" % (set_type, row["ImageID"], row["ID"])
            text_a = row["news_title"]
            text_b = row["WebDetectEntities"]
            label = row["Q3 Theme1"]
            examples.append(
                InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label)
            )
        return examples


class WebDetectOnlyProcessor(FrameProcessor):
    def _create_examples(self, df, set_type) -> T.List[InputExample]:
        """Creates examples for the training and dev sets."""

        # Headers should be
        # created_at,id_str,ID,Sejin,Rachael,Final Answer,text

        examples = []
        for _, row in df.iterrows():
            row = row.fillna("")
            guid = "%s-image_id_%s-id_%s" % (set_type, row["ImageID"], row["ID"])
            text_a = row["WebDetectEntities"]
            label = row["Q3 Theme1"]
            examples.append(InputExample(guid=guid, text_a=text_a, label=label))
        return examples


processors: T.Dict[str, DataProcessor] = {
    "frame": FrameProcessor,
    "webdetect": WebDetectProcessor,
    "webdetectonly": WebDetectOnlyProcessor,
}
output_modes = {
    "frame": "classification",
    "webdetect": "classification",
    "webdetectonly": "classification",
}


def main():
    DATA_D = "data_subsets/all_data/0"
    frame_proc = FrameProcessor()
    # webdetect_proc = WebDetectProcessor()
    examples_per_split = {
        "dev": frame_proc.get_dev_examples(DATA_D),
    }

    # print(f"Number of train phases: {frame_proc.get_number_of_train_phases(DATA_D)}")
    for split, examples in examples_per_split.items():
        print("A few {} samples are:".format(split))
        print(examples)


if __name__ == "__main__":
    main()
