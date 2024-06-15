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

    def __init__(self, scope: Construct, construct_id: str,stackname, branch,**kwargs) -> None:
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

        #CDK Coding starts from here
        client=boto3.client('imagebuilder')

        #----------------------------Creating Components-------------------------
        components=list_directories(local_path+'al2_cdk_code/components_in_yaml')
        component_arns=[]
        #-----------Looping through all the components one by one so that each can be created individually
        for component in components:
            component_name=f"al2-cdk-{component.split('.')[0]}-{branch}".lower().replace("_","-")
            component_file_name=component
            component_data,component_description=contents_of_file_and_description(local_path+'al2_cdk_code/components_in_yaml',componentFileName=component_file_name)
            version=auto_version_components(client,componentName=component_name)
            #CFN Resource Id
            id=f"{component_name}_{version}"
            cfn_component_response=imagebuilder.CfnComponent(self,id,name=component_name,platform=platform,version=version,
                    change_description="Creating New Version of this component",data=component_data,description=component_description,supported_os_versions=supported_os_versions)
            component_arns.append(imagebuilder.CfnImageRecipe.ComponentConfigurationProperty(component_arn=cfn_component_response.attr_arn))

        #---------------------------Component Ended-----------------------------------------------------------

        #---------------------------Recipe Creation Starts----------------------------------------------------
        cfn_image_recipe_response=imagebuilder.CfnImageRecipe(self,recipe_id,components=component_arns,name=recipe_name,parent_image=
                "arn:aws:imagebuilder:ap-south-1:aws:image/amazon-linux-2-kernel-5-x86/x.x.x",version=version,
                #SSM Agent is required for connecting to the client, hence we are not uninstalling it.
                additional_instance_configuration=imagebuilder.CfnImageRecipe.AdditionalInstanceConfigurationProperty(
                    systems_manager_agent=imagebuilder.CfnImageRecipe.SystemsManagerAgentProperty(uninstall_after_build=False)),
                    block_device_mappings=[imagebuilder.CfnImageRecipe.InstanceBlockDeviceMappingProperty(
                        device_name="/dev/xvda",ebs=imagebuilder.CfnImageRecipe.EbsInstanceBlockDeviceSpecificationProperty(
                            delete_on_termination=True,encrypted=False,iops=150,throughput=125,volume_size=10,volume_type="gp3"
                        )
                    )],
                    description="This is Amazon Linux 2 AMI recipe created for practice purpose.", working_directory="/tmp"
                    )
        
        #----------------------------Recipe Ends Here-----------------------------------------------------------------

        #----------------------------Infrastructure Configuration Goes here-----------------------------------------
        cfn_infrastructure_configuration_response=imagebuilder.CfnInfrastructureConfiguration(self,infraconfigId,name=infraconfig_name,
                description=f"This infrastructure configuration is created using CDK practice code. Stack name:-{stackname}",
                instance_types=instance_type,key_pair=key_pair,instance_profile_name=instance_profile_name,
                logging=imagebuilder.CfnInfrastructureConfiguration.LoggingProperty(
                    s3_logs=imagebuilder.CfnInfrastructureConfiguration.S3LogsProperty(
                        s3_bucket_name=s3_bucket,
                        s3_key_prefix=s3_bucket_prefix
                    )),
                security_group_ids=security_group_ids,subnet_id=subnet_id,terminate_instance_on_failure=True)
        
        #-----------------------------Infra Config Ends here-----------------------------------------------------------

        #-----------------------------Distribution Settings Begin-------------------------------------------------
        #----------Going with default settings


        #-----------------------------Imagepipeline creation-----------------------------------------------------
        cfn_image_pipeline=imagebuilder.CfnImagePipeline(self,imagepipelineId,
                infrastructure_configuration_arn=cfn_infrastructure_configuration_response.attr_arn,name=imagepipelineName,
                image_scanning_configuration=imagebuilder.CfnImagePipeline.ImageScanningConfigurationProperty(image_scanning_enabled=True),
                description="This pipeline is created using CDK code",enhanced_image_metadata_enabled=True,status="ENABLED",
                image_recipe_arn=cfn_image_recipe_response.attr_arn,image_tests_configuration=imagebuilder.CfnImagePipeline.ImageTestsConfigurationProperty(image_tests_enabled=True,timeout_minutes=60))
        
        #-----------------------------Imagepipeline creation Ends Here---------------------------------------------
        


