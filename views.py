from django.shortcuts import render, redirect,HttpResponse, HttpResponseRedirect
from django.http import JsonResponse,HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from jobportal import settings
from django.core.mail import send_mail
from .models import User,jobseeker, recruiter, company, company_gallery, job, apply, Contact, Subscriber,Questions,User_answers,Attempt,notifications,Questions_upload,Study_materials
from datetime import date
from .filter import Jobfilter
import random
from django.db.models import Max,Sum,F
import re
from PyPDF2 import PdfReader
from django.conf import settings
import os
from django.core.files.storage import FileSystemStorage


# general views
def home(request):
    data=job.objects.all().order_by('-startdate')[:8]
    return render(request,'home.html', {'data':data})

def registration(request):
    return render(request,'registration.html')

def about(request):
    return render(request,'about.html')

def contacts(request):
    if request.method == 'POST':
        
        try:
            message = request.POST['message']
            name = request.POST['name']
            email = request.POST['email']
            subject = request.POST['subject']
            
            # Create a Contact instance and save it
            contact_instance = Contact.objects.create(
                message=message,
                name=name,
                email=email,
                subject=subject
            )
            
            # Sending email
            send_mail(subject, f"UserEmail :{email}\nUsername:{name}\n\n\n QUERY : {message}\n\n\nfaithfully\n{name}", email, [settings.EMAIL_HOST_USER], fail_silently=False)
            
            return render(request, 'contact.html', {'name': name})  
        except Exception as e:
           
            print(e)  
           
    return render(request, 'contact.html')  


def subscribe(request):
    if request.method == 'POST':
        print("Received POST request for subscription")
        email = request.POST.get('email')
        if email:
            subscriber = Subscriber(email=email)
            subscriber.save()
            return JsonResponse({'message': 'Thank you for subscribing!'})
        else:
            return JsonResponse({'error': 'Email is required'}, status=400)


def joblist(request):
    data=job.objects.all().order_by('-startdate')
    filter=Jobfilter(request.GET, queryset=job.objects.filter(is_available=True).order_by('-startdate'))
    return render(request,'joblist.html', {'filter':filter})

def loginpage(request):
    if request.method=='POST':
        email=request.POST.get('email')
        password=request.POST.get('password')
        user=authenticate(request, username=email, password=password)
        if user is not None and user.is_superuser == 1:
            login(request,user)
            request.session['id']=user.id
            return redirect('admin_home')
        elif user is not None and user.is_staff==1:
           login(request, user)
           request.session['recruiter_id']=user.id
           return redirect('recruiter_home')
        elif user is not None and user.usertype=='jobseeker':
           login(request, user)
           request.session['emp_id']=user.id
           return redirect('jobseeker_home')
        else:
            messages.warning(request,'something went wrong, Please try again!')
            return render(request, 'loginpage.html')
    else:
        return render(request,'loginpage.html')
    
def forgetpwd(request):
    if request.method == 'POST':
        sub = request.POST.get('Email')
        subject = 'Job Flnder - password Reset'
        message = 'Please click the link to reset your password http://127.0.0.1:8000/passwordreset'
        recepient = str(sub)
        send_mail(subject,
                  message, settings.EMAIL_HOST_USER, [recepient], fail_silently=False)
        messages.success(request, 'Please check your Email to reset password')
        return render(request, 'forgetpwd.html', {'recepient': recepient})
    return render(request,'forgetpwd.html')


def passwordreset(request):
    return render(request, 'passwordreset.html')     
    
def reset(request):
    if request.method == 'POST':
        if User.objects.filter(email=request.POST['commail'] ).exists():
            member = User.objects.get(email=request.POST['commail'])
            return render(request, 'reset.html',{'member': member})
        else:
            context = {'msg': 'Invalid Username '}
            return render(request, 'passwordreset.html', context)
        
def update(request, id):
    if request.method == 'POST':
        current_password = request.POST.get('compassword')
        confirm_password = request.POST.get('comconpassword')
        
        if current_password and confirm_password and current_password == confirm_password:
            try:
                member = User.objects.get(id=id)
                member.set_password(confirm_password)
                member.save()
                messages.success(request,'Password updated successfully. Please Login..')
                return redirect('loginpage') 
            except User.DoesNotExist:
                pass  
        return render(request, 'passwordreset.html')  
    else:
        return render(request, 'passwordreset.html') 
    
        
def logout_user(request):
    logout(request)
    messages.info(request,'your session has ended, Please Login to continue..')
    return redirect('loginpage')


# Jobseeker's module views

def jobseeker_register(request):
    if request.method =='POST':
        fname=request.POST['fname']
        lname=request.POST['lname']
        mail=request.POST['mail']
        uname=request.POST['uname']
        pwd=request.POST['pwd']
        phone=request.POST['phone']
        pics=request.FILES['pic']

        add=User.objects.create_user(first_name=fname, last_name=lname, email=mail, username=uname, password=pwd, usertype='jobseeker')
        add.save()
        s=jobseeker.objects.create(emp_id=add, phone=phone, image=pics)
        s.save()
        messages.info(request,'Your account has been created, Please login')
        return redirect('loginpage')
    else:      
        return render(request,'jobseeker_register.html')
    
def jobseeker_home(request):
    emp_id = request.session.get('emp_id', None)
    if emp_id is not None: 
        data=jobseeker.objects.get(emp_id=emp_id) 
        return render(request,'jobseeker_home.html',{'data':data})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    
