from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse
from v4.models import *
from django.db.models import Sum, F, Value, Case, When, Q, TextField
from django.db.models.functions import Coalesce, Cast


def index(request):
    test = Matches.objects.using('dota2').filter(id=69)
    # player = Players.objects.get(id=14944).select_related('')
    mpd = MatchesPlayersDetails.objects.using('dota2')\
        .filter(player=14944).select_related('hero', 'player', 'match').\
        annotate(experiences_gained=Coalesce(F('xp_hero'), Value(0))+ Coalesce(F('xp_creep'), Value(0))+
                                    Coalesce(F('xp_other'), Value(0)) + Coalesce(F('xp_roshan'), Value(0)),
                 winner=Case(
                    When(Q(match__radiant_win=True) & Q(player_slot__gte=0) & Q(player_slot__lte=4), then=Value(True)),
                    When(Q(match__radiant_win=True) & Q(player_slot__gt=4), then=Value(False)),
                    When(Q(match__radiant_win=False) & Q(player_slot__lte=4), then=Value(False)),
                    When(Q(match__radiant_win=False) & Q(player_slot__gt=4), then=Value(True))
                ),
                nick=Coalesce('player__nick', Cast(Value('unknown'), output_field=TextField())))
    print(mpd[0].player_slot)
    for a in mpd:
        print(a.match.radiant_win, a.player_slot, a.winner)
    print(mpd[0].winner)
    print(mpd[0].experiences_gained)
    print(mpd[0].hero.localized_name)
    result = {
        "id": 14944,
        "player_nick": mpd[0].nick,
        "matches": []
    }
    for match in mpd:
        result["matches"].append({
            "match_id": match.match.id,
            "hero_localized_name": match.hero.localized_name,
            "match_duration_minutes": match.match.duration/60,
            "level_gained": match.level,
            "winner": match.winner
        })
    return JsonResponse(result)

def v3_3endpoint(request):
    mpd = MatchesPlayersDetails.objects.using('dota2').filter(player=14944).select_related('match', 'hero', 'game_objectives')
    return HttpResponse("JO")

