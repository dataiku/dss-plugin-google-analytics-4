import json
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import AccessTokenCredentials
from googleapiclient.discovery import build


class GoogleAnalyticsClient():
    def __init__(self, config, reporting=False):
        json_credentials = json.loads(config.get("credentials", {}).get("credentials", {}))
        auth_type = config.get("auth_type")
        if auth_type == "credentials":
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                json_credentials,
                ["https://www.googleapis.com/auth/analytics.readonly"]
            )
        elif auth_type == "oauth":
            oauth_credentials = config.get("oauth_credentials", {})
            access_token = oauth_credentials.get("access_token")
            credentials = AccessTokenCredentials(access_token, "dss-googleanalytics-plugin/2.0")
        if reporting:
            self.client = build("analyticsreporting", "v4", credentials=credentials)
        else:
            self.client = build("analytics", "v3", credentials=credentials)
        self.is_first_page = True
        self.next_page_token = None  # Todo: yoky daan

    def get_account_summaries(self):
        try:
            response = self.client.management().accountSummaries().list().execute()
        except Exception as api_error:
            return [], "Error: {}".format(api_error)
        return response, None

    def get_default_metrics_and_dimensions(self):
        response = self.client.metadata().columns().list(reportType='ga').execute()
        return response

    def get_custom_metrics(self, account_id, web_property_id):
        response = self.client.management().customMetrics().list(accountId=account_id, webPropertyId=web_property_id,).execute()
        return response

    def get_custom_dimensions(self, account_id, web_property_id):
        response = self.client.management().customDimensions().list(accountId=account_id, webPropertyId=web_property_id,).execute()
        return response

    def get_goals(self, account_id, web_property_id, view_id):
        response = self.client.management().goals().list(accountId=account_id, webPropertyId=web_property_id, profileId=view_id).execute()
        return response

    def get_segments(self):
        response = self.client.management().segments().list().execute()
        return response

    def get_report(self, query_body):
        try:
            response = self.client.reports().batchGet(body=query_body).execute()
        except Exception as api_error:
            return [], "Error: {}".format(api_error)
        return response, None

    def get_row(self, start_date, end_date, profile, metrics_ids, dimensions_ids=[], segments_ids=[]):
        while self.shoud_still_run():
            query = self.build_report_query(start_date, end_date, profile, metrics_ids, dimensions_ids, segments_ids)
            response, error_message = self.get_report(query)
            if error_message:
                raise Exception("{}".format(error_message))
            self.check_for_next_page(response)
            rows = reporting_row_generator(response, metrics_ids, dimensions_ids)
            for row in rows:
                yield row

    def shoud_still_run(self):
        if self.is_first_page is True:
            self.is_first_page = False
            return True
        if self.next_page_token:
            return True
        return False

    def check_for_next_page(self, response):
        self.is_first_page = False
        self.next_page_token = response.get("reports", [])[0].get("nextPageToken", None)

    def build_report_query(self, start_date, end_date, profile, metrics_ids, dimensions_ids, segments_ids):
        report_request = {
            "viewId": profile,
            "dateRanges": [{"startDate": start_date, "endDate": end_date}]
        }
        if self.next_page_token:
            report_request["pageToken"] = self.next_page_token
        if metrics_ids:
            report_request["metrics"] = format_query_inputs(metrics_ids, "expression")
        if dimensions_ids:
            report_request["dimensions"] = format_query_inputs(dimensions_ids, "name")
        if segments_ids:
            report_request["segments"] = format_query_inputs(segments_ids, "segmentId")
        return {
            "reportRequests": [report_request]
        }


def reporting_row_generator(response, metrics, dimensions):
    """
    Returns a generator of rows for the reponse of the "batchGet" API call:
    https://developers.google.com/analytics/devguides/reporting/core/v4/rest/v4/reports/batchGet

    Note that there may be no dimensions in a response, and the dimensions input may be an empty list.

    Returns:
    A generator that returns rows from the query as a dictionary, indexed by column name
    """

    # Replace the identifiers of the dimensions and metrics for their names
    metric_names = metrics  # Todo : think of something to replace ids with names
    dimension_names = dimensions

    # Create geenrator of rows (check first if response is empty)
    if not response.get("reports", [])[0].get("data", {}).get("rowCount", None):
        yield dict([(metric, None) for metric in metric_names])

    else:
        for row in response.get("reports", [])[0].get("data", {}).get("rows", []):
            metrics_dict = dict(zip(metric_names, row.get("metrics", [])[0].get("values", [])))

            dimensions_dict = dict()
            if dimensions:
                dimensions_dict = dict(zip(dimension_names, row.get("dimensions", [])))
            yield {**dimensions_dict, **metrics_dict}


def format_query_inputs(inputs, input_type):
    output = []
    for input in inputs:
        output.append(
            {
                input_type: "{}".format(input)
            }
        )
    return output
