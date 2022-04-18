# DBS SERVER

https://fiit-dbs-xkalny-app.azurewebsites.net

## Query k zadaniu 3

## 1. endpoint

```sql
SELECT x.name as patch_version, x.patch_start_date, x.patch_end_date, matches.id as match_id
,ROUND(matches.duration*1.0/60,2) as duration FROM matches
RIGHT JOIN (
    SELECT patches.name, EXTRACT(epoch from patches.release_date) as patch_start_date
    ,EXTRACT(epoch from (lead(patches.release_date) over (ORDER BY patches.release_date)))
    as patch_end_date FROM patches as patches) as x
ON matches.start_time BETWEEN x.patch_start_date and x.patch_end_date
ORDER BY x.name
```

## 2. endpoint

```sql
SELECT players.id, COALESCE(players.nick,'unknown'), heroes.localized_name, ROUND(matches.duration*1.0/60,2),
SUM(COALESCE(mpd.xp_hero,0)+COALESCE(mpd.xp_creep,0)+COALESCE(mpd.xp_other,0)+COALESCE(mpd.xp_roshan,0))
AS experiences_gained, mpd.level as level_gained, matches.id as match_id,
CASE matches.radiant_win
WHEN true and mpd.player_slot >=0 and mpd.player_slot <= 4 then true
WHEN true and mpd.player_slot > 4 then false
WHEN false and mpd.player_slot <= 4 then false
WHEN false  and mpd.player_slot > 4 then true END as winner
FROM players JOIN matches_players_details as mpd ON players.id = mpd.player_id
JOIN matches on mpd.match_id = matches.id JOIN heroes ON mpd.hero_id = heroes.id
WHERE players.id = {id_hraca}
GROUP BY players.id, players.nick, heroes.localized_name, matches.duration, mpd.level,
matches.radiant_win, matches.id, mpd.player_slot ORDER BY match_id
```

## 3. endpoint

```sql
SELECT players.id as player_id, COALESCE(players.nick,'unknown') as player_nick,
heroes.localized_name, matches.id as match_id, COALESCE(gob.subtype,'NO_ACTION') as hero_action,
count(COALESCE(gob.subtype,'NO_ACTION')) FROM players
JOIN matches_players_details as mpd ON mpd.player_id = players.id
JOIN matches ON mpd.match_id = matches.id
JOIN heroes ON mpd.hero_id = heroes.id
FULL JOIN game_objectives as gob ON
gob.match_player_detail_id_1 = mpd.id
WHERE players.id = {id_hraca}
GROUP BY  players.id, heroes.localized_name, matches.id, gob.subtype
ORDER BY matches.id
```

## 4. endpoint

```sql
SELECT players.id as player_id, COALESCE(players.nick,'unknown') as player_nick,
heroes.localized_name, matches.id as match_id, abilities.name as ability_name,
count(abilities.name), max(au.level) as upgrade_level FROM players
JOIN matches_players_details as mpd ON mpd.player_id = players.id
JOIN matches ON mpd.match_id = matches.id
JOIN heroes ON mpd.hero_id = heroes.id
JOIN ability_upgrades as au ON au.match_player_detail_id = mpd.id
JOIN abilities ON au.ability_id = abilities.id
WHERE players.id = {id_hraca}
GROUP BY  matches.id, players.id, heroes.localized_name,abilities.name
ORDER BY matches.id, abilities.name
```

# Query k zadaniu 5

## 1. endpoint

```sql
SELECT hero_id, localized_name, array_agg(tbl.item_id  || ','||name ||',' ||            purchases||'') FROM (
   SELECT * FROM (
    SELECT heroes.id as hero_id,heroes.localized_name, items.name, items.id as                 item_id, count(items.name) as purchases,
        row_number() over (partition by pl.match_player_detail_id ORDER BY                     COUNT(items.name) DESC, items.name) as row_num 
          FROM matches_players_details AS mpd
          JOIN matches ON mpd.match_id = matches.id
          JOIN purchase_logs AS pl ON mpd.id = pl.match_player_detail_id
          JOIN items ON pl.item_id = items.id
          JOIN heroes ON mpd.hero_id = heroes.id
          WHERE mpd.match_id = {match_id} AND((matches.radiant_win = true AND                         mpd.player_slot BETWEEN 0 AND 4) OR ( matches.radiant_win = false AND                 mpd.player_slot BETWEEN 128 AND 132))
   GROUP BY heroes.id, items.name, heroes.localized_name, items.id,                     pl.match_player_detail_id
   ORDER BY heroes.id, purchases DESC 
    ) as fin
  WHERE fin.row_num <= 5 ORDER BY hero_id, row_num 
  ) as tbl
 GROUP BY hero_id, localized_name 
```