def jobseeker_changepwd(request):
    emp_id = request.session.get('emp_id', None)
    if emp_id is not None:
        error1=""
        error2=""
        if request.method =='POST':
            currentpwd=request.POST['currentpwd']
            newpwd=request.POST['newpwd']
            u=User.objects.get(id=emp_id)
            if u.check_password(currentpwd):
                u.set_password(newpwd)
                u.save()
                error1='no'
                return render(request,'jobseeker_changepwd.html',{'error1':error1})
            else:
                error2='not'
                return render(request,'jobseeker_changepwd.html',{'error2':error2})
        else:
                return render(request,'jobseeker_changepwd.html')

    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def jobseeker_profile(request):
    emp_id = request.session.get('emp_id', None)
    if emp_id is not None:
        data=jobseeker.objects.get(emp_id=emp_id)
        if request.method =='POST':
            fname=request.POST['fname']
            lname=request.POST['lname']
            mail=request.POST['mail']
            uname=request.POST['uname']
            phone=request.POST['phone']

            if 'pic' in request.FILES:
                pics = request.FILES['pic']
                data.image = pics

            y=data.emp_id
            y.first_name=fname
            y.last_name=lname
            y.email=mail
            y.username=uname
            data.phone=phone
            data.save()
            y.save()

            error1='no'
            return render(request,'jobseeker_profile.html',{'error1':error1})
        else:
            return render(request,'jobseeker_profile.html', {'data':data})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    
    
def jobseeker_view_joblist(request):
    emp_id = request.session.get('emp_id', None)
    if emp_id is not None:
        data=job.objects.all().order_by('-startdate')
        filter=Jobfilter(request.GET, queryset=job.objects.filter(is_available=True).order_by('-startdate'))
        data2=jobseeker.objects.get(emp_id=emp_id)
        data1=apply.objects.filter(applicant=data2)
        li=[]
        for i in data1:
            li.append(i.jobapply_id.id)
        return render(request,'jobseeker_view_joblist.html',{'data':data, 'li':li, 'filter':filter})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    
