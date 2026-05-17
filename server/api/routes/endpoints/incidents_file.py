from fastapi import APIRouter, UploadFile, File
from loguru import logger
import pandas as pd
from io import BytesIO

from ....schemas import IncidentDTO, IncidentsResponse


router = APIRouter()


@router.post('/')
async def upload_incidents_file(file: UploadFile = File(...)) -> IncidentsResponse:
    try:
        contents = await file.read()
        excel_file = BytesIO(contents)
        df = pd.read_excel(excel_file, header=1)
        
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
            incidents=incidents
        )
        
    except Exception as e:
        logger.error(f"Error in processing file: {str(e)}")
        raise Exception(f"Error in processing file: {str(e)}")
