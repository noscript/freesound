# -*- coding: utf-8 -*-

#
# Freesound is (c) MUSIC TECHNOLOGY GROUP, UNIVERSITAT POMPEU FABRA
#
# Freesound is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Freesound is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     See AUTHORS file.
#

from sounds.models import Sound
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from rest_framework import serializers
import yaml


###############
# GENERAL UTILS
###############

def prepend_base(rel):
    return "http://%s%s" % (Site.objects.get_current().domain, rel)


###################
# SOUND SERIALIZERS
###################

DEFAULT_FIELDS_IN_SOUND_LIST = 'url,uri'  # Separated by commas (None = all)
DEFAULT_FIELDS_IN_SOUND_DETAIL = None  # Separated by commas (None = all)


class AbstractSoundSerializer(serializers.HyperlinkedModelSerializer):
    '''
    In this abstract class we define ALL possible fields that a sound object should serialize/deserialize.
    Inherited classes set the default fields that will be shown in each view, although those can be altered using
    the 'fields' request parameter.
    '''
    default_fields = None

    def __init__(self, *args, **kwargs):
        super(AbstractSoundSerializer, self).__init__(*args, **kwargs)
        requested_fields = kwargs['context']['request'].GET.get("fields", self.default_fields)
        if requested_fields:
            allowed = set(requested_fields.split(","))
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    class Meta:
        model = Sound
        fields = ('id',
                  'uri',
                  'url',
                  'original_filename',
                  'user',
                  'num_downloads',
                  'channels',
                  'duration',
                  'samplerate',
                  'analysis')


    uri = serializers.SerializerMethodField('get_uri')
    def get_uri(self, obj):
        return prepend_base(reverse('apiv2-sound-detail', args=[obj.id]))

    url = serializers.SerializerMethodField('get_url')
    def get_url(self, obj):
        return prepend_base(reverse('sound', args=[obj.user.username, obj.id]))

    user = serializers.SerializerMethodField('get_user')
    def get_user(self, obj):
        return prepend_base(reverse('apiv2-user-detail', args=[obj.user.id]))

    analysis = serializers.SerializerMethodField('get_analysis')
    def get_analysis(self, obj):
        try:
            # TODO: control selected descriptors with a request parameter. Current implementation is just to test
            analysis = yaml.load(file(obj.locations('analysis.statistics.path')))
            return analysis['lowlevel']['spectral_centroid']['mean']
        except Exception, e:
            return None


class SoundListSerializer(AbstractSoundSerializer):

    def __init__(self, *args, **kwargs):
        self.default_fields = DEFAULT_FIELDS_IN_SOUND_LIST
        super(SoundListSerializer, self).__init__(*args, **kwargs)


class SoundSerializer(AbstractSoundSerializer):

    def __init__(self, *args, **kwargs):
        self.default_fields = DEFAULT_FIELDS_IN_SOUND_DETAIL
        super(SoundSerializer, self).__init__(*args, **kwargs)


##################
# USER SERIALIZERS
##################


class UserSerializer(serializers.HyperlinkedModelSerializer):
    uri = serializers.SerializerMethodField('get_uri')
    url = serializers.SerializerMethodField('get_url')
    sounds = serializers.HyperlinkedIdentityField(view_name='apiv2-user-sound-list')

    class Meta:
        model = User
        fields = ('id',
                  'uri',
                  'url',
                  'username',
                  'date_joined',
                  'sounds')

    def get_url(self, obj):
        return prepend_base(reverse('account', args=[obj.username]))

    def get_uri(self, obj):
        return prepend_base(reverse('apiv2-user-detail', args=[obj.id]))