def jobseeker_jobdetails(request, id):
    emp_id = request.session.get('emp_id', None)
    if emp_id is not None:
        job_data = get_object_or_404(job, id=id)
        ideal_candidate_list = job_data.ideal_candidate.split(',') 
        experience=job_data.experience.split(',')
        return render(request, 'jobseeker_jobdetail_view.html', {'job_data': job_data, 'ideal_candidate_list': ideal_candidate_list, 'experience':experience})
    else:
        messages.warning(request, 'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def jobseeker_applyjob(request, id):
    emp_id = request.session.get('emp_id', None)
    error1 = None  

    if emp_id is not None:
        seekers = jobseeker.objects.get(emp_id=emp_id)
        applyjob = job.objects.get(id=id)
        date1 = date.today()

        if applyjob.enddate < date1:
            error1 = 'close'
        else:
            if request.method == 'POST':
                cv = request.FILES['resume']
                add = apply.objects.create(applicant=seekers, jobapply_id=applyjob, resume=cv, applydate=date.today(), status='pending')
                add.save()
                error='no'
                return render(request, 'jobseeker_applyjob.html', {'error': error})

        return render(request, 'jobseeker_applyjob.html', {'error1': error1})
    else:
        messages.warning(request, 'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def jobseeker_view_company(request):
    emp_id = request.session.get('emp_id', None)
    if emp_id is not None:
        data=company.objects.all()
        return render(request,'jobseeker_view_company.html', {'data':data})
    else:
        messages.warning(request, 'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def jobseeker_view_companydetails(request,id):
    emp_id = request.session.get('emp_id', None)
    if emp_id is not None:
        data=company.objects.get(id=id)
        comp_id=data.id
        view=company_gallery.objects.filter(company_imgid=comp_id)
        return render(request,'jobseeker_view_companydetails.html', {'data':data, 'view':view})
    else:
        messages.warning(request, 'Invalid session data. Please log in again.')
        return redirect('loginpage')


def jobseeker_view_myjoblist(request):
    emp_id = request.session.get('emp_id', None)
    if emp_id is not None:
        seeker=jobseeker.objects.get(emp_id=emp_id)
        appliedjob = apply.objects.all().filter(applicant=seeker).order_by('-applydate')
        return render(request,'jobseeker_view_myjoblist.html',{'appliedjob':appliedjob})
    else:
        messages.warning(request, 'Invalid session data. Please log in again.')
        return redirect('loginpage')

    

# Recruiter module views

def recruiter_register(request):

    if request.method =='POST':
        fname=request.POST['fname']
        lname=request.POST['lname']
        mail=request.POST['mail']
        uname=request.POST['uname']
        pwd=request.POST['pwd']
        phone=request.POST['phone']
        pics=request.FILES['pic']
        compname=request.POST['cmpname']
        pos=request.POST['position']
        licence=request.FILES['licence'] 

        if User.objects.filter(username=uname).exists():
            return HttpResponse("<script>window.alert('Username already taken!');window.location.href='/recruiter_register'</script>")

        add=User.objects.create_user(first_name=fname, last_name=lname, email=mail, username=uname, password=pwd, usertype='recruiter', is_staff=False)
        add.save()
        s=recruiter.objects.create(recruiter_id=add, phone=phone,licence=licence, image=pics, companyname=compname, position=pos, status='pending')
        s.save()
        messages.warning(request,'Your Account is not approved now. Our Team is checking your profile, Soon your account will be confirmed !!!')
        return redirect('loginpage')
    return render(request,'recruiter_register.html')
  
  
def recruiter_home(request):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None: 
        data=recruiter.objects.get(recruiter_id=recruiter_id) 
        return render(request,'recruiter_home.html', {'data':data})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    
    
def recruiter_changepwd(request):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None: 
        error1=""
        error2=""
        if request.method =='POST':
            currentpwd=request.POST['currentpwd']
            newpwd=request.POST['newpwd']
            u=User.objects.get(id=recruiter_id)
            if u.check_password(currentpwd):
                u.set_password(newpwd)
                u.save()
                error1='no'
                return render(request,'recruiter_changepwd.html',{'error1':error1})
            else:
                error2='not'
                return render(request,'recruiter_changepwd.html',{'error2':error2})
        else:
                return render(request,'recruiter_changepwd.html')
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    
    
def recruiter_profile(request):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None: 
        data=recruiter.objects.get(recruiter_id=recruiter_id)
        if request.method =='POST':
            fname=request.POST['fname']
            lname=request.POST['lname']
            mail=request.POST['mail']
            uname=request.POST['uname']
            compname=request.POST['compname']
            position=request.POST['position']
            phone=request.POST['phone']

            if 'pic' in request.FILES:
                pics = request.FILES['pic']
                data.image = pics

            y=data.recruiter_id
            y.first_name=fname
            y.last_name=lname
            y.email=mail
            y.username=uname
            data.companyname=compname
            data.position=position
            data.phone=phone
            data.save()
            y.save()

            error1='no'
            return render(request,'recruiter_profile.html',{'error1':error1})
        else:
            return render(request,'recruiter_profile.html', {'data':data})            
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def recruiter_addcompany(request):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None: 
        if request.method =='POST':
            comptype=request.POST['comptype']
            pics=request.FILES['pic']
            mail=request.POST['mail']
            about=request.POST['about']
            city=request.POST['city']
            state=request.POST['state']
            date=request.POST['date']
            phone=request.POST['phone']
            
            logged_in_user = request.user
            recruiter_obj = recruiter.objects.get(recruiter_id=logged_in_user)
            s=company.objects.create(company_id=recruiter_obj, company_type=comptype, logo=pics, company_email=mail,
                                     about=about, city=city, state=state, est_date=date, company_phn=phone)
            s.save()
            success_message = "yes"
            return render(request,'recruiter_addcompany.html', {'success_message':success_message})
        else:
            return render(request,'recruiter_addcompany.html')
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    
def recruiter_company(request):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None: 
        data1=recruiter.objects.get(recruiter_id=recruiter_id)
        data_id=data1.id
        try:
            data=company.objects.get(company_id=data_id) 
        except company.DoesNotExist:
            error='yes'
            return render(request, 'recruiter_company.html', {'error': error})
        if request.method =='POST':
            companyname=request.POST['companyname']
            comptype=request.POST['comptype']
            mail=request.POST['mail']
            about=request.POST['about']
            city=request.POST['city']
            state=request.POST['state']
            phone=request.POST['phone']
            date=request.POST['date']

            if 'pic' in request.FILES:
                pics = request.FILES['pic']
                data.logo = pics
            else:
                pass

            if date:
                data.est_date=date
                data.save()
            else:
                pass

            y=data.company_id
            y.companyname=companyname
            
            data.company_type=comptype
            data.company_email=mail
            data.about=about
            data.city=city
            data.state=state
            data.company_phn=phone
            data.save()
            y.save()

            error1='no'
            return render(request,'recruiter_company.html',{'error1':error1}) 
        else:  
            return render(request,'recruiter_company.html', {'data':data})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    
def recruiter_company_gallery(request):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None:
        company_images=''
        current_recruiter=recruiter.objects.get(recruiter_id=recruiter_id)
        current_recruiter_id=current_recruiter.id
        try:
            current_company=company.objects.get(company_id=current_recruiter_id) 
            current_company_id=current_company.id
        except company.DoesNotExist:
            error='yes'
            return render(request, 'recruiter_company_gallery.html', {'error': error})

        if request.method == 'POST':
            uploaded_images = request.FILES.getlist('pic')
            for image in uploaded_images:
                new_image = company_gallery(
                    recruiter_imgid_id=current_recruiter_id,
                    company_imgid_id=current_company_id,
                    companyimage=image
                )
                new_image.save()

        company_images = company_gallery.objects.filter(company_imgid=current_company_id)
        return render(request, 'recruiter_company_gallery.html', {'company_images': company_images})
        
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')


def recruiter_postjob(request):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None:
        current_recruiter=recruiter.objects.get(recruiter_id=recruiter_id)
        current_recruiter_id=current_recruiter.id
        job_types = job.JOB_TYPES
        success_message=''
        try:
            current_company=company.objects.get(company_id=current_recruiter_id) 
            current_company_id=current_company.id
            
        except company.DoesNotExist:
            error='yes'
            return render(request, 'recruiter_postjob.html', {'error': error})
        
        if request.method =='POST':
            title=request.POST['title']
            enddate=request.POST['enddate']
            description=request.POST['description']
            requirements=request.POST['requirements']
            experience=request.POST['experience']
            job_type=request.POST['job_type']
            salary=request.POST['salary']
            location=request.POST['location']
            vaccancy=request.POST['vaccancy']
            
            add=job.objects.create(job_id=current_recruiter, job_compid=current_company, title=title, enddate=enddate, salary=salary,
                                   ideal_candidate=requirements ,experience=experience, description=description, job_type=job_type,
                                   location=location, vaccancy=vaccancy)
            add.save()
            success_message = "yes"
        return render(request, 'recruiter_postjob.html',{'job_types':job_types, 'success_message':success_message})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def recruiter_managejobs(request):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None: 
        userid=recruiter.objects.get(recruiter_id=recruiter_id)
        user=userid.id
        jobs=job.objects.filter(job_id=user).order_by('-startdate')
        return render(request,'recruiter_managejobs.html',{'jobs':jobs})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def recruiter_update_jobpost(request,id):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None:
        jobs=job.objects.get(id=id)
        job_types = job.JOB_TYPES

        if request.method =='POST':
            title=request.POST['title']
            enddate=request.POST['enddate']
            description=request.POST['description']
            requirements=request.POST['requirements']
            experience=request.POST['experience']
            job_type=request.POST['job_type']
            salary=request.POST['salary']
            location=request.POST['location']
            vaccancy=request.POST['vaccancy']

            jobs.title=title
            jobs.salary=salary
            jobs.description=description
            jobs.ideal_candidate=requirements
            jobs.experience=experience
            jobs.location=location
            jobs.vaccancy=vaccancy
            jobs.job_type=job_type
           
            jobs.save()

            if enddate:
                jobs.enddate=enddate
                jobs.save()
            else:
                pass

            if 'is_available' in request.POST:
                is_available_value = request.POST.get('is_available')
                if is_available_value == 'on':  # Checkbox is checked
                    jobs.is_available = True
                else:
                    jobs.is_available = False
            else:
               
                pass

            jobs.save()

            success_message = "yes"
            return render(request,'recruiter_update_jobpost.html', {'success_message':success_message})

        return render(request,'recruiter_update_jobpost.html',{'jobs':jobs, 'job_types':job_types})
    else:
            messages.warning(request,'Invalid session data. Please log in again.')
            return redirect('loginpage')
    

def recruiter_view_applications(request):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None: 
        userid=recruiter.objects.get(recruiter_id=recruiter_id)
        user=userid.id
        jobs=job.objects.filter(job_id=user)
        return render(request,'recruiter_view_applications.html',{'jobs':jobs})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def recruiter_view_listof_application(request,id):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None: 
        jobs=job.objects.get(id=id)
        applicants=jobs.apply_set.all().order_by('-applydate')

        return render(request,'recruiter_view_listof_application.html',{'jobs':jobs, 'applicants':applicants})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def recruiter_accept_applicant(request,id):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None: 
        job_application = apply.objects.get(id=id)
        job_application.status = 'Accepted'
        job_application.save()
        # Get the applicant's email
        applicant_email = job_application.applicant.emp_id.email
                
                # Get the email of the logged-in recruiter
        recruiter_email = request.user.email
                
                # Sending the email
        subject = 'Application Accepted'
        message = 'Your application has been accepted. Congratulations!'
        send_mail(subject, message, recruiter_email, [applicant_email], fail_silently=False)
                
        return redirect('recruiter_view_listof_application', id=job_application.jobapply_id.id)

    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def recruiter_reject_applicant(request,id):
    recruiter_id = request.session.get('recruiter_id', None)
    if recruiter_id is not None: 
        job_application = apply.objects.get(id=id)
        job_application.status = 'Declined'
        job_application.save()
        # Get the applicant's email
        applicant_email = job_application.applicant.emp_id.email
                
                # Get the email of the logged-in recruiter
        recruiter_email = request.user.email
                
                # Sending the email
        subject = 'Application Declined'
        message = 'Your application has been Declined. Better luck next time!'
        send_mail(subject, message, recruiter_email, [applicant_email], fail_silently=False)
                
        return redirect('recruiter_view_listof_application', id=job_application.jobapply_id.id)

    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')


#admin module views

def admin_home(request):
    id=request.session.get('id', None)
    if id is not None:
        #for cards
        total=jobseeker.objects.all().count()
        totalcount=recruiter.objects.all().count()
        jobs=job.objects.all().count()
        acceptedcount=recruiter.objects.all().filter(status='accepted').count()
        pendingcount=recruiter.objects.all().filter(status='pending').count()
        rejectcount=recruiter.objects.all().filter(status='rejected').count()

           #for table in admin dashboard
        provider=recruiter.objects.all().order_by('-id')
        candidate=jobseeker.objects.all().order_by('-id')
        return render(request,'admin_home.html',{'acceptedcount':acceptedcount, 'pendingcount':pendingcount, 
                                                 'totalcount':totalcount, 'rejectcount':rejectcount, 'jobs':jobs,
                                                 'total':total, 'provider':provider, 'candidate':candidate})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def admin_add_recruiter(request):
    id=request.session.get('id', None)
    if id is not None:
        if request.method =='POST':
            fname=request.POST['fname']
            lname=request.POST['lname']
            mail=request.POST['mail']
            uname=request.POST['uname']
            pwd=request.POST['pwd']
            phone=request.POST['phone']
            pics=request.FILES['pic']
            compname=request.POST['cmpname']
            pos=request.POST['position']

            add=User.objects.create_user(first_name=fname, last_name=lname, email=mail, username=uname, password=pwd, usertype='recruiter', is_staff=True)
            add.save()
            s=recruiter.objects.create(recruiter_id=add, phone=phone, image=pics, companyname=compname, position=pos, status='accepted')
            s.save()
            success_message = "yes"
            return render(request,'admin_add_recruiter.html',{'success_message':success_message})
        else:
            return render(request,'admin_add_recruiter.html')
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def admin_changepwd(request):
    id=request.session.get('id', None)
    if id is not None:
        error1=""
        error2=""
        if request.method =='POST':
            currentpwd=request.POST['currentpwd']
            newpwd=request.POST['newpwd']
            u=User.objects.get(id=id)
            if u.check_password(currentpwd):
                u.set_password(newpwd)
                u.save()
                error1='no'
                return render(request,'admin_changepwd.html',{'error1':error1})
            else:
                error2='not'
                return render(request,'admin_changepwd.html',{'error2':error2})
        else:
                return render(request,'admin_changepwd.html')
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def admin_view_pendingrecruiter(request):
    id=request.session.get('id', None)
    if id is not None:
        data=recruiter.objects.all().filter(status='pending').order_by('-id')
        return render(request,'admin_view_pendingrecruiter.html', {'data':data})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def admin_delete_pendingrecruiter(request,id):
    data=recruiter.objects.get(id=id)
    user_id =data.recruiter_id.id
    user_mail=data.recruiter_id.email
    data.delete()
    User.objects.filter(id=user_id).delete()
    user_email = user_mail
    if user_email:
        subject = ' Job Flnder - Account Deletion Notification'
        message = 'Your recruiter profile has been deleted.If you have any further question please contact us. ph:9879879879'
        to_email = user_email
        send_mail(subject, message, settings.EMAIL_HOST_USER,[to_email] )
        return redirect('admin_view_pendingrecruiter')
    

def admin_approve_pendingrecruiter(request,id):
    confirm=recruiter.objects.select_related('recruiter_id').get(id=id)
    confirm.recruiter_id.is_staff=True
    user_mail=confirm.recruiter_id.email
    confirm.recruiter_id.save()
    confirm.status='accepted'
    confirm.save()
    user_email = user_mail
    if user_email:
        subject = ' Job Flnder - Account confirmation Notification'
        message = 'Your recruiter profile has been confirmed.Now you can login to your account, If you have any further question please contact us. ph:9879879879'
        to_email = user_email
        send_mail(subject, message, settings.EMAIL_HOST_USER,[to_email] )
        return redirect('admin_view_pendingrecruiter')
    

def admin_reject_pendingrecruiter(request,id):
    confirm=recruiter.objects.select_related('recruiter_id').get(id=id)
    confirm.recruiter_id.is_staff=False
    user_mail=confirm.recruiter_id.email
    confirm.recruiter_id.save()
    confirm.status='rejected'
    confirm.save()
    user_email = user_mail
    if user_email:
        subject = ' Job Flnder - Account Rejection Notification'
        message = 'Your recruiter profile has been rejected. If you have any further question please contact us. ph:9879879879'
        to_email = user_email
        send_mail(subject, message, settings.EMAIL_HOST_USER,[to_email] )
        return redirect('admin_view_pendingrecruiter')
      
    
def admin_view_acceptedrecruiter(request):
    id=request.session.get('id', None)
    if id is not None:
        data=recruiter.objects.all().filter(status='accepted').order_by('-id')
        return render(request,'admin_view_acceptedrecruiter.html', {'data':data})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def admin_delete_acceptedrecruiter(request,id):
    data=recruiter.objects.get(id=id)
    user_id =data.recruiter_id.id
    user_mail=data.recruiter_id.email
    data.delete()
    User.objects.filter(id=user_id).delete()
    user_email = user_mail
    if user_email:
        subject = ' Job Flnder - Account Deletion Notification'
        message = 'Your recruiter profile has been deleted.If you have any further question please contact us. ph:9879879879'
        to_email = user_email
        send_mail(subject, message, settings.EMAIL_HOST_USER,[to_email] )
        return redirect('admin_view_acceptedrecruiter')
    

def admin_reject_acceptedrecruiter(request,id):
    confirm=recruiter.objects.select_related('recruiter_id').get(id=id)
    confirm.recruiter_id.is_staff=False
    user_mail=confirm.recruiter_id.email
    confirm.recruiter_id.save()
    confirm.status='rejected'
    confirm.save()
    user_email = user_mail
    if user_email:
        subject = ' Job Flnder - Account Rejection Notification'
        message = 'Your recruiter profile has been rejected. If you have any further question please contact us. ph:9879879879'
        to_email = user_email
        send_mail(subject, message, settings.EMAIL_HOST_USER,[to_email] )
        return redirect('admin_view_acceptedrecruiter')
    

def admin_pending_acceptedrecruiter(request,id):
    confirm=recruiter.objects.select_related('recruiter_id').get(id=id)
    confirm.recruiter_id.is_staff=False
    user_mail=confirm.recruiter_id.email
    confirm.recruiter_id.save()
    confirm.status='pending'
    confirm.save()
    user_email = user_mail
    if user_email:
        subject = ' Job Flnder - Account Pending Notification'
        message = 'Your recruiter profile has been pending. If you have any further question please contact us. ph:9879879879'
        to_email = user_email
        send_mail(subject, message, settings.EMAIL_HOST_USER,[to_email] )
        return redirect('admin_view_acceptedrecruiter')


def admin_view_rejectedrecruiter(request):
    id=request.session.get('id', None)
    if id is not None:
        data=recruiter.objects.all().filter(status='rejected').order_by('-id')
        return render(request,'admin_view_rejectedrecruiter.html', {'data':data})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def admin_delete_rejectedrecruiter(request,id):
    data=recruiter.objects.get(id=id)
    user_id =data.recruiter_id.id
    user_mail=data.recruiter_id.email
    data.delete()
    User.objects.filter(id=user_id).delete()
    user_email = user_mail
    if user_email:
        subject = ' Job Flnder - Account Deletion Notification'
        message = 'Your recruiter profile has been deleted.If you have any further question please contact us. ph:9879879879'
        to_email = user_email
        send_mail(subject, message, settings.EMAIL_HOST_USER,[to_email] )
        return redirect('admin_view_rejectedrecruiter')
    

def admin_approve_rejectedrecruiter(request,id):
    confirm=recruiter.objects.select_related('recruiter_id').get(id=id)
    confirm.recruiter_id.is_staff=True
    user_mail=confirm.recruiter_id.email
    confirm.recruiter_id.save()
    confirm.status='accepted'
    confirm.save()
    user_email = user_mail
    if user_email:
        subject = ' Job Flnder - Account confirmation Notification'
        message = 'Your recruiter profile has been confirmed.Now you can login to your account, If you have any further question please contact us. ph:9879879879'
        to_email = user_email
        send_mail(subject, message, settings.EMAIL_HOST_USER,[to_email] )
        return redirect('admin_view_rejectedrecruiter')
    

def admin_pending_rejectedrecruiter(request,id):
    confirm=recruiter.objects.select_related('recruiter_id').get(id=id)
    confirm.recruiter_id.is_staff=False
    user_mail=confirm.recruiter_id.email
    confirm.recruiter_id.save()
    confirm.status='pending'
    confirm.save()
    user_email = user_mail
    if user_email:
        subject = ' Job Flnder - Account Pending Notification'
        message = 'Your recruiter profile has been pending. If you have any further question please contact us. ph:9879879879'
        to_email = user_email
        send_mail(subject, message, settings.EMAIL_HOST_USER,[to_email] )
        return redirect('admin_view_rejectedrecruiter')
    

def admin_view_applicants(request):
    id=request.session.get('id', None)
    if id is not None:
        data=jobseeker.objects.all().order_by('-id')
        return render(request,'admin_view_applicants.html', {'data':data})
    else:
        messages.warning(request,'Invalid session data. Please log in again.')
        return redirect('loginpage')
    

def admin_delete_applicant(request,id):
    data=jobseeker.objects.get(id=id)
    user_id =data.emp_id.id
    user_mail=data.emp_id.email
    data.delete()
    User.objects.filter(id=user_id).delete()
    user_email = user_mail
    if user_email:
        subject = ' Job Flnder - Account Deletion Notification'
        message = 'Your jobseeker profile has been deleted.If you have any further question please contact us. ph:9879879879'
        to_email = user_email
        send_mail(subject, message, settings.EMAIL_HOST_USER,[to_email] )
        return redirect('admin_view_applicants')

    
#################### Aptitude #######################

#add questions                                             #currently not using
def Add_questions(request):
    if request.method == 'POST':
        Question=request.POST['questions']
        option_1=request.POST['option_1']
        option_2=request.POST['option_2']
        option_3=request.POST['option_3']
        option_4=request.POST['option_4']
        correct_answer=request.POST['answer']
        aptitude_questions = Questions.objects.create(Question=Question,option_1=option_1,option_2=option_2,option_3=option_3,option_4=option_4,correct_answer=correct_answer )
        aptitude_questions.save()   
        return HttpResponse("<script>window.alert('successfully saved');window.location.href='/add_questions/'</script>")
    else:
        return render(request, 'aptitude/insert_questions.html') 


############################ questions upload ##########################

# Upload questions
def questions_upload(request):
    """Handles file uploads for question datasets."""
    if request.method == 'POST':
        Q_file = request.FILES.get('q_file')  # Get the uploaded file

        if Q_file:
            # Define the target directory within MEDIA_ROOT
            upload_dir = os.path.join('uploaded_questions')
            full_upload_path = os.path.join(settings.MEDIA_ROOT, upload_dir)
            os.makedirs(full_upload_path, exist_ok=True)

            # Save the file in the specified directory
            file_path = os.path.join(upload_dir, Q_file.name)
            full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            with open(full_file_path, 'wb+') as destination:
                for chunk in Q_file.chunks():
                    destination.write(chunk)

            # Save the relative file path to the database
            Questions_upload.objects.create(Question_dataset=file_path)

            # Redirect to the display page after successful upload
            return redirect('display_questions_and_answers')
            # return HttpResponse("<script>window.alert('Successfully Saved');window.location.href='/questions_upload/'</script>")

        else:
            return HttpResponse('No file uploaded', status=400)
    else:
        return render(request, 'aptitude/upload_questions.html')


def question_extract(file_path):
    """Extract text from a PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def parse_questions_and_answers(text):
    """
    Parses questions and answers from the extracted text.

    Assumes the following format:
    1. Question: Starts with a number followed by a period or parenthesis.
    2. Answer Options: Labeled with 'A.', 'B.', 'C.', 'D.' (case insensitive).
    3. Answer Key: Mentioned explicitly, e.g., "Answer: B".
    """
    questions = []
    current_question = None
    lines = text.splitlines()

    question_pattern = re.compile(r"^\d+[\.\)]\s+(.*)")
    answer_pattern = re.compile(r"^(A|B|C|D)[\.\)]\s+(.*)", re.IGNORECASE)
    answer_key_pattern = re.compile(r"^Answer:\s*(\w)", re.IGNORECASE)

    for line in lines:
        line = line.strip()

        # Match question
        question_match = question_pattern.match(line)
        if question_match:
            if current_question:
                questions.append(current_question)
            current_question = {
                "question": question_match.group(1).strip(),
                "options": {},
                "answer": None
            }
            continue

        # Match answer options
        if current_question:
            answer_match = answer_pattern.match(line)
            if answer_match:
                current_question["options"][answer_match.group(1).upper()] = answer_match.group(2).strip()
                continue

            # Match the correct answer
            answer_key_match = answer_key_pattern.match(line)
            if answer_key_match:
                current_question["answer"] = answer_key_match.group(1).upper()

    # Add the last question
    if current_question:
        questions.append(current_question)

    return questions

def find_questions_and_answers_from_dataset():
    """
    Processes all uploaded question datasets and saves them to the database.
    Ensures each question is saved only once by checking for duplicates.
    """
    all_questions = []  # Store processed questions for debugging or display

    # Process each file uploaded
    for question_record in Questions_upload.objects.all():
        questions_path = question_record.Question_dataset.path
        if os.path.exists(questions_path):
            # Extract and parse questions
            extracted_text = question_extract(questions_path)
            questions = parse_questions_and_answers(extracted_text)

            for question_data in questions:
                # Get question and options
                question_text = question_data.get("question")
                options = question_data.get("options", {})
                correct_answer = question_data.get("answer")

                # Ensure all fields are available
                if question_text and options and correct_answer:
                    option_1 = options.get("A", "")
                    option_2 = options.get("B", "")
                    option_3 = options.get("C", "")
                    option_4 = options.get("D", "")

                    # Check if the question already exists
                    if not Questions.objects.filter(
                        Question=question_text,
                        option_1=option_1,
                        option_2=option_2,
                        option_3=option_3,
                        option_4=option_4,
                        correct_answer=correct_answer,
                    ).exists():
                        # Save to the database
                        aptitude_question = Questions.objects.create(
                            Question=question_text,
                            option_1=option_1,
                            option_2=option_2,
                            option_3=option_3,
                            option_4=option_4,
                            correct_answer=correct_answer,
                        )
                        all_questions.append(aptitude_question)

    return all_questions

# Example usage in a Django view
def display_questions_and_answers(request):
    extracted_data = find_questions_and_answers_from_dataset()
    return render(request, 'aptitude/view_uploaded__datasets.html', {'questions': extracted_data})




#start test
def start_question(request):
    if request.method == 'POST':
        attemptid= Attempt.objects.create(user_id=102)
        attemptid.save()
        max_attempt_id = Attempt.objects.aggregate(Max('Attempt_id'))['Attempt_id__max']
        print("ma ==== Attempt_id ->",max_attempt_id)
        request.session['Attempt_id']=max_attempt_id
        return redirect('questions')
        
    else:
        return render(request,'aptitude/start_question.html')


#questions
def questions(request):
    attempt_id=request.session['Attempt_id']
    attempt=Attempt.objects.get(Attempt_id=attempt_id)
    if request.method == "POST":
        answer = request.POST.get("Aptitude")
        Question_num_id = request.POST.get("Question_num")
        count = Questions.objects.filter(Question_num=Question_num_id, correct_answer=answer).count()
        if count:
            marks = 1
        else:
            marks = 0
        Question_num=Questions.objects.get(Question_num=Question_num_id)
        total_marks = User_answers.objects.filter(Attempt_id=attempt).aggregate(total=Sum('mark'))['total']
        if total_marks is None:
            total_marks = 0
        attempt.obtained_marks = total_marks
        attempt.save()
        user = User_answers.objects.create(Attempt_id = attempt,question_id = Question_num,answer = answer,mark=marks)
        user.save()
        return redirect('questions')
    else:
        count = User_answers.objects.filter(Attempt_id=attempt_id).count()
        if count<15:
            # Subquery to get question IDs from UsersAnswer
            subquery = User_answers.objects.filter(Attempt_id_id=attempt_id).values_list('question_id', flat=True)
            # Filter AptitudeQuestions where Question_num is not in the subquery
            questions = Questions.objects.exclude(Question_num__in=subquery)
            # all_questions
            next_question = random.choice(questions)
            return render(request,'aptitude/questions.html',{'question':next_question,'qno':count+1})
        else:
            return redirect('results')

        
#results
def results(request):
    attempt_id = request.session.get('Attempt_id')
    if not attempt_id:
        return redirect('questions')
    user_answers = User_answers.objects.filter(Attempt_id=attempt_id)
    total_attempted = user_answers.count()
    correct_answers = user_answers.filter(answer=F('question_id__correct_answer')).count()
    score_percentage = (correct_answers / total_attempted) * 100 if total_attempted > 0 else 0
    return render(request, 'aptitude/results.html', {'total_attempted': total_attempted,'correct_answers': correct_answers,'percentage':round(score_percentage, 2)})

# #manage questions

def manage_questions(request):
    questions = Questions.objects.all()
    count = questions.count()
    a = 0
    while a < count:
        a += 1
    return render(request, 'aptitude/questions_table.html', {'questions': questions, 'count': count})

#delete
def delete_questions(request,o):
    question=Questions.objects.get(Question_num = o)
    question.delete()
    return redirect('manage_questions')

#edit
def edit_questions(request,o):
    question = Questions.objects.get(Question_num=o)
    return render(request,'aptitude/edit_questions.html',{'question':question})
#update
def update_questions(request,o):
    question=Questions.objects.get(Question_num = o)
    question.Question=request.POST.get('Question')
    question.option_1=request.POST.get('option_1')
    question.option_2=request.POST.get('option_2')
    question.option_3=request.POST.get('option_3')
    question.option_4=request.POST.get('option_4')
    question.correct_answer=request.POST.get('answer')
    question.save()
    return redirect('manage_questions')

##########################################

#add_notifications
def add_notifications(request):
    if request.method == 'POST':
        title = request.POST ['title']
        description = request.POST ['description']
        salary_package = request.POST ['salary_package']
        number_of_postings= request.POST ['number_of_postings']
        date = request.POST['date']
        job_type = request.POST['job_type']
        experience = request.POST['experience']
        location = request.POST['location']
        skills = request.POST['skills']
        qualification = request.POST['qualifications']
        link = request.POST['link']
        notification = notifications.objects.create(title=title,description=description,salary_package=salary_package,
        number_of_postings=number_of_postings,date=date, job_type=job_type,experience=experience,location=location,skills=skills,
        qualification=qualification,link=link)
        notification.save()
        return HttpResponse("<script>window.alert('successfully saved');window.location.href='/add_notifications/'</script>")
    else:
        return render(request,'notification/add_notification.html')


# view notifications
def view_notifications(request):
    notification = notifications.objects.all().order_by('-created_date')
    return render(request,'notification/view_notifications.html',{'note':notification})  


# detailed notifications
def notification_details(request, o): 
    notification = notifications.objects.get(note_id=o)   
    if notification:
        return render(request, 'notification/notification_details.html', {'notification': notification})
    else:
        return HttpResponse ('404 ERROR')



##################  admin notification settings ###################

def admin_view_notification(request):
    # detail = notifications.objects.all()
    detail = notifications.objects.all().order_by('-created_date')
    return render(request,'notification/admin_table.html',{'detail':detail})


#edit notifications
def edit_notifications(request,o):
    details = notifications.objects.get(note_id = o)
    return render(request, 'notification/edit_notification.html', {'details': details})


#update notification
def update_notification(request,o):
    detail = notifications.objects.get(note_id=o)
    detail.title = request.POST.get('title')
    detail.description = request.POST.get('description')
    detail.number_of_postings = request.POST.get('number_of_postings')
    detail.salary_package = request.POST.get('salary_package')
    detail.date = request.POST.get('date')
    detail.job_type = request.POST.get('job_type')
    detail.experience = request.POST.get('experience')
    detail.skills = request.POST.get('skills')
    detail.location = request.POST.get('location')
    detail.qualification = request.POST.get('qualification')
    detail.link = request.POST.get('link')
    detail.save()
    return HttpResponse("<script>window.alert('successfully saved');window.location.href='/admin_view_notifications/'</script>")


#delete notification
def delete_notifications(request, o):
    data = notifications.objects.get(note_id=o)
    data.delete()
    return redirect('admin_view_notification')

##################################################


import os
from PyPDF2 import PdfReader
from django.db.models import Q

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def find_matching_applicants_with_emails(keywords):
    """Find applicants matching keywords and return their email IDs."""
    matching_applicants  = set()
    keyword_set = set(keywords.lower().split())  # Convert keywords to a set for efficient comparison

    # Iterate through all applications
    for application in apply.objects.select_related('applicant__emp_id'):  # Optimize query with related data
        resume_path = application.resume.path  # Get the full path of the resume
        if os.path.exists(resume_path):
            # Extract text from the resume
            resume_text = extract_text_from_pdf(resume_path).lower()
            # Check for keyword matches
            if keyword_set & set(resume_text.split()):  # Intersection of keyword and resume words
                email = application.applicant.emp_id.email  # Get the applicant's email ID
                matching_applicants.add((
                     application.applicant.id,
                     email
                ))

    return list(matching_applicants)



# Email filtering
def recruiter_filter_jobseekers(request):
    recruiter_id = request.session.get('recruiter_id', None)
    print("...................................")
    
    if request.method == 'POST':    
        keywords=request.POST ['content']
        print(',,,,,,,,,,,,,,,,,',keywords)

        if recruiter_id is not None: 
            matching_applicants  = find_matching_applicants_with_emails(keywords)
            # print("Matching Jobseeker IDs:", matching_ids)
            print('----------------',matching_applicants) 
            for jobseeker_id, email in matching_applicants:
                print(f"Jobseeker ID: {jobseeker_id}, Email: {email}")
                # Get the applicant's email
                applicant_email = email
                        # Get the email of the logged-in recruiter
                recruiter_email = request.user.email
                        # Sending the email
                subject = 'Application Accepted'
                message = 'Your application has been accepted. Congratulations!'
                send_mail(subject, message, recruiter_email, [applicant_email], fail_silently=False)
                return HttpResponse("<script>window.alert('Mail Send Successfully');window.location.href='/recruiter_filter_jobseekers/'</script>")
            return HttpResponse("<script>window.alert('Mail Filtering Unsuccessfull');window.location.href='/recruiter_filter_jobseekers/'</script>")
    else:    
        return render(request,'recruiter_jobseekers_mail.html')  



############### study materials upload & download ###############

#upload
def study_materials(request):
    if request.method == 'POST':
        # Retrieve file and category from the request
        S_file = request.FILES['s_file']
        category = request.POST['category']
        file_category = request.POST['file_category']

        # Define the target directory within MEDIA_ROOT
        upload_dir = os.path.join('uploaded_study_materials', category)

        # Use FileSystemStorage to save the file
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, upload_dir))  
        filename = fs.save(S_file.name, S_file)
        file_path = fs.path(filename)

        # Save the file path in the database
        add = Study_materials.objects.create(study_files=os.path.join(upload_dir, filename))
        add.file_name = category
        add.file_category = file_category
        add.save()
        return HttpResponse("<script>window.alert('Successfully Uploaded');window.location.href='/study_materials/'</script>") 
    else:
        return render(request,'aptitude/upload_study_materials.html')   


#download study materials 
def download_study_materials(request):
    files_by_name = {}
    study_materials = Study_materials.objects.all()
    for material in study_materials:
        category = material.file_name
        if category not in files_by_name:
            files_by_name[category] = []
        files_by_name[category].append(material)
    return render(request, 'aptitude/download_study_materials.html', {'files_by_name': files_by_name, 'year': 2025})


