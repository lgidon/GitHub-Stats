with metrics as (

    select * from {{ ref('int_pull_requests_metrics') }}

),

authors as (

    select
        author_username,
        author_type,
        
        -- Aggregate Metrics
        count(distinct pull_request_id) as total_prs_submitted,
        count(distinct case when is_merged then pull_request_id end) as total_prs_merged,
        
        -- Activity Windows
        min(created_at) as first_pr_created_at,
        max(created_at) as latest_pr_created_at,
        
        -- Performance Averages
        round(avg(time_to_merge_hours), 2) as avg_time_to_merge_hours

    from metrics
    group by 1, 2

)

select * from authors