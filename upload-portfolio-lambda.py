import boto3
import StringIO
import zipfile
import mimetypes
def lambda_handler(event, context):

    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:265051230937:deployPortfolioTopic')

    location = {
        'bucketName' : 'portfoliobuild.robertwoods.info',
        'objectKey' : 'portfoliobuild.zip'
    }

    try:
        s3 = boto3.resource('s3')
        job = event.get("CodePipeline.job")

        if job:
            for artifact in job['data']['inputArtifacts']:
                if artifact['name'] == 'MyAppBuild':
                    location = artifact['location']['s3Location']

        print('Building portfolio from ' + str(location))
        portfolio_bucket = s3.Bucket('portfolio.robertwoods.info')
        build_bucket = s3.Bucket(location['bucketName'])
        portfolio_zip = StringIO.StringIO()

        build_bucket.download_fileobj(location['objectKey'], portfolio_zip)
        #check what StringIO implements later

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm,
                    ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        topic.publish(Subject='Portfolio deployed', Message='Portfolio deployed succsesfully')

        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job['id'])

    except:
        topic.publish(Subject='Portfolio deployed', Message='Portfolio deployed unsuccsesfully')
        job = event.get("CodePipeline.job")
        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_failure_result(jobId=job['id'],
                failureDetails={'type': 'JobFailed', 'message': 'Unlucky'}
            )
        raise
    return 'Job finished'
