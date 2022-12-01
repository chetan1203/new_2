import os, requests
import html2text
from bs4 import BeautifulSoup
import boto3
import argparse
from botocore.client import Config
webhook_url = "https://hooks.slack.com/services/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"
payload = { 'channels':['Chetan Chauhan'] }
bucket_name = " "
report_name = " "
report_dir = " "

def report_test_summary_notification():
	parser = argparse.ArgumentParser()
	parser.add_argument('--parameters', action="store_true", required=True, help="Pass path to the HTML report")
	parser.add_argument('--html_report_path', type=str, required=False, default=None, help="Path to the HTML report in the API Framework")
	parser.add_argument('--framework_type', type=str, required=False, default=None, help="Server type either web or api")
	parser.add_argument('--test_suite', type=str, required=False, default=None, help="provide test suite name in run time ")
	#parser.add_argument('--DurationSeconds', type=int, required=False, default=None, help="provide DurationSeconds in run time ")
	parser.add_argument('--Access_key', type=str, required=False, default=None, help="provide AccessKeyId in run time ")
	parser.add_argument('--Secreat_access', type=str, required=False, default=None, help="provide Secreat_access in run time ")
	arguments = parser.parse_args()

	test_suite = arguments.test_suite
	title_test_suit = "*Test Suit Name*" + " :-   "
	#Access = arguments.Access_key
	#Secreat_access = arguments.Secreat_access

	if arguments.parameters == True:
		if arguments.html_report_path is not None:
			for file in os.listdir(arguments.html_report_path):
				if file.endswith(".html"):
					report_name = file
					print (report_name)
					print (arguments.html_report_path)
	else:
		print("Please provide the html report path as an argument")
		exit(0)

	if arguments.framework_type == "web":
		title = "*Web Testing Automation Framework execution details*" +  " \n " 
	else:
		title = "*API Testing Automation Framework execution details*"

	with open(os.path.join(arguments.html_report_path, report_name), "r") as f:
		text = f.read()
	soup = BeautifulSoup(text, 'html.parser')
	passed_test = soup.find_all('td', attrs = { 'class': 'pass' })
	failed_test = soup.find_all('td', attrs = { 'class': 'fail' })
	error_test = soup.find_all('td', attrs = { 'class': 'error' })

	h = html2text.HTML2Text()
	passed = h.handle(str(passed_test[0]))
	failed = h.handle(str(failed_test[0])).strip('|')
	error = h.handle(str(error_test[0])).strip('|')
	
	s3 = boto3.client('s3', config=Config(signature_version='s3v4' ))
	#response = boto3.client('s3').get_session_token(DurationSeconds=129600, SerialNumber='string', TokenCode='string')
	location = boto3.client('s3').get_bucket_location(Bucket=bucket_name)['LocationConstraint']
	get_last_modified = lambda obj: (obj['LastModified'].strftime('%Y-%m-%dT%H:%M:%S'))
	reports_list = s3.list_objects_v2(Bucket=bucket_name).get('Contents', [])
	reports_list = [ report['Key'] for report in sorted(reports_list, key=get_last_modified, reverse=True) if report['Key'].endswith('.html')]
	if len(reports_list) > 0:
		latest_report_name = reports_list[0]
		s3_report_name = os.path.basename(latest_report_name)
		print (s3_report_name)
	s3_file_location = s3.generate_presigned_url('get_object',
													Params={
															'Bucket': bucket_name,
															'Key': report_dir+report_name
															},
													ExpiresIn= 12500)

	attachments = [{
		"pretext": title +title_test_suit+ test_suite,
		"color": "good",
		"fields": [{
			"title": "Passed Test Cases",
			"value": passed,
			"short": True,
		}, {
			"title": "Failed Test Cases",
			"value": failed,
			"short": True
			}, {
			"title": "Erroneous Test Cases",
			"value": error,
			"short": True
			}],
		"title":"Click on the link for test report",
		"title_link": s3_file_location
		}]
	payload['attachments'] = attachments
	r = requests.post(webhook_url, json=payload)

if __name__ == '__main__':
	report_test_summary_notification()
