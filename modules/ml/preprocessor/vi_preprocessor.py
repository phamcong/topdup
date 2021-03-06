import logging
import os
import re
from copy import deepcopy
from typing import Any, Dict, List, Optional

import nltk
from more_itertools.more import windowed

from modules.ml.plugins.vncorenlp import VnCoreNLPSingleton

from .base import BasePreProcessor
from .cleaning import normalize_text

logger = logging.getLogger(__name__)


class ViPreProcessor(BasePreProcessor):
    def __init__(
        self,
        split_by: Optional[str] = "word",
        split_length: Optional[int] = 1000,
        split_overlap: Optional[int] = None,
        split_respect_sentence_boundary: Optional[bool] = True,
        use_fixed_stopwords: Optional[bool] = False,
    ):
        """
        Attributes:
            split_by (str, optional): Unit for splitting the document.
                Can be "word", "sentence", or "passage".
                Set `None` to disable spliting. Defaults to "word".
            split_length (int, optional): Max. number of the above split unit (e.g. words)
                that are allowed in one document. Defaults to 1000.
            split_overlap (int, optional): Word overlap between two adjacent documents after a split.
                Setting this to a positive number essentially enables the sliding window approach.
                For example, if split_by -> `word`,
                split_length -> 5 & split_overlap -> 2, then the splits would be like:
                [w1 w2 w3 w4 w5, w4 w5 w6 w7 w8, w7 w8 w10 w11 w12].
                Set the value to None to ensure there is no overlap among the documents after splitting.
                Defaults to None.
            split_respect_sentence_boundary (bool, optional): Whether to split in
                partial sentences if split_by -> `word`.
                If set to True, the individual split will always have complete sentences &
                the number of words will be <= split_length.. Defaults to True.
            use_fixed_stopwords (bool, optional): remove stopwords that appears in pre-defined files.
                Defaults to False.
        """
        nltk.download("punkt")
        self.rdrsegmenter = VnCoreNLPSingleton.get_instance()

        self.use_fixed_stopwords = use_fixed_stopwords
        self.split_by = split_by
        self.split_length = split_length
        self.split_overlap = split_overlap
        self.split_respect_sentence_boundary = split_respect_sentence_boundary

        self.stopwords: List[str]
        if use_fixed_stopwords:
            self._load_stopwords()

    def clean(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Performs document cleaning on a single document and return a single document.
        Includes dealing with whitespaces, empty lines.
        """
        text = document["text"]

        text = normalize_text(text)
        text = self._word_segment(text)
        text = _clean_vncore_result(text)

        document["text"] = text
        return document

    def split(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.split_by:
            return [document]

        if not self.split_length:
            raise ValueError("split_length needs be set when using split_by.")

        if self.split_respect_sentence_boundary and self.split_by not in (
            "word",
            "sentence",
        ):
            raise NotImplementedError(
                "'split_respect_sentence_boundary=True' is only compatible with"
                " split_by='word' or split_by='sentence'."
            )

        text = document["text"]

        if self.split_respect_sentence_boundary and self.split_by == "word":
            sentences = nltk.tokenize.sent_tokenize(text)
            word_count = 0
            list_splits = []
            current_slice: List[str] = []
            for sen in sentences:
                current_word_count = len(sen.split(" "))
                if current_word_count > self.split_length:
                    logger.warning(
                        "A sentence found with word count higher than the split length."
                    )
                if word_count + current_word_count > self.split_length:
                    list_splits.append(current_slice)

                    if self.split_overlap:
                        overlap = []
                        w_count = 0
                        for s in current_slice[::-1]:
                            sen_len = len(s.split(" "))
                            if w_count < self.split_overlap:
                                overlap.append(s)
                                w_count += sen_len
                            else:
                                break
                        current_slice = list(reversed(overlap))
                        word_count = w_count
                    else:
                        current_slice = []
                        word_count = 0
                current_slice.append(sen)
                word_count += len(sen.split(" "))
            if current_slice:
                list_splits.append(current_slice)
            text_splits = [" ".join(sl) for sl in list_splits]
        else:
            if self.split_by == "passage":
                elems = text.split("\n\n")
            elif self.split_by == "sentence":
                elems = nltk.tokenize.sent_tokenize(text)
            elif self.split_by == "word":
                elems = text.split(" ")
            else:
                raise NotImplementedError(
                    "ViPreProcessor only supports 'passage', \
                    'sentence' or 'word' split_by options"
                )

            if self.split_overlap:
                segments = windowed(
                    elems,
                    n=self.split_length,
                    step=self.split_length - self.split_length,
                )
            else:
                segments = windowed(elems, n=self.split_length, step=self.split_length)
            text_splits = []
            for seg in segments:
                # txt = " ".join([t for t in seg if t])
                # text_splits.append(txt)
                text_splits = [t for t in seg if t]

        # create new document dicts for each text split
        documents = []
        for i, txt in enumerate(text_splits):
            doc = deepcopy(document)
            doc["text"] = txt
            if "meta" not in doc.keys() or doc["meta"] is None:
                doc["meta"] = {}
            doc["meta"]["_split_id"] = i
            documents.append(doc)

        return documents

    def _word_segment(self, text: str) -> str:
        """Uses VnCoreNLP-based tokenizer for word segmentation.
        """
        sentences = self.rdrsegmenter.tokenize(text)

        tokenized_sents = []
        for words in sentences:
            if self.use_fixed_stopwords:
                words = filter(lambda w: w not in self.stopwords, words)
            tokenized_sents.append(" ".join(words))

        result = " ".join(tokenized_sents)
        return result

    def _load_stopwords(
        self, stopword_path: str = "modules/ml/data/vietnamese-stopwords.txt"
    ):
        """Loads list of stopwords from given path.

        ref: https://github.com/stopwords/vietnamese-stopwords/
        """
        if not os.path.isfile(stopword_path):
            logger.error("File not found, stopwords list not initialized")
            return
        if not self.stopwords:
            self.stopwords = []
        with open(stopword_path, "r") as f:
            for line in f:
                word = line.replace("\n", "")
                self.stopwords.append(word)


def _clean_vncore_result(text: str) -> str:
    """Cleans special cases caused by VnCoreNLP.

    Example: "cho đến thời_điểm này , có_thể nói ,"
    """
    text = re.sub(r"\s([?.!,](?:\s|$))", r"\1", text)
    text = re.sub(r"\(\s", "(", text)
    text = re.sub(r"\s\)", ")", text)
    return text
