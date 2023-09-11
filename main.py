import re

import pandas as pd
import numpy as np
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST

columns = ["timestamp", "employment_type", "company_name", "company_size", "country", "city", "industry",
           "company_type", "industry_years", "current_years", "job_title", "job_ladder", "job_level", "required_hours",
           "actual_hours", "education", "salary", "bonus", "stock", "insurance", "vacation",
           "happy_on_current_position", "resign_in_the_next_12_months", "thoughts", "gender", "final_question",
           "bootcamp_attend"]

df_init = pd.read_csv("datasets/salary_survey.csv")
# setting tipe of 'Timestamp' column for correct sorting and searching
df_init["Timestamp"] = df_init["Timestamp"].astype("datetime64[ns]")

operation_map = {
    "gte": ">=",
    "lte": "<=",
    "gt": ">",
    "lt": "<",
}

app = FastAPI()


@app.get("/compensation_data")
async def get_compensation_data(request: Request):
    df_copy = df_init.copy()
    df_copy.columns = columns
    conditions = []
    try:
        if request.query_params.items():
            for key, value in request.query_params.items():
                if key not in (["sort", "fields"]):
                    conditions.append(get_condition(key, value))
                    continue
                if key == "sort":
                    df_copy.sort_values(by=get_fields(value), inplace=True)
                    continue
                if key == "fields":
                    df_copy = df_copy[get_fields(value)]

        if conditions:
            df_copy = df_copy.query(' and '.join(conditions))

        return {"message": df_copy.fillna("").to_dict("records")}
    except KeyError as exc:
        return JSONResponse({"message": str(exc)}, HTTP_400_BAD_REQUEST)


@app.get("/column_definitions")
async def column_info():
    return {"message": zip(columns, df_init.columns)}


def get_fields(fields: str):
    '''
    Return list of unique field names.
    If some field not found in column list - throw error.
    :param fields: string with field names separated by commas
    :return: list of unique field names
    '''
    field_list = np.char.strip(fields.split(","))
    unique_fields = np.unique(field_list)

    if not set(unique_fields).issubset(columns):
        raise KeyError(f"Unsupported column in fields")
    return unique_fields.tolist()


def get_condition(key: str, value: str) -> str:
    '''
    Return list of parsed conditions.
    Supported gte, lte, gt, lt operations.
    By default, is the 'equal' operation.
    If some field not found in column list - throw error.
    :param key: name of field from dataset with operation. For example salary[gte]
    :param value: value of field
    :return: list of parsed conditions
    '''
    match = re.match(r"(.+)\[(gte|lte|gt|lt)]", key)
    if match:
        field, op = match.groups()
        op = operation_map[op]
    else:
        field, op = key, "=="
    if field not in columns:
        raise KeyError(f"Unsupported key {field}")
    if value.isnumeric():
        return f"{field} {op} {value}"

    return f"{field} {op} '{value}'"
