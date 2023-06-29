import re
from typing import List

import pandas as pd
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

from helpers.common import DayOfWeek, ToDo

TODO_PATTERN = r"(\d{2}:\d{2})\s+-\s+(\d{2}:\d{2})\s+(.*)"

TODAY_HABITS_TEMPLATE = """
Habits for scheduling in Markdown:

```
{habits_table}
```

Given that today is {day_of_week}, decide whether each habit should be scheduled for today using the `schedule_days`. `schedule_days` ranges (e.g. Monday to Friday) must be scheduled on all days between Monday and Friday (inclusive). Your response should always end with a list of comma separated scheduled habits on a new line, eg: 
foo, bar, baz

Think about how to schedule each habit step by step. 
""".strip()

SCHEDULE_HABITS_TEMPLATE = """
You're an expert personal assistant responsible for managing individual schedules. Assign start and end time for each habit from the markdown table:

```
{habits_table}
```

Write a list of scheduled items, formatted like this:

HH:MM - HH:MM Habit name

I wake up at 08:00 and finish my day at 21:30.

Each habit must be scheduled exactly once. Sort the list by start time. Think step by step.
""".strip()

SCHEDULE_QUESTION_TEMPLATE = """
As an expert personal assistant responsible for managing personal schedules, use the following schedule:

```
{schedule}
```

The schedule uses 24-hour format and is formatted as such:

```
(start time) - (end time) task name
```

Change the schedule according to the question:

```
{question}
```

Think step by step. Reply with the updated schedule at the end.
""".strip()


def parse_todo_items(schedule: str) -> List[ToDo]:
    items = []
    matched_once = False
    for line in reversed(schedule.split("\n")):
        matches = re.findall(TODO_PATTERN, line)
        if matches:
            matched_once = True
            match = matches[0]
            todo = ToDo(
                start_time=match[0],
                end_time=match[1],
                name=match[2].strip(),
            )
            items.append(todo)
        elif matched_once:
            break
    return list(reversed(items))


def find_scheduled_habits(habits_df: pd.DataFrame, llm_response: str) -> List[str]:
    all_habits = set(habits_df["name"].tolist())
    for line in reversed(llm_response.split("\n")):
        scheduled_habits = [habit.strip() for habit in line.split(",")]
        if all_habits.issuperset(scheduled_habits):
            return scheduled_habits
    return []


def create_schedule(habits_df: pd.DataFrame, day_of_week: DayOfWeek) -> List[ToDo]:
    chat_gpt = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    prompt = PromptTemplate(
        template=TODAY_HABITS_TEMPLATE, input_variables=["habits_table", "day_of_week"]
    )

    chain = LLMChain(llm=chat_gpt, prompt=prompt)
    habits_table = habits_df[["name", "schedule_days"]].to_markdown(index=None)
    result = chain.run(day_of_week=day_of_week, habits_table=habits_table)
    scheduled_habits = find_scheduled_habits(habits_df, result)
    if len(scheduled_habits) == 0:
        return []
    scheduled_df = habits_df[habits_df.name.isin(scheduled_habits)]

    prompt = PromptTemplate(
        template=SCHEDULE_HABITS_TEMPLATE, input_variables=["habits_table"]
    )
    habits_table = scheduled_df[["name", "preferred_time", "duration"]].to_markdown(
        index=None
    )
    chain = LLMChain(llm=chat_gpt, prompt=prompt)
    result = chain.run(habits_table=habits_table)
    return parse_todo_items(result)


def update_schedule(schedule: List[ToDo], question: str) -> List[ToDo]:
    chat_gpt = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    prompt = PromptTemplate(
        template=SCHEDULE_QUESTION_TEMPLATE, input_variables=["schedule", "question"]
    )
    schedule_text = "\n".join([str(todo) for todo in schedule])
    chain = LLMChain(llm=chat_gpt, prompt=prompt)
    result = chain.run(schedule=schedule_text, question=question)
    return parse_todo_items(result)
