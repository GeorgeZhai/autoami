# Auto AMI and snpshot deleting
# George Zhai
# 19/05/2016
# This automatic ami cleanup script runs in AWS lambda to clean ec2 ami and associated EBS snapshots based on TAG: DELETEAFTER
# DELETEAFTER e.g. 2016-05-05 18:22:11
#     type: datatime ('%Y-%m-%d %H:%M:%S'), When this ami will be deleted.
#
# There is exceptions: If an AMI has been tagged as a release use, This script will not remove it!
# e.g. Tag Release ISHP-1.03.1-20160520
# schedule this lambda function to be called multiple times a day. frequency need to be calculated based on AWS API limit and throttling param: max_amitoremove_prerun


import boto3
import datetime


#ec = boto3.client('ec2')
#ec2 = boto3.resource('ec2')

ec = boto3.client('ec2', 'us-east-1')
ec2 = boto3.resource('ec2', 'us-east-1')


def lambda_handler(event, context):

    max_amitoremove_prerun = 5  # 1 to 10?
    aws_account_number = '151876473584'

    removecount = 0

    print (event, context)
    images = ec2.images.filter(Owners=[aws_account_number])



    for image in images:
        current_time = datetime.datetime.now()
        delete_after = current_time + datetime.timedelta(days=100)
        remove_flag = False
        donotremove_flag = False

        ami_id = image.id
        snapshot_ids = []
        ami_state = image.state

        if hasattr(image, 'tags') and (image.tags is not None) and (len(image.tags) > 0):
            for tag in image.tags:
                if (tag['Key'].strip().upper()=='DELETEAFTER'):
                    try:
                        delete_after = datetime.datetime.strptime(tag['Value'], '%Y-%m-%d %H:%M:%S')
                        print "DELETEAFTER tag found and datetime captured"
                    except Exception as ex:
                        print ex
                        print 'Error in connverting date in tag DELETEAFTER'
                        pass

                if (tag['Key'].strip().upper()=='RELEASE'):
                    donotremove_flag = True


        if hasattr(image, 'block_device_mappings') and (image.block_device_mappings is not None) and (len(image.block_device_mappings) > 0):
            for blockdev in image.block_device_mappings:
                snapshot_ids.append(blockdev['Ebs']['SnapshotId'])



        if( removecount < max_amitoremove_prerun and (not donotremove_flag) and current_time > delete_after and ami_state == "available"):
            remove_flag = True


#        print "ami_id: %s name: %s snapshots: %s delete_after: %s remove_flag %s" % (ami_id, image.name, snapshot_ids, delete_after, remove_flag)


        if (remove_flag):
            removecount = removecount +1
            print "ami_id: %s name: %s snapshots: %s delete_after: %s remove_flag %s" % (ami_id, image.name, snapshot_ids, delete_after, remove_flag)
            print ("-------------removing ---------------------------!!!!!!!!!!!!!!!!")
            try:
                print "Deregistering ami " + ami_id
                amiResponse = ec.deregister_image(
                    DryRun=False,
                    ImageId=ami_id,
                )
                print amiResponse
                for snapshot_id in snapshot_ids:
                    print "Deleting snapshot " + snapshot_id
                    snapResponse = ec.delete_snapshot(SnapshotId=snapshot_id)
                    print snapResponse
            except Exception as ex:
                print ex
                pass


    print ("Removed %d AMIs and their snapshots" % (removecount))


# Debug use, comment this out in lambda
# lambda_handler(1, 2)