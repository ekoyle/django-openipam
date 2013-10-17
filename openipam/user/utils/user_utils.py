from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group as AuthGroup, Permission
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.timezone import utc

from guardian.shortcuts import assign_perm
from guardian.models import UserObjectPermission, GroupObjectPermission

from django_auth_ldap.backend import LDAPBackend

from openipam.user.models import Permission, Group, UserToGroup, HostToGroup
from openipam.hosts.models import HostGroupObjectPermission, HostUserObjectPermission

from datetime import datetime
import gc

User = get_user_model()


def get_objects_for_owner(user, app_label):
    owner_perm = Permission.objects.get(content_type__app_label=app_label, name='Is owner')
    content_type = owner_perm.content_type
    model_class = content_type.model_class()
    user_objects = UserObjectPermission.objects.filter(user=user, content_type=content_type,
                                                       permission=owner_perm).values_list('object_pk')
    user_objects = [obj[0] for obj in user_objects]
    return model_class.objects.filter(pk__in=user_objects)


def convert_groups():
    groups = Group.objects.all()

    for group in groups:
        if not group.name.lower().startswith('user_'):
            AuthGroup.objects.create(name=group.name)


def convert_host_permissions(delete=False):
    # First delete to make a clean slate
    if delete:
        owner_perm = Permission.objects.get(content_type__app_label='hosts', codename='is_owner_host')
        HostUserObjectPermission.objects.filter(permission=owner_perm).delete()
        HostGroupObjectPermission.objects.filter(permission=owner_perm).delete()

    host_groups = (HostToGroup.objects.prefetch_related('group__group_users')
             .filter(mac__expires__gte=timezone.now))

    for host_group in queryset_iterator(host_groups):
        # Convert User Permissions (Group = user_A0000000)
        if host_group.group.name.lower().startswith('user_'):
            users = host_group.group.group_users.select_related().all()
            for user in users:
                username = user.user.username
                #is_anumber = True if username.split('a')[-1].isdigit() else False

                # Convert owner permissions becuase thats all there is
                if user.host_permissions.name == 'OWNER':
                    #ry:
                    auth_user, created = User.objects.get_or_create(username__iexact=username)
                    # except User.DoesNotExist:
                    #     auth_user = User(username=username)
                    #     auth_user.set_unusable_password()
                    #     auth_user.save()

                    # If these are local accounts, disable for now
                    # if not is_anumber:
                    #     auth_user.active = False
                    #     auth_user.save()
                    if not auth_user.has_perm('is_owner_host', host_group.mac):
                        print 'Assigning owner permission to user %s for mac %s \n' % (auth_user, host_group.mac)
                        assign_perm('is_owner_host', auth_user, host_group.mac)
                else:
                    continue
        else:
            auth_group, created = AuthGroup.objects.get_or_create(name=host_group.group.name)
            if not auth_user.has_perm('is_owner_host', host_group.mac):
                print 'Assigning owner permission to group %s for mac %s \n' % (auth_group, host_group.mac)
                assign_perm('is_owner_host', auth_group, host_group.mac)


def populate_user_from_ldap():
    users = User.objects.all()
    ldap_backend = LDAPBackend()
    for user in users:
        if not user.first_name or not user.last_name or not user.email:
            ldap_user = ldap_backend.populate_user(username=user.username)
            if ldap_user:
                ldap_user.save()


# Not needed anymore because we switched django user model
# def convert_users():
#     users = User.objects.all()
#     for user in queryset_iterator(users):
#         auth_user, created = AuthUser.objects.get_or_create(
#             username=user.username.lower()
#         )
#         if created:
#             auth_user.active = False
#             auth_user.set_unusable_password()
#             auth_user.save()


# def convert_groups():
#     groups = Groups.objects.all()

#     for group in groups:


def queryset_iterator(queryset, chunksize=1000):
    '''''
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.
    '''
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()
