import json
import requests
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import AccessTokenCredentials
from googleapiclient.discovery import build
from google_analytics_auth import GoogleAnalyticsAuth


class GoogleAnalyticsClient():
    def __init__(self, config, reporting=False):
        oauth_credentials = config.get("oauth_credentials", {})
        access_token = oauth_credentials.get("access_token")
        credentials = AccessTokenCredentials(access_token, "dss-googleanalytics-plugin/2.0")
        if reporting:
            self.client = build("analyticsreporting", "v4", credentials=credentials)
        else:
            self.client = build("analytics", "v3", credentials=credentials)
        self.access_token = credentials.access_token
        self.is_first_page = True
        self.next_page_token = None
        self.offset = 0
        self.limit = 200
        self.row_count = 0
        self.session = requests.Session()
        self.session.auth = GoogleAnalyticsAuth(access_token=self.access_token)

    def get_account_summaries(self):
        try:
            response = self.client.management().accountSummaries().list().execute()
        except Exception as api_error:
            return [], "Error: {}".format(api_error)
        return response, None

    def get_property_list(self, item_id):
        params = {
            "filter": "parent:accounts/{}".format(item_id)
        }
        try:
            response = self.session.get(
                "https://analyticsadmin.googleapis.com/v1beta/properties",
                params=params
            )
        except Exception as api_error:
            return [], "Error: {}".format(api_error)
        json_response = response.json()
        properties = json_response.get("properties", [])
        return properties, None

    def get_property_metadata(self, property_id):
        url = "https://analyticsdata.googleapis.com/v1beta/{}/metadata".format(property_id)
        try:
            response = self.session.get(
                url
            )
            json_response = response.json()
        except Exception as api_error:
            return [], [], "Error: {}".format(api_error)
        return json_response.get("dimensions", []), json_response.get("metrics", []), None

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

    def get_report_v4(self, property_id, query_body):
        url = "https://analyticsdata.googleapis.com/v1beta/{}:runReport".format(property_id)
        try:
            response = self.session.post(
                url,
                json=query_body
            )
        except Exception as api_error:
            return [], "Error: {}".format(api_error)
        status_code = response.status_code
        if status_code == 404:
            raise Exception("This property is not GA4. Try with the UA report.")
        json_response = response.json()
        assert_no_error(json_response)
        return json_response, None

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

    def get_v4_row(self, property_id, start_date, end_date, metrics_ids, dimensions_ids=[]):
        while self.should_still_run_v4():
            query = self.build_v4_report_query(start_date, end_date, metrics_ids, dimensions_ids, self.offset, self.limit)
            response, error_message = self.get_report_v4(property_id, query)
            self.check_for_next_v4_page(response)
            self.offset += self.limit
            rows = reporting_row_generator_v4(response, metrics_ids, dimensions_ids)
            for row in rows:
                yield row

    def shoud_still_run(self):
        if self.is_first_page is True:
            self.is_first_page = False
            return True
        if self.next_page_token:
            return True
        return False

    def should_still_run_v4(self):
        if self.is_first_page is True:
            self.is_first_page = False
            return True
        if self.offset <= self.row_count:
            return True
        return False

    def check_for_next_page(self, response):
        self.is_first_page = False
        self.next_page_token = response.get("reports", [])[0].get("nextPageToken", None)

    def check_for_next_v4_page(self, response):
        self.is_first_page = False
        self.row_count = response.get("rowCount", 0)

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

    def build_v4_report_query(self, start_date, end_date, metrics_ids, dimensions_ids, offset, limit):
        report_request = {}
        report_request["dateRanges"] = {
            "startDate": start_date,
            "endDate": end_date
        }
        report_request["dimensions"] = format_query_inputs(dimensions_ids, "name")
        report_request["metrics"] = format_query_inputs(metrics_ids, "name")
        report_request["offset"] = offset
        report_request["limit"] = limit
        return report_request


def reporting_row_generator(response, metrics, dimensions):
    """
    Returns a generator of rows for the response of the "batchGet" API call:
    https://developers.google.com/analytics/devguides/reporting/core/v4/rest/v4/reports/batchGet

    Note that there may be no dimensions in a response, and the dimensions input may be an empty list.

    Returns:
    A generator that returns rows from the query as a dictionary, indexed by column name
    """
    # Replace the identifiers of the dimensions and metrics for their names
    metric_names = metrics  # Todo : think of something to replace ids with names
    dimension_names = dimensions

    # Create generator of rows (check first if response is empty)
    if not response.get("reports", [])[0].get("data", {}).get("rowCount", None):
        yield dict([(metric, None) for metric in metric_names])

    else:
        for row in response.get("reports", [])[0].get("data", {}).get("rows", []):
            metrics_dict = dict(zip(metric_names, row.get("metrics", [])[0].get("values", [])))

            dimensions_dict = dict()
            if dimensions:
                dimensions_dict = dict(zip(dimension_names, row.get("dimensions", [])))
            yield {**dimensions_dict, **metrics_dict}


def reporting_row_generator_v4(response, metrics, dimensions):
    metric_names = metrics
    dimension_names = dimensions
    rows = response.get("rows")
    if rows is None:
        yield dict([(metric, None) for metric in metric_names])
    else:
        for row in rows:
            metrics_dict = {}
            counter = 0
            for metric_name in metric_names:
                metrics_dict[metric_name] = row.get("metricValues", [])[counter].get("value")
                counter += 1
            dimensions_dict = dict()
            if dimensions:
                dimension_dicts = row.get("dimensionValues", [])
                dimension_values = []
                for dimension_dict in dimension_dicts:
                    dimension_values.append(dimension_dict.get("value"))
                dimensions_dict = dict(zip(dimension_names, dimension_values))
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


def assert_no_error(json_response):
    if "error" in json_response:
        message = json_response.get("error", {}).get("message")
        if not message:
            message = "Error while retrieving the report: {}".format(json_response)
        raise Exception(message)
