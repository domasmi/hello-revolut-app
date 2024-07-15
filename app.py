import aws_cdk as cdk
from stacks.hello_world_revolut_cdk_stack import HelloWorldRevolutCdkStack

app = cdk.App()
HelloWorldRevolutCdkStack(app, "HelloWorldRevolutCdkStack")
app.synth()
