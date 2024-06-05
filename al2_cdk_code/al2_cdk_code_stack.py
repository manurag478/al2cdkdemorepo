from aws_cdk import (
    Stack,
    aws_imagebuilder as imagebuilder
)
import boto3
import os
from constructs import Construct

def list_directories(path):
    component_files_in_repo=os.listdir(path)
    return component_files_in_repo

def contents_of_file_and_description(dir,componentFileName):
    with open(dir + componentFileName) as f:
        content=f.read()
        content_as_list=content.split("\n")
        dict1={}
        for x in content_as_list:
            if x.split(":")[0]=="phases":
                break
            else:
                try:
                    key=x.split(":")[0].lower()
                    value=x.split(":")[1].strip()
                    dict1[key]=value
                except IndexError as e:
                    continue
        if "description" in dict1.keys():
            description=dict1["description"]
        else:
            msg=f"""Description is missing in {componentFileName}, kindly write Component File Properly. Format should be something like this:
                    name: "<your_component_name>"
                    description: "<What is your component achieving>"
                    schemaVersion: 1.0
                    phases:
                        <Statement afterwards>
                    """
            print(msg)
            exit(1)
        return content, description

def auto_version_components(client, componentName):
    #In this function, the current version of resources is checked and if it exists, then value of versions is increased by 0.0.1
    v=client.list_components(owner='Self')
    response=client.list_components(owner='Self',
                                    filters=[
                                        {
                                            'name':'name',
                                            'values':[componentName]
                                        }
                                    ])
    try:
        arn=response['componentVersionList'][0]['arn']
        current_version=int(response['componentVersionList'][0]['version'].split(".")[2])
        new_version_int=current_version+1
        final_version_str=f'0.0.{new_version_int}'
    except IndexError as e:
        final_version_str='0.0.0'
    return final_version_str

class Al2CdkCodeStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, branch,workspace,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        if branch is None:
            branch="master"
        print(f"You are presently working in {branch} branch")
        platform="Linux"
        supported_os_versions=["Amazon Linux 2"]
        #kms_key="#"
        #For Component Execution
        local_path="./"
        #For Infra config
        instance_profile_name="Ec2tos3Access"
        instance_type=["t2.micro"]
        key_pair="aws_instances"
        s3_bucket="ec2-logs-imagebuilder-ki"
        s3_bucket_prefix="ec2imagebuilderlogs"
        security_group_ids=["sg-0cd787e5740a3f3cb"]
        subnet_id="subnet-0728b6b0367b67666"
        #Distribution_Settings
        aws_accounts=["339712830316"]
        region="ap-south-1"
        ############### Logical IDs Declaration ###################
        #For Components, logical ID is generated in the loop itself
        #Recipe logical Id:-
        recipe_id="al2-cdk-recipe"+branch
        infraconfigId="al2-cdk-infraconfig"+branch
        distribution_settings_id="al2-cdk-distribution-settings"+branch
        imagepipelineId="al2-cdk-pipeline"+branch
        #------------------------Naming AWS Resources------------------
        recipe_name="al2-cdk-recipe"+branch
        infraconfig_name="al2-cdk-infraconfig"+branch
        distribution_settings_name="al2-cdk-dis-settings"+branch
        imagepipelineName="al2-cdk-ami-pipeline"+branch
        #----------------------------------Logical Ids and Names section Ends here------------------------------ 


