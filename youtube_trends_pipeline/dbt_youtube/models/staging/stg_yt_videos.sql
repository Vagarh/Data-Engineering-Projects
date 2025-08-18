-- models/staging/stg_yt_videos.sql
SELECT
    video_id,
    TO_DATE(trending_date, 'YY.DD.MM') AS trending_date, -- Convert to proper date format
    title,
    channel_title,
    category_id,
    publish_time,
    tags,
    views,
    likes,
    dislikes,
    comment_count,
    thumbnail_link,
    comments_disabled,
    ratings_disabled,
    video_error_or_removed,
    description
FROM
    {{ source('public', 'raw_youtube_videos') }} -- Assuming raw data lands in 'public.raw_youtube_videos'
