
# -*- coding: utf-8 -*-
import io
from typing import IO, Callable, List, TypeVar, Union

import pandas as pd
from sqlalchemy.sql.schema import Column

T = TypeVar('T')


class GenerateField:
    source_column: str
    field_name: str
    value_mapping: Callable

    def __init__(self, column: Union[Column, str], field_name: str, value_mapping=None):
        self.source_column = column.name if hasattr(column, 'name') else column
        self.field_name = field_name
        self.value_mapping = value_mapping

    def convert_value(self, value):
        if self.value_mapping is None:
            return value
        return self.value_mapping(value)


def generate_xlsx_stream(rows: List[T], fields: List[GenerateField]) -> io.BytesIO:
    def map_value(row, field: GenerateField):
        return field.convert_value(getattr(row, field.source_column))

    all_data = [{
        field.field_name: map_value(row, field) for field in fields
    } for row in rows]

    df = pd.DataFrame(all_data)
    bio = io.BytesIO()
    writer = pd.ExcelWriter(bio, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    bio.seek(0)
    return bio
