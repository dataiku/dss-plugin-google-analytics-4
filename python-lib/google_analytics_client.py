import requests
from oauth2client.client import AccessTokenCredentials
from google_analytics_auth import GoogleAnalyticsAuth


def normalize_property_name(property_id):
    if not property_id:
        return property_id
    if property_id.startswith("properties/"):
        return property_id
    return "properties/{}".format(property_id)


class GoogleAnalyticsClient():
    def __init__(self, config):
        oauth_credentials = config.get("oauth_credentials", {})
        access_token = oauth_credentials.get("access_token")
        credentials = AccessTokenCredentials(access_token, "dss-googleanalytics-plugin/2.0")
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
            response = self._get_paginated_json(
                "https://analyticsadmin.googleapis.com/v1beta/accountSummaries",
                "accountSummaries"
            )
        except Exception as api_error:
            return [], "Error: {}".format(api_error)
        return response, None

    def get_property_list(self, item_id):
        params = {
            "filter": "parent:accounts/{}".format(item_id)
        }
        try:
            json_response = self._get_paginated_json(
                "https://analyticsadmin.googleapis.com/v1beta/properties",
                "properties",
                params=params
            )
        except Exception as api_error:
            return [], "Error: {}".format(api_error)
        properties = json_response.get("properties", [])
        return properties, None

    def get_data_streams(self, property_id):
        property_name = normalize_property_name(property_id)
        url = "https://analyticsadmin.googleapis.com/v1beta/{}/dataStreams".format(property_name)
        try:
            response = self._get_paginated_json(url, "dataStreams")
        except Exception as api_error:
            return [], "Error: {}".format(api_error)
        return response.get("dataStreams", []), None

    def get_property_metadata(self, property_id):
        property_name = normalize_property_name(property_id)
        url = "https://analyticsdata.googleapis.com/v1beta/{}/metadata".format(property_name)
        try:
            json_response = self._get_json(url)
        except Exception as api_error:
            return [], [], "Error: {}".format(api_error)
        return json_response.get("dimensions", []), json_response.get("metrics", []), None

    def get_report_v4(self, property_id, query_body):
        property_name = normalize_property_name(property_id)
        url = "https://analyticsdata.googleapis.com/v1beta/{}:runReport".format(property_name)
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

    def get_v4_row(self, property_id, start_date, end_date, metrics_ids, dimensions_ids=[]):
        while self.should_still_run_v4():
            query = self.build_v4_report_query(start_date, end_date, metrics_ids, dimensions_ids, self.offset, self.limit)
            response, error_message = self.get_report_v4(property_id, query)
            self.check_for_next_v4_page(response)
            self.offset += self.limit
            rows = reporting_row_generator_v4(response, metrics_ids, dimensions_ids)
            for row in rows:
                yield row

    def should_still_run_v4(self):
        if self.is_first_page is True:
            self.is_first_page = False
            return True
        if self.offset < self.row_count:
            return True
        return False

    def check_for_next_v4_page(self, response):
        self.is_first_page = False
        self.row_count = response.get("rowCount", 0)

    def build_v4_report_query(self, start_date, end_date, metrics_ids, dimensions_ids, offset, limit):
        report_request = {}
        report_request["dateRanges"] = [{
            "startDate": start_date,
            "endDate": end_date
        }]
        report_request["dimensions"] = format_query_inputs(dimensions_ids, "name")
        report_request["metrics"] = format_query_inputs(metrics_ids, "name")
        report_request["offset"] = offset
        report_request["limit"] = limit
        return report_request

    def _get_paginated_json(self, url, items_key, params=None):
        aggregated_items = []
        next_page_token = None

        while True:
            current_params = dict(params or {})
            if next_page_token:
                current_params["pageToken"] = next_page_token

            json_response = self._get_json(url, params=current_params)
            aggregated_items.extend(json_response.get(items_key, []))
            next_page_token = json_response.get("nextPageToken")

            if not next_page_token:
                return {items_key: aggregated_items}

    def _get_json(self, url, params=None):
        response = self.session.get(url, params=params)
        json_response = response.json()
        assert_no_error(json_response)
        return json_response


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
