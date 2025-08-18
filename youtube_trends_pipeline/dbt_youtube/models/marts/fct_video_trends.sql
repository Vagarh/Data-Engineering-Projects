-- models/marts/fct_video_trends.sql
SELECT
    video_id,
    trending_date,
    title,
    channel_title,
    category_id,
    views,
    likes,
    dislikes,
    comment_count,
    -- Calculate engagement rate (likes + dislikes + comments) / views
    (likes + dislikes + comment_count) * 1.0 / views AS engagement_rate,
    -- Extract day of the week
    TRIM(TO_CHAR(trending_date, 'Day')) AS trending_day_of_week
FROM
    {{ ref('stg_yt_videos') }}
WHERE
    views > 0 -- Avoid division by zero for engagement_rate
