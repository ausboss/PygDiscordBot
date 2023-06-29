import discord
from discord.ext import commands
import pandas as pd
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from enum import Enum


@dataclass
class ToDo:
    name: str
    start_time: str
    end_time: str

    def __str__(self) -> str:
        return f"{self.start_time} - {self.end_time} {self.name}"


class DayOfWeek(Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"

# from helpers.common import DayOfWeek, ToDo
from helpers.scheduler import create_schedule, update_schedule


class HabitTrackerCog(commands.Cog, name="HabitTracker"):
    def __init__(self, bot):
        self.bot = bot
        self.habits_df = None

    @commands.command(name="load_google_sheet", help="Load habits from Google Sheet")
    async def load_google_sheet(self, ctx, *, google_sheets_url: str):
        csv_url = google_sheets_url.replace("/edit#gid=", "/export?format=csv&gid=")
        self.habits_df = pd.read_csv(csv_url)
        await ctx.send("Loaded habits from Google Sheet")

    @commands.command(name="generate_schedule", help="Generate a schedule for the given day")
    async def generate_schedule(self, ctx, *, day_of_week: str):
        if self.habits_df is None:
            await ctx.send("You must first load habits with the `load_google_sheet` command")
        else:
            try:
                day_of_week = DayOfWeek[day_of_week.upper()]
            except KeyError:
                await ctx.send("Invalid day of week. Please enter one of: " + ", ".join([d.value for d in DayOfWeek]))
                return

            todo_list = create_schedule(self.habits_df, day_of_week)
            schedule_str = "\n".join([str(todo) for todo in todo_list])
            await ctx.send(f"Schedule for {day_of_week.value}:\n{schedule_str}")

    @commands.command(name="update_schedule", help="Update the schedule based on a prompt")
    async def update_schedule(self, ctx, *, question: str):
        if self.habits_df is None:
            await ctx.send("You must first load habits with the `load_google_sheet` command")
        else:
            try:
                todo_list = update_schedule(self.habits_df, question)
                schedule_str = "\n".join([str(todo) for todo in todo_list])
                await ctx.send(f"Updated schedule:\n{schedule_str}")
            except Exception as e:
                await ctx.send(f"An error occurred while updating schedule: {str(e)}")

async def setup(bot):
    await bot.add_cog(HabitTrackerCog(bot))
