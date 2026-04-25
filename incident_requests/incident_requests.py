from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd
from natasha import Doc, MorphVocab, NewsEmbedding, NewsMorphTagger, Segmenter


logger = logging.getLogger(__name__)


DEFAULT_COLUMNS_TO_DROP = ("Источник", "Категория")
DEFAULT_DESCRIPTION_COLUMN = "Описание"
INCIDENT_TYPE_COLUMN = "Тип инцидента"
ENGINEERING_SYSTEM_COLUMN = "Инж. система"

INCIDENT_PATTERNS = {
    "Замена ХВС на уровне техэтажа": (
        r"(замен|демонтаж|монтаж).*(труб|трубопровод).*(хвс|холодн).*(техническ.*этаж|тех.?этаж)"
    ),
    "Замена главных стояков ГВС": r"(замен|запланир).*(главн.*стояк).*(гвс|горяч)",
    "Замена трубы ГВС": r"(замен|демонтаж|монтаж).*(труб|трубопровод).*(гвс|горяч)",
    "Замена трубы ХВС": r"(замен|демонтаж|монтаж).*(труб|трубопровод).*(хвс|холодн)",
    "Замена розлива": r"(замен|демонтаж|монтаж).*(розлив)",
    "Анализ труб": (
        r"(анализ|обследова).*(труб|трубопровод)|(труб|трубопровод).*(анализ|обследова)"
    ),
    "Утечка радиатора": r"(теч|протеч|утеч).*(радиатор)|(радиатор).*(теч|протеч|утеч)",
    "Утечка стояка": r"(теч|протеч|утеч).*(стояк)|(стояк).*(теч|протеч|утеч)",
}

ENGINEERING_SYSTEM_PATTERNS = {
    "гвс": (r"гвс"),
    "хвс": (r"хвс"),
    "лифт": (r"лифт"),
}


