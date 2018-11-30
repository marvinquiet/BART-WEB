import boto3

directory = "neal-test"

# Testing SQS by hand
def send_sqs_message(directory):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='bart-web')
    response = queue.send_message(MessageBody='BART submission', MessageAttributes={
        'submission': {
            'StringValue': directory,
            'DataType': 'String'
        }
    })

send_sqs_message(directory)
