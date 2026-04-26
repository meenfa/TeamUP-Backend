import django_filters

from common.constants import GameStatus, SkillLevel

from .models import Game


class GameFilter(django_filters.FilterSet):
    area_city = django_filters.CharFilter(lookup_expr='icontains')
    skill_level = django_filters.ChoiceFilter(choices=SkillLevel.choices)
    status = django_filters.ChoiceFilter(choices=GameStatus.choices)
    game_date = django_filters.DateFilter()
    game_date_after = django_filters.DateFilter(field_name='game_date', lookup_expr='gte')
    game_date_before = django_filters.DateFilter(field_name='game_date', lookup_expr='lte')

    class Meta:
        model = Game
        fields = ['area_city', 'skill_level', 'status', 'game_date']
