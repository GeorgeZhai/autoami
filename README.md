# autoami


AWS IAM policy for Lambda
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:*"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "ec2:Describe*",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateImage",
                "ec2:DeregisterImage",
                "ec2:CreateSnapshot",
                "ec2:ModifySnapshotAttribute",
                "ec2:ResetSnapshotAttribute",
                "ec2:DeleteSnapshot",
                "ec2:CreateTags"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}