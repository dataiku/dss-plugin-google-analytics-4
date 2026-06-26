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

    if not config.get("start_date") and not config.get("manual_start_date"):
        raise Exception("Please enter start date")

    if not config.get("end_date") and not config.get("manual_end_date"):
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
