from dataiku.connector import Connector
from google_analytics_client import GoogleAnalyticsClient
from google_analytics_common import RecordsLimit, assert_valid_config_v4, get_selected_value, get_date_range
from google_analytics_constants import GA4Constants
from safe_logger import SafeLogger


logger = SafeLogger("Google Analytics 4 plugin", GA4Constants.FORBIDDEN_KEYS)


class GoogleAnalyticsConnector(Connector):

    def __init__(self, config, plugin_config):
        Connector.__init__(self, config, plugin_config)  # pass the parameters to the base class
        logger.info("Starting Google Analytics 4 plugin v{} with config={}".format(
            GA4Constants.PLUGIN_VERSION,
            logger.filter_secrets(config)
        ))
        assert_valid_config_v4(config)
        self.start_date, self.end_date = get_date_range(config)
        self.start_date = self.start_date.split("T")[0]
        self.end_date = self.end_date.split("T")[0]
        self.metrics_ids = config.get("metrics_id_select")
        self.dimensions_ids = config.get("dimensions_id_select", [])
        self.metrics_ids = get_selected_value(config, "metrics_id", separator=",")
        self.dimensions_ids = get_selected_value(config, "dimensions_id", separator=",")
        self.property_id = get_selected_value(config, "property_id")
        self.web_property_id = get_selected_value(config, "web_property_id")
        self.client = GoogleAnalyticsClient(config)

    def get_read_schema(self):
        return None

    def generate_rows(self, dataset_schema=None, dataset_partitioning=None,
                      partition_id=None, records_limit=-1):

        limit = RecordsLimit(records_limit=records_limit)
        for row in self.client.get_v4_row(
                self.web_property_id,
                self.start_date, self.end_date, self.metrics_ids, self.dimensions_ids):
            yield row
            if limit.is_reached():
                return

    def get_writer(self, dataset_schema=None, dataset_partitioning=None,
                   partition_id=None):
        raise NotImplementedError

    def get_partitioning(self):
        raise NotImplementedError

    def list_partitions(self, partitioning):
        """Return the list of partitions for the partitioning scheme
        passed as parameter"""
        return []

    def partition_exists(self, partitioning, partition_id):
        """Return whether the partition passed as parameter exists

        Implementation is only required if the corresponding flag is set to True
        in the connector definition
        """
        raise NotImplementedError

    def get_records_count(self, partitioning=None, partition_id=None):
        """
        Returns the count of records for the dataset (or a partition).

        Implementation is only required if the corresponding flag is set to True
        in the connector definition
        """
        raise NotImplementedError
