#!/usr/bin/env python3
import os

import aws_cdk as cdk

from al2_cdk_code.al2_cdk_code_stack import Al2CdkCodeStack
from pygit2 import Repository
app = cdk.App()
branch=app.node.try_get_context("branch")
branch=str(branch).replace("_","-")
try:
    stackname="al2-cdk-stack"+branch
except TypeError as e:
    repo_url="."
    repo=Repository(repo_url)
    branch=repo.head.shorthand
    stackname="al2-cdk-stack"+branch

Al2CdkCodeStack(app, stackname, stackname=stackname,branch=branch, env=cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"), 
                                                                                      region=os.getenv("CDK_DEFAULT_REGION")))
app.synth()