## 2. endpoint

```sql
SELECT id,localized_name, ability_name, winner, bucket, count FROM (
    SELECT *, rank() over (partition by winner,localized_name, ability_name             ORDER BY count DESC) FROM (
            SELECT *,COUNT(tbl.bucket) as count 
            FROM (
                SELECT heroes.id,heroes.localized_name,abilities.name as                                 ability_name,
                    CASE 
                        WHEN matches.radiant_win = true and mpd.player_slot                                 between 0 and 4 then 'winner'
                        WHEN matches.radiant_win = false and mpd.player_slot                                 between 128 and 132 then 'winner'
                        ELSE 'loser'
                        END as winner,
                    CASE 
                        WHEN FLOOR(au.time*1.0/matches.duration*100) between 0                                 and 9 then '0-9'
                        WHEN FLOOR(au.time*1.0/matches.duration*100) between 10                             and 19 then '10-19'
                        WHEN FLOOR(au.time*1.0/matches.duration*100) between 20                             and 29 then '20-29'
                        WHEN FLOOR(au.time*1.0/matches.duration*100) between 30                             and 39 then '30-39'
                        WHEN FLOOR(au.time*1.0/matches.duration*100) between 40                             and 49 then '40-49'
                        WHEN FLOOR(au.time*1.0/matches.duration*100) between 50                             and 59 then '50-59'
                        WHEN FLOOR(au.time*1.0/matches.duration*100) between 60                             and 69 then '60-69'
                        WHEN FLOOR(au.time*1.0/matches.duration*100) between 70                             and 79 then '70-79'
                        WHEN FLOOR(au.time*1.0/matches.duration*100) between 80                             and 89 then '80-89'
                        WHEN FLOOR(au.time*1.0/matches.duration*100) between 90                             and 99 then '90-99'
                        WHEN FLOOR(au.time*1.0/matches.duration*100) >= 100 then                             '100-109'
                     END as bucket
                     FROM abilities
                     JOIN ability_upgrades as au ON abilities.id = au.ability_id
                     JOIN matches_players_details as mpd ON mpd.id =                                      au.match_player_detail_id
                     JOIN matches ON matches.id= mpd.match_id
                     JOIN heroes ON mpd.hero_id = heroes.id
                     WHERE abilities.id = {ability_id}
                 ) as tbl
        GROUP BY tbl.id, tbl.winner, tbl.localized_name, tbl.ability_name,                     tbl.bucket
         ORDER BY count DESC
        ) as table2 
    ) as table3 
    WHERE rank=1 ORDER BY id, winner DESC 
```

## 3. endpoint

```sql
SELECT hero_id, localized_name, MAX(count) FROM (
    SELECT localized_name, hero_id, count(localized_name) over (partition by  			match_id, hero_id, seq) 
    FROM (
        SELECT localized_name, hero_id,a,b, (a-b) as seq, match_id 
        FROM (
            SELECT heroes.localized_name, heroes.id as hero_id, mpd.match_id,                     go.time,
            row_number() over (partition by mpd.match_id order by go.time) as a,
            row_number() over (partition by  heroes.id, mpd.match_id order by                     go.time) as b
            FROM heroes
            JOIN matches_players_details as mpd ON mpd.hero_id = heroes.id
            JOIN game_objectives as go ON go.match_player_detail_id_1 = mpd.id  or                 go.match_player_detail_id_2 = mpd.id
            WHERE go.subtype = 'CHAT_MESSAGE_TOWER_KILL'
            ORDER BY mpd.match_id, go.time
        ) as tbl
    ) as f
     ORDER BY count DESC, localized_name
) as g
 GROUP BY localized_name, hero_id
 ORDER BY max DESC, localized_name
```
