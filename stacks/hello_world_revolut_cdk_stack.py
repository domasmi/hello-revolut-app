
import os
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb_,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigwv2_,
    aws_apigatewayv2_integrations as apigwv2_integr_,
    aws_ec2 as ec2,
    aws_iam as iam,
    Duration,
)
from constructs import Construct

TABLE_NAME = "dateofbirth_table"


class HelloWorldRevolutCdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        vpc = ec2.Vpc(
            self,
            "Ingress",
            ip_addresses=ec2.IpAddresses.cidr("10.1.0.0/16"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private-Subnet", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ],
        )
        
        # Create VPC endpoint
        dynamo_db_endpoint = ec2.GatewayVpcEndpoint(
            self,
            "DynamoDBVpce",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
            vpc=vpc,
        )

        # This allows to customize the endpoint policy
        dynamo_db_endpoint.add_to_policy(
            iam.PolicyStatement(  # Restrict to listing and describing tables
                principals=[iam.AnyPrincipal()],
                actions=[                "dynamodb:DescribeStream",
                "dynamodb:DescribeTable",
                "dynamodb:Get*",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:CreateTable",
                "dynamodb:Delete*",
                "dynamodb:Update*",
                "dynamodb:PutItem"],
                resources=["*"],
            )
        )

        # Create DynamoDb Table
        table = dynamodb_.Table(
            self,
            TABLE_NAME,
            partition_key=dynamodb_.Attribute(
                name="username", type=dynamodb_.AttributeType.STRING
            ),
        )

        # Create the Lambda function to receive the request
        api_handler = lambda_.Function(
            self,
            "ApiHandler",
            function_name="apigw_handler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambda/apigw-handler"),
            handler="index.handler",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
        )

        # Grant the Lambda read and write permissions on the DynamoDb Table
        table.grant_read_write_data(api_handler)
        api_handler.add_environment("TABLE_NAME", table.table_name)

        # Create HTTP API endpoint with lambda integration
        lambda_integration = apigwv2_integr_.HttpLambdaIntegration("HttpApiLambdaIntegration", api_handler)

        http_api = apigwv2_.HttpApi(self, "HttpApi")

        http_api.add_routes(
            path="/hello/{username}",
            methods=[apigwv2_.HttpMethod.GET, apigwv2_.HttpMethod.PUT],
            integration=lambda_integration
        )