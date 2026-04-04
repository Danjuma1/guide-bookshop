from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from .models import StaffProfile
from .decorators import module_required
import uuid


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated.')
                return render(request, 'accounts/login.html')
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next', '')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard')
        messages.error(request, 'Invalid credentials. Please try again.')
    return render(request, 'accounts/login.html', {'next': request.GET.get('next', '')})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('landing')


@login_required
@module_required('staff')
def staff_list(request):
    profiles = StaffProfile.objects.select_related('user').all()
    return render(request, 'accounts/staff_list.html', {'profiles': profiles})


@login_required
@module_required('staff')
def staff_add(request):
    requester_is_admin = request.user.is_superuser or (
        hasattr(request.user, 'staff_profile') and request.user.staff_profile.is_admin_level
    )
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'cashier')
        phone = request.POST.get('phone', '').strip()

        # Only admins can create admin-level accounts
        admin_roles = ('super_admin', 'admin')
        if role in admin_roles and not requester_is_admin:
            messages.error(request, "You don't have permission to create admin-level accounts.")
            return render(request, 'accounts/staff_form.html', {'action': 'Add'})

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = User.objects.create_user(
                username=username, email=email,
                first_name=first_name, last_name=last_name, password=password
            )
            emp_id = f"EMP-{str(uuid.uuid4())[:6].upper()}"
            StaffProfile.objects.create(user=user, role=role, phone=phone, employee_id=emp_id)
            messages.success(request, f'Staff member {first_name} {last_name} added successfully.')
            return redirect('staff_list')
    return render(request, 'accounts/staff_form.html', {'action': 'Add'})


@login_required
@module_required('staff')
def staff_edit(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    can_manage_modules = request.user.is_superuser or (
        hasattr(request.user, 'staff_profile') and request.user.staff_profile.role == 'admin'
    )
    if request.method == 'POST':
        profile.user.first_name = request.POST.get('first_name')
        profile.user.last_name = request.POST.get('last_name')
        profile.user.email = request.POST.get('email')
        profile.user.save()
        profile.role = request.POST.get('role')
        profile.phone = request.POST.get('phone')
        profile.is_active = 'is_active' in request.POST
        if can_manage_modules and profile.role != 'admin':
            modules = [m for m, _ in StaffProfile.MODULES]
            profile.module_permissions = {m: (f'mod_{m}' in request.POST) for m in modules}
        profile.save()
        messages.success(request, 'Staff profile updated.')
        return redirect('staff_list')
    modules_with_state = [
        (key, label, profile.has_module_access(key))
        for key, label in StaffProfile.MODULES
    ]
    return render(request, 'accounts/staff_form.html', {
        'profile': profile, 'action': 'Edit',
        'can_manage_modules': can_manage_modules,
        'modules_with_state': modules_with_state,
    })


@login_required
@module_required('staff')
def staff_delete(request, pk):
    if request.method == 'POST':
        profile = get_object_or_404(StaffProfile, pk=pk)
        if profile.user == request.user:
            messages.error(request, "You can't delete your own account.")
            return redirect('staff_list')
        # Prevent non-admins from deleting admin-level staff
        requester_is_admin = request.user.is_superuser or (
            hasattr(request.user, 'staff_profile') and request.user.staff_profile.is_admin_level
        )
        if profile.is_admin_level and not requester_is_admin:
            messages.error(request, "You don't have permission to delete an admin account.")
            return redirect('staff_list')
        profile.user.delete()
        messages.success(request, 'Staff member deleted.')
    return redirect('staff_list')


@login_required
def profile_view(request):
    try:
        profile = request.user.staff_profile
    except StaffProfile.DoesNotExist:
        profile = None
    return render(request, 'accounts/profile.html', {'profile': profile})
