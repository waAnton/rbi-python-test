import re

import numpy as np
import pandas as pd
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
    "in": "in",
    "notin": "in",
    "ne": "!="
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
                    df_copy.sort_values(by=get_word_list(value), inplace=True)
                    continue
                if key == "fields":
                    df_copy = df_copy[get_word_list(value)]

        if conditions:
            df_copy = df_copy.query(' and '.join(conditions))

        return {"message": df_copy.fillna("").to_dict("records")}
    except KeyError as exc:
        return JSONResponse({"message": str(exc)}, HTTP_400_BAD_REQUEST)


@app.get("/column_definitions")
async def column_info():
    return {"message": zip(columns, df_init.columns)}


def get_word_list(words: str, is_field: bool = True):
    """
    Return list of unique words from input string
    :param words: string with words separated by commas
    :param is_field: if true, we have additional condition (If some field not found in column list - throw error).
    :return: list of unique words
    """
    word_list = np.char.strip(words.split(","))
    unique_words = np.unique(word_list)

    if is_field and not set(unique_words).issubset(columns):
        raise KeyError(f"Unsupported column in fields")
    return unique_words.tolist()


def get_condition(key: str, value: str) -> str:
    """
    Return parsed condition.
    Supported gte, lte, gt, lt, ne, in, notin operations.
    By default, is the 'equal' operation.
    If some field not found in column list - throw error.
    :param key: name of field from dataset with operation. For example salary[gte]
    :param value: value of field
    :return: parsed condition
    """
    match = re.match(r"(.+)\[(gte|lte|gt|lt|in|ne|notin)]", key)
    in_operation = False
    not_in_operation = False
    if match:
        field, op = match.groups()
        if op == "in":
            in_operation = True
        else:
            if op == "notin":
                not_in_operation = True
        op = operation_map[op]
    else:
        field, op = key, "=="
    if field not in columns:
        raise KeyError(f"Unsupported key {field}")

    if in_operation:
        return f"{field} {op} ({get_word_list(value, False)})"

    if not_in_operation:
        return f"~({field} {op} ({get_word_list(value, False)}))"

    if value.isnumeric():
        return f"{field} {op} {value}"

    return f"{field} {op} '{value}'"
