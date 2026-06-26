from google_analytics_client import GoogleAnalyticsClient
from google_analytics_common import DSSSelectorChoices, get_selected_value
from safe_logger import SafeLogger


logger = SafeLogger("Google Analytics 4 plugin")


def do(payload, config, plugin_config, inputs):
    choices = DSSSelectorChoices()
    parameter_name = payload.get("parameterName")
    root_model = payload.get("rootModel", {})
    client = GoogleAnalyticsClient(config)

    if parameter_name == "property_id_select":
        oauth_credentials = config.get("oauth_credentials", {})
        if not oauth_credentials:
            return choices.text_message("First select a valid preset")
        account_summaries, errors = client.get_account_summaries()
        logger.info("property_id_select={}, error={}".format(account_summaries, errors))
        if errors:
            return choices.text_message(errors)
        for item in account_summaries.get("accountSummaries", []):
            label = item.get("displayName") or item.get("account")
            choices.append(label, extract_account_id(item))
        choices.start_with_manual_select()

    if parameter_name == "web_property_id_select":
        account_id = get_selected_value(root_model, "property_id")
        if not account_id:
            return choices.text_message("Select a property ID")
        account_summaries, errors = client.get_account_summaries()
        logger.info("web_property_id_select={}, error={}".format(account_summaries, errors))
        if errors:
            return choices.text_message(errors)
        account_summary = get_matching_account_summary(account_summaries.get("accountSummaries", []), account_id)
        properties = account_summary.get("propertySummaries", []) if account_summary else []
        if not properties:
            properties, errors = client.get_property_list(account_id)
            if errors:
                return choices.text_message(errors)
        for property_item in properties:
            property_name = property_item.get("property") or property_item.get("name")
            if not property_name:
                continue
            label = format_property_label(client, property_item, property_name)
            choices.append(label, property_name)
        choices.start_with_manual_select()

    if parameter_name == "metrics_id_select":
        property_name = get_selected_value(root_model, "web_property_id")
        if not property_name:
            return choices.text_message("Select a property")
        _, metrics, errors = client.get_property_metadata(property_name)
        if errors:
            return choices.text_message(errors)
        for metric in metrics:
            choices.append(metric.get("uiName"), metric.get("apiName"))
        choices.start_with_manual_select()

    if parameter_name == "dimensions_id_select":
        property_name = get_selected_value(root_model, "web_property_id")
        if not property_name:
            return choices.text_message("Select a property")
        dimensions, _, errors = client.get_property_metadata(property_name)
        if errors:
            return choices.text_message(errors)
        for dimension in dimensions:
            choices.append(dimension.get("uiName"), dimension.get("apiName"))
        choices.start_with_manual_select()
    return choices.to_dss()


def extract_account_id(account_summary):
    account_name = account_summary.get("account", "")
    if "/" in account_name:
        return account_name.split("/")[-1]
    return account_summary.get("name", "").split("/")[-1]


def get_matching_account_summary(account_summaries, account_id):
    for account_summary in account_summaries:
        if extract_account_id(account_summary) == account_id:
            return account_summary
    return None


def format_property_label(client, property_item, property_name):
    label = property_item.get("displayName") or property_name
    data_streams, errors = client.get_data_streams(property_name)
    if errors or not data_streams:
        return label

    stream_labels = []
    for data_stream in data_streams:
        stream_name = data_stream.get("displayName")
        stream_type = data_stream.get("type", "").replace("DATA_STREAM_TYPE_", "").replace("_", " ").title()
        if stream_name and stream_type:
            stream_labels.append("{} ({})".format(stream_name, stream_type))
        elif stream_name:
            stream_labels.append(stream_name)

    if not stream_labels:
        return label
    return "{} [{}]".format(label, ", ".join(stream_labels))
