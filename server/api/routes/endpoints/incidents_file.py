from fastapi import APIRouter, UploadFile, File, Query
from loguru import logger
import pandas as pd
from io import BytesIO

from incident_requests import (
    estimate_incident_probabilities_from_dataframe,
    update_incident_probabilities,
)
from incident_simulator.incident_type import IncidentType

from ....schemas import IncidentDTO, IncidentsResponse


router = APIRouter()


@router.post('/')
async def upload_incidents_file(
    file: UploadFile = File(...),
    days: int = Query(...),
    top_houses_limit: int = 30,
    alpha: float = 0.8,
) -> IncidentsResponse:
    try:
        contents = await file.read()
        excel_file = BytesIO(contents)
        df = pd.read_excel(excel_file, header=1)

        probability_estimation = estimate_incident_probabilities_from_dataframe(
            df,
            days=days,
            top_houses_limit=top_houses_limit,
        )
        old_probabilities = {
            incident_type.value: incident_type.base_probability
            for incident_type in IncidentType
        }
        updated_probabilities = update_incident_probabilities(
            old_probabilities,
            probability_estimation["probabilities"],
            alpha=alpha,
        )
        probability_update = {
            incident_type: {
                "old_probability": old_probabilities[incident_type],
                "new_probability": probability_estimation["probabilities"][
                    incident_type
                ],
                "updated_probability": updated_probabilities[incident_type],
                "count": probability_estimation["counts"][incident_type],
                "exposure": probability_estimation["exposure"][incident_type],
                "selected_houses_count": probability_estimation[
                    "selected_houses_count"
                ],
            }
            for incident_type in probability_estimation["probabilities"]
        }
        
        column_mapping = {
            'Дата': 'date',
            'Время': 'time',
            'Источник': 'source',
            'Адрес': 'address',
            'Пом.': 'room_number',
            'Категория': 'category',
            'Подкатегория': 'subcategory',
            'Описание': 'description',
            'Комментарий к выполненным работам': 'work_comments',
            'Статус заявки': 'status',
            'Желаемое время выполнения': 'desired_completion_time',
            'Дата исполнения': 'execution_date',
            'Исполнители': 'executors',
            'Координаторы': 'coordinators',
            'Перечень материалов': 'materials',
            'Услуги': 'services',
            'Стоимость': 'cost',
            'Вложения': 'attachments',
        }
        
        df = df.copy()
        df.rename(columns=column_mapping, inplace=True)
        
        dto_fields = IncidentDTO.model_fields.keys()
        available_columns = [col for col in dto_fields if col in df.columns]
        df = df[available_columns]
        
        incidents = []
        for _, row in df.iterrows():
            incident = IncidentDTO(**row.to_dict())
            incidents.append(incident)
        
        return IncidentsResponse(
            total_count=len(incidents),
            incidents=incidents,
            probability_update=probability_update,
        )
        
    except Exception as e:
        logger.error(f"Error in processing file: {str(e)}")
        raise Exception(f"Error in processing file: {str(e)}")
