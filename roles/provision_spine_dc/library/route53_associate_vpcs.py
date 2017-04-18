import json

try:
  import boto3
  import botocore
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False


def main():
  argument_spec = ec2_argument_spec()
  argument_spec.update(dict(
      hosted_zone_id = dict(required=True),
      vpc_ids        = dict(required=True),
    )
  )
  module = AnsibleModule(argument_spec=argument_spec)

  if not HAS_BOTO3:
    module.fail_json(msg='boto3/botocore required for this module')

  hosted_zone_id = module.params.get('hosted_zone_id')
  vpc_ids = json.loads(module.params.get('vpc_ids'))

  responses = []
  try:
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    route53_client = boto3_conn(module, conn_type='client', resource='route53',
      region=region, endpoint=ec2_url, **aws_connect_kwargs)
    for vpc_id in vpc_ids:
      responses.append(route53_client.associate_vpc_with_hosted_zone(
          HostedZoneId=hosted_zone_id,
          VPC={
            'VPCRegion': region,
            'VPCId': vpc_id,
          },
      ))
    module.exit_json(changed=True, responses=responses)
  except botocore.exceptions.NoRegionError:
    module.fail_json(msg="region must be specified as a parameter")
  except Exception as e:
    module.fail_json(
      msg="can't establish connection - " + str(e), exception=traceback.format_exc(e))


from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *


main()
