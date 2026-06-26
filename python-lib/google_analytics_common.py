from datetime import datetime, timedelta


MANUAL_SELECT_ENTRY = {"label": "✍️ Enter manually", "value": "dku_manual_select"}
COLUMN_SELECT_ENTRY = {"label": "🏛️ Get from column", "value": "dku_column_select"}


class DSSSelectorChoices(object):

    def __init__(self):
        self.choices = []

    def is_empty(self):
        return not self.choices

    def append(self, label, value):
        self.choices.append(
            {
                "label": label,
                "value": value
            }
        )

    def append_alphabetically(self, new_label, new_value):
        index = 0
        new_choice = {
            "label": new_label,
            "value": new_value
        }
        for choice in self.choices:
            choice_label = choice.get("label")
            if choice_label < new_label:
                index += 1
            else:
                break
        self.choices.insert(index, new_choice)

    def append_manual_select(self):
        self.choices.append(MANUAL_SELECT_ENTRY)

    def start_with_manual_select(self):
        self.choices.insert(0, MANUAL_SELECT_ENTRY)

    def _build_select_choices(self, choices=None):
        if not choices:
            return {"choices": []}
        if isinstance(choices, str):
            return {"choices": [{"label": "{}".format(choices)}]}
        if isinstance(choices, list):
            return {"choices": choices}
        if isinstance(choices, dict):
            returned_choices = []
            for choice_key, choice_value in choices.items():
                returned_choices.append({
                    "label": choice_key,
                    "value": choice_value
                })
            return {"choices": returned_choices}

    def text_message(self, text_message):
        return self._build_select_choices(text_message)

    def to_dss(self):
        return self._build_select_choices(self.choices)


class RecordsLimit():
    def __init__(self, records_limit=-1):
        self.has_no_limit = (records_limit == -1)
        self.records_limit = records_limit
        self.counter = 0

    def is_reached(self):
        if self.has_no_limit:
            return False
        self.counter += 1
        return self.counter > self.records_limit


def assert_valid_config_v4(config):

    if not config.get("property_id_select"):
        raise Exception("Please select the account")
    if config.get("property_id_select") == "dku_manual_select":
        if not config.get("property_id") or config.get("property_id") == "":
            raise Exception("Please enter the account ID")

    if not config.get("web_property_id_select"):
        raise Exception("Please select the web property")
    if config.get("web_property_id_select") == "dku_manual_select":
        if not config.get("web_property_id") or config.get("web_property_id") == "":
            raise Exception("Please enter the web property ID")

    if not config.get("start_date") and not config.get("manual_start_date") and config.get("date_range") in [None, "manual"]:
        raise Exception("Please enter start date")

    if not config.get("end_date") and not config.get("manual_end_date") and config.get("date_range") in [None, "manual"]:
        raise Exception("Please enter end date")


def get_selected_value(payload, manual_key, separator=None):
    select_key = "{}_select".format(manual_key)
    selected_value = payload.get(select_key)
    if selected_value == "dku_manual_select":
        return payload.get(manual_key)
    elif selected_value == ["dku_manual_select"]:
        selected_value = payload.get(manual_key)
        selected_value=selected_value.split(separator)
    return selected_value


def get_date_range(config):
    #  output format should be 2024-12-31T23:59:00.000
    date_range = config.get("date_range", None)  # Custom by default
    if date_range is None:  # not is_date_entered_manually:
        start_date = config.get("start_date")
        end_date = config.get("end_date")
    elif date_range == "manual":
        start_date = config.get("manual_start_date")
        end_date = config.get("manual_end_date")
    elif date_range == "today":
        today = datetime.now() - timedelta(days=0)
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
        end_date = today.replace(hour=23, minute=59, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
    elif date_range == "yesterday":
        yesterday = datetime.now() - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
        end_date = yesterday.replace(hour=23, minute=59, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
    elif date_range == "last_7_days":
        today = datetime.now()
        start_day = today - timedelta(days=7)
        end_day = today - timedelta(days=1)
        start_date = start_day.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
        end_date = end_day.replace(hour=23, minute=59, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
    elif date_range == "last_14_days":
        today = datetime.now()
        start_day = today - timedelta(days=14)
        end_day = today - timedelta(days=1)
        start_date = start_day.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
        end_date = end_day.replace(hour=23, minute=59, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
    elif date_range == "last_work_week":
        today = datetime.now()
        current_monday = today - timedelta(days=today.weekday())
        last_monday = current_monday - timedelta(days=7)
        last_friday = last_monday + timedelta(days=4)
        start_date = last_monday.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
        end_date = last_friday.replace(hour=23, minute=59, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
    elif date_range == "last_week":
        today = datetime.now()
        current_monday = today - timedelta(days=today.weekday())
        last_monday = current_monday - timedelta(days=7)
        last_sunday = last_monday + timedelta(days=6)
        start_date = last_monday.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
        end_date = last_sunday.replace(hour=23, minute=59, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
    elif date_range == "last_30_days":
        today = datetime.now()
        start_day = today - timedelta(days=30)
        end_day = today - timedelta(days=1)
        start_date = start_day.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
        end_date = end_day.replace(hour=23, minute=59, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
    elif date_range == "last_60_days":
        today = datetime.now()
        start_day = today - timedelta(days=60)
        end_day = today - timedelta(days=1)
        start_date = start_day.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
        end_date = end_day.replace(hour=23, minute=59, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
    elif date_range == "last_month":
        today = datetime.now()
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        start_date = first_day_last_month.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
        end_date = last_day_last_month.replace(hour=23, minute=59, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000")
    elif date_range == "last_quarter":
        today = datetime.now()
        current_quarter = (today.month - 1) // 3 + 1
        current_year = today.year
        if current_quarter == 1:
            last_quarter = 4
            year_of_last_quarter = current_year - 1
        else:
            last_quarter = current_quarter - 1
            year_of_last_quarter = current_year
        start_month = (last_quarter - 1) * 3 + 1
        end_month = start_month + 2
        start_date = datetime(year_of_last_quarter, start_month, 1, 0, 0, 0).strftime("%Y-%m-%dT%H:%M:%S.000")
        if end_month == 12:
            end_date_dt = datetime(year_of_last_quarter, 12, 31, 23, 59, 0)
        else:
            first_day_after_quarter = datetime(year_of_last_quarter, end_month + 1, 1)
            end_date_dt = first_day_after_quarter - timedelta(days=1)
            end_date_dt = end_date_dt.replace(hour=23, minute=59, second=0, microsecond=0)
        end_date = end_date_dt.strftime("%Y-%m-%dT%H:%M:%S.000")
    elif date_range == "last_year":
        today = datetime.now()
        last_year = today.year - 1
        start_date = datetime(last_year, 1, 1, 0, 0, 0).strftime("%Y-%m-%dT%H:%M:%S.000")
        end_date = datetime(last_year, 12, 31, 23, 59, 0).strftime("%Y-%m-%dT%H:%M:%S.000")
    return start_date, end_date
