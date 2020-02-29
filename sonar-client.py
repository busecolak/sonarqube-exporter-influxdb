import requests
import datetime

BASE_URL = os.environ['SONAR_URL']
USER = os.environ['SONAR_USER']
PASSWORD = os.environ['SONAR_PASSWORD']
INFLUX_URL = os.environ['INFLUX_URL']
INFLUX_USER = os.environ['INFLUX_USER']
INFLUX_PASSWORD = os.environ['INFLUX_PASSWORD']
INFLUX_DB = os.environ['INFLUX_DB']

class SonarApiClient:
	def __init__(self, user, password):
        	self.user = user
        	self.password = password

	def _make_request(self, endpoint):
		r = requests.get(BASE_URL + endpoint, auth=(self.user, self.password))
		return r.json() 
	
	def get_all_ids(self, endpoint):
		data = self._make_request(endpoint)
		ids = []
		for component in data['components']:
			dict = {
				"id": component['id'],
				"key": component['key']
			}
			ids.append(dict)
		return ids

	def get_all_available_metrics(self, endpoint):
		data = self._make_request(endpoint)
		metrics = []
		for metric in data['metrics']:
			metrics.append(metric['key'])
		return metrics

	def get_measures_by_component_id(self, endpoint):
		data = self._make_request(endpoint)
		return data['component']['measures']

class Project:
        def __init__(self, identifier, key):
                self.id = identifier
                self.key = key
                self.metrics = None
                self.timestamp = datetime.datetime.utcnow().isoformat()

        def set_metrics(self, metrics):
                self.metrics = metrics

        def export_metrics(self):
              	influx_url = INFLUX_URL + '/write?db=' + INFLUX_DB
		r = requests.post(influx_url, data=self._prepare_metrics())
                
	def _prepare_metrics(self):
		data = ""
		for metric in self.metrics:
			v = 0
			if ('value' in metric):
				v = metric['value']
			elif ('value' in metric['periods'][0]):
				v = metric['periods'][0]['value'] 
			data_string = metric['metric'] + ",id=" +  str(self.id) + ",key=" + str(self.key) + " value=" +  str(v)
			data = data + data_string + '\n'
		return data	

# Fetch all projects IDs
client = SonarApiClient(USER, PASSWORD)
ids = client.get_all_ids('/api/components/search?qualifiers=TRK')

# Fetch all available metrics
metrics = client.get_all_available_metrics('/api/metrics/search')
comma_separated_metrics = ''
for metric in metrics:
	if metric != 'new_development_cost':
		comma_separated_metrics += metric + ','

# Collect metrics per project
uri = '/api/measures/component'
for item in ids:
	project_id = item['id']
	project_key = item['key']
	project = Project(identifier=project_id, key=project_key)		
	component_id_query_param = 'componentId=' + project_id
	metric_key_query_param = 'metricKeys=' + comma_separated_metrics
	measures = client.get_measures_by_component_id(uri + '?' + component_id_query_param + '&' + metric_key_query_param)
        project.set_metrics(measures)
        project.export_metrics()
