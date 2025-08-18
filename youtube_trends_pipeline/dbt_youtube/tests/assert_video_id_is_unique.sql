-- tests/assert_video_id_is_unique.sql
SELECT
    video_id
FROM
    {{ ref('stg_yt_videos') }}
GROUP BY
    video_id
HAVING
    COUNT(*) > 1
