from google_analytics_client import GoogleAnalyticsClient
from google_analytics_common import DSSSelectorChoices


def do(payload, config, plugin_config, inputs):
    json_credentials = config.get("credentials", {}).get("credentials", {})
    choices = DSSSelectorChoices()
    if not json_credentials:
        return choices.text_message("Select a preset")
    parameter_name = payload.get("parameterName")

    if parameter_name == "property_id_select":
        account_summaries, errors = GoogleAnalyticsClient(config).get_account_summaries()
        if errors:
            return choices.text_message(errors)
        for item in account_summaries.get("items", []):
            choices.append(item.get("name"), item.get("id"))
        choices.append_manual_select()

    if parameter_name == "web_property_id_select":
        property_id = payload.get("rootModel", {}).get("property_id_select")
        if not property_id:
            return choices.text_message("Select a property ID")
        account_summaries, errors = GoogleAnalyticsClient(config).get_account_summaries()
        if errors:
            return choices.text_message(errors)
        for item in account_summaries.get("items", []):
            if item.get("id") == property_id:
                web_properties = item.get("webProperties", [])
                for web_property in web_properties:
                    choices.append(web_property.get("name"), web_property.get("id"))
        choices.append_manual_select()

    if parameter_name == "profile_id_select":
        property_id = payload.get("rootModel", {}).get("property_id_select")
        if not property_id:
            return choices.text_message("Select a property ID")
        web_property_id = payload.get("rootModel", {}).get("web_property_id_select")
        if not web_property_id:
            return choices.text_message("Select a property ID")
        account_summaries, errors = GoogleAnalyticsClient(config).get_account_summaries()
        if errors:
            return choices.text_message(errors)
        for item in account_summaries.get("items", []):
            if item.get("id") == property_id:
                web_properties = item.get("webProperties", [])
                for web_property in web_properties:
                    if web_property.get("id") == web_property_id:
                        profiles = web_property.get("profiles", [])
                        for profile in profiles:
                            choices.append(profile.get("name"), profile.get("id"))
        choices.append_manual_select()

    if parameter_name == "metrics_id_select":
        default_metrics_and_dimensions = GoogleAnalyticsClient(config).get_default_metrics_and_dimensions()
        for metric in default_metrics_and_dimensions.get("items", []):
            if metric.get("attributes", {}).get("type") == "METRIC":
                choices.append(format_label(metric), metric.get("id"))
        choices.append_manual_select()

    if parameter_name == "dimensions_id_select":
        default_metrics_and_dimensions = GoogleAnalyticsClient(config).get_default_metrics_and_dimensions()
        for dimension in default_metrics_and_dimensions.get("items", []):
            if dimension.get("attributes", {}).get("type") == "DIMENSION":
                choices.append(format_label(dimension), dimension.get("id"))
        choices.append_manual_select()

    if parameter_name == "segments_id_select":
        segments = GoogleAnalyticsClient(config).get_segments()
        for segment in segments.get("items", []):
            choices.append(segment.get("name"), segment.get("id"))
    return choices.to_dss()


def format_label(metric_or_dimension):
    attribute = metric_or_dimension.get("attributes", {})
    name = attribute.get("uiName")
    status = attribute.get("status")
    if status == "DEPRECATED":
        return "{} (deprecated {})".format(name, metric_or_dimension.get("id", ""))
    else:
        return name
