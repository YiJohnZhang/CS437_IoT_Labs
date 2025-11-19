################################################### Connecting to AWS
import boto3
import json
import os
################################################### Create random name for things
import random
import string

################################################### Parameters for Thing
# thingArn = ''
# thingId = ''
THING_NAME_PREFIX = 'cs437_car_'
DEFAULT_POLICY_NAME = 'cs437_l04_policy'
THING_ARN = ''
THING_GROUP_NAME = ''
THING_GROUP_ARN = ''

THING_CLIENT = boto3.client('iot')

BOTO3_ACCESS_KEY_ID = '';
BOTO3_SECRET_ACCESS_KEY = '';
BOTO3_REGION_NAME = '';

'''
THING_CLIENT = boto3.client(
	'iot', 
	aws_access_key_id = BOTO3_ACCESS_KEY_ID,
	aws_secret_access_key = BOTO3_SECRET_ACCESS_KEY,
	region_name = BOTO3_REGION_NAME
)
'''

###################################################
def create_certificate_and_add_to_group(thing_id, thing_name, thing_arn):
	certResponse = THING_CLIENT.create_keys_and_certificate(
		setAsActive = True
	)

	data = json.loads(json.dumps(certResponse, sort_keys=False, indent=4))
	for element in data: 
			if element == 'certificateArn':
					certificateArn = data['certificateArn']
			elif element == 'keyPair':
					PublicKey = data['keyPair']['PublicKey']
					PrivateKey = data['keyPair']['PrivateKey']
			elif element == 'certificatePem':
					certificatePem = data['certificatePem']
			elif element == 'certificateId':
					certificateId = data['certificateId']
							
	with open(os.path.join('certs', '') + thing_name + '-public.key', 'w') as outfile:
			outfile.write(PublicKey)
	with open(os.path.join('certs', '') + thing_name + '-private.key', 'w') as outfile:
			outfile.write(PrivateKey)
	with open(os.path.join('certs', '') + thing_name + '-cert.pem', 'w') as outfile:
			outfile.write(certificatePem)

	response = THING_CLIENT.attach_policy(
			policyName = DEFAULT_POLICY_NAME,
			target = certificateArn
	)
	response = THING_CLIENT.attach_thing_principal(
			thingName = thing_name,
			principal = certificateArn
	)
	print(f'create_certificate_and_add_to_group()::attached policy and certificat to device {thing_id}')

	response = THING_CLIENT.add_thing_to_group(
		thingGroupName = THING_GROUP_NAME,
		thingGroupArn = THING_GROUP_ARN,
		thingName = thing_name
		thingArn = thing_arn
	)
	print(f'create_certificate_and_add_to_group()::added {thing_id} to group {THING_GROUP_NAME}')


def createThing(thing_name):
	# global THING_CLIENT
	thingResponse = THING_CLIENT.create_thing(
			thingName = thing_name
	)

	data = json.loads(json.dumps(thingResponse, sort_keys=False, indent=4))
	for element in data: 
		if element == 'thingArn':
				thing_arn = data['thingArn']
		elif element == 'thingId':
				thing_id = data['thingId']
	create_certificate_and_add_to_group(thing_id, thing_name, thing_arn)

def main():
	for i in range (1, 5):
		# thing0 already created
		thing_name = THING_NAME_PREFIX + str(i)
		createThing(thing_name)

if __name__ == "__main__":
	main()