class IncidentRequestsPreprocessor:
    def __init__(self, dataframe: pd.DataFrame) -> None:
        self.dataframe = dataframe.copy()
        self._natasha_components = self._build_natasha_components()

    # TODO: add tqdm
    def preprocess(self, drop_columns: tuple = DEFAULT_COLUMNS_TO_DROP) -> pd.DataFrame:
        dataframe = self.dataframe.copy()
        dataframe.columns = [str(column).strip() for column in dataframe.columns]

        if dataframe.empty and len(dataframe.columns) == 0:
            raise ValueError("В таблице нет колонок для предобработки.")

        first_column = dataframe.columns[0]
        dataframe = dataframe.rename(columns={first_column: "Дата"})

        cols2drop = [column for column in drop_columns if column in dataframe.columns]
        if cols2drop:
            dataframe = dataframe.drop(columns=cols2drop, errors="ignore")

        if DEFAULT_DESCRIPTION_COLUMN not in dataframe.columns:
            raise ValueError(
                f"Колонка '{DEFAULT_DESCRIPTION_COLUMN}' не найдена. "
                f"Доступные колонки: {list(dataframe.columns)}"
            )

        dataframe[INCIDENT_TYPE_COLUMN] = dataframe[DEFAULT_DESCRIPTION_COLUMN].apply(
            self._detect_incident_type
        )

        dataframe[ENGINEERING_SYSTEM_COLUMN] = dataframe[DEFAULT_DESCRIPTION_COLUMN].apply(
            self._detect_system_type
        )

        self.dataframe = dataframe
        return dataframe
    
    def getOverview(self) -> pd.DataFrame:
            dataframe = self.dataframe

            if INCIDENT_TYPE_COLUMN not in dataframe.columns:
                dataframe = self.preprocess()

            incidents = list(INCIDENT_PATTERNS.keys()) + ["Прочее", "Не определен"]
            incident_counts = dataframe[INCIDENT_TYPE_COLUMN].value_counts()

            return pd.DataFrame(
                [(incident, int(incident_counts.get(incident, 0))) for incident in incidents],
                columns=["incident", "count"],
            )
    
    def getIncidentsData(self):
        if INCIDENT_TYPE_COLUMN not in self.dataframe.columns:
            self.dataframe = self.preprocess()

        incidents = []
        gvs_incidents = 0
        hvs_incidents = 0
        lift_incidents = 0

        for _, row in self.dataframe.iterrows():
            description = str(row.get(DEFAULT_DESCRIPTION_COLUMN) or "").lower()

            # TODO: i already define engineering system type and add this as feature, so may delete block below
            if "гвс" in description:
                gvs_incidents += 1
            if "хвс" in description:
                hvs_incidents += 1
            if "лифт" in description:
                lift_incidents += 1

            incidents.append(
                {
                    "date_start": self._json_value(row.get("Дата")),
                    "date_end": self._json_value(row.get("Дата исполнения")),
                    "incident_time_start": self._json_value(row.get("Время")),
                    "address": self._json_value(row.get("Адрес")),
                    "incident_location": self._json_value(row.get("Пом.")),
                    "subcategory": self._json_value(row.get("Подкатегория")),
                    "incident_type": self._json_value(row.get(INCIDENT_TYPE_COLUMN)),
                    "performers": self._json_value(row.get("Исполнители")),
                    "materials": self._json_value(row.get("Перечень материалов")),
                    "cost": self._json_value(row.get("Стоимость")),
                }
            )

        return {
            "metadata": {
                "total_incidents": len(incidents),
                "gvs_incidents": gvs_incidents,
                "hvs_incidents": hvs_incidents,
                "lift_incidents": lift_incidents,
            },
            "incidents": incidents,
        }

    def _detect_incident_type(self, description: Any) -> str:
        normalized_description = self._lemmatize_natasha(description)

        if not normalized_description:
            return "Не определен"

        for incident_type, pattern in INCIDENT_PATTERNS.items():
            if re.search(pattern, normalized_description, flags=re.IGNORECASE):
                return incident_type

        return "Прочее"
    
    def _detect_system_type(self, description: Any) -> str:
        normalized_description = self._lemmatize_natasha(description)

        if not normalized_description:
            return "Не определен"

        for engineering_system_type, pattern in ENGINEERING_SYSTEM_PATTERNS.items():
            if re.search(pattern, normalized_description, flags=re.IGNORECASE):
                return engineering_system_type

        return "Прочее"

    def getOverview(self) -> pd.DataFrame:
        dataframe = self.dataframe

        if INCIDENT_TYPE_COLUMN not in dataframe.columns:
            dataframe = self.preprocess()

        incidents = list(INCIDENT_PATTERNS.keys()) + ["Прочее", "Не определен"]
        incident_counts = dataframe[INCIDENT_TYPE_COLUMN].value_counts()

        return pd.DataFrame(
            [(incident, int(incident_counts.get(incident, 0))) for incident in incidents],
            columns=["incident", "count"],
        )
    
    def _json_value(self, value):
        if pd.isna(value):
            return None

        if isinstance(value, pd.Timestamp):
            return value.isoformat()

        return value


    def _lemmatize_natasha(self, text: Any) -> str:
        if pd.isna(text):
            return ""

        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            return ""

        if self._natasha_components is None:
            return text

        segmenter, morph_vocab, morph_tagger = self._natasha_components

        doc = Doc(text)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)

        lemmas = []
        for token in doc.tokens:
            token.lemmatize(morph_vocab)
            lemmas.append(token.lemma)

        return " ".join(lemmas)

    def _build_natasha_components(self) -> tuple[Any, Any, Any] | None:
        if None in (Doc, MorphVocab, NewsEmbedding, NewsMorphTagger, Segmenter):
            logger.warning(
                "Natasha не установлена. Тип инцидента будет определяться без лемматизации."
            )
            return None

        segmenter = Segmenter()
        morph_vocab = MorphVocab()
        embedding = NewsEmbedding()
        morph_tagger = NewsMorphTagger(embedding)

        return segmenter, morph_vocab, morph_tagger
