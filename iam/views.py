from django.shortcuts import render
from django.contrib.auth import logout
from django.http.response import HttpResponse, HttpResponseRedirect
from iam.models import *
from iam.forms import *
import json
import boto3
from django.core.urlresolvers import reverse
from botocore.exceptions import ClientError


def home(request):
    '''
    Authored by:Swetha
    Other Modules Involved:
    Description:when user hits the url "^home/$" this function is called
    This function renders to "base" template,
    After log in with thier Access keys and Secret Keys.
    '''
    return render(request, "base.html")


def user_logout(request):
    '''
    Authored by:Swetha
    Other Modules Involved:
    Tasks Involved:Logout
    Description:when user hits the url "^/logout$" this function is called, user gets logged out and redirected to login template.
    Here when user log out respective user access key, secret key, username will be removed from session.
    '''
    if 'access_key' in request.session:
        request.session['access_key'] = None
    if 'secret_key' in request.session:
        request.session['secret_key'] = None
    if 'client_username' in request.session:
        request.session['client_username'] = None
    logout(request)
    return HttpResponseRedirect('/')


def login(request):
    '''
    Authored by:Swetha
    Other Modules Involved:
    Tasks Involved:login
    Description:when user hits the url "^$" this function is called
    First this function renders to "login" template,
    Here user login by entering valid access key and secret keys, then these varibles are stored in django session for further use.
    '''

    if request.method == "POST":
        client = boto3.client(
           'iam',
           aws_access_key_id=request.POST.get("access_key"),
           aws_secret_access_key=request.POST.get("secret_key")
        )
        try:
            if request.POST.get("access_key") and request.POST.get("secret_key") and request.POST.get("username"):
                if 'access_key' not in request.session:
                    request.session['access_key'] = request.POST.get("access_key")
                if 'secret_key' not in request.session:
                    request.session['secret_key'] = request.POST.get("secret_key")
                if 'client_username' not in request.session:
                    request.session['client_username'] = request.POST.get("username")
                client.get_user(UserName=request.POST.get("username"))

                data = {"error": False}
            else:
                data = {"error": True, "response": "Please Enter Username, Access key, Secret Key."}
            return HttpResponse(json.dumps(data))

        except ClientError as e:
            data = {"error": True, "response": str(e)}
            return HttpResponse(json.dumps(data))
    if 'access_key' in request.session:
        return HttpResponseRedirect(reverse("home"))
    return render(request, "login.html")


def add_iam_user(request):
    '''
    Authored by:Swetha
    Other Modules Involved:
    Tasks Involved:Add IAM User
    Description:when user hits the url "^iam/user/add/$" this function is called
    First this function renders to "add_iam_user" template,
    New IAM user can create only when User updated settings(Access key, secret Keys).
    Connecting to boto3 IAM client with AWS Access key and Secret Keys.
    when post data is requested, new IAM user is created, when user selects to generate access and
    secret keys then acess keys are generated and saved in our database.
    '''
    client = boto3.client(
       'iam',
       aws_access_key_id=request.session["access_key"],
       aws_secret_access_key=request.session["secret_key"]
    )

    # client_ec2 = boto3.client(
    #    'ec2', region_name="us-west-2",
    #    aws_access_key_id=request.session["access_key"],
    #    aws_secret_access_key=request.session["secret_key"]
    # )

    # incomplete code will be impleted later.
    # ec2 = boto3.resource(
    #    'ec2',
    #    region_name="us-west-2",
    #    aws_access_key_id=request.session["access_key"],
    #    aws_secret_access_key=request.session["secret_key"]
    # )

    # client_s3 = boto3.client(
    #     's3',
    #     aws_access_key_id=request.session["access_key"],
    #     aws_secret_access_key=request.session["secret_key"])

    # response_buckets = client_s3.list_buckets()

    # response_inst = client_ec2.describe_instances(
    #         DryRun=False,
    #         Filters=[],
    #         MaxResults=6
    #     )
    if request.method == "POST":
        if request.POST.get("username"):
            try:
                client.create_user(Path="/", UserName=request.POST.get("username"))
                if request.POST.get("generate_keys"):
                    client.create_access_key(UserName=request.POST.get("username"))
                data = {"error": False}
            except ClientError as e:
                data = {"error": True, "response": "Please enter IAM User Name"}
            return HttpResponse(json.dumps(data))
        else:
            data = {"error": True, "response": "Please enter IAM User Name"}
        return HttpResponse(json.dumps(data))
    # return render(request, "iam_user/add_iam_user.html", {"response_inst": response_inst["Reservations"],
    #               "response_buckets": response_buckets["Buckets"]})
    return render(request, "iam_user/add_iam_user.html")


