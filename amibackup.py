# Auto AMI Backup
# George Zhai
# 19/05/2016
#This automatic backup script runs in AWS lambda to backup ec2 instances with following TAGs:
# AMIBACKUPCYCLE e.g. 7
#     type: int, backup cycle in days
# AMIRETENTIONDAYS e.g. 60
#     type: int, AMI will be auto deleted after these days(default to 7)
# AMILASTBACKUP e.g. 2016-05-05 18:22:11
#     type: datatime ('%Y-%m-%d %H:%M:%S'), When was the latest backup happened.
#
# Name
#     type: string, Will be used as part of the AMI name
#
# Logic:
#     Use AMILASTBACKUP and AMIBACKUPCYCLE to find out backup candidates
#     Use AMIRETENTIONDAYS to set tag for AMI auto cleanup
# Example:
#   Add a tag key "AMIBACKUPCYCLE" and value 2 to any ec2 instances
# schedule this lambda function to be called multiple times a day. frequency need to be calculated based on AWS API limit and throttling param: max_instances_prerun


import boto3
import datetime

#ec = boto3.client('ec2')
ec = boto3.client('ec2', 'us-east-1')




def lambda_handler(event, context):

    # print(event, context)

    # This lambda function can be triggered multiple times a day to complete the backup if there are more instances than max_instances_prerun to backup.
    max_instances_prerun = 5
    default_retention_days = 7


    backupcount = 0
    reservations = ec.describe_instances(
        Filters=[
            {'Name': 'tag-key', 'Values': ['AMIBACKUPCYCLE', 'amibackupcycle']},
        ]
    ).get(
        'Reservations', []
    )

    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

    print "Found %d instances with tag AMIBACKUPCYCLE" % len(instances)

    for instance in instances:
        #print instance
        backup_flag= False
        instance_id = instance['InstanceId']
        instance_name = ''
        backup_cycle = 0
        retention_days = default_retention_days
        last_backup = ''
        last_backup_date = datetime.datetime.now() - datetime.timedelta(days=1*365) #default to be 1 year ago
        backup_due_date =  datetime.datetime.now()
        ami_del_date =  datetime.datetime.now()
        current_time = datetime.datetime.now()
        current_time_fmt = current_time.strftime('%Y-%m-%d %H:%M:%S')
        current_time_aminame = current_time.strftime('%Y-%m-%d.%H.%M.%S')
        ami_to_tag = []
        ec2_to_tag = []
        AMIid = {}

        for tag in instance['Tags']:
            if (tag['Key'].strip().upper()=='NAME'):
                    instance_name = tag['Value']
            if (tag['Key'].strip().upper()=='AMIBACKUPCYCLE'):
                try:
                    backup_cycle = int(tag['Value'])
                except ValueError as verr:
                    print verr
                    print 'AMIBACKUPCYCLE does not contain anything convertible to int'
                    pass
                except Exception as ex:
                    print ex
                    print 'error in connverting AMIBACKUPCYCLE to int'
                    pass
            if (tag['Key'].strip().upper()=='AMIRETENTIONDAYS'):
                try:
                    retention_days = int(tag['Value'])
                except ValueError as verr:
                    print verr
                    print 'AMIRETENTIONDAYS does not contain anything convertible to int'
                    pass
                except Exception as ex:
                    print ex
                    print 'error in connverting AMIRETENTIONDAYS to int'
                    pass
            if (tag['Key'].strip().upper()=='AMILASTBACKUP'):
                try:
                    last_backup = tag['Value']
                    last_backup_date = datetime.datetime.strptime(last_backup, '%Y-%m-%d %H:%M:%S')
                    print "proper converted"
                except Exception as ex:
                    last_backup_date = datetime.datetime.today() - datetime.timedelta(days=(backup_cycle+1))
                    print ex
                    print 'error in connverting AMILASTBACKUP date'
                    pass

            backup_due_date = last_backup_date + datetime.timedelta(days=backup_cycle)
            ami_del_date = current_time + datetime.timedelta(days=retention_days)
            ami_del_date_fmt = ami_del_date.strftime('%Y-%m-%d %H:%M:%S')

#        print "instance_id: %s instance_name %s === value backup_cycle: %s retention_days: %s last_backup: %s" % (instance_id, instance_name, backup_cycle, retention_days, last_backup)
#        print "backup_due_date: %s current_time_fmt: %s ami_del_date_fmt: %s" % (backup_due_date, current_time_fmt, ami_del_date_fmt)

        if(backup_cycle > 0 and current_time > backup_due_date and backupcount < max_instances_prerun):
            backup_flag = True

#        print (backup_flag)

        if (backup_flag):
            print "instance to backup --- id: %s instance_name %s === value backup_cycle: %s retention_days: %s last_backup: %s" % (instance_id, instance_name, backup_cycle, retention_days, last_backup)
            print "vars : backup_due_date: %s current_time_fmt: %s ami_del_date_fmt: %s" % (backup_due_date, current_time_fmt, ami_del_date_fmt)
            backupcount = backupcount +1
            try:
                AMIid = ec.create_image(InstanceId=instance['InstanceId'], Name= instance_name + "-" + instance_id + "on" + current_time_aminame, Description="auto backup: " + instance_name + " - " + instance_id, NoReboot=True, DryRun=False)
                # AMIid = {u'ImageId': 'ami-6667410c'}
            except Exception as ex:
                print ex
                pass # do job to handle: Exception occurred while converting to int

        if 'ImageId' in AMIid:
            ami_to_tag.append(AMIid['ImageId'])
            ec2_to_tag.append(instance_id)

            print 'Update tags on EC2 and AMI'
            print AMIid
            try:
                ec.create_tags(
                    Resources=ec2_to_tag,
                    Tags=[
                        {'Key': 'AMILASTBACKUP', 'Value': current_time_fmt},
                    ]
                )
            except Exception as ex:
                print ex
                pass

            try:
                ec.create_tags(
                    Resources=ami_to_tag,
                    Tags=[
                        {'Key': 'DELETEAFTER', 'Value': ami_del_date_fmt},
                        {'Key': 'CREATEDON', 'Value': current_time_fmt},
                    ]
                )
            except Exception as ex:
                print ex
                pass

    print ("Backup %d instances completed!" % (backupcount))




# Debug use, comment this out in lambda
#lambda_handler(1, 2)