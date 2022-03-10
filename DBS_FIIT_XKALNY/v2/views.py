from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from DBS_FIIT_XKALNY.connection import *
# Create your views here.
def patches(request):
    cursor = conn.cursor()
    cursor.execute("SELECT x.name as patch_version, x.patch_start_date, x.patch_end_date, matches.id as match_id"
                   ", ROUND(matches.duration*1.0/60,2) as duration FROM matches "
                   "JOIN (SELECT patches.name, EXTRACT(epoch from patches.release_date) as patch_start_date"
                   ",COALESCE(EXTRACT(epoch from (lead(patches.release_date) over (ORDER BY patches.release_date))),"
                   "EXTRACT(epoch from CURRENT_DATE)) as patch_end_date FROM patches as patches) as x "
                   "ON matches.start_time BETWEEN x.patch_start_date and x.patch_end_date"
                   " ORDER BY x.name")
    data = cursor.fetchall()
    print(data[0])
    print(len(data))
    # return [a + [b[1]] for (a, b) in zip(lst1, lst2)]
    #test = [a + [b[1], b[2]] for (a, b) in zip(data[0], data[1])]]
    result = {"patches": []}
    procc_patches= []
    length = len(data)
    i = 0
    while i < length:
        row = data[i]
        patch_name = data[i][0]
        # najdem prvy nespracovany patch, teda vsetky zapasy z predosleho patchu uz skoncili
        if patch_name not in procc_patches:
            prev_patch_name = patch_name
            procc_patches.append(patch_name)
            matches = list()
            # zaznamenam prvy match
            matches.append({"match_id": row[3], "duration": row[4]})
            i += 1
            if i <length:
                patch_name = data[i][0]
            # prechadzam dalsie riadky pokial nenajdem novy patch
            while patch_name in procc_patches and i < length:
                next_row = data[i]
                matches.append({"match_id": next_row[3], "duration": next_row[4]})
                i += 1
                if i < length:
                    patch_name = data[i][0]
            # vsetky informacie o patchi a matchov v nom si ulozim a pokracujem dalej
            result["patches"].append({
                "patch_version": prev_patch_name,
                "patch_start_date": row[1],
                "patch_end_date": row[2],
                "matches": matches
            })

    print(result)
    #return HttpResponse(data)
    return JsonResponse(result)
