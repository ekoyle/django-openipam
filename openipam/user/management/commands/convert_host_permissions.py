from django.core.management.base import BaseCommand, CommandError
from openipam.user.utils.user_utils import convert_host_permissions
from optparse import make_option


class Command(BaseCommand):
    args = ''
    help = 'Convert User Permissions'


    option_list = BaseCommand.option_list + (
        make_option('--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete poll instead of closing it'),
        )

    def handle(self, *args, **options):
        delete = options['delete']
        convert_host_permissions(delete)
        self.stdout.write('Converting Host Permissions...')