def iam_users_list(request):
    '''
    Authored by:Swetha
    Other Modules Involved:
    Tasks Involved:Add IAM User List
    Description:when user hits the url "^iam/user/list/$" this function is called
    First this function renders to "iam_users_list" template,
    Connecting to boto3 IAM client, Displays all IAM Users.
    '''
    client = boto3.client(
       'iam',
       aws_access_key_id=request.session["access_key"],
       aws_secret_access_key=request.session["secret_key"]
    )
    response = client.list_users()
    return render(request, "iam_user/iam_users_list.html", {"response": response["Users"]})


def iam_user_detail(request, user_name):
    '''
    Authored by:Swetha
    Other Modules Involved:
    Tasks Involved:Add IAM User Detail
    Description:when user hits the url "^iam/user/detail/$" this function is called
    First this function renders to "iam_users_list" template,
    Connecting to boto3 IAM client, Display details of specific IAM User.
    '''
    client = boto3.client(
       'iam',
       aws_access_key_id=request.session["access_key"],
       aws_secret_access_key=request.session["secret_key"]
    )

    if request.GET.get("generate_keys"):
        response = client.create_access_key(UserName=user_name)
        return HttpResponseRedirect(reverse("iam_user_detail", kwargs={'user_name': user_name}))

    response = client.get_user(UserName=user_name)

    user_policies = client.list_attached_user_policies(
        UserName=response["User"]["UserName"]
    )

    user_access_keys = client.list_access_keys(
        UserName=response["User"]["UserName"],
    )

    return render(request, "iam_user/iam_user_detail.html", {"response": response["User"],
                  "user_policies": user_policies["AttachedPolicies"],
                  "user_name": user_name, "user_access_keys": user_access_keys["AccessKeyMetadata"]})


def iam_user_change_password(request, user_name):
    '''
    Authored by:Swetha
    Other Modules Involved:
    Tasks Involved:Change password of IAM User
    Description:when user hits the url "^iam/user/change-password/username/$" this function is called
    First this function renders to "change_password" template,
    Connecting to boto3 IAM client, Checks whether the new password and confirm password matches, if not raises an error if not save the data.
    '''
    client = boto3.client(
       'iam',
       aws_access_key_id=request.session["access_key"],
       aws_secret_access_key=request.session["secret_key"]
    )
    if request.method == 'POST':
        if request.POST.get("new_pwd") and request.POST.get("confirm_pwd"):
            if request.POST.get("new_pwd") != request.POST.get("confirm_pwd"):
                data = {"error": True, 'response': "Confirm Password should match with Password."}
                return HttpResponse(json.dumps(data))
            elif request.POST.get("new_pwd") == request.POST.get("confirm_pwd"):

                client.create_login_profile(
                    UserName=user_name,
                    Password=request.POST.get("new_pwd"),
                    PasswordResetRequired=False
                )
                data = {"error": False}
                return HttpResponse(json.dumps(data))
        else:
            data = {'error': True, 'response': "Please enter new password and confirm password."}
            return HttpResponse(json.dumps(data))
    return render(request, 'iam_user/change_password.html')


def policies_list(request, user_name):
    '''
    Authored by:Swetha
    Other Modules Involved:
    Tasks Involved:Policies list
    Description:when user hits the url "^policies/username/$" this function is called
    First this function renders to "policies" template,
    Connecting to boto3 IAM client,when user can attach multiple policies.
    '''
    client = boto3.client(
       'iam',
       aws_access_key_id=request.session["access_key"],
       aws_secret_access_key=request.session["secret_key"]
    )
    response = client.list_policies(
            Scope='All',
            OnlyAttached=False,
            MaxItems=10
            )
    if request.method == "POST":
        for policy in request.POST.getlist("policy"):
            client.attach_user_policy(
                UserName=user_name,
                PolicyArn=policy
            )
        return HttpResponseRedirect(reverse("iam_user_detail", kwargs={'user_name': user_name}))
    return render(request, "policies.html", {"response": response["Policies"], "user_name": user_name})


def detach_user_policies(request, user_name):
    '''
    Authored by:Swetha
    Other Modules Involved:
    Tasks Involved:Policy detach
    Description:when user hits the url "^iam-userpolicy/detach/username/$" this function is called
    First this function renders to 'iam_user_detail' template,
    Connecting to boto3 IAM client,detach policy for the particular user.
    '''
    client = boto3.client(
       'iam',
       aws_access_key_id=request.session["access_key"],
       aws_secret_access_key=request.session["secret_key"]
    )

    client.detach_user_policy(
        UserName=user_name,
        PolicyArn=request.GET.get("policy_arn")
    )
    return HttpResponseRedirect(reverse("iam_user_detail", kwargs={'user_name': user_name}))